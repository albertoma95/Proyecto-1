from django.shortcuts import render
import folium
import json
import mysql.connector
import heapq
import os
import itertools
from datetime import datetime, timedelta

# Cargar el grafo desde el archivo de distancias
def load_graph():
    file_path = os.path.join(os.path.dirname(__file__), "distancias_provincias.json")
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Implementar el algoritmo de Dijkstra que retorna costo y camino
def dijkstra(graph, start, end):
    queue = [(0, start, [])]  # (cost, current_node, path)
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

# Obtener los pedidos y ubicaciones desde la base de datos
def get_orders():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="iadelivery"
        )
        
        cursor = connection.cursor()
        # Obtener todas las ubicaciones
        cursor.execute("""
            SELECT l.name, l.latitude, l.longitude
            FROM Locations l
        """)
        locations = cursor.fetchall()

        # Obtener los pedidos desde la vista Order_Expiration
        cursor.execute("""
            SELECT id_order, name AS destination, expiration_date, total_quantity
            FROM Order_Expiration1
            ORDER BY expiration_date ASC  -- Ordenar por fecha de expiración ascendente
            LIMIT 30
        """)
        orders = cursor.fetchall()

        cursor.close()
        connection.close()
        
        return locations, orders
    except mysql.connector.Error as error:
        print(f"Error connecting to MySQL: {error}")
        return [], []

# Precomputar las distancias entre todas las ubicaciones necesarias
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

# Calcular la ruta óptima sin considerar la vuelta al origen
def calculate_optimal_route(graph, origin, destinations):
    # Crear una lista de todas las ubicaciones
    all_locations = [origin] + destinations
    n = len(all_locations)
    index = {all_locations[i]: i for i in range(n)}
    dist_matrix = precompute_distances(graph, all_locations)

    # Crear la matriz de programación dinámica
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

    # Encontrar el costo mínimo para terminar en cualquier destino
    full_set = frozenset(range(1, n))
    min_cost = float('inf')
    last_node = None
    for k in range(1, n):
        cost = C[(full_set, k)][0]
        if cost < min_cost:
            min_cost = cost
            last_node = k

    # Reconstruir el camino óptimo
    path = []
    set_subset = full_set
    k = last_node
    while set_subset:
        path.append(all_locations[k])
        prev_k = C[(set_subset, k)][1]
        set_subset = set_subset - {k}
        k = prev_k if isinstance(prev_k, int) else index[prev_k]
    path.append(origin)  # Añadir el origen al inicio
    path.reverse()  # Invertir para obtener el orden correcto

    return min_cost, path

# Asignar pedidos a camiones respetando capacidad y expiración
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
            order_id, destination, expiration_date, total_quantity = order
            if truck['total_quantity'] + total_quantity > capacity:
                continue  # Excede la capacidad

            # Verificar si el pedido llega antes de caducar
            # Suponiendo que expiration_date es una fecha en formato 'YYYY-MM-DD'
            expiration_date_obj = datetime.strptime(str(expiration_date), '%Y-%m-%d')
            current_date = datetime.now()

            # Calcular distancia desde el origen al destino
            distance, _ = dijkstra(graph, origin, destination)
            if distance == float('inf'):
                continue  # No hay ruta

            # Estimación de tiempo de entrega (suponiendo velocidad constante)
            speed = 60  # km/h
            time_to_destination = timedelta(hours=distance / speed)
            arrival_date = current_date + time_to_destination

            if arrival_date > expiration_date_obj:
                continue  # No llega a tiempo

            # Asignar el pedido al camión
            truck['orders'].append(order)
            truck['total_quantity'] += total_quantity
            assigned_orders.append(order)

        # Añadir el camión a la lista si tiene pedidos asignados
        if truck['orders']:
            trucks.append(truck)

        # Remover pedidos asignados
        for order in assigned_orders:
            unassigned_orders.remove(order)

        # Si no se pudo asignar ningún pedido en esta iteración, romper el bucle para evitar un ciclo infinito
        if not assigned_orders:
            break

    return trucks

# Vista para generar el mapa dinámicamente
def map_view(request):
    graph = load_graph()
    locations, orders = get_orders()
    origin = "Mataró"  # Punto de inicio
    capacity = 50000  # Capacidad del camión

    if origin not in graph:
        return render(request, "error.html", {"message": "'Mataró' no está en el grafo."})

    # Crear un diccionario de ubicaciones por nombre
    location_coords = {loc[0]: (loc[1], loc[2]) for loc in locations}

    # Crear mapa
    m = folium.Map(location=location_coords[origin], zoom_start=6.5, tiles='CartoDB positron')

    # Mostrar todo el grafo con conexiones en gris
    for province, neighbors in graph.items():
        if province in location_coords:
            for neighbor, distance in neighbors.items():
                if neighbor in location_coords:
                    folium.PolyLine(
                        locations=[location_coords[province], location_coords[neighbor]],
                        color="grey",  # Conexiones del grafo en gris
                        weight=1,
                        opacity=0.5
                    ).add_to(m)

    # Asignar pedidos a camiones
    trucks = assign_orders_to_trucks(graph, origin, orders, capacity)

    # Colores para diferentes camiones
    colors = ['blue', 'green', 'purple', 'orange', 'darkred', 'cadetblue']

    for idx, truck in enumerate(trucks):
        # Obtener destinos de los pedidos del camión
        destinations = [order[1] for order in truck['orders']]

        # Calcular la ruta óptima para el camión
        cost, best_route = calculate_optimal_route(graph, origin, destinations)

        # Dibujar la ruta del camión
        route_coords = []
        for i in range(len(best_route) - 1):
            from_node = best_route[i]
            to_node = best_route[i + 1]
            _, path = dijkstra(graph, from_node, to_node)
            coords = [location_coords[node] for node in path if node in location_coords]
            route_coords.extend(coords)

        # Dibujar ruta del camión con el total de cantidad en el tooltip
        if route_coords:
            folium.PolyLine(
                locations=route_coords,
                color=colors[idx % len(colors)],
                weight=3,
                opacity=0.8,
                tooltip=f"Camión {idx + 1}: Carga Total {truck['total_quantity']} unidades"
            ).add_to(m)

        # Añadir marcadores para los destinos con la cantidad del pedido
        for order in truck['orders']:
            order_id, destination, _, total_quantity = order
            folium.Marker(
                location=location_coords[destination],
                popup=f"Pedido {order_id}: {destination} (Cantidad: {total_quantity} unidades, Camión {idx + 1})",
                icon=folium.Icon(color=colors[idx % len(colors)], icon="info-sign")
            ).add_to(m)

    # Añadir marcador para el origen
    folium.Marker(
        location=location_coords[origin],
        popup=f"Origen: {origin}",
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)

    # Convertir el mapa en HTML
    map_html = m._repr_html_()
    return render(request, "map.html", {"map": map_html})
