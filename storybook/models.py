
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Story(models.Model):
    class SourceType(models.TextChoices):
        PASTE = "PASTE", "Paste"
        PDF = "PDF", "PDF"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        GENERATING = "GENERATING", "Generating"
        READY = "READY", "Ready"
        ERROR = "ERROR", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True, default="")
    source_type = models.CharField(max_length=8, choices=SourceType.choices)
    source_text = models.TextField(blank=True)
    source_pdf = models.FileField(upload_to="storybook/sources/", blank=True, null=True)
    page_count = models.PositiveIntegerField(default=0)
    settings = models.JSONField(default=dict)  
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_by", "-created_at"]),
        ]

    def __str__(self):
        return self.title or f"Story {self.id}"


class Page(models.Model):
    class Kind(models.TextChoices):
        TEXT = "TEXT", "Text"
        IMAGE = "IMAGE", "Image"

    class GenStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        READY = "READY", "Ready"
        ERROR = "ERROR", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    
    storybook = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="pages")

    index = models.PositiveIntegerField()

    kind = models.CharField(max_length=8, choices=Kind.choices)

    text_content = models.TextField(blank=True, null=True)

    image_prompt = models.TextField(blank=True, null=True)
    image_prompt_negative = models.TextField(blank=True, null= True)

    seed = models.BigIntegerField(default=0)

    image_file = models.ImageField(upload_to="storybook/pages/", blank=True, null=True)

    gen_status = models.CharField(max_length=8, choices=GenStatus.choices, default=GenStatus.PENDING)
    gen_error = models.TextField(blank=True, null = True)

    image_meta = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("storybook", "index")]
        indexes = [
            models.Index(fields=["storybook", "index"]),
            models.Index(fields=["storybook", "gen_status"]),
            models.Index(fields=["kind"]),
        ]

    def __str__(self):
        return f"{self.storybook_id}#{self.index}:{self.kind}"

    def generate_ai_image(self):
      
        if self.kind != Page.Kind.IMAGE:
            return None
        from .services.ai_image_service import AIImageService  
        svc = AIImageService()
        return svc.generate_for_page(self)


class Export(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        READY = "READY", "Ready"
        ERROR = "ERROR", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    storybook = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="exports")
    pdf_file = models.FileField(upload_to="storybook/exports/")
    page_size = models.CharField(max_length=16, default="A4")
    dpi = models.PositiveIntegerField(default=300)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Export {self.id} for {self.storybook_id}"


class ImageJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="jobs")

    provider = models.CharField(max_length=50, default="hf_sdxl")
    request_payload = models.JSONField(default=dict)
    response_payload = models.JSONField(default=dict, blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    cost_cents = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["page"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"ImageJob {self.id} [{self.status}]"
