from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('procesar-opcion/', views.procesar_opcion, name='procesar_opcion'),
]