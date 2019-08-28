from enum import Enum

class Elos(Enum):
    retardatario = 0
    bronze       = 1
    prata        = 2
    ouro         = 3
    platina      = 4
    diamante     = 5
    mestre       = 6
    grandmestre  = 7

def get_elo(elo_name):
    return Elos[elo_name.lower().replace("á", "a")]

def validate_elo_battle(elo1, elo2):
    diff = abs(elo1.value - elo2.value)
    is_retardatario = elo1 == Elos.retardatario or elo2 == Elos.retardatario
    
    return (diff <= 2) if not is_retardatario else diff <= 1