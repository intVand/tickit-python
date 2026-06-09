"""
Módulo de rutas para la gestión de usuarios y accesos en tickit.

En este fichero he centralizado el controlador que maneja la autenticación,
el registro de nuevas cuentas, la actualización del perfil y la baja de usuarios.
Se coordina la seguridad del lado del servidor mediante hashes y sesiones.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import re
from db import obtener_conexion
from auditoria import registrar_evento
from validaciones import validar_campos_vacios, validar_formato_email, validar_longitud_contrasenya

usuario_bp = Blueprint("usuario", __name__)


@usuario_bp.route("/")
def index():
    """
    Se renderiza la página de presentación o Landing Page del proyecto.

    :return: Plantilla HTML estática de bienvenida.
    :rtype: str
    """

    return render_template("index.html")

@usuario_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Se gestiona el acceso de los usuarios al sistema web.
    
    Si la petición es POST, se capturan y limpian las credenciales, se valida
    que no haya campos vacíos y se contrasta la contraseña en texto plano
    contra el hash almacenado de manera segura en la base de datos.

    :return: Redirección al panel o renderizado del formulario de acceso.
    :rtype: str o werkzeug.wrappers.Response
    """

    if request.method == "POST":
        # Capturamos los datos que el usuario escribió en el formulario
        email = request.form.get("email", "").strip()
        contrasenya = request.form.get("contrasenya", "").strip()
        
        # Se validan que no hayan campos vacios
        if not validar_campos_vacios(email, contrasenya):
            flash("Debes rellenar todos los campos para iniciar sesión.", "danger")
            return redirect(url_for("usuario.login"))

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                # Buscamos si existe un usuario con ese email
                sql = "SELECT id, nombre, email, contrasenya, id_rol FROM usuarios WHERE email = %s"
                cursor.execute(sql, (email,))
                usuario = cursor.fetchone() # Nos devuelve un diccionario con los datos o None
                
                # Si el usuario existe y la contraseña coincide con el hash guardado
                if usuario and check_password_hash(usuario["contrasenya"], contrasenya):
                    # Se limpian sesiones viejas por seguridad y se guardan los datos
                    session.clear()
                    session["usuario_id"] = usuario["id"]
                    session["usuario_nombre"] = usuario["nombre"]
                    session["usuario_rol"] = usuario["id_rol"]
                    
                    # Auditoria de inicio de sesión
                    registrar_evento("Inicio de sesión exitoso")    

                    flash("¡Bienvenid@ de nuevo a Tickit!", "success")
                    return redirect(url_for("tickets.panel_control"))
                else:
                    flash("Correo o contraseña incorrectos.", "danger")
                    return redirect(url_for("usuario.login"))
                    
        except Exception as e:
            flash("Error al conectar con la base de datos.", "danger")
            return redirect(url_for("usuario.login"))
        finally:
            conexion.close() 
        
    # Si entra por GET (simplemente haciendo clic en el enlace), le mostramos el HTML
    return render_template("login.html")

