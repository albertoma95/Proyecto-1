from django.shortcuts import render
import folium
import json
import mysql.connector
import heapq
import os
from itertools import permutations

# Cargar el grafo desde el archivo de distancias
def load_graph():
    file_path = os.path.join(os.path.dirname(__file__), "distancias_provincias.json")
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Implementar el algoritmo de Dijkstra
def dijkstra(graph, start, end):
    queue = [(0, start, [])]  # (cost, current_node, path)
    visited = set()
    
    while queue:
        (cost, node, path) = heapq.heappop(queue)
        if node in visited:
            continue
        
        path = path + [node]
        visited.add(node)
        
        if node == end:
            return cost, path
        
        for neighbor, weight in graph.get(node, {}).items():
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path))
    
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
            SELECT id_order, name AS destination
            FROM Order_Expiration
            LIMIT 7
        """)
        orders = cursor.fetchall()

        cursor.close()
        connection.close()
        
        return locations, orders
    except mysql.connector.Error as error:
        print(f"Error connecting to MySQL: {error}")
        return [], []

# Calcular la ruta óptima que pase por todos los destinos
def calculate_optimal_route(graph, origin, destinations):
    min_cost = float('inf')
    best_route = []

    # Probar todas las permutaciones de los destinos
    for perm in permutations(destinations):
        route = [origin] + list(perm)
        cost = 0
        valid = True
        for i in range(len(route) - 1):
            dist, _ = dijkstra(graph, route[i], route[i + 1])
            if dist == float('inf'):  # Ruta no válida
                valid = False
                break
            cost += dist
        if valid and cost < min_cost:
            min_cost = cost
            best_route = route

    return min_cost, best_route

# Vista para generar el mapa dinámicamente
def map_view(request):
    graph = load_graph()
    locations, orders = get_orders()
    origin = "Barcelona"  # Punto de inicio

    if origin not in graph:
        return render(request, "error.html", {"message": "'Barcelona' no está en el grafo."})

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

    # Obtener destinos de los pedidos
    destinations = [order[1] for order in orders]

    # Calcular la ruta óptima
    cost, best_route = calculate_optimal_route(graph, origin, destinations)

    # Dibujar la ruta óptima en azul
    route_coords = []
    for i in range(len(best_route) - 1):
        _, path = dijkstra(graph, best_route[i], best_route[i + 1])
        for node in path:
            if node in location_coords:
                route_coords.append(location_coords[node])

    folium.PolyLine(
        locations=route_coords,
        color="blue",  # Ruta óptima en azul
        weight=3,
        opacity=0.8,
        tooltip=f"Ruta óptima: Costo {cost:.1f} km"
    ).add_to(m)

    # Añadir marcadores para los destinos
    for order_id, destination in orders:
        folium.Marker(
            location=location_coords[destination],
            popup=f"Pedido {order_id}: {destination}",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    # Convertir el mapa en HTML
    map_html = m._repr_html_()
    return render(request, "map.html", {"map": map_html})
