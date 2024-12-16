from django.shortcuts import render
from django.http import HttpResponse
from .models import pedido,destino, producto, pedido_producto, Truck
import random
import folium
from django.shortcuts import render
from django.http import JsonResponse
import json
import os
from datetime import datetime, timedelta
import heapq
from typing import Optional,List, Tuple
import itertools
import math

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

    for _ in range(20):  # Repetir 20 veces para crear 20 pedidos
        id_destino = random.choice(ids_destino)  # Elegir un destino aleatorio

        # Crear un nuevo pedido
        nuevo_pedido = pedido(id_destino=id_destino)
        nuevo_pedido.save()

        # Determinar cuántos productos tendrá este pedido (entre 1 y 5, por ejemplo)
        num_productos = random.randint(1, 5)

        for _ in range(num_productos):
            id_producto = random.choice(ids_producto)  # Elegir un producto aleatorio
            cantidad = random.randint(1, 10)  # Cantidad aleatoria entre 1 y 10

            # Crear un nuevo registro en `pedido_producto`
            pedidoProducto = pedido_producto(
                id_pedido=nuevo_pedido.id,
                id_producto=id_producto,
                cantidad=cantidad
            )
            pedidoProducto.save()

            # Agregar un mensaje con los detalles del producto para este pedido
            mensajes.append(f"Pedido ID: {nuevo_pedido.id}, "
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


def can_add_order(truck,order, order_quantity,graph, origin, speed, capacity):
        if truck.total_quantity + order_quantity > capacity:
            return False
        
        expiration_date_obj = calcular_fecha_limite(order)
        distance, _ = dijkstra(graph, origin, order.id_destino)
        if distance == float('inf'):
            return False
        time_to_destination = timedelta(hours=distance / speed)
        arrival_date = datetime.now() + time_to_destination
        expiration_date_naive = expiration_date_obj.replace(tzinfo=None)
        if arrival_date > expiration_date_naive:
            return False

        return True


def assign_orders_to_trucks(ordered_orders,graph, origin,speed,capacity):
    trucks = []  # Lista para almacenar los camiones llenos
    truck_id = 1  # Identificador único para los camiones

    # Inicializar el primer camión
    current_truck = Truck(truck_id)
    truck_id += 1

    for order, _ in ordered_orders:  # Iterar sobre los pedidos con prioridad
        # Obtener la cantidad total de productos en el pedido
        productos_pedido = pedido_producto.objects.filter(id_pedido=order.id)
        total_quantity = sum(prod.cantidad for prod in productos_pedido)

        # Verificar si el camión actual puede aceptar el pedido
        if can_add_order(current_truck,order,total_quantity,graph,origin,speed,capacity):
            current_truck.add_order(order, total_quantity)
        else:
            # Si el camión está lleno, agregarlo a la lista y crear uno nuevo
            trucks.append(current_truck)
            current_truck = Truck(truck_id)
            truck_id += 1

            # Añadir el pedido al nuevo camión
            current_truck.add_order(order, total_quantity)

    # Agregar el último camión (si tiene pedidos) a la lista
    if current_truck.orders:
        trucks.append(current_truck)

    return trucks

def calcular_inicio_envio(orders: List[pedido]) -> Optional[datetime]:
    fecha_maxima = datetime.now()
    for order in orders:
        productos_pedido = pedido_producto.objects.filter(id_pedido=order.id)
        for prod_pedido in productos_pedido:
            producto_info = producto.objects.get(id=prod_pedido.id_producto)
            dias = producto_info.tiempo 
            fecha_producto = datetime.now() + timedelta(days=dias)
            fecha_maxima = max(fecha_maxima, fecha_producto)

    return fecha_maxima

def calcular_fecha_limite(pedido: pedido) -> Optional[datetime]:
    # Obtener productos relacionados con el pedido
    productos_pedido = pedido_producto.objects.filter(id_pedido=pedido.id)
    
    # Calcular las fechas límites
    fechas_limite = []
    for prod_pedido in productos_pedido:
        producto_info = producto.objects.get(id=prod_pedido.id_producto)
        # Fecha Pedido + Tiempo Fabricación + Días Caducidad 
        fecha_limite_producto = pedido.fecha + timedelta(days=producto_info.tiempo) + timedelta(days=producto_info.caducidad)
        fechas_limite.append(fecha_limite_producto)
    
    # Retornar la fecha más temprana
    return min(fechas_limite) if fechas_limite else None


def obtener_pedidos_prioritarios(orders: List[pedido]) -> List[Tuple[pedido, datetime]]:
    pedidos_con_prioridad = []
    
    # Asociar cada pedido con su fecha límite
    for ped in orders:
        fecha_limite = calcular_fecha_limite(ped)
        if fecha_limite:  # Ignorar pedidos sin productos
            pedidos_con_prioridad.append((ped, fecha_limite))
    
    # Ordenar por fecha de caducidad más temprana
    pedidos_con_prioridad.sort(key=lambda x: x[1])

    return pedidos_con_prioridad
  
    
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

def precompute_distances(graph, nodes):
    dist_matrix = {}
    for from_node in nodes:
        dist_matrix[from_node] = {}
        for to_node in nodes:
            if from_node == to_node:
                dist_matrix[from_node][to_node] = 0
            else:
                distance, _ = dijkstra(graph, from_node, to_node)
                dist_matrix[from_node][to_node] = distance
    return dist_matrix


def calculate_optimal_route(graph, origin, destinations):
    # Resolución simplificada tipo TSP
    all_locations = [origin] + destinations
    n = len(all_locations)
    index = {all_locations[i]: i for i in range(n)}
    dist_matrix = precompute_distances(graph, all_locations)

    C = {}
    for k in range(1, n):
        C[(frozenset([k]), k)] = (dist_matrix[origin][all_locations[k]], origin)

    for s in range(2, n):
        for subset in itertools.combinations(range(1, n), s):
            set_subset = frozenset(subset)
            for k in subset:
                prev_subset = set_subset - {k}
                min_cost = float('inf')
                min_prev = None
                for m in prev_subset:
                    cost = C[(prev_subset, m)][0] + dist_matrix[all_locations[m]][all_locations[k]]
                    if cost < min_cost:
                        min_cost = cost
                        min_prev = m
                C[(set_subset, k)] = (min_cost, min_prev)

    full_set = frozenset(range(1, n))
    min_cost = float('inf')
    last_node = None
    for k in range(1, n):
        cost = C[(full_set, k)][0]
        if cost < min_cost:
            min_cost = cost
            last_node = k

    path = []
    set_subset = full_set
    k = last_node
    while set_subset:
        path.append(all_locations[k])
        prev_k = C[(set_subset, k)][1]
        set_subset = set_subset - {k}
        k = prev_k if isinstance(prev_k, int) else index[prev_k]
    path.append(origin)
    path.reverse()

    return min_cost, path


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat/2)**2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dLon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance

