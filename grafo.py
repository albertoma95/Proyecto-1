import mysql.connector
import folium
import json

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

def create_map():
    # Cargar datos
    with open('provincias.json', 'r', encoding='utf-8') as file:
        adjacency = json.load(file)
    
    coordinates = get_coordinates()
    if not coordinates:
        return
    
    # Crear mapa
    m = folium.Map(
        location=[40.416775, -3.703790],
        zoom_start=6,
        tiles='CartoDB positron'
    )
    
    # Grupo de características
    marker_group = folium.FeatureGroup(name="Provincias")
    
    # Añadir marcadores y líneas sin distancias
    for province, coords in coordinates.items():
        neighbors = adjacency.get(province, [])
        popup_text = f"<b>{province}</b><br>Vecinos:<br>" + "<br>".join(neighbors)
        
        # Añadir marcador
        folium.CircleMarker(
            location=coords,
            radius=5,
            popup=popup_text,
            color='blue',
            fill=True,
            fill_color='blue'
        ).add_to(marker_group)
        
        # Dibujar líneas sin etiquetas de distancia
        for neighbor in neighbors:
            if neighbor in coordinates:
                folium.PolyLine(
                    locations=[coords, coordinates[neighbor]],
                    weight=2,
                    color='gray',
                    opacity=0.5
                ).add_to(marker_group)
    
    marker_group.add_to(m)
    folium.LayerControl().add_to(m)
    
    # Guardar el mapa
    m.save('mapa_provincias.html')

if __name__ == "__main__":
    create_map()
