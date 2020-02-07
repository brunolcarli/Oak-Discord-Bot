"""
Modulo para requisições de mutation para a API.
"""
from gql import gql

class Mutations:

  @staticmethod
  def create_trainer(discord_id):
      """
      Envia uma requisição para a API solicitando a criação de um treinador.
      """
      mutation = f'''
      mutation{{
        createTrainer(input:{{
          discordId: "{discord_id}"
        }}){{
          trainer{{
            id
            discordId
            name
            joinDate
            battleCounter
            badgeCounter
            leaguesCounter
            winPercentage
            loosePercentage
            lv
            exp
            nextLv
          }}
        }}
      }}
      '''
      return gql(mutation)

  @staticmethod
  def create_league(reference):
    mutation = f'''
      mutation{{
        createLeague(input: {{
          reference: "{reference}"
        }}){{
          league{{
            id
            reference
            startDate
            endDate
          }}
        }}
      }}
    '''
    return gql(mutation)

  @staticmethod
  def create_leader(discord_id, poke_type, role):
    mutation = f'''
    mutation{{
      createLeader(input:{{
        discordId: "{discord_id}"
        pokemonType: {poke_type}
        role: {role}
      }}){{
        leader{{
          id
          name
          role
          pokemonType
          joinDate
          battleCounter
          winPercentage
          loosePercentage
          discordId
          lv
          nextLv
          exp
        }}
      }}
    }}
    '''
    return gql(mutation)
