# storybook/views.py
from pathlib import Path
import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction


from .models import Story, Page  
from .services.storybook_pipeline import create_storybook_from_text
from .services.pdf_builder import build_pdf
from .services.pdf_extractor import extract_text_from_pdf  
from .services.ai_image_service import AIImageService


@csrf_exempt
@require_http_methods(["GET", "POST"])
def create_storybook(request):
    if request.method == "GET":
        return render(request, "storybook/create_storybook.html")

   
    title = request.POST.get("title") or "Untitled"
    description = request.POST.get("description", "")
    text = request.POST.get("text", "") or ""
    pdf = request.FILES.get("pdf")

    
    if pdf:
        try:
            source_text = extract_text_from_pdf(pdf)
            source_type = Story.SourceType.PDF
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"PDF read failed: {e}"}, status=400)
    else:
        source_text = text.strip()
        source_type = Story.SourceType.PASTE

    if not source_text:
        return JsonResponse({"status": "error", "message": "Provide text or upload a PDF."}, status=400)

    # Creating story 
    story = Story.objects.create(
        title=title,
        description=description,
        source_type=source_type,
        source_text=source_text,
        settings={"page_size": "A4", "font_family": "Helvetica", "font_size": 12},
        status=Story.Status.GENERATING,
    )

    # Building pages (TEXT + IMAGE prompts)
    try:
        create_storybook_from_text(story, source_text)
        story.page_count = story.pages.count()
        story.save(update_fields=["page_count", "status"])
    except Exception as e:
        story.status = Story.Status.ERROR
        story.save(update_fields=["status"])
        return JsonResponse({"status": "error", "message": f"Pipeline failed: {e}"}, status=500)

    image_page_ids = list(
        story.pages.filter(kind="IMAGE", gen_status="PENDING").values_list("id", flat=True)
    )
    service = AIImageService()

    def _kick_off():
        for pid in image_page_ids:
            try:
                page = Page.objects.get(id=pid)  
                service.generate_for_page(page)
            except Exception:
                continue

    transaction.on_commit(_kick_off)

    return JsonResponse({"status": "success", "storybook_id": str(story.id)})


def preview_storybook(request, storybook_id):
    """Renders a preview with alternating Text → Image."""
    story = get_object_or_404(Story, id=storybook_id)
    pages = story.pages.all().order_by("index")
    context = {"storybook": story, "pages": pages}
    return render(request, "storybook/preview.html", context)


@csrf_exempt
def download_pdf(request, storybook_id):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid request: POST required"},
            status=405,
        )

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
        font_family = data.get("font_family", "Helvetica")
        try:
            font_size = int(data.get("font_size", 12))
        except (TypeError, ValueError):
            return JsonResponse(
                {"status": "error", "message": "font_size must be an integer"},
                status=400,
            )

        story = get_object_or_404(Story, id=storybook_id)
        pages = story.pages.all().order_by("index")

        # Build output path under MEDIA_ROOT
        output_dir = Path(settings.MEDIA_ROOT) / "storybooks"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"storybook_{story.id}.pdf"

        build_pdf(
            storybook=story,
            pages=pages,
            output_path=str(output_path),
            font_family=font_family,
            font_size=font_size,
        )

        pdf_url = f"{settings.MEDIA_URL.rstrip('/')}/storybooks/storybook_{story.id}.pdf"
        return JsonResponse({"status": "success", "pdf_url": pdf_url})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
