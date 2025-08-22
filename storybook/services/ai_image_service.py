
import os
import uuid
import logging
from typing import Optional

from django.conf import settings
from django.core.files import File

from .image_generator import generate_images
from ..models import Page

logger = logging.getLogger(__name__)


class AIImageService:
    def __init__(
        self,
        output_dir: str = "storybook/generated_images",
        timeout: int = 120,
        max_retries: int = 1,
    ):
        
        self.output_dir = output_dir.strip("/")
        self.media_root = getattr(settings, "MEDIA_ROOT", os.path.join(os.getcwd(), "media"))
        self.timeout = timeout
        self.max_retries = max_retries

    def _build_output_path(self) -> str:
        
        fname = f"{uuid.uuid4().hex}.png"
        dir_path = os.path.join(self.media_root, self.output_dir)
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, fname)

    def generate_for_page(self, page: Page) -> Optional[str]:
        
        if page.kind != "IMAGE":
            raise ValueError("AIImageService.generate_for_page: page.kind must be 'IMAGE'.")

        if not page.image_prompt:
            raise ValueError("AIImageService.generate_for_page: page.image_prompt is empty.")

        page.gen_status = "RUNNING"
        page.gen_error = ""
        page.save(update_fields=["gen_status", "gen_error"])

        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                tmp_path = self._build_output_path()

                
                final_path = generate_images(
                    prompt=page.image_prompt,
                    output_path=tmp_path,
                    timeout=self.timeout,
                )

                
                filename = os.path.basename(final_path)
                with open(final_path, "rb") as fp:
                    page.image_file.save(filename, File(fp), save=False)

                page.gen_status = "READY"
                page.save(update_fields=["image_file", "gen_status"])

                
                try:
                    os.remove(final_path)
                except Exception:
                    logger.debug("Could not remove temp file: %s", final_path)

                return filename

            except Exception as e:
                last_error = str(e)
                logger.exception(
                    "Image generation failed (attempt %s/%s): %s",
                    attempt + 1, self.max_retries + 1, last_error
                )

                if attempt < self.max_retries:
                    continue  # retry

               
                page.gen_status = "ERROR"
                page.gen_error = (last_error or "Unknown error")[:500]
                page.save(update_fields=["gen_status", "gen_error"])
                return None

    def generate_for_storybook(self, storybook_id) -> int:
        """
        Generate images for all IMAGE pages in a storybook that are still pending.
        :returns: Count of pages successfully generated.
        """
        qs = Page.objects.filter(
            storybook_id=storybook_id,
            kind="IMAGE",
            gen_status__in=["PENDING", "ERROR"],  # retry errored ones if desired
        ).order_by("index")

        success = 0
        for page in qs:
            if self.generate_for_page(page):
                success += 1
        return success
