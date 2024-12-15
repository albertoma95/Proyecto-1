from django.shortcuts import render
from django.http import HttpResponse
from .models import pedido,destino, producto, pedido_producto
import random
import folium
from django.shortcuts import render
from django.http import JsonResponse
import json
import os
from datetime import datetime, timedelta
import heapq

def index(request):
   
    # Centrar el mapa en Mataró
    mapa = folium.Map(location=[41.5381, 2.4445], zoom_start=14)

    # Añadir marcador inicial en Mataró
    folium.Marker(
        location=[41.5381, 2.4445],
        popup="Mataró",
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(mapa)

    # Renderizar el mapa
    mapa_html = mapa._repr_html_()

    return render(request, "index.html", {"mapa_html": mapa_html})



from django.http import JsonResponse

def generar_pedidos(request):
    if request.method == 'POST':
        try:
            resultado = generateData()
            return JsonResponse({"message": "Pedidos generados exitosamente.", "result": resultado})
        except Exception as e:
            # Manejo de errores
            return JsonResponse({"error": f"Hubo un problema al generar pedidos: {str(e)}"}, status=500)
    return JsonResponse({"error": "Método no permitido."}, status=405)

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


def load_graph():
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "Plataforma_logistica/static/Plataforma_logistica/data/provincias.json"
    )
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
    

def assign_orders_to_trucks(graph, origin, orders, capacity):
    trucks = []
    unassigned_orders = orders.copy()

    while unassigned_orders:
        truck = {
            'orders': [],
            'total_quantity': 0
        }
        assigned_orders = []

        for order in unassigned_orders:
            # Ahora order incluye order_ready en el índice 4
            # Desempaquetamos:
            # id_order, destination, expiration_date, total_quantity, order_ready
            order_id, destination, expiration_date, total_quantity, order_ready = order

            if truck['total_quantity'] + total_quantity > capacity:
                continue

            # Comprobaciones de expiración y tiempos no cambian en esta parte,
            # se podrían hacer más chequeos si fuera necesario.
            
            expiration_date_obj = datetime.strptime(str(expiration_date), '%Y-%m-%d')
            current_date = datetime.now()

            distance, _ = dijkstra(graph, origin, destination)
            if distance == float('inf'):
                continue

            speed = 120.0
            time_to_destination = timedelta(hours=distance / speed)
            arrival_date = current_date + time_to_destination

            if arrival_date > expiration_date_obj:
                continue

            # Asignar el pedido
            truck['orders'].append(order)
            truck['total_quantity'] += total_quantity
            assigned_orders.append(order)

        if truck['orders']:
            trucks.append(truck)

        for order in assigned_orders:
            unassigned_orders.remove(order)

        if not assigned_orders:
            break

    return trucks
    
def dijkstra(graph, start, end):
    queue = [(0, start, [])]
    visited = set()
    while queue:
        (cost, node, path) = heapq.heappop(queue)
        if node == end:
            return cost, path + [end]
        if node in visited:
            continue
        visited.add(node)
        for neighbor, weight in graph.get(node, {}).items():
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path + [node]))
    return float('inf'), []

def calcular_rutas(request):
    if request.method == 'POST':
        graph = load_graph()
        locations =  destino.objects.all()
        orders = pedido.objects.all().order_by('fecha')
        id_mataro = 73
        capacity = 50000


        location_coords = {loc.id: (loc.latitud, loc.longitud) for loc in locations}

        m = folium.Map(location=location_coords[id_mataro], zoom_start=6.5, tiles='CartoDB positron')

        for province, neighbors in graph.items():
            if province in location_coords:
                for neighbor, distance in neighbors.items():
                    if neighbor in location_coords:
                        folium.PolyLine(
                            locations=[location_coords[province], location_coords[neighbor]],
                            color="grey",
                            weight=1,
                            opacity=0.5
                        ).add_to(m)
        
        trucks = assign_orders_to_trucks(graph, id_mataro, orders, capacity)
        original_colors = ['blue', 'green', 'purple', 'orange', 'darkred', 'cadetblue']
        speed = 120.0
        daily_hours = 8
        daily_limit_distance = daily_hours * speed




        # Simulación: Cambiar el mapa con una ruta nueva
        mapa = folium.Map(location=[40.4168, -3.7038], zoom_start=12)  # Madrid, España

        # Añadir marcadores simulados para la ruta
        folium.Marker(
            location=[40.4168, -3.7038],
            popup="Inicio: Madrid",
            icon=folium.Icon(color="green", icon="info-sign"),
        ).add_to(mapa)

        folium.Marker(
            location=[40.4268, -3.7138],
            popup="Destino: Ubicación simulada",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(mapa)

        # Devolver el HTML del nuevo mapa
        mapa_html = mapa._repr_html_()
        return JsonResponse({"mapa_html": mapa_html})
    
    return JsonResponse({"error": "Método no permitido."}, status=405)