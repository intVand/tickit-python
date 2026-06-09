"""
Módulo de rutas para la gestión de tickets de soporte técnico.

En este fichero he agrupado todas las rutas asociadas al panel de control 
del usuario común. Se implementan las operaciones principales del CRUD 
para las incidencias, así como los motores de exportación en formatos planos.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from db import obtener_conexion
import json
from datetime import datetime
from auditoria import registrar_evento
from validaciones import validar_campos_vacios

tickets_bp = Blueprint("tickets", __name__)


@tickets_bp.route("/panel_control")
def panel_control():
    """
    Se renderiza el panel de control principal del usuario autenticado.
    
    Se extraen de la base de datos tanto los departamentos disponibles 
    como el historial de incidencias pertenecientes única y exclusivamente 
    al usuario que ha iniciado sesión.

    :return: Plantilla HTML con las tablas y formularios de tickets actualizados.
    :rtype: str
    """

    # Si no hay un usuario en la sesión, lo echamos de vuelta al login
    if "usuario_id" not in session:
        flash("Debes iniciar sesión para acceder al panel.", "warning")
        return redirect(url_for("usuario.login"))
    
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Se obtienen los departamentos para el formulario de crear ticket (Ocultando "Sin asignar")
            cursor.execute("SELECT id, nombre FROM departamentos WHERE nombre != 'Sin asignar'")
            departamentos = cursor.fetchall()
            
            # Se obtienen SOLO los tickets del usuario logueado
            sql_tickets = """
                SELECT t.id, t.titulo, t.descripcion, t.id_departamento, t.estado, 
                       t.fecha_creacion, t.fecha_resolucion, d.nombre as departamento,
                       u_tec.nombre as tecnico_asignado
                FROM tickets t
                JOIN departamentos d ON t.id_departamento = d.id
                LEFT JOIN asignaciones_tickets at ON t.id = at.id_ticket
                LEFT JOIN usuarios u_tec ON at.id_tecnico = u_tec.id
                WHERE t.id_usuario = %s
                ORDER BY t.fecha_creacion DESC
            """
            cursor.execute(sql_tickets, (session["usuario_id"],))
            mis_tickets = cursor.fetchall()
    finally:
        conexion.close()
        
    return render_template("panel_control.html", departamentos=departamentos, tickets=mis_tickets)


@tickets_bp.route("/crear_ticket", methods=["POST"])
def crear_ticket():
    """
    Se procesa el formulario enviado para registrar una nueva incidencia.
    
    Se capturan los parámetros del formulario, se descartan entradas vacías 
    mediante el módulo de validaciones y se efectúa la inserción SQL.

    :return: Redirección al panel de control con el mensaje de estado del proceso.
    :rtype: werkzeug.wrappers.Response
    """

    if "usuario_id" not in session:
        return redirect(url_for("usuario.login"))
        
    titulo = request.form.get("titulo", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    id_departamento = request.form.get("id_departamento")
    
    if not validar_campos_vacios(titulo, descripcion, id_departamento):
        flash("Todos los campos son obligatorios para crear un ticket.", "danger")
        return redirect(url_for("tickets.panel_control"))
        
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """INSERT INTO tickets (titulo, descripcion, id_usuario, id_departamento) 
                     VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql, (titulo, descripcion, session["usuario_id"], id_departamento))
        conexion.commit()
        flash("Ticket creado correctamente.", "success")
    except Exception as e:
        flash("Error al crear el ticket.", "danger")
    finally:
        conexion.close()
        
    return redirect(url_for("tickets.panel_control"))


@tickets_bp.route("/eliminar_ticket/<int:id_ticket>", methods=["POST"])
def eliminar_ticket(id_ticket):
    """
    Se ejecuta el borrado físico de un ticket de la base de datos.
    
    Se comprueba previamente que el solicitante sea el propietario del ticket
    y que la incidencia no haya cambiado a un estado activo o cerrado.

    :param id_ticket: El identificador único del ticket a eliminar.
    :type id_ticket: int
    :return: Redirección al panel de control con confirmación de la eliminación.
    :rtype: werkzeug.wrappers.Response
    """

    if "usuario_id" not in session:
        return redirect(url_for("usuario.login"))
        
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Primero verificamos si el ticket es del usuario y si su estado es "Pendiente"
            cursor.execute("SELECT estado FROM tickets WHERE id = %s AND id_usuario = %s", (id_ticket, session["usuario_id"]))
            ticket = cursor.fetchone()
            
            # Solo se pueden eliminar tickets "Pendientes"
            if ticket and ticket["estado"] == "Pendiente":
                # Auditoria de borrado de tickets
                registrar_evento(f"Ticket #{id_ticket} ha sido eliminado por el propietario")
                
                cursor.execute("DELETE FROM tickets WHERE id = %s", (id_ticket,))
                conexion.commit()
                flash("Ticket eliminado correctamente.", "success")
            else:
                flash("No tienes permiso para eliminar este ticket o ya está en progreso.", "danger")
    finally:
        conexion.close()
        
    return redirect(url_for("tickets.panel_control"))


