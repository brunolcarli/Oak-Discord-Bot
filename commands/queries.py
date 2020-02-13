"""
Módulo para definição de queries utilizadas para consultar o
serviço de ligas da ABP: Bill API
"""
from gql import gql


class Query:
    """
    Queries GraphQL
    """

    @staticmethod
    def get_leagues(id=None):
        """
        Retorna a query de ligas
        """
        filters = '' if not id else f'(id:"{id}")' 
        query = '''
        query {
            leagues %s {
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
        ''' % filters

        return gql(query)

    @staticmethod
    def get_trainers(**kwargs):
        """
        Retorna a query de treinadores
        """
        filters = ' '.join([f'{k}:"{v}"' for k, v in kwargs.items()])
        query = '''
        query {
            trainers %s {
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
        ''' % '' if not filters else f'({filters})'

        return gql(query)
