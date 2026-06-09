"""
Módulo de administración global y supervisión del sistema tickit.

En este fichero he concentrado todo el núcleo de control exclusivo para el perfil 
de administrador (rol 1). Maneja los flujos avanzados de CRUD para tickets cruzados,
usuarios, departamentos relacionales, exportaciones completas y lectura del archivo de logs.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
import pymysql
from db import obtener_conexion
from werkzeug.security import generate_password_hash
import json
from datetime import datetime
from auditoria import registrar_evento
import os
from validaciones import validar_campos_vacios, validar_formato_email, validar_longitud_contrasenya

administrador_bp = Blueprint("administrador", __name__)


@administrador_bp.route("/panel_administrador")
def panel_administrador():
    """
    Se renderiza la interfaz del centro de control del Administrador.
    
    Se verifica rigurosamente el rol de la sesión activa y se realizan múltiples
    consultas SQL concurrentes para poblar las pestañas de control. Además, se 
    vuelcan las líneas del fichero de log físico de manera inversa.

    :return: Plantilla HTML del panel global inyectada con todas las colecciones de datos.
    :rtype: str
    """

    # Solo puede entrar si tiene sesión y si su rol es 1 (Admin)
    if session.get("usuario_rol") != 1:
        flash("Acceso denegado. Área exclusiva para administradores.", "danger")
        return redirect(url_for("usuario.login"))
        
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Se extraen los tickets del sistema
            sql_tickets = """
                SELECT t.id, t.titulo, t.descripcion, t.id_departamento, t.estado, t.fecha_creacion, t.fecha_resolucion, 
                       d.nombre as departamento, u_creador.nombre as creador, 
                       u_tec.nombre as tecnico_asignado, at.id_tecnico as id_tecnico_asignado
                FROM tickets t
                JOIN departamentos d ON t.id_departamento = d.id
                JOIN usuarios u_creador ON t.id_usuario = u_creador.id
                LEFT JOIN asignaciones_tickets at ON t.id = at.id_ticket
                LEFT JOIN usuarios u_tec ON at.id_tecnico = u_tec.id
                ORDER BY t.fecha_creacion DESC
            """
            cursor.execute(sql_tickets)
            todos_los_tickets = cursor.fetchall()
            
            # Se extraen todos los departamentos (Ocultando el "Sin asignar")
            cursor.execute("SELECT id, nombre, edificio FROM departamentos WHERE nombre != 'Sin asignar' ORDER BY nombre ASC")
            todos_los_departamentos = cursor.fetchall()

            # Se extraen todos los usuarios y sus respectivos roles
            sql_usuarios = """
                SELECT u.id, u.nombre, u.email, u.id_rol, r.nombre_rol 
                FROM usuarios u
                JOIN roles r ON u.id_rol = r.id
                ORDER BY u.id ASC
            """
            cursor.execute(sql_usuarios)
            todos_los_usuarios = cursor.fetchall()

            cursor.execute("SELECT id, nombre_rol FROM roles")
            todos_los_roles = cursor.fetchall()

            # Se extrae la lista de técnicos habilitados (en este caso usuarios con rol de administrador)
            cursor.execute("SELECT id, nombre FROM usuarios WHERE id_rol = 1")
            lista_tecnicos = cursor.fetchall()
            
    finally:
        conexion.close()

    # Se procesa la lectura y formateo del archivo físico de auditoría
    logs_auditoria = []
    if os.path.exists("auditoria.log"):
        with open("auditoria.log", "r", encoding="utf-8") as archivo_log:
            lineas = archivo_log.readlines()
            # Se cogen las últimas 50 líneas y las invertimos (las más nuevas primero)
            logs_auditoria = lineas[-50:]
            logs_auditoria.reverse()
    else:
        logs_auditoria.append("El archivo de auditoría aún no se ha creado o está vacío.")    
        
    return render_template("panel_administrador.html", tickets=todos_los_tickets, departamentos=todos_los_departamentos, usuarios=todos_los_usuarios, roles=todos_los_roles, tecnicos=lista_tecnicos, logs=logs_auditoria)


# Sección: CRUD de Tickets

@administrador_bp.route("/actualizar_estado_ticket/<int:id_ticket>", methods=["POST"])
def actualizar_estado_ticket(id_ticket):
    """
    Se procesa el cambio de estado rápido desde las opciones de la tabla.
    
    Actualiza el estado, conmuta la fecha de resolución según corresponda 
    y manipula la inserción/borrado en la tabla intermedia de asignaciones.

    :param id_ticket: Clave primaria del ticket a actualizar.
    :type id_ticket: int
    :return: Redirección inmediata al panel de administrador.
    :rtype: werkzeug.wrappers.Response
    """

    if session.get("usuario_rol") != 1:
        flash("Acceso denegado.", "danger")
        return redirect(url_for("usuario.login"))
        
    nuevo_estado = request.form.get("estado")
    tecnico_actual_id = session["usuario_id"]
    
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Se actualiza estado y fecha de resolución automáticamente
            if nuevo_estado == "Resuelto":
                sql_ticket = "UPDATE tickets SET estado = %s, fecha_resolucion = NOW() WHERE id = %s"
            else:
                sql_ticket = "UPDATE tickets SET estado = %s, fecha_resolucion = NULL WHERE id = %s"
            
            cursor.execute(sql_ticket, (nuevo_estado, id_ticket))
            
            # Se gestiona la asignación del técnico en la tabla intermedia
            if nuevo_estado == "Pendiente":
                cursor.execute("DELETE FROM asignaciones_tickets WHERE id_ticket = %s", (id_ticket,))
            else:
                cursor.execute("SELECT id FROM asignaciones_tickets WHERE id_ticket = %s", (id_ticket,))
                asignacion_existe = cursor.fetchone()
                
                if asignacion_existe:
                    sql_asignacion = "UPDATE asignaciones_tickets SET id_tecnico = %s WHERE id_ticket = %s"
                    cursor.execute(sql_asignacion, (tecnico_actual_id, id_ticket))
                else:
                    sql_asignacion = "INSERT INTO asignaciones_tickets (id_ticket, id_tecnico) VALUES (%s, %s)"
                    cursor.execute(sql_asignacion, (id_ticket, tecnico_actual_id))
                    
            conexion.commit()
            flash(f"Ticket #{id_ticket} actualizado a '{nuevo_estado}'.", "success")
    except Exception as e:
        flash("Error al actualizar el estado del ticket.", "danger")
    finally:
        conexion.close()

    return redirect(url_for("administrador.panel_administrador"))    

@administrador_bp.route("/editar_ticket_admin/<int:id_ticket>", methods=["POST"])
def editar_ticket_admin(id_ticket):
    """
    Se ejecuta el formulario de edición avanzada y reasignación de un ticket.

    :param id_ticket: Identificador único de la incidencia.
    :type id_ticket: int
    :return: Redirección al panel con mensaje flash informativo.
    :rtype: werkzeug.wrappers.Response
    """

    if session.get("usuario_rol") != 1:
        return redirect(url_for("usuario.login"))
        
    titulo = request.form.get("titulo", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    id_departamento = request.form.get("id_departamento")
    estado = request.form.get("estado")
    id_tecnico = request.form.get("id_tecnico") # Puede venir vacío si está en "Pendiente"
    
    if not validar_campos_vacios(titulo, descripcion, id_departamento, estado):
        flash("Todos los campos del ticket son obligatorios.", "warning")
        return redirect(url_for("administrador.panel_administrador"))

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Se actualizan los datos básicos del ticket y la fecha según el estado
            if estado == "Resuelto":
                sql_ticket = "UPDATE tickets SET titulo=%s, descripcion=%s, id_departamento=%s, estado=%s, fecha_resolucion=NOW() WHERE id=%s"
            else:
                sql_ticket = "UPDATE tickets SET titulo=%s, descripcion=%s, id_departamento=%s, estado=%s, fecha_resolucion=NULL WHERE id=%s"
            
            cursor.execute(sql_ticket, (titulo, descripcion, id_departamento, estado, id_ticket))
            
            # Lógica del técnico
            if estado == "Pendiente":
                # Si vuelve a pendiente, se borra la relación para que quede libre
                cursor.execute("DELETE FROM asignaciones_tickets WHERE id_ticket = %s", (id_ticket,))
            elif id_tecnico:
                # Si está En Progreso o Resuelto, se asigna/actualiza al técnico
                cursor.execute("SELECT id FROM asignaciones_tickets WHERE id_ticket = %s", (id_ticket,))
                if cursor.fetchone():
                    cursor.execute("UPDATE asignaciones_tickets SET id_tecnico = %s WHERE id_ticket = %s", (id_tecnico, id_ticket))
                else:
                    cursor.execute("INSERT INTO asignaciones_tickets (id_ticket, id_tecnico) VALUES (%s, %s)", (id_ticket, id_tecnico))
                    
        conexion.commit()
        flash("Ticket modificado correctamente por el administrador.", "success")
    except Exception as e:
        flash("Error al modificar el ticket.", "danger")
    finally:
        conexion.close()
        
    return redirect(url_for("administrador.panel_administrador"))


@administrador_bp.route("/eliminar_ticket_admin/<int:id_ticket>", methods=["POST"])
def eliminar_ticket_admin(id_ticket):
    """
    Se elimina un ticket del sistema de forma irreversible.

    :param id_ticket: El identificador único del ticket.
    :type id_ticket: int
    :return: Redirección al panel del administrador.
    :rtype: werkzeug.wrappers.Response
    """

    if session.get("usuario_rol") != 1:
        return redirect(url_for("usuario.login"))
        
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Auditoria de eliminación de tickets
            registrar_evento(f"ADMIN eliminó el Ticket #{id_ticket}")

            cursor.execute("DELETE FROM tickets WHERE id = %s", (id_ticket,))
        conexion.commit()
        flash("Ticket eliminado definitivamente.", "success")
    except Exception as e:
        flash("Error al eliminar el ticket.", "danger")
    finally:
        conexion.close()
        
    return redirect(url_for("administrador.panel_administrador"))


# Sección: CRUD de departamentos

@administrador_bp.route("/crear_departamento", methods=["POST"])
def crear_departamento():
    """
    Se registra un nuevo departamento en la base de datos.

    :return: Redirección al panel administrativo.
    :rtype: werkzeug.wrappers.Response
    """

    if session.get("usuario_rol") != 1:
        return redirect(url_for("usuario.login"))
        
    nombre = request.form.get("nombre", "").strip()
    edificio = request.form.get("edificio", "").strip()
    
    if not validar_campos_vacios(nombre, edificio):
        flash("Todos los campos del departamento son obligatorios.", "warning")
        return redirect(url_for("administrador.panel_administrador"))
        
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("INSERT INTO departamentos (nombre, edificio) VALUES (%s, %s)", (nombre, edificio))
        conexion.commit()
        flash("Departamento creado con éxito.", "success")
    finally:
        conexion.close()
        
    return redirect(url_for("administrador.panel_administrador"))


@administrador_bp.route("/editar_departamento/<int:id_departamento>", methods=["POST"])
def editar_departamento(id_departamento):
    """
    Se modifican las propiedades de un departamento existente.

    :param id_departamento: Clave única del departamento.
    :type id_departamento: int
    :return: Redirección al panel con confirmación.
    :rtype: werkzeug.wrappers.Response
    """

    if session.get("usuario_rol") != 1:
        return redirect(url_for("usuario.login"))
        
    nuevo_nombre = request.form.get("nombre", "").strip()
    nuevo_edificio = request.form.get("edificio", "").strip()
    
    if not validar_campos_vacios(nuevo_nombre, nuevo_edificio):
        flash("Los campos del departamento no pueden estar vacíos.", "warning")
        return redirect(url_for("administrador.panel_administrador"))

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("UPDATE departamentos SET nombre = %s, edificio = %s WHERE id = %s", 
                           (nuevo_nombre, nuevo_edificio, id_departamento))
        conexion.commit()
        flash("Departamento actualizado correctamente.", "success")
    finally:
        conexion.close()
        
    return redirect(url_for("administrador.panel_administrador"))


@administrador_bp.route("/eliminar_departamento/<int:id_departamento>", methods=["POST"])
def eliminar_departamento(id_departamento):
    """
    Se procesa la baja de un departamento del sistema de forma segura.
    
    He resuelto la restricción de integridad foránea reasignando automáticamente
    todos los tickets huérfanos a un departamento neutro 'Sin asignar'.

    :param id_departamento: Clave a remover del sistema.
    :type id_departamento: int
    :return: Redirección al panel del administrador.
    :rtype: werkzeug.wrappers.Response
    """

    if session.get("usuario_rol") != 1:
        return redirect(url_for("usuario.login"))
        
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Se obtiene el ID del departamento "Sin asignar"
            cursor.execute("SELECT id FROM departamentos WHERE nombre = 'Sin asignar'")
            depto_neutro = cursor.fetchone()
            
            if not depto_neutro:
                flash("Error: El departamento 'Sin asignar' no existe en la base de datos.", "danger")
                return redirect(url_for("administrador.panel_administrador"))
                
            id_sin_asignar = depto_neutro["id"]
                
            # Se reasignan los tickets al departamento "Sin asignar"
            sql_reasignar = "UPDATE tickets SET id_departamento = %s WHERE id_departamento = %s"
            cursor.execute(sql_reasignar, (id_sin_asignar, id_departamento))
            
            # Se borra el departamento viejo
            # Auditoria de eliminación de departamentos
            registrar_evento(f"ADMIN eliminó el departamento con ID: {id_departamento}")

            cursor.execute("DELETE FROM departamentos WHERE id = %s", (id_departamento,))
            
        conexion.commit()
        flash("Departamento eliminado. Los tickets asociados se han movido a 'Sin asignar'.", "success")
        
    except Exception as e:
        flash("Hubo un error al eliminar el departamento.", "danger")
    finally:
        conexion.close()
        
    return redirect(url_for("administrador.panel_administrador"))


# Sección: CRUD de usuarios

@administrador_bp.route("/crear_usuario", methods=["POST"])
def crear_usuario():
    """
    Se registra de forma directa un nuevo usuario o administrador en el sistema.

    :return: Redirección al panel de administración.
    :rtype: werkzeug.wrappers.Response
    """

    if session.get("usuario_rol") != 1:
        return redirect(url_for("usuario.login"))
        
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip()
    contrasenya = request.form.get("contrasenya", "").strip()
    id_rol = request.form.get("id_rol")
    
    if not validar_campos_vacios(nombre, email, contrasenya, id_rol):
        flash("Todos los campos son obligatorios.", "warning")
        return redirect(url_for("administrador.panel_administrador"))
        
    if not validar_formato_email(email):
        flash("El formato del correo electrónico no es válido.", "danger")
        return redirect(url_for("administrador.panel_administrador"))
        
    if not validar_longitud_contrasenya(contrasenya):
        flash("La contraseña debe tener al menos 8 caracteres.", "danger")
        return redirect(url_for("administrador.panel_administrador"))

    contrasenya_encriptada = generate_password_hash(contrasenya)
    
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "INSERT INTO usuarios (nombre, email, contrasenya, id_rol) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (nombre, email, contrasenya_encriptada, id_rol))
        conexion.commit()
        flash("Usuario creado con éxito.", "success")
    except pymysql.err.IntegrityError:
        flash("Error: Ya existe un usuario con ese correo electrónico.", "danger")
    finally:
        conexion.close()
        
    return redirect(url_for("administrador.panel_administrador"))


@administrador_bp.route("/editar_usuario/<int:id_usuario>", methods=["POST"])
def editar_usuario(id_usuario):
    """
    Se modifican los privilegios, credenciales e identidad de un perfil de usuario.

    :param id_usuario: El ID del usuario que se va a editar.
    :type id_usuario: int
    :return: Redirección de vuelta al panel de administrador.
    :rtype: werkzeug.wrappers.Response
    """

    if session.get("usuario_rol") != 1:
        return redirect(url_for("usuario.login"))
        
    nuevo_nombre = request.form.get("nombre", "").strip()
    nuevo_email = request.form.get("email", "").strip()
    nueva_contrasenya = request.form.get("contrasenya", "").strip()
    nuevo_rol = request.form.get("id_rol")
    
    if not validar_campos_vacios(nuevo_nombre, nuevo_email, nuevo_rol):
        flash("Nombre, correo y rol son campos obligatorios.", "warning")
        return redirect(url_for("administrador.panel_administrador"))
        
    if not validar_formato_email(nuevo_email):
        flash("El formato del correo electrónico no es válido.", "danger")
        return redirect(url_for("administrador.panel_administrador"))
        
    # La contraseña se valida solo si se intenta cambiar    
    if nueva_contrasenya and not validar_longitud_contrasenya(nueva_contrasenya):
        flash("La nueva contraseña debe tener al menos 8 caracteres.", "danger")
        return redirect(url_for("administrador.panel_administrador"))

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Si el admin ha escrito una contraseña nueva, se actualiza cifrada
            if nueva_contrasenya:
                contrasenya_encriptada = generate_password_hash(nueva_contrasenya)
                sql = "UPDATE usuarios SET nombre = %s, email = %s, contrasenya = %s, id_rol = %s WHERE id = %s"
                cursor.execute(sql, (nuevo_nombre, nuevo_email, contrasenya_encriptada, nuevo_rol, id_usuario))
            # Si se deja en blanco, se actualizan el resto de datos pero se mantiene su contraseña actual
            else:
                sql = "UPDATE usuarios SET nombre = %s, email = %s, id_rol = %s WHERE id = %s"
                cursor.execute(sql, (nuevo_nombre, nuevo_email, nuevo_rol, id_usuario))
                
        conexion.commit()
        flash("Usuario actualizado correctamente.", "success")
    except pymysql.err.IntegrityError:
        flash("Error: El correo electrónico introducido ya pertenece a otro usuario.", "danger")
    finally:
        conexion.close()
        
    return redirect(url_for("administrador.panel_administrador"))


@administrador_bp.route("/eliminar_usuario/<int:id_usuario>", methods=["POST"])
def eliminar_usuario(id_usuario):
    """
    Se remueve un usuario de la base de datos aplicando reglas de seguridad.

    :param id_usuario: El ID del usuario seleccionado.
    :type id_usuario: int
    :return: Redirección al panel con el resultado flash.
    :rtype: werkzeug.wrappers.Response
    """

    if session.get("usuario_rol") != 1:
        return redirect(url_for("usuario.login"))
        
    # Un admin no puede borrar su propia cuenta activa
    if id_usuario == session["usuario_id"]:
        flash("Por seguridad, no puedes eliminar tu propia cuenta mientras estás logueado.", "danger")
        return redirect(url_for("administrador.panel_administrador"))
        
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Auditoria de eliminación de usuarios
            registrar_evento(f"ADMIN eliminó al usuario con ID: {id_usuario}")

            cursor.execute("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
        conexion.commit()
        flash("Usuario eliminado del sistema.", "success")
    except Exception as e:
        flash("No se puede eliminar el usuario (probablemente tenga tickets asociados o resueltos).", "danger")
    finally:
        conexion.close()
        
    return redirect(url_for("administrador.panel_administrador"))


# Exportación de datos (TXT y JSON)

@administrador_bp.route("/exportar_tickets_txt")
def exportar_tickets_txt():
    """
    Se genera y descarga un informe textual de auditoría total de tickets.

    :return: Objeto Response de Flask configurado como descarga de texto adjunto.
    :rtype: flask.Response
    """

    if session.get("usuario_rol") != 1:
        return redirect(url_for("usuario.login"))
        
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT t.id, t.titulo, t.descripcion, t.estado, t.fecha_creacion, t.fecha_resolucion, d.nombre as departamento, u.nombre as creador
                FROM tickets t
                JOIN departamentos d ON t.id_departamento = d.id
                JOIN usuarios u ON t.id_usuario = u.id
                ORDER BY t.fecha_creacion DESC
            """
            cursor.execute(sql)
            tickets = cursor.fetchall()
    finally:
        conexion.close()

    contenido = "=== REPORTE GENERAL DE TICKETS - TICKIT ===\n"
    contenido += f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    for t in tickets:

        # Se asegura de establecer como "No resuelto", en caso de que no haya fecha de resolución
        fecha_res = t["fecha_resolucion"].strftime('%d/%m/%Y %H:%M') if t["fecha_resolucion"] else "No resuelto"

        contenido += f"Ticket #{t['id']} | Estado: {t['estado']}\n"
        contenido += f"Título: {t['titulo']}\n"
        contenido += f"Descripción: {t['descripcion']}\n"
        contenido += f"Departamento: {t['departamento']}\n"
        contenido += f"Creado por: {t['creador']} el {t['fecha_creacion'].strftime('%d/%m/%Y %H:%M')}\n"
        contenido += f"Fecha de resolución: {fecha_res}\n"
        contenido += "-" * 50 + "\n"

    # Se envia el archivo al navegador como descarga
    return Response(
        contenido,
        mimetype="text/plain",
        headers={"Content-disposition": "attachment; filename=reporte_tickets.txt"}
    )

