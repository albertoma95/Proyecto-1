# mapapp/views.py
from django.shortcuts import render, redirect
import folium
from datetime import datetime, timedelta
from branca.element import Element  # ADICIÓN

# Importar el formulario
from .forms import TruckParamsForm

# Importar utilidades y algoritmos
from .db_utils import get_orders
from .graph_utils import load_graph, haversine_distance
from .routing_alg import dijkstra, calculate_optimal_route
from .assignment import assign_orders_to_trucks
from mapapp.data.generate_data import generate_orders, generate_test_orders
from django.http import JsonResponse
from decimal import Decimal

base_colors = {
    'blue': '#0000FF',
    'green': '#008000',
    'purple': '#800080',
    'orange': '#FFA500',
    'darkred': '#8B0000',
    'cadetblue': '#5F9EA0'
}



def darken_color(hex_color, day_num):
    factor = 1.0 - (day_num - 1)*0.2
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
    """
    Vista principal que maneja GET y POST:
    - GET: muestra el formulario para capturar speed, cost_per_km, capacity.
    - POST: procesa el formulario y genera el mapa con los cálculos.
    """

    if request.method == 'POST':
        form = TruckParamsForm(request.POST)
        if form.is_valid():
            speed = form.cleaned_data['speed']
            cost_per_km = form.cleaned_data['cost_per_km']
            capacity = form.cleaned_data['capacity']

            # Lógica de cálculo de rutas usando los parámetros del formulario
            graph = load_graph()
            locations, orders = get_orders()
            origin = "Mataró"

            if origin not in graph:
                return render(request, "error.html", {"message": f"'{origin}' no está en el grafo."})

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
            trucks = assign_orders_to_trucks(graph, origin, orders, capacity, speed)

            daily_hours = 8
            daily_limit_distance = daily_hours * speed  # distancia máxima al día

            trucks_info_for_template = []
            original_colors = ['blue', 'green', 'purple', 'orange', 'darkred', 'cadetblue']

            # Creamos una lista para guardar los FeatureGroups de camiones
            truck_groups = []

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

                base_color_name = original_colors[idx % len(original_colors)]
                truck_group = folium.FeatureGroup(name=f"Camión {idx+1}", show=True)
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
                total_benefits = 0
                for order in truck['orders']:
                    order_id, destination, expiration_date, total_quantity, order_ready, name, total_cost = order
                    total_benefits += total_cost
                    folium.Marker(
                        location=location_coords[destination],
                        popup=(f"Pedido {order_id}: {destination}\n"
                               f"Cantidad: {total_quantity} unidades, Camión {idx + 1}\n"
                               f"Listo desde: {order_ready}\n"
                               f"Caduca: {expiration_date}"),
                        icon=folium.Icon(color=base_color_name, icon="info-sign")
                    ).add_to(truck_group)

                truck_group.add_to(m)
                truck_groups.append(truck_group)

                daily_order_deliveries = {d[0]: [] for d in daily_routes}

                def find_day_for_coord(coord):
                    for dnum, clist in daily_routes:
                        if coord in clist:
                            return dnum
                    return None

                for order in truck['orders']:
                    order_id, destination, expiration_date, total_quantity, order_ready, name, total_cost = order
                    for (node, node_coord) in route_segments:
                        if node == destination:
                            delivery_day = find_day_for_coord(node_coord)
                            if delivery_day is not None:
                                daily_order_deliveries[delivery_day].append({
                                    'id': order_id,
                                    'expiration_date': expiration_date,
                                    'name' : name,
                                    'total_quantity' : total_quantity,
                                    'benefits' : total_cost
                                })
                            break
                
                total_cost_km = cost*cost_per_km+1000
                truck_info = {
                    'truck_number': idx + 1,
                    'total_days': day_count,
                    'start_date': start_route_date.strftime('%Y-%m-%d'),
                    'total_cost': total_cost_km,
                    'total_benefits': round(total_benefits-Decimal(total_cost_km), 2), 
                    'daily_orders': []
                }
                for dnum in range(1, day_count+1):
                    orders_this_day = daily_order_deliveries.get(dnum, [])
                    for order in orders_this_day:
                        order['day_cost'] = cost * cost_per_km
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

            # ADICIÓN: Botón para seleccionar/deseleccionar todas las capas
            toggle_button_html = """
            <div style="position: fixed; top: 10px; left: 10px; z-index:9999; background: white; padding:5px; border-radius:5px;">
              <button onclick="toggleAllLayers()" class="btn btn-sm btn-primary">Toggle Todos Camiones</button>
            </div>
            <script>
            function toggleAllLayers(){
                var inputs = document.querySelectorAll('.leaflet-control-layers-list input[type="checkbox"]');
                var allChecked = true;
                inputs.forEach(i => { if(!i.checked) {allChecked=false;} });
                inputs.forEach(i => { i.checked = !allChecked; i.dispatchEvent(new Event('change')); });
            }
            </script>
            """

            # Insertamos el HTML/JS en el mapa
            m.get_root().html.add_child(Element(toggle_button_html))
            # FIN ADICIÓN

            map_html = m._repr_html_()
            return render(request, "map.html", {
                "map": map_html,
                "trucks_info": trucks_info_for_template,
                "speed": speed,
                "cost_per_km": cost_per_km,
                "capacity": capacity,
            })
        else:
             data_defaults = {
                'num_orders': 10,
                'avg_lines_per_order': 20,
                'max_quantity_per_line': 100
            }
        return render(request, "map_form.html", {"form": form, "data_defaults": data_defaults})
    
    else:
        # Si la petición es GET, mostramos el formulario vacío
        form = TruckParamsForm()
        data_defaults = {
            'num_orders': 10,
            'avg_lines_per_order': 20,
            'max_quantity_per_line': 100
        }
    
    return render(request, "map_form.html", {"form": form, "data_defaults": data_defaults})



def generate_data_ajax(request):
    # Esta vista recibe una llamada AJAX con los parámetros
    # y llama a generate_orders
    if request.method == 'POST':
        num_orders = int(request.POST.get('num_orders', 10))
        avg_lines_per_order = int(request.POST.get('avg_lines_per_order', 20))
        max_quantity_per_line = int(request.POST.get('max_quantity_per_line', 500))
        
        generate_orders(num_orders, avg_lines_per_order, max_quantity_per_line)
        return JsonResponse({"status": "ok", "message": "Datos generados con éxito"})
    else:
        return JsonResponse({"status": "error", "message": "Solo se admite POST"}, status=405)
    

def generate_test_data_ajax(request):
    try:
        generate_test_orders()  # Tu función de generación de datos de prueba
        return JsonResponse({
            'status': 'ok', 
            'message': 'Datos de prueba generados correctamente'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        })