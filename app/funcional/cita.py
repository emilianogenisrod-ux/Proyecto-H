"""Cálculo del fin de una cita con funciones que no cambian los datos de entrada.

Los minutos se cuentan desde la medianoche.
Ejemplo: las 9:00 son 540 minutos.
"""

from __future__ import annotations

MINUTOS_DEL_DIA = 24 * 60
DURACION_MINIMA = 5
DURACION_MAXIMA = 240


def duracion_es_valida(duracion_minutos) -> bool:
    """Una duración válida es un número entero entre 5 y 240 minutos."""
    if isinstance(duracion_minutos, bool) or not isinstance(duracion_minutos, int):
        return False
    return DURACION_MINIMA <= duracion_minutos <= DURACION_MAXIMA


def inicio_es_valido(inicio_minutos) -> bool:
    """La hora de inicio debe caber dentro del mismo día."""
    if isinstance(inicio_minutos, bool) or not isinstance(inicio_minutos, int):
        return False
    return 0 <= inicio_minutos < MINUTOS_DEL_DIA


def calcular_fin_cita(inicio_minutos, duracion_minutos) -> dict:
    """Devuelve un resultado nuevo. No modifica lo que recibió."""
    if not duracion_es_valida(duracion_minutos):
        return {
            "aceptada": False,
            "mensaje": "La duración no es válida. Use un número entre 5 y 240 minutos.",
            "fin": None,
        }
    if not inicio_es_valido(inicio_minutos):
        return {
            "aceptada": False,
            "mensaje": "La hora de inicio no es válida.",
            "fin": None,
        }
    fin = inicio_minutos + duracion_minutos
    if fin > MINUTOS_DEL_DIA:
        return {
            "aceptada": False,
            "mensaje": "La cita se sale del día.",
            "fin": None,
        }
    return {
        "aceptada": True,
        "mensaje": "Cita dentro del horario.",
        "fin": fin,
        "inicio": inicio_minutos,
        "duracion": duracion_minutos,
    }


def aplicar_a_varias(citas: list[dict]) -> list[dict]:
    """Recorre varias citas y arma una lista nueva, sin cambiar la original."""
    return list(
        map(
            lambda cita: calcular_fin_cita(cita["inicio"], cita["duracion"]),
            citas,
        )
    )
