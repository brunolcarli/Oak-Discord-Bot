"""
Módulo contendo dados específicos para o sistema de elos da ABP.
"""

from enum import Enum


ELOS_MAP = [
    ["grand mestre", 0x303030, "http://bit.ly/2Zyf0fv"],
    ["mestre", 0x80e891, "http://bit.ly/2ZNonYV"],
    ["diamante", 0x59d0e4, "http://bit.ly/34jdT2M"],
    ["platina", 0xd7d7d7, "http://bit.ly/32nmwHw"],
    ["ouro", 0xbfa617, "http://bit.ly/2HE0wQR"],
    ["prata", 0x8e8e8e, "http://bit.ly/2HCsbSr"],
    ["bronze", 0xc0702d, "http://bit.ly/2ZMhKWM"],
    ["retardatario", 0xb73232, "http://bit.ly/2ZGr8qJ"]
]


class Elos(Enum):
    """
    Enumerador para tradução dos valores dos elos.
    """
    retardatario = 0
    bronze = 1
    prata = 2
    ouro = 3
    platina = 4
    diamante = 5
    mestre = 6
    grandmestre = 7


def get_elo(elo_name):
    """
    Retorna um o elo solicitado.
    """

    return Elos[elo_name.lower().replace("á", "a")]


def validate_elo_battle(elo1, elo2):
    """
    Realiza a validação de uma batalha entre elos diferentes.
    Deve haver uma diferença entre dois elos para retardatário.
    Do contrário a diferença deve ser de um elo.
    """
    diff = abs(elo1.value - elo2.value)
    is_retardatario = elo1 == Elos.retardatario or elo2 == Elos.retardatario

    return (diff <= 2) if not is_retardatario else diff <= 1
