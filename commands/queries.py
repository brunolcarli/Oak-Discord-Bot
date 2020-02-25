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
    def get_trainers(id=None):
        """
        Retorna a query de treinadores
        """
        filters = '' if not id else f'(discordId_Icontains:"{id}")' 
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
                        lv
                        discordId
                        fc
                        sdId
                        badgeCounter
                        leaguesCounter
                        exp
                        nextLv
                    }
                }
            }
        }
        ''' % filters

        return gql(query)

    @staticmethod
    def get_leaders(id=None):
        """
        Requisição solicitando a consulta de líderes registrados
        """
        filters = '' if not id else f'(discordId_Icontains:"{id}")'
        query = f'''
          query {{
            leaders {filters} {{
              edges{{
                node{{
                  id
                  discordId
                  lv
                  fc
                  name
                  role
                  pokemonType
                  joinDate
                  battleCounter
                  winPercentage
                  loosePercentage
                  exp
                  nextLv
                  sdId
                }}
              }}
            }}
          }}
        '''

        return gql(query)

    @staticmethod
    def get_scores(league_id):
        """
        Requisição solicitando a consulta do score dos treinadores de uma liga
        """
        query = f'''
        query{{
          scores(league_Id_In: "{league_id}"){{
            edges{{
            node{{
                trainer{{
                  discordId
                  lv
                }}
                wins
                losses
                badges
              }}
            }}
          }}
        }}
        '''
        return gql(query)

    @staticmethod
    def get_trainer_score(discord_id, league_id):
        """
        Solicita o score de um treinador específico em uma liga
        """
        query = f"""
        query scores{{
          scores(
              trainer_DiscordId:  "{discord_id}"
              league_Id_In: "{league_id}"
          ){{
            edges{{
              node{{
                trainer{{
                  discordId
                  lv
                }}
                wins
                losses
                badges
                battles(last: 1){{
                  edges{{
                    node{{
                      battleDatetime
                      winner
                      leader{{
                        discordId
                      }}
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        """
        return gql(query)
