from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('generar_pedidos/', views.generar_pedidos, name='generar_pedidos'),
    path('calcular_rutas/', views.calcular_rutas, name='calcular_rutas'),
]