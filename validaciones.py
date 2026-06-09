"""
Módulo de validaciones lógicas del sistema.

En este fichero he centralizado todas las funciones encargadas de verificar
que los datos introducidos por el usuario cumplen con los requisitos mínimos
de seguridad y formato antes de ser procesados por la base de datos.
"""

import re

def validar_campos_vacios(*campos):
    """
    Comprueba si alguno de los campos de texto está vacío o solo contiene espacios.
    
    :param campos: Número variable de cadenas de texto a comprobar.
    :type campos: tuple de str
    :return: True si todos los campos tienen contenido válido, False si alguno está vacío.
    :rtype: bool
    """
    
    for campo in campos:
        if not campo or not campo.strip():
            return False
    return True

def validar_formato_email(email):
    """
    Verifica que una cadena de texto tenga el formato de un correo electrónico válido.
    
    :param email: La dirección de correo a validar.
    :type email: str
    :return: True si el formato es correcto, False en caso contrario o si está vacío.
    :rtype: bool
    :raises TypeError: si 'email' no es una cadena de texto.
    """

    # Se comprueba primero que el tipo de dato sea correcto para evitar errores en tiempo de ejecución.
    if not isinstance(email, str):
        raise TypeError("El email debe ser una cadena de texto")
    
    if not email:
        return False
    
    # He definido una expresión regular estándar para validar la estructura del correo.
    # Se busca que contenga un usuario, el símbolo @, un dominio y una extensión.
    patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(patron, email))

def validar_longitud_contrasenya(contrasenya, longitud_minima=8):
    """
    Comprueba que la contraseña cumpla con la longitud mínima requerida.
    
    :param contrasenya: La contraseña a validar.
    :type contrasenya: str
    :param longitud_minima: Longitud mínima exigida (por defecto 8).
    :type longitud_minima: int
    :return: True si la longitud es válida, False en caso contrario.
    :rtype: bool
    :raises TypeError: si 'contrasenya' no es una cadena de texto.
    """
    
    if not isinstance(contrasenya, str):
        raise TypeError("La contraseña debe ser una cadena de texto")
    
    return len(contrasenya.strip()) >= longitud_minima