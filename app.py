"""
Módulo principal de la aplicación tickit.

Este script inicializa el servidor Flask, configura la clave de seguridad
y centraliza el registro de todos los Blueprints que componen el sistema.
"""

from flask import Flask
from rutas.usuario import usuario_bp
from rutas.tickets import tickets_bp
from rutas.administrador import administrador_bp

# Inicialización de la instancia de Flask
app = Flask(__name__)

# Se utiliza para cifrar la sesión del lado del cliente.
# En un entorno de producción real, debería cargarse desde variables de entorno
app.secret_key = "5j3jiZJJD4cfUmRyhnXK"

# Se separa la lógica del programa mediante blueprints,
# de está forma el código queda más organizado

# Gestiona Login, Registro y Perfil
app.register_blueprint(usuario_bp)

# Gestiona el Panel de Control, Creación y Edición de Tickets
app.register_blueprint(tickets_bp)

# Gestiona la administración de Usuarios, Departamentos y Auditoría
app.register_blueprint(administrador_bp)

if __name__ == "__main__":
    # Se arranca el servidor en modo depuración,
    # de está forma es más sencillo detectar errores
    app.run(debug=True)