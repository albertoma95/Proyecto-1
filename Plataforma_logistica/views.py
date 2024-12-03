from django.shortcuts import render
from django.http import HttpResponse
from .models import destino

def index(request):
    opciones = destino.objects.all()
    return render(request, 'index.html', {'opciones': opciones})


def procesar_opcion(request):
    if request.method == 'POST':
        opcion_seleccionada = request.POST.get('opcion')
        return HttpResponse(f"Has seleccionado: {opcion_seleccionada}")
    return HttpResponse("Método no permitido.")