@administrador_bp.route("/exportar_tickets_json")
def exportar_tickets_json():
    """
    Se exporta el historial completo de incidencias en un estándar legible JSON.
    
    Se aplica una rutina interna de serialización para los campos de tipo datetime 
    que MySQL devuelve y que el módulo nativo json de Python no puede procesar directamente.

    :return: Respuesta HTTP con cabecera application/json adaptada como attachment.
    :rtype: flask.Response
    """

    if session.get("usuario_rol") != 1:
        return redirect(url_for("usuario.login"))
        
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT t.id, t.titulo, t.descripcion, t.estado, t.fecha_creacion, t.fecha_resolucion, 
                       d.nombre as departamento, u.nombre as creador
                FROM tickets t
                JOIN departamentos d ON t.id_departamento = d.id
                JOIN usuarios u ON t.id_usuario = u.id
            """
            cursor.execute(sql)
            tickets = cursor.fetchall()
    finally:
        conexion.close()

    def serializador_fechas(obj):
        # He creado esta subfunción de serialización para transformar las fechas en texto legible por JSON
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return str(obj)

    # Se convierte la lista de diccionarios a formato JSON con indentación para que sea legible
    contenido_json = json.dumps(tickets, default=serializador_fechas, indent=4, ensure_ascii=False)

    return Response(
        contenido_json,
        mimetype="application/json",
        headers={"Content-disposition": "attachment; filename=reporte_tickets.json"}
    )
