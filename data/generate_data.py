import mysql.connector
import random
from datetime import datetime, timedelta

# Configuración de la conexión a MySQL
db_config = {
    'host': 'localhost',  # Cambia según tu configuración
    'user': 'root',       # Usuario de la base de datos
    'password': '1234',   # Contraseña de la base de datos
    'database': 'iadelivery'  # Nombre de la base de datos
}

# Parámetros de generación
NUM_ORDERS = 100
AVG_LINES_PER_ORDER = 20
MAX_QUANTITY_PER_LINE = 500
NUM_CUSTOMERS = 100
NUM_LOCATIONS = 72
NUM_PRODUCTS = 40

def generate_orders():
    try:
        # Conexión a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Lista de clientes (asegurando que cada cliente solo tenga un pedido)
        customers = list(range(1, NUM_CUSTOMERS + 1))
        random.shuffle(customers)  # Mezclar aleatoriamente los clientes

        # Generar pedidos y líneas de pedido
        for i in range(NUM_ORDERS):
            # Datos del pedido
            customer_id = customers[i]  # Cliente único para este pedido
            destination_id = random.randint(1, NUM_LOCATIONS)
            order_date = datetime.now()
            
            # Insertar pedido
            cursor.execute(
                "INSERT INTO Orders (date, id_customer, id_destination) VALUES (%s, %s, %s)",
                (order_date.strftime('%Y-%m-%d'), customer_id, destination_id)
            )
            order_id = cursor.lastrowid  # Obtener el ID del pedido recién insertado

            # Generar líneas de pedido
            num_lines = max(1, int(random.gauss(AVG_LINES_PER_ORDER, 2)))  # Promedio de 20 líneas
            for _ in range(num_lines):
                product_id = random.randint(1, NUM_PRODUCTS)
                quantity = random.randint(1, MAX_QUANTITY_PER_LINE)

                # Insertar línea de pedido
                cursor.execute(
                    "INSERT INTO Order_line (id_order, id_product, quantity) VALUES (%s, %s, %s)",
                    (order_id, product_id, quantity)
                )

        # Confirmar transacciones
        conn.commit()
        print(f"Se han generado {NUM_ORDERS} pedidos y sus líneas correctamente, uno por cliente.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        if conn.is_connected():
            conn.rollback()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Ejecutar el script
if __name__ == "__main__":
    generate_orders()