@tickets_bp.route("/editar_ticket/<int:id_ticket>", methods=["POST"])
def editar_ticket(id_ticket):
    """
    Se procesan los cambios de una incidencia existente del usuario.
    
    Se extraen los nuevos textos ingresados, se validan contra nulos y 
    se actualizan en el servidor si los permisos del ticket son correctos.

    :param id_ticket: El identificador del ticket.
    :type id_ticket: int
    :return: Redirección de vuelta al panel con el mensaje flash correspondiente.
    :rtype: werkzeug.wrappers.Response
    """

    if "usuario_id" not in session:
        return redirect(url_for("usuario.login"))
        
    nuevo_titulo = request.form.get("titulo", "").strip()
    nueva_descripcion = request.form.get("descripcion", "").strip()
    nuevo_departamento = request.form.get("id_departamento")
    
    if not validar_campos_vacios(nuevo_titulo, nueva_descripcion, nuevo_departamento):
        flash("No puedes dejar campos vacíos al editar el ticket.", "danger")
        return redirect(url_for("tickets.panel_control"))

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Verificamos que sea del usuario y el estado permita la edición
            cursor.execute("SELECT estado FROM tickets WHERE id = %s AND id_usuario = %s", (id_ticket, session["usuario_id"]))
            ticket = cursor.fetchone()
            
            # No se podrán editar tickets que ya hayan sido resueltos por un técnico
            if ticket and ticket["estado"] in ["Pendiente", "En Progreso"]:
                sql = "UPDATE tickets SET titulo = %s, descripcion = %s, id_departamento = %s WHERE id = %s"
                cursor.execute(sql, (nuevo_titulo, nueva_descripcion, nuevo_departamento, id_ticket))
                conexion.commit()
                flash("Ticket actualizado correctamente.", "success")
            else:
                flash("Este ticket no se puede editar porque ya está resuelto.", "danger")
    finally:
        conexion.close()
        
    return redirect(url_for("tickets.panel_control"))


# Exportación de datos (TXT y JSON)

@tickets_bp.route("/exportar_mis_tickets_txt")
def exportar_mis_tickets_txt():
    """
    Se genera dinámicamente un archivo de texto plano descargable (.txt).
    
    Se recogen los datos actuales del usuario, se parsean línea a línea 
    en formato legible y se devuelven encapsulados en un flujo HTTP de descarga.

    :return: Objeto Response de Flask configurado como descarga de texto adjunto.
    :rtype: flask.Response
    """

    if "usuario_id" not in session:
        return redirect(url_for("usuario.login"))
        
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT t.id, t.titulo, t.descripcion, t.estado, t.fecha_creacion, t.fecha_resolucion, d.nombre as departamento
                FROM tickets t
                JOIN departamentos d ON t.id_departamento = d.id
                WHERE t.id_usuario = %s
                ORDER BY t.fecha_creacion DESC
            """
            cursor.execute(sql, (session["usuario_id"],))
            tickets = cursor.fetchall()
    finally:
        conexion.close()

    contenido = f"=== MIS TICKETS - {session.get('usuario_nombre')} ===\n"
    contenido += f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    for t in tickets:

        # Se asegura de establecer como "No resuelto", en caso de que no haya fecha de resolución
        fecha_res = t["fecha_resolucion"].strftime('%d/%m/%Y %H:%M') if t["fecha_resolucion"] else "No resuelto"

        contenido += f"Ticket #{t['id']} | Estado: {t['estado']}\n"
        contenido += f"Título: {t['titulo']}\n"
        contenido += f"Descripción: {t['descripcion']}\n"
        contenido += f"Departamento: {t['departamento']}\n"
        contenido += f"Fecha de reporte: {t['fecha_creacion'].strftime('%d/%m/%Y %H:%M')}\n"
        contenido += f"Fecha de resolución: {fecha_res}\n"
        contenido += "-" * 50 + "\n"

    return Response(
        contenido,
        mimetype="text/plain",
        headers={"Content-disposition": "attachment; filename=mis_tickets.txt"}
    )

@tickets_bp.route("/exportar_mis_tickets_json")
def exportar_mis_tickets_json():
    """
    Se exporta el historial completo de incidencias en un estándar legible JSON.
    
    Se aplica una rutina interna de serialización para los campos de tipo datetime 
    que MySQL devuelve y que el módulo nativo json de Python no puede procesar directamente.

    :return: Respuesta HTTP con cabecera application/json adaptada como attachment.
    :rtype: flask.Response
    """

    if "usuario_id" not in session:
        return redirect(url_for("usuario.login"))
        
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT t.id, t.titulo, t.descripcion, t.estado, t.fecha_creacion, t.fecha_resolucion, 
                       d.nombre as departamento
                FROM tickets t
                JOIN departamentos d ON t.id_departamento = d.id
                WHERE t.id_usuario = %s
            """
            cursor.execute(sql, (session["usuario_id"],))
            tickets = cursor.fetchall()
    finally:
        conexion.close()

    def serializador_fechas(obj):
        # He creado esta subfunción de serialización para transformar las fechas en texto legible por JSON
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return str(obj)

    contenido_json = json.dumps(tickets, default=serializador_fechas, indent=4, ensure_ascii=False)

    return Response(
        contenido_json,
        mimetype="application/json",
        headers={"Content-disposition": "attachment; filename=mis_tickets.json"}
    )