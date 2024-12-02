import mysql.connector
import folium

def conectar_mysql():
    conexion = mysql.connector.connect(
        host='localhost',
        user='root',
        password='1234',
        database='IADelivery'
    )
    return conexion, conexion.cursor(dictionary=True)

def crear_mapa_ubicaciones():
    # Conectar a la base de datos
    conexion, cursor = conectar_mysql()
    
    # Consultar ubicaciones
    cursor.execute("SELECT * FROM Locations")
    ubicaciones = cursor.fetchall()
    
    # Crear mapa centrado en España
    mapa = folium.Map(location=[40.4637, -3.7492], zoom_start=6)
    
    # Añadir marcadores
    for ubicacion in ubicaciones:
        folium.Marker(
            location=[ubicacion['latitude'], ubicacion['longitude']],
            popup=f"{ubicacion['name']} ({ubicacion['region']})",
            tooltip=ubicacion['name']
        ).add_to(mapa)
    
    # Guardar mapa
    mapa.save("mapa_ubicaciones_espana.html")
    
    # Cerrar conexiones
    cursor.close()
    conexion.close()

    print("Mapa generado exitosamente en mapa_ubicaciones_espana.html")

# Ejecutar generación de mapa
crear_mapa_ubicaciones()