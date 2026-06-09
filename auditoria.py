"""
Módulo de Auditoría del sistema tickit.

Se encarga de gestionar el registro de eventos en un archivo físico (log).
De esta forma, se mantiene un control de seguridad sobre las acciones 
que realizan tanto los usuarios como el administrador.
"""

from datetime import datetime
from flask import session

def registrar_evento(accion):
    """
    Se guarda una línea en el archivo auditoria.log con los detalles de la acción.
    
    Se extrae la información del usuario desde la sesión actual y se 
    añade una marca de tiempo antes de escribir en el fichero.

    :param accion: Descripción de la tarea o evento realizado.
    :type accion: str
    :raises Exception: Si ocurre un error al abrir o escribir en el archivo de log.
    """

    # Se obtienen los datos de la sesión o valores por defecto si no hay usuario logueado
    nombre_usuario = session.get("usuario_nombre", "Invitado/Sistema")
    usuario_id = session.get("usuario_id", "N/A")
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Se formatea la línea del log con una estructura clara para su posterior lectura
    linea_log = f"[{fecha_hora}] [ID-USUARIO: {usuario_id}] [NOMBRE: {nombre_usuario}] -> ACCIÓN: {accion}\n"
    
    # Se abre el archivo en modo "a" (append) para añadir información al final del fichero
    try:
        with open("auditoria.log", "a", encoding="utf-8") as archivo:
            archivo.write(linea_log)
    except Exception as e:
        # En caso de error, se muestra por consola para no interrumpir el flujo del programa
        print(f"Error al escribir en el log: {e}")