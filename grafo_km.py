import mysql.connector
import folium
import json
import openrouteservice

# Configuración de la API de OpenRouteService
ORS_API_KEY = '5b3ce3597851110001cf6248b8adbe3d64254a23b7309740ccc64c30'  # Reemplaza con tu clave API
client = openrouteservice.Client(key=ORS_API_KEY)

def get_coordinates():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="iadelivery"
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT name, latitude, longitude FROM locations")
        results = cursor.fetchall()
        
        coordinates = {row[0]: (float(row[1]), float(row[2])) for row in results}
        
        cursor.close()
        connection.close()
        
        return coordinates
    except mysql.connector.Error as error:
        print(f"Error connecting to MySQL: {error}")
        return None

def calculate_distances(coordinates, adjacency):
    distances = {}
    for province, neighbors in adjacency.items():
        distances[province] = {}
        for neighbor in neighbors:
            if neighbor in coordinates:
                coords_start = coordinates[province]
                coords_end = coordinates[neighbor]
                
                try:
                    # Solicitar distancia a la API
                    route = client.directions(
                        coordinates=[(coords_start[1], coords_start[0]), (coords_end[1], coords_end[0])],
                        profile='driving-car',
                        format='geojson'
                    )
                    distance = route['features'][0]['properties']['segments'][0]['distance'] / 1000  # Convertir a km
                    distances[province][neighbor] = distance
                except openrouteservice.exceptions.ApiError as e:
                    print(f"Error al calcular distancia entre {province} y {neighbor}: {e}")
    return distances

def create_map_with_distances():
    # Cargar datos
    with open('provincias.json', 'r', encoding='utf-8') as file:
        adjacency = json.load(file)
    
    coordinates = get_coordinates()
    if not coordinates:
        return
    
    # Calcular distancias con OpenRouteService
    distances = calculate_distances(coordinates, adjacency)
    
    # Crear mapa
    m = folium.Map(
        location=[40.416775, -3.703790],
        zoom_start=6,
        tiles='CartoDB positron'
    )
    
    # Grupo de características
    marker_group = folium.FeatureGroup(name="Provincias")
    
    # Añadir marcadores y líneas con distancias
    for province, coords in coordinates.items():
        neighbors = adjacency.get(province, [])
        popup_text = f"<b>{province}</b><br>Distancias aproximadas:<br>"
        
        for neighbor in neighbors:
            distance = distances.get(province, {}).get(neighbor)
            if distance:
                popup_text += f"{neighbor}: {distance:.1f} km<br>"
        
        # Añadir marcador
        folium.CircleMarker(
            location=coords,
            radius=5,
            popup=popup_text,
            color='blue',
            fill=True,
            fill_color='blue'
        ).add_to(marker_group)
        
        # Dibujar líneas con etiquetas de distancia
        for neighbor in neighbors:
            if neighbor in coordinates:
                distance = distances.get(province, {}).get(neighbor)
                if distance:
                    mid_lat = (coords[0] + coordinates[neighbor][0]) / 2
                    mid_lon = (coords[1] + coordinates[neighbor][1]) / 2
                    
                    # Dibujar línea
                    folium.PolyLine(
                        locations=[coords, coordinates[neighbor]],
                        weight=2,
                        color='gray',
                        opacity=0.5
                    ).add_to(marker_group)
                    
                    # Añadir etiqueta de distancia
                    folium.Marker(
                        location=[mid_lat, mid_lon],
                        icon=folium.DivIcon(
                            html=f'<div style="font-size: 10px; color: black;">{distance:.1f} km</div>'
                        )
                    ).add_to(marker_group)
    
    marker_group.add_to(m)
    folium.LayerControl().add_to(m)
    
    # Guardar el mapa y las distancias
    m.save('mapa_provincias_con_distancias.html')
    with open('distancias_provincias.json', 'w', encoding='utf-8') as f:
        json.dump(distances, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    create_map_with_distances()
