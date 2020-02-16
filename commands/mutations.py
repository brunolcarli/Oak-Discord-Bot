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

  @staticmethod
  def league_registration(discord_id, league_id, is_trainer):
    is_trainer = str(is_trainer).lower()
    mutation = f'''
    mutation{{
      leagueRegistration(input:{{
        discordId: "{discord_id}"
        league: "{league_id}"
        isTrainer: {is_trainer}
      }}){{
        registration
      }}
    }}
    '''
    return gql(mutation)

  @staticmethod
  def battle_registration(league_id, trainer_id, leader_id, winner):
    mutation = f'''
        mutation{{
      battleRegister(input:{{
        league:"{league_id}"
        trainer: "{trainer_id}"
        leader: "{leader_id}"
        winner: "{winner}"
      }}){{
        battle{{
          id
          battleDatetime
          winner
        }}
      }}
    }}
    '''
    print(mutation)
    return gql(mutation)

  @staticmethod
  def add_badge(discord_id, badge, league):
    """
    Requisição para Bill solicitando a adição de uma insígnia à um treinador
    """
    mutation = f'''mutation{{
      addBadgeToTrainer(input:{{
        discordId: "{discord_id}"
        badge: "{badge}"
        league: "{league}"
      }}){{
        response
      }}
    }}
    '''
    return gql(mutation)

  @staticmethod
  def update_trainer(discord_id, name=None, fc=None, sd_id=None):
    """
    Requisição para Bill solicitando a alteração dos dados
    de um treinador
    """
    mutation = f'''
    mutation update_trainer{{
      updateTrainer(input:{{
        discordId: "{discord_id}"
        name: "{name if name else ''}"
        fc:"{fc if fc else ''}"
        sdId: "{sd_id if sd_id else ''}"
      }}) {{
        trainer{{
          name
          sdId
          fc
          discordId
        }}
      }}
    }}
    '''

    return gql(mutation)

  @staticmethod
  def update_leader(discord_id, **kwargs):
    """
    TODO docstring
    """
    poke_type = kwargs.get('poke_type')
    poke_type = f'pokemonType: {poke_type.upper()}' if poke_type else ''

    role = kwargs.get('role')
    role = f'role: {role.upper()}' if role else ''

    mutation = f'''
    mutation{{
      updateLeader(input:{{
        discordId: "{discord_id}"
        name: "{kwargs.get('name', '')}"
        {poke_type}
        {role}
        fc:"{kwargs.get('fc', '')}"
        sdId: "{kwargs.get('sd_id', '')}"
        clauses: "{kwargs.get('clauses', '')}"
      }}){{
        leader{{
          name
          role
          pokemonType
          clauses
          fc
          sdId
          discordId
        }}
      }}
    }}
    '''
    print(mutation)
    return gql(mutation)
