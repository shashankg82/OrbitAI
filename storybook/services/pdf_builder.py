
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4, letter

def build_pdf(storybook, pages, output_path, font_family="Helvetica", font_size=12):
    page_size_value = (getattr(storybook, "page_size", None)
                       or (storybook.settings or {}).get("page_size", "A4"))
    page_size = A4 if str(page_size_value).upper() == "A4" else letter

    doc = SimpleDocTemplate(output_path, pagesize=page_size)
    elements = []

    custom_style = ParagraphStyle(
        "Custom",
        fontName=font_family,
        fontSize=font_size,
        leading=font_size + 2,
    )
    title_style = ParagraphStyle(
        "Title",
        fontName=font_family,
        fontSize=font_size + 10,
        leading=font_size + 14,
        alignment=1,  # center
    )
    desc_style = ParagraphStyle(
        "Description",
        fontName=font_family,
        fontSize=font_size + 2,
        leading=font_size + 4,
        spaceBefore=20,
        spaceAfter=40,
        alignment=1,  # center
    )

    # --- Title Page ---
    elements.append(Spacer(1, 100))
    elements.append(Paragraph(storybook.title, title_style))
    if storybook.description:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(storybook.description, desc_style))
    elements.append(PageBreak())


    for i, page in enumerate(pages):
        if page.kind == "TEXT" and page.text_content:
            elements.append(Paragraph(page.text_content, custom_style))
        elif page.kind == "IMAGE" and page.image_file:
            elements.append(Image(page.image_file.path, width=400, height=400))

        if i != len(pages) - 1:
            elements.append(PageBreak())

    doc.build(elements)
    return output_path
