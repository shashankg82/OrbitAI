from .text_splitter import split_text_into_chunks
from ..models import Page
from .ai_image_service import AIImageService

service = AIImageService()
def create_storybook_from_text(storybook,text):
    chunks = split_text_into_chunks(text, max_words= 200)

    for i,chunk in enumerate(chunks):
        Page.objects.create(
            storybook = storybook,
            index = 2*i,
            kind = "TEXT",
            text_content = chunk
        )

        image_page = Page.objects.create(
            storybook=storybook,
            index=2 * i + 1,       # odd index = image page
            kind="IMAGE",
            image_prompt=chunk,    # prompt for AI image generation
            gen_status="PENDING"
        )

        service.generate_for_page(image_page)