from django.urls import path
from .views import map_view, generate_data_ajax, generate_test_data_ajax

urlpatterns = [
    path('', map_view, name='map_view'),
    path('generate-data-ajax/', generate_data_ajax, name='generate_data_ajax'),
    path('generate_test_data_ajax/', generate_test_data_ajax, name='generate_test_data_ajax'),
]
