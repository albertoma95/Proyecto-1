import mysql.connector
import tkinter as tk
from tkinter import ttk

class DatabaseViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Visor de Base de Datos IADelivery")
        self.root.geometry("800x600")

        # Crear notebook (pestañas)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tablas de la base de datos
        self.tablas = ['Locations', 'Products', 'Customers', 'Orders', 'Order_line']

        # Conexión a la base de datos
        self.conexion, self.cursor = self.conectar_mysql()

        # Crear pestañas para cada tabla
        if self.conexion and self.cursor:
            for tabla in self.tablas:
                self.crear_pestaña(tabla)

    def conectar_mysql(self):
        try:
            conexion = mysql.connector.connect(
                host='localhost',
                user='root',
                password='1234',
                database='IADelivery'
            )
            
            if conexion.is_connected():
                cursor = conexion.cursor(dictionary=True)
                return conexion, cursor
        
        except mysql.connector.Error as error:
            tk.messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos: {error}")
        
        return None, None

    def crear_pestaña(self, tabla):
        # Crear frame para la pestaña
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=tabla)

        # Crear Treeview
        tree = ttk.Treeview(frame)
        tree.pack(fill=tk.BOTH, expand=True)

        # Obtener columnas
        self.cursor.execute(f"SHOW COLUMNS FROM {tabla}")
        columnas = [columna['Field'] for columna in self.cursor.fetchall()]

        # Configurar columnas
        tree['columns'] = columnas
        tree.heading('#0', text='')
        tree.column('#0', width=0, stretch=tk.NO)
        
        for columna in columnas:
            tree.heading(columna, text=columna)
            tree.column(columna, anchor=tk.CENTER)

        # Obtener datos
        self.cursor.execute(f"SELECT * FROM {tabla}")
        datos = self.cursor.fetchall()

        # Insertar datos
        for i, registro in enumerate(datos):
            valores = [registro[col] for col in columnas]
            tree.insert(parent='', index='end', iid=i, values=valores)

        # Añadir scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def __del__(self):
        if hasattr(self, 'conexion') and self.conexion and self.conexion.is_connected():
            self.cursor.close()
            self.conexion.close()

def main():
    root = tk.Tk()
    app = DatabaseViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()