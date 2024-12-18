import mysql.connector
import random
from datetime import datetime, timedelta
from django.conf import settings

def generate_orders(num_orders, avg_lines_per_order, max_quantity_per_line):
    
    NUM_CUSTOMERS = 100
    NUM_LOCATIONS = 72
    NUM_PRODUCTS = 40
    print(num_orders, avg_lines_per_order, max_quantity_per_line)
    try:
        db_config = settings.DATABASES['default']  # Extrae la config de la BD

        conn = mysql.connector.connect(
            host=db_config['HOST'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            database=db_config['NAME'],
            port=db_config['PORT']
        )
        # Conexión a la base de datos
        cursor = conn.cursor()

        cursor.execute("DELETE FROM order_line")
        cursor.execute("DELETE FROM orders")
        cursor.execute("ALTER TABLE orders AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE order_line AUTO_INCREMENT = 1")

        # Lista de clientes (asegurando que cada cliente solo tenga un pedido)
        customers = list(range(1, NUM_CUSTOMERS + 1))
        random.shuffle(customers)  # Mezclar aleatoriamente los clientes

        # Generar pedidos y líneas de pedido
        for i in range(num_orders):
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
            num_lines = max(1, int(random.gauss(avg_lines_per_order, 2)))  # Promedio de 20 líneas
            for _ in range(num_lines):
                product_id = random.randint(1, NUM_PRODUCTS)
                quantity = random.randint(1, max_quantity_per_line)

                # Insertar línea de pedido
                cursor.execute(
                    "INSERT INTO Order_line (id_order, id_product, quantity) VALUES (%s, %s, %s)",
                    (order_id, product_id, quantity)
                )

        # Confirmar transacciones
        conn.commit()
        print(f"Se han generado {num_orders} pedidos y sus líneas correctamente, uno por cliente.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        if conn.is_connected():
            conn.rollback()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def generate_test_orders():
    try:
        db_config = settings.DATABASES['default']  # Extrae la config de la BD

        conn = mysql.connector.connect(
            host=db_config['HOST'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            database=db_config['NAME'],
            port=db_config['PORT'],
            buffered=True
        )
        # Conexión a la base de datos
        cursor = conn.cursor()

        # Limpiar datos existentes
        cursor.execute("DELETE FROM order_line")
        cursor.execute("DELETE FROM orders")
        cursor.execute("ALTER TABLE orders AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE order_line AUTO_INCREMENT = 1")

        # Ciudades específicas (asumiendo que ya existen en la tabla de destinos)
        ciudades = {
            'Madrid': 26,      # Ajusta estos IDs según tu tabla de destinos
            'Sevilla': 38,
            'Lleida': 23,
            'Bilbao': 8,
            'Zaragoza': 47
        }

        # Generar un pedido para cada ciudad
        for ciudad, destination_id in ciudades.items():
            # Datos del pedido
            customer_id = random.randint(1, 100)  # Cliente aleatorio
            order_date = datetime.now()
            
            # Insertar pedido
            cursor.execute(
                "INSERT INTO Orders (date, id_customer, id_destination) VALUES (%s, %s, %s)",
                (order_date.strftime('%Y-%m-%d'), customer_id, destination_id)
            )
            order_id = cursor.lastrowid  # Obtener el ID del pedido recién insertado

            # Generar 20 líneas de pedido con máximo 500 unidades
            for _ in range(20):
                product_id = random.randint(1, 40)  # Asumiendo 40 productos
                quantity = random.randint(1, 500)

                # Insertar línea de pedido
                cursor.execute(
                    "INSERT INTO Order_line (id_order, id_product, quantity) VALUES (%s, %s, %s)",
                    (order_id, product_id, quantity)
                )

            print(f"Generado pedido para {ciudad} (Destino ID: {destination_id})")

        # Confirmar transacciones
        conn.commit()
        print("Se han generado 5 pedidos de prueba correctamente.")

    except mysql.connector.Error as err:
        print(f"Error completo: {err}")
        print(f"Código de error: {err.errno}")
        print(f"Estado SQL: {err.sqlstate}")
        print(f"Mensaje: {err.msg}")
        if conn.is_connected():
            conn.rollback()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()