@usuario_bp.route("/registro", methods=["GET", "POST"])
def registro():
    """
    Se procesa el alta de nuevas cuentas de usuario en el sistema.
    
    Se encadena las tres funciones de validación. 
    Si todas pasan, se encripta la contraseña utilizando 
    algoritmos de hashing y se persiste el registro en la base de datos.

    :return: Redirección a la pantalla de login o renderizado del formulario.
    :rtype: str o werkzeug.wrappers.Response
    """

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        contrasenya = request.form.get("contrasenya", "").strip()

        # Validar campos vacíos
        if not validar_campos_vacios(nombre, email, contrasenya):
            flash("Todos los campos son obligatorios. No se permiten solo espacios.", "danger")
            return redirect(url_for("usuario.registro"))
            
        # Validar formato de email
        if not validar_formato_email(email):
            flash("El formato del correo electrónico no es válido.", "danger")
            return redirect(url_for("usuario.registro"))
            
        # Validar longitud de contraseña
        if not validar_longitud_contrasenya(contrasenya):
            flash("La contraseña debe tener al menos 8 caracteres.", "danger")
            return redirect(url_for("usuario.registro"))

        # Se cifra la contraseña antes de guardarla
        contrasenya_encriptada = generate_password_hash(contrasenya)

        # Se asigna el rol 2 por defecto (Usuario)
        rol_por_defecto = 2 
        
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                sql = "INSERT INTO usuarios (nombre, email, contrasenya, id_rol) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (nombre, email, contrasenya_encriptada, rol_por_defecto))
            conexion.commit()
            
            # Auditoria de registro de usuario
            registrar_evento(f"Nuevo usuario registrado: {email}")

            # Se manda un mensaje a la siguiente pantalla
            flash("Cuenta creada correctamente. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("usuario.login"))
            
        except:
            # Si el email ya existe en la base de datos, saltará este error
            flash("Ese correo electrónico ya está registrado.", "danger")
            return redirect(url_for("usuario.registro"))
        finally:
            conexion.close()

    return render_template("registro.html")

@usuario_bp.route("/perfil", methods=["GET", "POST"])
def perfil():
    """
    Se gestiona la visualización y actualización de los datos del propio usuario.
    
    Permite cambiar el nombre y la contraseña actual. Si la contraseña se 
    envía vacía, el sistema inteligentemente actualiza solo el campo del nombre.

    :return: Plantilla HTML de configuración de perfil con los datos del usuario.
    :rtype: str o werkzeug.wrappers.Response
    """

    if "usuario_id" not in session:
        return redirect(url_for("usuario.login"))

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            if request.method == "POST":
                nuevo_nombre = request.form.get("nombre", "").strip()
                nueva_contrasenya = request.form.get("contrasenya", "").strip()
                
                if not validar_campos_vacios(nuevo_nombre):
                    flash("El nombre no puede estar vacío.", "warning")
                    return redirect(url_for("usuario.perfil"))

                if nueva_contrasenya:
                    if not validar_longitud_contrasenya(nueva_contrasenya):
                        flash("La nueva contraseña debe tener al menos 8 caracteres.", "danger")
                        return redirect(url_for("usuario.perfil"))
                    
                    contrasenya_encriptada = generate_password_hash(nueva_contrasenya)
                    sql = "UPDATE usuarios SET nombre = %s, contrasenya = %s WHERE id = %s"
                    cursor.execute(sql, (nuevo_nombre, contrasenya_encriptada, session["usuario_id"]))
                else:
                    sql = "UPDATE usuarios SET nombre = %s WHERE id = %s"
                    cursor.execute(sql, (nuevo_nombre, session["usuario_id"]))
                
                conexion.commit()
                # Se actualiza el nombre en la sesión actual para que cambie en la barra superior
                session["usuario_nombre"] = nuevo_nombre 
                flash("Tu perfil ha sido actualizado correctamente.", "success")
                return redirect(url_for("usuario.perfil"))

            # Si es por GET, simplemente extraemos sus datos para mostrarlos en el formulario
            cursor.execute("SELECT nombre, email, id_rol FROM usuarios WHERE id = %s", (session["usuario_id"],))
            usuario_actual = cursor.fetchone()
            
    finally:
        conexion.close()
        
    return render_template("perfil.html", usuario=usuario_actual)


@usuario_bp.route("/eliminar_mi_cuenta", methods=["POST"])
def eliminar_mi_cuenta():
    """
    Se tramita la baja definitiva del usuario del sistema.
    
    Se bloquea la acción para administradores y se ejecuta la eliminación.
    Los registros vinculados en otras tablas se eliminan por cascada en la BD.

    :return: Redirección a la landing page tras limpiar la sesión del navegador.
    :rtype: werkzeug.wrappers.Response
    """

    if "usuario_id" not in session:
        return redirect(url_for("usuario.login"))
        
    # Los administradores no pueden eliminarse su propia cuenta por seguridad    
    if session.get("usuario_rol") == 1:
        flash("Los administradores no pueden eliminar su propia cuenta por razones de seguridad.", "danger")
        return redirect(url_for("usuario.perfil"))

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Auditoria de borrado de cuentas
            registrar_evento("El usuario ha eliminado su propia cuenta")

            # Gracias al ON DELETE CASCADE, esto borra al usuario y todos sus tickets asociados
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (session["usuario_id"],))
        conexion.commit()
        session.clear() # Cerramos su sesión
        flash("Tu cuenta y todos tus datos han sido eliminados de Tickit.", "info")
        return redirect(url_for("usuario.login"))
    except Exception as e:
        flash("Hubo un error al intentar eliminar tu cuenta.", "danger")
        return redirect(url_for("usuario.perfil"))
    finally:
        conexion.close()

@usuario_bp.route("/cerrar_sesion")
def cerrar_sesion():
    """
    Se destruye la sesión del cliente para salir de la aplicación de forma segura.

    :return: Redirección al formulario de acceso.
    :rtype: werkzeug.wrappers.Response
    """
    
    session.clear() # Borra todos los datos de la sesión actual
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("usuario.login"))