base_colors = {
    'blue': '#0000FF',
    'green': '#008000',
    'purple': '#800080',
    'orange': '#FFA500',
    'darkred': '#8B0000',
    'cadetblue': '#5F9EA0'
}

def darken_color(hex_color, day_num):
    factor = 1.0 - (day_num - 1)*0.1
    if factor < 0:
        factor = 0
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f"#{r:02X}{g:02X}{b:02X}"


def calcular_rutas(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        velocidad = float(body.get('velocidad', 0)) 
        capacidad = int(body.get('capacidad', 0))
        coste_km = float(body.get('coste_km', 0)) 

        print(velocidad)
        print(capacidad)

        if not velocidad or not capacidad or not coste_km or velocidad <= 0 or capacidad <= 0 or coste_km <= 0:
            return JsonResponse({'error': 'Todos los valores deben ser mayores que 0.'}, status=400)

        graph = load_graph()
        graph = {int(k): {int(neighbor): weight for neighbor, weight in v.items()} for k, v in graph.items()}
        locations =  destino.objects.all()
        orders = list(pedido.objects.all().order_by('fecha'))
        id_mataro = 73

        

        location_coords = {loc.id: (loc.latitud, loc.longitud) for loc in locations}

        m = folium.Map(location=location_coords[id_mataro], zoom_start=6, tiles='CartoDB positron')


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


        
        pedidos_prioritarios = (obtener_pedidos_prioritarios(orders))
        trucks = assign_orders_to_trucks(pedidos_prioritarios,graph,id_mataro,velocidad,capacidad)
        original_colors = ['blue', 'green', 'purple', 'orange', 'darkred', 'cadetblue']
        daily_hours = 8
        daily_limit_distance = daily_hours * velocidad  # 960 km/día
        trucks_info_for_template = []


        for idx, truck in enumerate(trucks):
            if not truck.orders:
                continue

            # de todos los pedidos del camion obtener la fecha del producto que mas tarde en hacerse

            start_route_date = calcular_inicio_envio(truck.orders)
            print(start_route_date)

            destinations = [order.id_destino for order in truck.orders]
            cost, best_route = calculate_optimal_route(graph, id_mataro, destinations)

            full_route_coords = []
            route_segments = []
            for i in range(len(best_route) - 1):
                from_node = best_route[i]
                to_node = best_route[i + 1]
                _, path = dijkstra(graph, from_node, to_node)
                segment_coords = [location_coords[node] for node in path if node in location_coords]
                if full_route_coords and segment_coords:
                    if full_route_coords[-1] == segment_coords[0]:
                        full_route_coords.extend(segment_coords[1:])
                    else:
                        full_route_coords.extend(segment_coords)
                else:
                    full_route_coords.extend(segment_coords)
                route_segments.append((to_node, segment_coords[-1]))

            daily_routes = []
            current_day_coords = [full_route_coords[0]]
            remaining_distance_day = daily_limit_distance
            day_count = 1

            for i in range(len(full_route_coords) - 1):
                start_p = full_route_coords[i]
                end_p = full_route_coords[i+1]
                segment_dist = haversine_distance(start_p[0], start_p[1], end_p[0], end_p[1])

                if segment_dist <= remaining_distance_day:
                    current_day_coords.append(end_p)
                    remaining_distance_day -= segment_dist
                else:
                    fraction = remaining_distance_day / segment_dist
                    partial_lat = start_p[0] + fraction * (end_p[0] - start_p[0])
                    partial_lng = start_p[1] + fraction * (end_p[1] - start_p[1])
                    partial_point = (partial_lat, partial_lng)
                    current_day_coords.append(partial_point)
                    daily_routes.append((day_count, current_day_coords.copy()))
                    day_count += 1
                    current_day_coords = [partial_point]

                    leftover_dist = segment_dist - remaining_distance_day
                    remaining_distance_day = daily_limit_distance

                    dist_to_cover = leftover_dist
                    start_temp = partial_point
                    end_temp = end_p
                    while dist_to_cover > remaining_distance_day:
                        frac = remaining_distance_day / dist_to_cover
                        p_lat = start_temp[0] + frac*(end_temp[0] - start_temp[0])
                        p_lng = start_temp[1] + frac*(end_temp[1] - start_temp[1])
                        p_point = (p_lat, p_lng)
                        current_day_coords.append(p_point)
                        daily_routes.append((day_count, current_day_coords.copy()))
                        day_count += 1
                        current_day_coords = [p_point]
                        dist_to_cover -= remaining_distance_day
                        remaining_distance_day = daily_limit_distance
                        start_temp = p_point

                    current_day_coords.append(end_temp)
                    remaining_distance_day -= dist_to_cover

            if current_day_coords:
                daily_routes.append((day_count, current_day_coords.copy()))


            

            # Crear un FeatureGroup por camión
            truck_group = folium.FeatureGroup(name=f"Camión {idx+1}", show=True)

            # Dibujar rutas en el mapa dentro del FeatureGroup
            base_color_name = original_colors[idx % len(original_colors)]
            base_hex = base_colors[base_color_name]

            for day_num, coords_list in daily_routes:
                day_color = darken_color(base_hex, day_num)
                current_date_for_day = (start_route_date + timedelta(days=day_num - 1)).strftime('%Y-%m-%d')

                popup_html = f"""
                    <div class='route-popup' data-truck-id='{idx + 1}'>
                        <strong>Camión {idx + 1}</strong><br>
                        Día: {day_num} ({current_date_for_day})<br>
                        Carga: {truck.total_quantity} unidades<br>
                        Distancia: {cost:.2f} km<br>
                    </div>
                """

                folium.PolyLine(
                    locations=coords_list,
                    color=day_color,
                    weight=3,
                    opacity=0.8,
                    popup=folium.Popup(popup_html, max_width=300),
                ).add_to(truck_group)

            # Marcar pedidos en el mapa
            for order in truck.orders:
                folium.Marker(
                    location=location_coords[order.id_destino],
                    popup=(f"Pedido {order.id}: {order.id_destino}"),
                    icon=folium.Icon(color=base_color_name, icon="info-sign")
                ).add_to(truck_group)

            truck_group.add_to(m)

            # Determinar el día de entrega de cada pedido
            daily_order_deliveries = {d[0]: [] for d in daily_routes}

            def find_day_for_coord(coord):
                for dnum, clist in daily_routes:
                    if coord in clist:
                        return dnum
                return None

            for order in truck.orders:
                for (node, node_coord) in route_segments:
                    if node == order.id_destino:
                        delivery_day = find_day_for_coord(node_coord)
                        if delivery_day is not None:
                            daily_order_deliveries[delivery_day].append({
                                'id': order.id
                            })
                        break

            truck_info = {
                'truck_number': idx + 1,
                'total_days': day_count,
                'start_date': start_route_date.strftime('%Y-%m-%d'),
                'daily_orders': []
            }
            for dnum in range(1, day_count+1):
                orders_this_day = daily_order_deliveries.get(dnum, [])
                truck_info['daily_orders'].append({
                    'day_num': dnum,
                    'orders': orders_this_day
                })


            trucks_info_for_template.append(truck_info)

        folium.Marker(
            location=location_coords[id_mataro],
            popup=f"Origen: {id_mataro}",
            icon=folium.Icon(color="red", icon="home")
        ).add_to(m)

        # Añadir el control de capas que mostrará checkboxes para cada camión
        folium.LayerControl().add_to(m)


        # Devolver el HTML del nuevo mapa
        mapa_html = m._repr_html_()
        return JsonResponse({"mapa_html": mapa_html,"trucks_info": trucks_info_for_template})
    
    return JsonResponse({"error": "Método no permitido."}, status=405)