from django.shortcuts import render
from vectorsearch.models import Persona
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import os
from django.conf import settings
from django.http import FileResponse


PINECONE_INDEX_NAME = getattr(settings, "PINECONE_INDEX_NAME", "index1")
PINECONE_NAMESPACE = getattr(settings, "PINECONE_NAMESPACE", None)  


model = SentenceTransformer('all-MiniLM-L6-v2')
pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

def _normalize_hobbies(h):
    if isinstance(h, list):
        return h
    if isinstance(h, str):
        
        parts = [p.strip() for p in h.split(",") if p.strip()]
        return parts if parts else [h]
    return []

def compute_compatibility(score, persona, query_filters):
    
    compatibility = float(score) * 100.0
    for field, value in query_filters.items():
        
        if hasattr(persona, field) and getattr(persona, field) == value:
            compatibility += 5
    return min(compatibility, 100.0)

def generate_insight(persona, query_filters):
    insights = []
    for field, value in query_filters.items():
        if hasattr(persona, field) and getattr(persona, field) == value:
            if field == "smoker":
                insights.append("Non-smoker as requested." if value is False else "Smoker as requested.")
            else:
                insights.append(f"{field.capitalize()}: {getattr(persona, field)}")
    insights.append(f"Expertise: {persona.job_role}")
    hobbies_list = _normalize_hobbies(persona.hobbies)
    if hobbies_list:
        insights.append(f"Hobbies: {', '.join(hobbies_list)}")
    return " | ".join(insights)

def search_personas(request):
    query = request.GET.get('q', '') or ''
    filter_smoker = request.GET.get('smoker', None)

    # Structured filters
    query_filters = {}
    if filter_smoker:
        query_filters['smoker'] = (filter_smoker.lower() == 'true')

    results = []

    
    if not query:
        
        return render(request, "vectorsearch/search.html", {
            "results": results,
            "query": query,
            "smoker": filter_smoker,  
        })

    # 1) Vector search
    query_embedding = model.encode(query).tolist()

    pinecone_kwargs = dict(
        vector=query_embedding,
        top_k=50,
        include_metadata=True,
        include_values=False,
    )
    if PINECONE_NAMESPACE:
        pinecone_kwargs["namespace"] = PINECONE_NAMESPACE

    try:
        pinecone_results = index.query(**pinecone_kwargs)
    except Exception as e:
        
        return render(request, "vectorsearch/search.html", {
            "results": [],
            "query": query,
            "smoker": filter_smoker,
            "error": f"Pinecone query error: {e}",
        })

    matches = pinecone_results.get("matches", []) or []
    if not matches:
        return render(request, "vectorsearch/search.html", {
            "results": [],
            "query": query,
            "smoker": filter_smoker,
            "info": "No vector matches found. Check your namespace/index IDs and that vectors are upserted.",
        })

    # 2) Map Pinecone IDs → scores
    candidate_ids = [m.get("id") for m in matches if m.get("id") is not None]
    scores_dict = {m.get("id"): m.get("score", 0.0) for m in matches}

    # 3) Fetch matching personas
    numeric_ids = []
    for pid in candidate_ids:
        try:
            numeric_ids.append(int(pid))
        except (TypeError, ValueError):
            pass

    personas_qs = Persona.objects.none()
    if numeric_ids:
        personas_qs = Persona.objects.filter(id__in=numeric_ids)

    # CASE B: If you used a custom Pinecone ID (e.g., "persona_42"), add a pinecone_id field to Persona
    
    if query_filters:
        personas_qs = personas_qs.filter(**query_filters)

    personas = list(personas_qs)

    # 4) Sort by Pinecone similarity score (defensively)
    def persona_score(p):
        key = str(p.id)
        return scores_dict.get(key, 0.0)

    personas.sort(key=persona_score, reverse=True)

    # 5) Build response
    for persona in personas:
        score = persona_score(persona)
        compatibility = compute_compatibility(score, persona, query_filters)
        insight = generate_insight(persona, query_filters)

        results.append({
            "name": persona.name,
            "bio": persona.bio,
            "job_role": persona.job_role,
            "location": getattr(persona, "location", ""),
            "smoker": getattr(persona, "smoker", None),
            "hobbies": _normalize_hobbies(getattr(persona, "hobbies", [])),
            "compatibility": f"{compatibility:.2f}%",
            "insight": insight
        })

    return render(request, "vectorsearch/search.html", {
        "results": results,
        "query": query,
        "smoker": filter_smoker,
    })

def download_json(request):
    app_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(app_dir, 'orbitai.json')
    return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='orbitai.json')
