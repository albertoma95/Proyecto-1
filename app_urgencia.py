import mysql.connector
import folium

# Configuración de base de datos
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'IADelivery'
}

def get_order_urgency():
    """Recupera detalles de pedidos con urgencia de entrega"""
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)
    
    query = """
    SELECT 
        o.id_order, 
        l.name AS location_name, 
        l.latitude, 
        l.longitude,
        MIN(p.expiration_date) AS min_expiration_days,
        GROUP_CONCAT(
            CONCAT(p.name, ' (', ol.quantity, ' unidades, ', p.expiration_date, ' días)') 
            SEPARATOR ', '
        ) AS products
    FROM Orders o
    JOIN Locations l ON o.id_destination = l.id_location
    JOIN Order_line ol ON o.id_order = ol.id_order
    JOIN Products p ON ol.id_product = p.id_product
    GROUP BY o.id_order, l.name, l.latitude, l.longitude
    """
    
    cursor.execute(query)
    orders = cursor.fetchall()
    
    connection.close()
    return orders

def get_marker_color(expiration_days):
    """Determina el color del marcador según días de caducidad"""
    if expiration_days <= 3:
        return 'red'  # Muy urgente
    elif expiration_days <= 7:
        return 'orange'  # Urgente
    elif expiration_days <= 14:
        return 'yellow'  # Moderadamente urgente
    else:
        return 'green'  # No urgente

def create_order_map(orders):
    """Crea mapa con marcadores de pedidos coloreados por urgencia"""
    m = folium.Map(location=[41.54211, 2.4445], zoom_start=7)
    
    for order in orders:
        color = get_marker_color(order['min_expiration_days'])
        
        popup_text = f"""
        <b>Pedido #{order['id_order']}</b><br>
        <b>Ubicación:</b> {order['location_name']}<br>
        <b>Días hasta caducidad:</b> {order['min_expiration_days']}<br>
        <b>Productos:</b> {order['products']}
        """
        
        folium.Marker(
            [order['latitude'], order['longitude']],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"Pedido #{order['id_order']} - Caducidad: {order['min_expiration_days']} días",
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(m)
    
    # Leyenda
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 120px; height: 130px; 
                border:2px solid grey; z-index:9999; font-size:14px;
                background-color:white;
                ">
        <p><span style="color:red;">■</span> 0-3 días: Muy Urgente</p>
        <p><span style="color:orange;">■</span> 4-7 días: Urgente</p>
        <p><span style="color:yellow;">■</span> 8-14 días: Moderado</p>
        <p><span style="color:green;">■</span> +14 días: Normal</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    m.save('pedidos_urgencia_mapa.html')

def main():
    orders = get_order_urgency()
    create_order_map(orders)
    print("Mapa generado como 'pedidos_urgencia_mapa.html'")

if __name__ == "__main__":
    main()