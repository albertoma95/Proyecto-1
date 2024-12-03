from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('ejecutar_funcion/', views.ejecutar_funcion, name='ejecutar_funcion'),
]