from django.shortcuts import render
from django.http import HttpResponse
from .models import pedido,destino, producto, pedido_producto
import random

def index(request):
    return render(request, 'index.html')

def ejecutar_funcion(request):
    if request.method == 'POST':
        # Llama a la función para insertar en la base de datos
        resultado = generateData()
        return HttpResponse(resultado)
    return HttpResponse("Método no permitido.")

def generateData():
    # Obtener todos los IDs de destino
    ids_destino = destino.objects.values_list('id', flat=True)  # Obtiene solo los IDs

    if not ids_destino:
        return "No hay destinos disponibles en la base de datos."

    # Obtener todos los IDs de producto
    ids_producto = producto.objects.values_list('id', flat=True)
    if not ids_producto:
        return "No hay productos disponibles en la base de datos."

    mensajes = []  # Para almacenar los resultados de cada inserción

    for _ in range(20):  # Repetir 20 veces
        id_destino = random.choice(ids_destino)  # Elegir uno aleatorio de los destinos

        # Crear un nuevo pedido
        nuevo_pedido = pedido(id_destino=id_destino)
        nuevo_pedido.save()

        # Elegir un producto aleatorio
        id_producto = random.choice(ids_producto)  # Elegir un producto aleatorio
        cantidad = random.randint(1, 10)  # Cantidad aleatoria entre 1 y 10

        # Crear un nuevo registro en `pedido_producto`
        pedidoProducto = pedido_producto(
            id_pedido=nuevo_pedido.id,
            id_producto=id_producto,
            cantidad=cantidad
        )
        pedidoProducto.save()

        # Agregar un mensaje con los detalles del pedido y el producto
        mensajes.append(f"Pedido creado con ID: {nuevo_pedido.id}, "
                        f"Destino: {id_destino}, Producto: {id_producto}, Cantidad: {cantidad}")

    # Unir todos los mensajes y devolverlos como respuesta
    return "\n".join(mensajes)