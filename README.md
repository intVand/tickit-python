# Tickit - Sistema Integral de Gestión de Incidencias (Helpdesk)

**Tickit** es una aplicación web completa desarrollada en Python utilizando el microframework **Flask** y una base de datos relacional **MySQL**. El sistema emula un entorno empresarial real de soporte técnico corporativo, permitiendo a los empleados de una organización reportar incidencias técnicas, de infraestructura o conectividad, mientras que ofrece al equipo técnico y de administración un panel centralizado para gestionar, asignar y resolver las solicitudes mediante un flujo de estados dinámico.

Este desarrollo forma parte de mi porfolio personal para demostrar competencias sólidas en arquitectura modular de software, persistencia relacional, control de accesos basado en roles (RBAC) y fases de calidad mediante pruebas automatizadas.

---

## Características Principales

* **Autenticación y Control de Sesiones:** Login centralizado mediante formularios seguros con persistencia en el servidor a través del objeto `session` de Flask y limpieza total de cookies en el logout.
* **Seguridad por Roles (RBAC) en Backend:** La seguridad no depende del HTML. Cada controlador valida el rol de la sesión activa directamente en Python:
    * **Rol Usuario:** Acceso exclusivo a su panel personal. Puede crear incidencias y visualizar/editar únicamente sus propios registros mediante consultas parametrizadas con filtrado obligatorio por ID de usuario.
    * **Rol Administrador:** Acceso completo (CRUD) para la gestión global de tickets, administración de cuentas de usuario, creación y modificación de departamentos corporativos y lectura de logs.
* **Integridad Referencial Controlada:** Base de datos relacional robusta con borrados en cascada (`ON DELETE CASCADE`). Incluye una regla de negocio avanzada en el backend: si se elimina un departamento operativo, todos sus tickets se reasignan automáticamente a un registro neutro llamado *'Sin asignar'*, impidiendo errores foráneos o registros huérfanos.
* **Exportación Dinámica de Datos:** Motores de extracción de reportes integrados que generan descargas directas en el navegador en formatos estructurados `.txt` (formateado para lectura rápida) y `.json` (preparado para interoperabilidad con otros sistemas).
* **Entorno 100% Offline (UI/UX):** Interfaz fluida maquetada con **Bootstrap 5** y **Bootstrap Icons** descargados localmente en el directorio de recursos estáticos, garantizando un funcionamiento autónomo sin dependencias de conexiones externas o CDNs.

---

## Ecosistema Tecnológico

* **Lenguaje:** `Python 3.14.0`
* **Framework Backend:** `Flask 3.1.3` (Estructurado de forma limpia mediante *Blueprints*)
* **Base de Datos:** `MySQL` / `MariaDB` (Puerto local de desarrollo: 3308)
* **Conector BD:** `PyMySQL 1.1.3`
* **Gestor de Contraseñas:** `Werkzeug 3.1.8` (Hashing asimétrico mediante algoritmo `scrypt`)
* **Testing:** `Pytest 9.0.3` (Pruebas unitarias automatizadas)
* **Documentación:** `Pydoc` (Generador automatizado de manuales técnicos en HTML)
* **Frontend:** `HTML5`, `CSS3`, `Jinja2 3.1.6 Templates`, `Bootstrap 5`

---

## Módulo de Valor Añadido: Logs de Auditoría

Para dotar al sistema de herramientas de control reales, se implementó un motor de auditoría persistente (`auditoria.py`). Cada acción crítica (inicios de sesión, creación de incidencias o eliminaciones de registros) se estampa de forma inmutable en un archivo local `auditoria.log` con marcas de tiempo detalladas. 

El panel del administrador incorpora una consola interactiva que lee este fichero, extrae **únicamente las últimas 50 acciones** (optimizando el uso de memoria RAM del servidor) y les aplica un reverso lógico para mostrar siempre los eventos más recientes en la parte superior con estética de terminal CLI.

---

## Estructura del Proyecto

```text
├── rutas/                    # Blueprints modulares (usuario, tickets, administrador)
├── static/                   # Estilos CSS, fuentes y librerías de Bootstrap (Modo Offline)
├── templates/                # Vistas HTML dinámicas gestionadas con Jinja2
├── Documentación con Pydoc/  # Manuales de código generados con Pydoc y capturas de calidad
├── app.py                    # Punto de entrada y arranque de la aplicación web
├── db.py                     # Configuración y pool de conexiones a MySQL
├── validaciones.py           # Funciones puras de validación de formularios
├── test_validaciones.py      # Banco de pruebas unitarias automatizadas con Pytest
├── auditoria.py              # Motor lógico del sistema de logs y auditoría
├── requirements.txt          # Archivo de congelación de dependencias del proyecto
└── tickit_db.sql             # Script SQL de inicialización completa de la Base de Datos
```

---

## Instalación y Puesta en Marcha (Desarrollo Local)

### 1. Clonar el repositorio y preparar el entorno

```bash
git clone https://github.com/intVand/tickit.git
cd tickit

# Crear e iniciar el entorno virtual (Recomendado)
python -m venv venv
# Activar en Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Instalar todas las dependencias necesarias
pip install -r requirements.txt
```

### 2. Despliegue de la Base de Datos
1. Levanta tu servidor local de bases de datos (XAMPP / WampServer) configurado en el puerto 3308.

2. Importa el archivo tickit_db.sql en tu gestor de confianza (phpMyAdmin). El script cuenta con sentencias de control IF NOT EXISTS por lo que creará la estructura relacional y los datos de prueba de forma totalmente automatizada.

### 3. Lanzar el Servidor

```bash
python app.py
```

Navega en tu navegador web a la dirección de escucha local: `http://localhost:5000`

---

## Calidad de Software y Documentación

### Ejecución de Tests Automatizados
La lógica de control de formularios está respaldada por pruebas unitarias que analizan casos normales, strings vacíos y excepciones de tipo. Puedes ejecutar el banco de pruebas con:

```bash
python -m pytest -v
```

### Documentación del Código Fuente
La documentación técnica autogenerada a partir de los Docstrings del código se encuentra disponible abriendo los ficheros HTML interactivos dentro de la carpeta `/Documentación con Pydoc`.

---

## Credenciales de Acceso para Pruebas

El volcado de la base de datos incluye dos perfiles preconfigurados para comprobar la escalabilidad de roles de forma inmediata:

| Rol del Sistema | Correo Electrónico | Contraseña de Entrada |
| :--- | :--- | :--- |
| **Administrador** | ivan@fixer.com | 12345678 |
| **Usuario Estándar** | jose@fixer.com | 87654321 |