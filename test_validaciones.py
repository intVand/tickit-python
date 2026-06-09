"""
Módulo de pruebas unitarias para las validaciones del sistema.

En este fichero he implementado diferentes casos de prueba utilizando Pytest
para asegurar que las funciones de validación responden correctamente ante
datos normales, casos límite y errores de tipo.
"""

import pytest
from validaciones import validar_campos_vacios, validar_formato_email, validar_longitud_contrasenya


# Pruebas para validar_campos_vacios

def test_campos_vacios_caso_normal():
    """
    Se comprueba el comportamiento normal con datos válidos.
    """
   
    assert validar_campos_vacios("Juan", "juan@test.com", "password") == True

def test_campos_vacios_caso_limite():
    """
    Se verifican casos donde los campos están vacíos o contienen solo espacios.
    """

    assert validar_campos_vacios("Juan", "", "password") == False
    assert validar_campos_vacios("Juan", "juan@test.com", "    ") == False

def test_campos_vacios_todos_vacios():
    """
    Se analiza el escenario extremo donde no se envía ningún dato.
    """

    assert validar_campos_vacios("", "", "") == False


# Pruebas para validar_formato_email

def test_email_caso_normal():
    """
    Se valida que un correo con estructura estándar sea aceptado.
    """

    assert validar_formato_email("usuario@empresa.com") == True

def test_email_caso_limite():
    """
    Se comprueba que una cadena vacía no se valide como email.
    """

    assert validar_formato_email("") == False

def test_email_caso_incorrecto():
    """
    Se testean formatos de correo mal formados (sin @ o sin dominio).
    """

    assert validar_formato_email("usuario_sin_arroba.com") == False
    assert validar_formato_email("usuario@dominio_sin_punto") == False

def test_email_excepcion():
    """
    Se verifica la gestión de errores cuando el dato no es una cadena de texto.
    """

    with pytest.raises(TypeError):
        validar_formato_email(12345)
    with pytest.raises(TypeError):
        validar_formato_email(None)


# Pruebas para validar_longitud_contrasenya

def test_contrasenya_caso_normal():
    """
    Se valida una contraseña que cumple holgadamente con la longitud mínima.
    """

    assert validar_longitud_contrasenya("SuperSegura123") == True

def test_contrasenya_casos_limite():
    """
    Se testea el límite exacto de 8 caracteres y el valor inmediatamente inferior (7).
    """

    assert validar_longitud_contrasenya("12345678") == True
    assert validar_longitud_contrasenya("1234567") == False

def test_contrasenya_espacios():
    """
    Se comprueba que una contraseña de solo espacios no sea válida.
    """

    assert validar_longitud_contrasenya("        ") == False

def test_contrasenya_excepcion():
    """
    Se asegura que solo se acepten cadenas de texto para la contraseña.
    """
    
    with pytest.raises(TypeError):
        validar_longitud_contrasenya(123456789)