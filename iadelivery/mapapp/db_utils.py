import mysql.connector
from django.conf import settings

def get_orders():
    try:
        db_config = settings.DATABASES['default']  # Extrae la config de la BD

        connection = mysql.connector.connect(
            host=db_config['HOST'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            database=db_config['NAME'],
            port=db_config['PORT']
        )
        
        cursor = connection.cursor()

        # Obtener ubicaciones
        cursor.execute("""
            SELECT l.name, l.latitude, l.longitude
            FROM Locations l
        """)
        locations = cursor.fetchall()

        # Obtener pedidos
        cursor.execute("""
            SELECT id_order, name AS destination, expiration_date, total_quantity, order_ready, name, total_cost
            FROM Order_Expiration1
            ORDER BY expiration_date ASC
        """)
        orders = cursor.fetchall()

        cursor.close()
        connection.close()

        return locations, orders

    except mysql.connector.Error as error:
        print(f"Error connecting to MySQL: {error}")
        return [], []
