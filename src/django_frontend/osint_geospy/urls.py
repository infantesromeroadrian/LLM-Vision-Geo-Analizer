from django.urls import path
from . import views

app_name = 'osint_geospy'

urlpatterns = [
    path('', views.index, name='index'),
    path('image-analysis/', views.image_analysis, name='image_analysis'),
    path('analyze-image/', views.analyze_image, name='analyze_image'),
    path('drone-stream/', views.drone_stream, name='drone_stream'),
    path('interrogation/', views.interrogation, name='interrogation'),
    path('search-location/', views.search_location, name='search_location'),
    path('api/chat-with-image/', views.chat_with_image, name='chat_with_image'),
] 