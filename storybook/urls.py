from django.urls import path
from . import views

app_name = "storybook"

urlpatterns = [
    path("create/", views.create_storybook, name="create_storybook"),
    path("preview/<uuid:storybook_id>/", views.preview_storybook, name="preview_storybook"),
    path("download/<uuid:storybook_id>/", views.download_pdf, name="download_pdf"),
]