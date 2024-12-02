import mysql.connector
import pandas as pd

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'IADelivery'
}

def obtener_dataframe_productos():
    connection = mysql.connector.connect(**DB_CONFIG)
    
    query = """
    SELECT 
        p.id_product,
        o.id_order,
        o.id_destination AS location_id,
        DATE_ADD(o.date, INTERVAL (p.manufacturing_time + p.expiration_date) DAY) AS expiration_date,
        SUM(ol.quantity) AS total_quantity
    FROM 
        Products p
    JOIN Order_line ol ON p.id_product = ol.id_product
    JOIN Orders o ON ol.id_order = o.id_order
    GROUP BY 
        p.id_product, 
        o.id_order, 
        o.id_destination, 
        o.date, 
        p.manufacturing_time, 
        p.expiration_date
    ORDER BY 
        p.id_product
    """
    
    df_productos = pd.read_sql(query, connection)
    
    connection.close()
    
    return df_productos

def main():
    df_productos = obtener_dataframe_productos()
    print(df_productos)
    
    df_productos.to_csv('productos_detalle.csv', index=False)

if __name__ == "__main__":
    main()