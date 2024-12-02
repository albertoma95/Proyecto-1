import mysql.connector
from faker import Faker

# Configuración de la conexión a MySQL
db_config = {
    'host': 'localhost',  # Cambia según tu configuración
    'user': 'root',       # Usuario de la base de datos
    'password': '1234',   # Contraseña de la base de datos
    'database': 'iadelivery'  # Nombre de la base de datos
}

# Número de clientes a generar
NUM_CUSTOMERS = 100

def generate_customers():
    fake = Faker('es_ES')  # Configuración regional para datos en español
    try:
        # Conexión a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Generar clientes
        for customer_id in range(1, NUM_CUSTOMERS + 1):
            name = fake.name()
            email = fake.email()
            
            # Insertar cliente
            cursor.execute(
                "INSERT INTO customers (id_customer, name, email) VALUES (%s, %s, %s)",
                (customer_id, name, email)
            )

        # Confirmar transacciones
        conn.commit()
        print(f"Se han generado {NUM_CUSTOMERS} clientes correctamente.")

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
    generate_customers()
