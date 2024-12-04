import json
import folium
import mysql.connector
import heapq
import random

# Cargar el grafo desde el archivo de distancias
def load_graph():
    with open('distancias_provincias.json', 'r', encoding='utf-8') as file:
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

# Obtener los pedidos desde la vista Order_Expiration
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
            LIMIT 5
        """)
        orders = cursor.fetchall()

        cursor.close()
        connection.close()
        
        return locations, orders
    except mysql.connector.Error as error:
        print(f"Error connecting to MySQL: {error}")
        return [], []

# Crear el mapa con el grafo y las rutas de los pedidos
def create_routes_map():
    graph = load_graph()
    locations, orders = get_orders()
    origin = "Barcelona"  # Punto de inicio

    if origin not in graph:
        print(f"Error: '{origin}' no está en el grafo.")
        return

    # Crear un diccionario de ubicaciones por nombre
    location_coords = {loc[0]: (loc[1], loc[2]) for loc in locations}

    # Crear mapa
    m = folium.Map(location=location_coords[origin], zoom_start=7, tiles='CartoDB positron')

    # Mostrar todo el grafo con conexiones en rojo
    for province, neighbors in graph.items():
        if province in location_coords:
            for neighbor, distance in neighbors.items():
                if neighbor in location_coords:
                    folium.PolyLine(
                        locations=[location_coords[province], location_coords[neighbor]],
                        color="grey",  # Conexiones del grafo en rojo
                        weight=1,
                        opacity=0.5
                    ).add_to(m)

    # Generar colores aleatorios para las rutas de los pedidos
    route_colors = [
        "#%06x" % random.randint(0, 0xFFFFFF)
        for _ in range(len(orders))
    ]

    # Añadir pedidos y rutas
    for idx, (order_id, destination) in enumerate(orders):
        if destination in graph:
            cost, path = dijkstra(graph, origin, destination)

            # Añadir marcador del pedido
            if destination in location_coords:
                folium.Marker(
                    location=location_coords[destination],
                    popup=f"Pedido {order_id}: {destination} (Costo: {cost:.1f} km)",
                    icon=folium.Icon(color="blue", icon="info-sign")
                ).add_to(m)

            # Dibujar línea de la ruta en un color único
            coords = [location_coords[origin]]  # Coordenadas iniciales (Barcelona)
            for node in path:
                if node in location_coords:
                    coords.append(location_coords[node])

            folium.PolyLine(
                locations=coords,
                color=route_colors[idx],  # Color único para cada ruta
                weight=3,
                opacity=0.8,
                tooltip=f"Pedido {order_id}: {destination} (Costo: {cost:.1f} km)"
            ).add_to(m)

    folium.LayerControl().add_to(m)

    # Guardar el mapa en un archivo HTML
    m.save('rutas_pedidos.html')
    print("Mapa generado: rutas_pedidos.html")

if __name__ == "__main__":
    create_routes_map()
