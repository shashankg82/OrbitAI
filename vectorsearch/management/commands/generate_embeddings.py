from django.conf import settings
from django.core.management.base import BaseCommand
from vectorsearch.models import Persona
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import os



class Command(BaseCommand):
    help = "Generate embeddings for all personas and upload to Pinecone"

    def handle(self, *args, **kwargs):
        # -----------------------------
        # Load Hugging Face model
        # -----------------------------
        model = SentenceTransformer('all-MiniLM-L6-v2')
        self.stdout.write(self.style.SUCCESS("Model loaded successfully."))

        # -----------------------------
        # Initialize Pinecone
        # -----------------------------
        
        PINECONE_API_KEY = settings.PINECONE_API_KEY
        PINECONE_ENV = settings.PINECONE_ENV  # e.g., "us-east1-gcp"

        pc = Pinecone(api_key=settings.PINECONE_API_KEY)

        index_name = "index1"
        if index_name not in [i.name for i in pc.list_indexes()]:
            pc.create_index(
                name=index_name,
                dimension=384,  # all-MiniLM-L6-v2 embedding size
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV)
            )

        index = pc.Index(index_name)

        # -----------------------------
        # Generate embeddings and upsert
        # -----------------------------
        personas = Persona.objects.all()
        total = personas.count()
        self.stdout.write(f"Generating embeddings for {total} personas...")

        for i, persona in enumerate(personas, start=1):
            if not persona.embedding:
                embedding_vector = model.encode(persona.bio)
                persona.embedding = embedding_vector.tolist()
                persona.save()

                # Upsert to Pinecone
                index.upsert(
                    vectors=[(
                        str(persona.id),
                        embedding_vector.tolist(),
                        {"name": persona.name, "job_role": persona.job_role}
                    )]
                )
                self.stdout.write(f"[{i}/{total}] Generated & uploaded embedding for {persona.name}")

        self.stdout.write(self.style.SUCCESS("✅ All embeddings generated and uploaded to Pinecone!"))
