"""
Módulo de configuración de la Base de Datos.

En este archivo se centraliza la lógica de conexión con el servidor MySQL.
Se utiliza la librería PyMySQL para gestionar la comunicación entre
la aplicación Flask y los datos del sistema.
"""

import pymysql

def obtener_conexion():
    """
    Se establece y devuelve una conexión activa con la base de datos.
    
    Se configuran los parámetros de acceso al servidor local y se define
    el uso de DictCursor para que los resultados de las consultas se
    manejen como diccionarios de Python.

    :return: Objeto de conexión a la base de datos MySQL.
    :rtype: pymysql.connections.Connection
    """
    
    # Se recomienda que en un entorno real, se cambien el usuario y contraseña predetermiandos,
    # pero los he mantenido para mayor facilidad de configuración
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        db="tickit_db",
        # AVISO: Por lo general el puerto predeterminado es el 3306, 
        # pero se ha configurado el 3308 debido a problemas que he tenido con XAMPP
        port=3308, 
        cursorclass=pymysql.cursors.DictCursor
    )