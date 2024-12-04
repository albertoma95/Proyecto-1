import mysql.connector
import folium
import json
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en kilómetros
    
    # Convertir coordenadas a radianes
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Diferencias en coordenadas
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Fórmula Haversine
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

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

def create_weighted_map():
    # Cargar datos
    with open('provincias.json', 'r', encoding='utf-8') as file:
        adjacency = json.load(file)
    
    coordinates = get_coordinates()
    if not coordinates:
        return
    
    # Calcular distancias
    distances = {}
    for province, neighbors in adjacency.items():
        distances[province] = {}
        for neighbor in neighbors:
            if neighbor in coordinates:
                lat1, lon1 = coordinates[province]
                lat2, lon2 = coordinates[neighbor]
                distance = haversine_distance(lat1, lon1, lat2, lon2)
                distances[province][neighbor] = distance
    
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
        # Crear popup con información detallada
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
                    # Calcular punto medio para la etiqueta
                    mid_lat = (coords[0] + coordinates[neighbor][0]) / 2
                    mid_lon = (coords[1] + coordinates[neighbor][1]) / 2
                    
                    # Dibujar línea
                    line = folium.PolyLine(
                        locations=[coords, coordinates[neighbor]],
                        weight=2,
                        color='gray',
                        opacity=0.5,
                        popup=f"{distance:.1f} km"
                    ).add_to(marker_group)
                    
                    # Añadir etiqueta de distancia
                    folium.Popup(
                        f"{distance:.1f} km",
                        permanent=True
                    ).add_to(folium.CircleMarker(
                        location=[mid_lat, mid_lon],
                        radius=1,
                        color="transparent",
                        fill=False
                    ).add_to(marker_group))
    
    marker_group.add_to(m)
    folium.LayerControl().add_to(m)
    
    # Guardar el mapa y las distancias
    m.save('mapa_provincias_distancias.html')
    with open('distancias_provincias.json', 'w', encoding='utf-8') as f:
        json.dump(distances, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    create_weighted_map()