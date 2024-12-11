from django.shortcuts import render
import folium
import json
import mysql.connector
import heapq
import os
import itertools
from datetime import datetime, timedelta
import math

def load_graph():
    file_path = os.path.join(os.path.dirname(__file__), "distancias_provincias.json")
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

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

def get_orders():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="iadelivery"
        )
        
        cursor = connection.cursor()
        # Obtener ubicaciones
        cursor.execute("""
            SELECT l.name, l.latitude, l.longitude
            FROM Locations l
        """)
        locations = cursor.fetchall()

        # Obtener pedidos (incluyendo order_ready)
        cursor.execute("""
            SELECT id_order, name AS destination, expiration_date, total_quantity, order_ready
            FROM Order_Expiration1
            ORDER BY expiration_date ASC
            LIMIT 50
        """)
        orders = cursor.fetchall()

        cursor.close()
        connection.close()
        
        return locations, orders
    except mysql.connector.Error as error:
        print(f"Error connecting to MySQL: {error}")
        return [], []

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

def can_assign_order_to_truck(order, truck, graph, origin):
    order_id, destination, expiration_date, total_quantity, order_ready = order
    if truck['total_quantity'] + total_quantity > truck['capacity']:
        return False

    expiration_date_obj = datetime.strptime(str(expiration_date), '%Y-%m-%d')
    current_date = truck['current_date']
    distance, _ = dijkstra(graph, origin, destination)
    if distance == float('inf'):
        return False
    speed = 120.0
    time_to_destination = timedelta(hours=distance / speed)
    arrival_date = current_date + time_to_destination
    if arrival_date > expiration_date_obj:
        return False

    return True

def assign_orders_to_trucks(graph, origin, orders, capacity):
    unassigned_orders = list(orders)
    trucks = []
    speed = 120.0
    unassigned_orders.sort(key=lambda x: x[2])  # x[2] es expiration_date

    while unassigned_orders:
        truck = {
            'orders': [],
            'total_quantity': 0,
            'capacity': capacity,
            'current_date': datetime.now()
        }

        assigned_this_round = True
        while assigned_this_round and unassigned_orders:
            assigned_this_round = False
            for order in unassigned_orders:
                if truck['orders']:
                    max_order_ready = max(datetime.strptime(str(o[4]), '%Y-%m-%d') for o in truck['orders'])
                else:
                    max_order_ready = datetime.strptime(str(order[4]), '%Y-%m-%d')

                if max_order_ready > truck['current_date']:
                    truck['current_date'] = max_order_ready

                if can_assign_order_to_truck(order, truck, graph, origin):
                    truck['orders'].append(order)
                    truck['total_quantity'] += order[3]
                    unassigned_orders.remove(order)
                    assigned_this_round = True
                    break

        if truck['orders']:
            trucks.append(truck)

    return trucks

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

def map_view(request):
    graph = load_graph()
    locations, orders = get_orders()
    origin = "Mataró"
    capacity = 60000

    if origin not in graph:
        return render(request, "error.html", {"message": "'Mataró' no está en el grafo."})

    location_coords = {loc[0]: (loc[1], loc[2]) for loc in locations}
    m = folium.Map(location=[40.0, -3.7], zoom_start=6, tiles='CartoDB positron')


    # Dibujar las conexiones
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

    # Asignar pedidos a camiones
    trucks = assign_orders_to_trucks(graph, origin, orders, capacity)

    original_colors = ['blue', 'green', 'purple', 'orange', 'darkred', 'cadetblue']
    speed = 120.0
    daily_hours = 8
    daily_limit_distance = daily_hours * speed  # 960 km/día

    trucks_info_for_template = []

    for idx, truck in enumerate(trucks):
        if not truck['orders']:
            continue

        max_order_ready = max(datetime.strptime(str(o[4]), '%Y-%m-%d') for o in truck['orders'])
        start_route_date = max_order_ready

        destinations = [order[1] for order in truck['orders']]
        cost, best_route = calculate_optimal_route(graph, origin, destinations)

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
            folium.PolyLine(
                locations=coords_list,
                color=day_color,
                weight=3,
                opacity=0.8,
                tooltip=(f"Camión {idx + 1}, Día {day_num} ({current_date_for_day}): "
                         f"Carga {truck['total_quantity']} unidades / Total {cost:.2f} km")
            ).add_to(truck_group)

        # Marcar pedidos en el mapa
        for order in truck['orders']:
            order_id, destination, expiration_date, total_quantity, order_ready = order
            folium.Marker(
                location=location_coords[destination],
                popup=(f"Pedido {order_id}: {destination}\n"
                       f"Cantidad: {total_quantity} unidades, Camión {idx + 1}\n"
                       f"Listo desde: {order_ready}\n"
                       f"Caduca: {expiration_date}"),
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

        for order in truck['orders']:
            order_id, destination, expiration_date, total_quantity, order_ready = order
            for (node, node_coord) in route_segments:
                if node == destination:
                    delivery_day = find_day_for_coord(node_coord)
                    if delivery_day is not None:
                        daily_order_deliveries[delivery_day].append({
                            'id': order_id,
                            'expiration_date': expiration_date
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
        location=location_coords[origin],
        popup=f"Origen: {origin}",
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)

    # Añadir el control de capas que mostrará checkboxes para cada camión
    folium.LayerControl().add_to(m)

    map_html = m._repr_html_()
    return render(request, "map.html", {"map": map_html, "trucks_info": trucks_info_for_template})
