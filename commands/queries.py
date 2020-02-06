"""
Módulo para definição de queries utilizadas para consultar o
serviço de ligas da ABP: Bill API
"""
from gql import gql

def get_leagues(**kwargs):
    """
    Retorna a query de ligas
    """

    query = """
    query{
        leagues{
            edges{
                node{
                    id
                    reference
                    startDate
                    endDate
                    description
                    gymLeaders{
                        edges{
                            node{
                                id
                                name
                                pokemonType
                            }
                        }
                    }
                    eliteFour{
                    edges{
                        node{
                            id
                            name
                            pokemonType
                            }
                    }
                    }
                    champion{
                        id
                        name
                        pokemonType
                    }
                    competitors{
                    edges{
                        node{
                            id
                            name
                            joinDate
                        }
                    }
                    }
                    winner{
                        id
                        name
                    }
                }
            }
        }
    }
    """
    return gql(query)


def get_trainers(**kwargs):
    """
    Retorna a query de treinadores
    """
    query = '''
    query{
        trainers{
            edges{
                node{
                    id
                    name
                    joinDate
                    battleCounter
                    winPercentage
                    loosePercentage
                }
            }
        }
    }
    '''

    return gql(query)
