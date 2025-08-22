from django.urls import path
from . import views

urlpatterns = [
    path('vectorsearch/', views.search_personas, name='search_personas'),
    path('download_json/', views.download_json, name='download_json'),
]