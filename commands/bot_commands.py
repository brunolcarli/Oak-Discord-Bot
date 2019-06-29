from random import choice
import discord
from discord.ext import commands
from util.general_tools import get_similar_pokemon
from util.get_api_data import (dex_information, get_pokemon_data, 
                            get_item_data, item_information,
                            get_ability_data, ability_information)
from settings import LISA_URL
import requests
import json
from tabulate import tabulate


# TODO - move this to a constants, settings or config file
class ErrorResponses:
    E404 = 'Não encontrei esta informação! (E404)'
    E111 = 'Agora estou ocupado. A Lisa está dodói. (E111)'
    E112 = 'Agora não posso, a pokedex quebrou, estou consertando. (E112)'


client = commands.Bot(command_prefix='/')

@client.event
async def on_ready():
    print("The bot is ready!")

@client.event
async def on_member_join(member):
    print('{} entrou no rolê!'.format(member))

@client.event
async def on_member_remove(member):
    print('{} saiu do rolê!'.format(member))

@client.command()
async def ping(ctx):
    await ctx.send('pong')

@client.command()
async def dex(ctx, pokemon):
    '''
    Responde informações sobre um pokemon
    '''
    poke = get_pokemon_data(pokemon.lower())
    response = dex_information(poke)
    if not response:
        response = 'Pokémon não registrado na PokeDex.\n'
        response += 'Talvez você queira dizer: {}'.format(
            get_similar_pokemon(pokemon)
        )

    await ctx.send(response)

@client.command()
async def item(ctx, item):
    '''
    Responde informações sobre um item
    '''
    data = get_item_data(item.lower())
    response = item_information(data)
    await ctx.send(response)

@client.command()
async def regras_liga(ctx):
    '''
    Responde com as regras da liga
    '''
    with open('files/regras_da_liga.txt', 'r') as f:
        rules = f.readlines()
    await ctx.send(''.join(line for line in rules))

@client.command()
async def ability(ctx, ability):
    '''
    Responde informações sobre uma habilidade
    '''
    data = get_ability_data(ability.lower())
    response = ability_information(data)
    await ctx.send(response)

@client.command()
async def frase_do_sidney(ctx):
    options = ['VAI SER EMOCIONANTE!', 'manicaca']
    await ctx.send(choice(options))

@client.command()
async def quote(ctx, *phrase):
    '''
    Salva uma mensagem como quote para ser eternamente lembrado
    '''
    if phrase:
        quoted = ' '.join(word for word in phrase)

        part_1 = "{\"query\":\"mutation{\\n  createAbpQuote(input:{\\n    quote: \\\" " 
        part_2 = "\\\"\\n  }){\\n    response\\n  }\\n}\"}"
        headers = {
            'content-type': "application/json"
            }
        payload = part_1 + quoted + part_2
        response = requests.request("POST", LISA_URL, data=payload, headers=headers)
        response = json.loads(response.text)
        response = response['data']['createAbpQuote'].get('response')

    else:
        response = "Insira alguma pérola!"

    await ctx.send(response)

@client.command()
async def random_quote(ctx):
    '''
    Retorna um quote aleatório
    '''
    payload = "{\"query\":\"query{\\n  abpQuotes\\n}\"}"
    headers = {
        'content-type': "application/json"
        }

    response = requests.request("POST", LISA_URL, data=payload, headers=headers)
    response = json.loads(response.text)
    quotes = response['data'].get('abpQuotes')

    await ctx.send(choice(quotes))

@client.command()
async def random_pokemon(ctx):
    '''
    Responde com um pokémon aleatório
    '''
    with open('files/pokes.txt', 'r') as f:
        pokes = f.readlines()

    i_choose_you = choice(pokes).split('\n')[0]
    poke = get_pokemon_data(i_choose_you.lower())
    response = dex_information(poke)
    await ctx.send(response)

@client.command()
async def gugasaur(ctx):
    '''
    Responde com o pokemon do guga
    '''
    poke = get_pokemon_data('tyrantrum')
    response = dex_information(poke)

    await ctx.send(response)

@client.command()
async def trainer_register(ctx, nickname=''):
    '''
    Registra um treinador na liga
    '''
    user_permissions = set([i.name for i in ctx.author.roles])
    if 'ADM' not in user_permissions:
        oak_response = 'Você não tem permissão para isso!'

    else:

        if not nickname:
            oak_response = 'Por favor insira o nickname do treinador'
        
        else:

            part_1 = "{\"query\":\"mutation createTrainer{\\n  createTrainer(input:{\\n    nickname: \\\""
            part_2 = "\\\"\\n  }){\\n    trainer{\\n      id\\n      nickname\\n      isWinner\\n      numWins\\n      numLosses\\n      numBattles\\n      badges{\\n        id\\n        reference\\n      }\\n    }\\n  }\\n}\\n\",\"operationName\":\"createTrainer\"}"

            headers = {
                'content-type': "application/json"
                }

            payload = part_1 + nickname + part_2

            response = requests.request("POST", LISA_URL, data=payload, headers=headers)
            response = json.loads(response.text)
            trainer = response['data']['createTrainer'].get('trainer')

            badges = ', '.join(badge for badge in trainer.get('badges'))

            oak_response = '\nTREINADOR REGISTRADO:\n\n'
            oak_response += 'Nick: {}\n'.format(
                trainer.get('nickname')
            )
            oak_response += 'Vitórias: {}\nDerrotas: {}\n'.format(
                trainer.get('numWins'),
                trainer.get('numLosses')
            )
            oak_response += 'Batalhas Disputadas: {}\n'.format(
                trainer.get('numBattles')
            )
            oak_response += 'Insígnias conquistadas:\n{}\n\n'.format(
                badges
            )
    await ctx.send(oak_response)

@client.command()
async def league_trainers(ctx):
    '''
    Retorna uma lista com o nickname de todos os treinadores
    registrados na liga.
    '''
    payload = "{\"query\":\"query trainers{\\n  abpTrainers{\\n    nickname\\n\\t}\\n}\\n\\n\",\"operationName\":\"trainers\"}"
    headers = {
        'content-type': "application/json"
    }

    response = requests.request("POST", LISA_URL, data=payload, headers=headers)
    response = json.loads(response.text)
    trainer_list = response['data'].get('abpTrainers')
    trainers = '\n'.join(trainer.get('nickname') for trainer in trainer_list)

    await ctx.send(trainers)

@client.command()
async def trainer(ctx, nickname=''):
    '''
    Retorna informações de um trainer.
    '''
    if not nickname:
        oak_response = 'Insira o nickname do treinador'
    else:

        part_1 = "{\"query\":\"query trainers{\\n  abpTrainers(nickname: \\\""
        
        part_2 = "\\\"){\\n    nickname\\n    numWins\\n    numLosses\\n    numBattles\\n    badges{\\n      reference\\n    }\\n    battles{\\n      leader{\\n        nickname\\n      }\\n      winner\\n      battleDatetime\\n    }\\n\\t}\\n}\\n\\n\",\"operationName\":\"trainers\"}"
        headers = {
            'content-type': "application/json"
        }
        payload = part_1 + nickname + part_2

        response = requests.request("POST", LISA_URL, data=payload, headers=headers)
        response = json.loads(response.text)

        trainer = response['data'].get('abpTrainers')
        if not trainer:
            oak_response = 'Treinador não cadastrado! Você inseriu o nickname corretamente?'

        else:

            # Processa as insignias do treinador
            badges = ', '.join(
                badge.get('reference', '') for badge in trainer[0].get('badges')
            )

            # Processa as batalhas disputadas pelo jogador
            battles = '\n'.join(
                '\nDATA: {}\nVS: {}\nVencedor: {}\n'.format(
                    b.get('battleDatetime'),
                    b['leader'].get('nickname'),
                    b.get('winner')
                ) for b in trainer[0].get('battles')
            )

            oak_response = '\nINFO TRAINER:\n\n'
            oak_response += 'NICK: {}\n'.format(
                trainer[0].get('nickname')
            )
            oak_response += 'VITÓRIAS: {}\nDERROTAS: {}\n'.format(
                trainer[0].get('numWins'),
                trainer[0].get('numLosses')
            )
            oak_response += 'BATALHAS DISPUTADAS: {}\n'.format(
                trainer[0].get('numBattles')
            )
            oak_response += 'INSÍGNIAS CONQUISTADAS: \n{}\n\n'.format(
                badges
            )
            oak_response += 'REGISTRO DE BATALHAS: \n{}\n'.format(
                battles
            )

        await ctx.send(oak_response)

@client.command()
async def league_leaders(ctx):
    '''
    Retorna todos os líderes e elites
    '''

    payload = "{\"query\":\"query{\\n  abpLeaders{\\n    nickname\\n  role\\n  pokemonType\\n  }\\n}\"}"
    headers = {
        'content-type': "application/json"
    }

    try:
        response = requests.request(
            "POST",
            LISA_URL,
            data=payload,
            headers=headers
        )
    except:
        await ctx.send(ErrorResponses.E111)

    response = json.loads(response.text)
    leaders_list = response['data'].get('abpLeaders')
    leaders = '\n'.join(
        'Nick: {} - {} : {}'.format(
            leader.get('nickname'),
            leader.get('role'),
            leader.get('pokemonType')
        ) for leader in leaders_list
    )

    await ctx.send(leaders)

@client.command()
async def leader(ctx, nickname=''):
    '''
    Retorna informações de um líder da liga.
    '''
    if not nickname:
        oak_response = 'Insira o nickname do líder'

    else:
        part_1 = "{\"query\":\"query{\\n  abpLeaders(nickname: \\\""
        part_2 = "\\\"){\\n    nickname\\n    numWins\\n    numLosses\\n    numBattles\\n    battles{\\n      trainer{\\n        nickname\\n      }\\n      winner\\n      battleDatetime\\n    }\\n  }\\n}\"}"
        headers = {
            'content-type': "application/json"
        }
        payload = part_1 + nickname + part_2
        try:
            response = requests.request("POST", LISA_URL, data=payload, headers=headers)
        except:
            await ctx.send(ErrorResponses.E111)

        response = json.loads(response.text)
        leader = response['data'].get('abpLeaders')
        if not leader:
            oak_response = 'Líder não cadastrado! Você inseriu o nickname corretamente?'

        else:
            # Processa as batalhas disputadas pelo jogador
            battles = '\n'.join(
                '\nDATA: {}\nVS: {}\nVencedor: {}\n'.format(
                    b.get('battleDatetime'),
                    b['trainer'].get('nickname'),
                    b.get('winner')
                ) for b in leader[0].get('battles')
            )

            oak_response = '\nINFO LEADER:\n\n'
            oak_response += 'NICK: {}\n'.format(
                leader[0].get('nickname')
            )
            oak_response += 'VITÓRIAS: {}\nDERROTAS: {}\n'.format(
                leader[0].get('numWins'),
                leader[0].get('numLosses')
            )
            oak_response += 'BATALHAS DISPUTADAS: {}\n'.format(
                leader[0].get('numBattles')
            )
            oak_response += 'REGISTRO DE BATALHAS: \n{}\n'.format(
                battles
            )

        await ctx.send(oak_response)

@client.command()
async def leader_register(ctx, nickname='',  role='', poke_type=None):
    '''
    Registra um líder de ginásio ou elite four
    '''
    user_permissions = set([i.name for i in ctx.author.roles])
    if 'ADM' not in user_permissions:
        oak_response = 'Você não tem permissão para isso!'

    else:
        role = role.upper()

        if not nickname:
            oak_response = 'Por favor insira o nickname do líder'
            oak_response += '\nUso: `/leader_register NAME NICKNAME ROLE TYPE`\n'
        if not role:
            oak_response = 'Por favor um dos cargos: gym_leader, elite_four'
            oak_response += ' ou champion'
            oak_response += '\nUso: `/leader_register NAME NICKNAME ROLE TYPE`\n'
        if not poke_type and role != 'CHAMPION':
            oak_response = 'Por favor insira o tipo de pokemon do líder'
            oak_response += '\nUso: `/leader_register NAME NICKNAME ROLE TYPE`\n'
            await ctx.send(oak_response)

        if nickname and role:

            part_1 = "{\"query\":\"mutation createLeader{\\n  createLeader(input:{\\n    nickname: \\\""
            part_2 = "\\\",\\n\\t\\tpokemonType: "
            part_3 = ",\\n    role: "
            part_4 = "\\n  }){\\n    leader{\\n      id\\n      numWins\\n    nickname\\n      numLosses\\n      numBattles\\n    pokemonType\\n    role\\n}\\n  }\\n}\\n\\n\",\"operationName\":\"createLeader\"}"

            poke_type = poke_type.upper() if poke_type else 'null'

            payload = part_1 + nickname + part_2 + poke_type + part_3
            payload += role.upper() + part_4

            headers = {
                'content-type': "application/json"
            }

            response = requests.request("POST", LISA_URL, data=payload, headers=headers)
            response = json.loads(response.text)
            leader = response['data']['createLeader'].get('leader')

            oak_response = '\nLIDER REGISTRADO:\n\n'
            oak_response += 'Nick: {}\n'.format(
                leader.get('nickname')
            )
            oak_response += 'Vitórias: {}\nDerrotas: {}\n'.format(
                leader.get('numWins'),
                leader.get('numLosses')
            )
            oak_response += 'Batalhas Disputadas: {}\n'.format(
                leader.get('numBattles')
            )
            oak_response += 'Tipo: {}\nCargo: {}\n'.format(
                leader.get('pokemonType').capitalize(),
                leader.get('role').capitalize()
            )
    await ctx.send(oak_response)

@client.command()
async def battle_register(ctx, trainer='', leader='', winner=''):
    '''
    Registra uma batalha entre um treinador e um lider ou elite four
    '''
    user_permissions = set([i.name for i in ctx.author.roles])

    # TODO get this from settings or config file
    auth_only = {'ADM', 'Gym Leader', 'Elite Four'}

    if not auth_only.intersection(set(user_permissions)):
        oak_response = 'Você não tem permissão para isso!'

    else:
        if not trainer or not leader or not winner:
            oak_response = 'Registro incorreto de batalha.\n'
            oak_response += 'Uso: `/battle_register TRAINER_NICKNAME'
            oak_response += ' LEADER_NICKNAME WINNER_NICKNAME`\n'
        else:

            part_1 = "{\"query\":\"mutation{\\n  createBattle(input:{\\n    trainerNickname: \\\""
            part_2 = "\\\",\\n    leaderNickname: \\\""
            part_3 = "\\\",\\n    winner: \\\""
            part_4 = "\\\"\\n  }){\\n    battle{\\n      trainer{\\n        nickname\\n      }\\n      leader{\\n        nickname\\n      }\\n      winner\\n      battleDatetime\\n    }\\n  }\\n}\"}"
            
            payload = part_1 + trainer + part_2 + leader + part_3 + winner + part_4

            headers = {
                'content-type': "application/json"
            }

            response = requests.request("POST", LISA_URL, data=payload, headers=headers)
            response = json.loads(response.text)
            battle = response['data']['createBattle'].get('battle')

            oak_response = '\nBATALHA REGISTRADA\n'
            oak_response += 'Trainer: {}\nLíder: {}\nVencedor: {}\n'.format(
                battle['trainer'].get('nickname'),
                battle['leader'].get('nickname'),
                battle.get('winner'),
            )
            oak_response += 'Data da Batalha: {}\n\n'.format(
                battle.get('battleDatetime')
            )
    await ctx.send(oak_response)

@client.command()
async def add_badge(ctx, trainer='', badge=''):
    '''
    Presenteia um treinador com uma insígnia.
    '''
    user_roles = set([i.name for i in ctx.author.roles])
    if 'ADM' not in user_roles and 'Gym Leader' not in user_roles:
        await ctx.send('Você não tem permissão para isso!')

    if not trainer:
        await ctx.send('Especifique o nickname do treinador.')

    if not badge:
        await ctx.send('Especifique a insignia.')

    badges = {
        'Normal', 'Rock', 'Electric',
        'Ghost', 'Ice', 'Poison', 'Water',
        'Dark', 'Grass', 'Dragon', 'Psychic',
        'Fairy'
    }

    if badge.capitalize() not in badges:
        response = 'Insígnia inválida, a insignia deve ser uma das seguintes:\n'
        response += ', '.join(b for b in badges)
        await ctx.send(response)

    if 'ADM' not in user_roles and badge.capitalize() not in user_roles:
        await ctx.send(
            'Você só pode dar a insígnia do seu ginásio.'
        )

    part_1 = "{\"query\":\"mutation addBadge{\\n  addBadgeToTrainer(input:{\\n    badge: "
    part_2 = "\\n    trainer: \\\""
    part_3 = "\\\"\\n  }){\\n    trainer{\\n      id\\n      nickname\\n      isWinner\\n      numWins\\n      numLosses\\n      numBattles\\n      badges{\\n        id\\n        reference\\n      }\\n    }\\n  }\\n}\\n\",\"operationName\":\"addBadge\"}"

    payload = part_1 + badge.upper() + part_2 + trainer + part_3

    headers = {
        'content-type': "application/json"
        }

    response = requests.request("POST", LISA_URL, data=payload, headers=headers)
    response = json.loads(response.text)
    trainer = response['data']['addBadgeToTrainer'].get('trainer')

    # Processa as insignias do treinador
    badges = ', '.join(
        badge.get('reference', '') for badge in trainer.get('badges')
    )

    oak_response = '\nINFO TRAINER:\n\n'
    oak_response += 'NICK: {}\n'.format(
        trainer.get('nickname')
    )
    oak_response += 'VITÓRIAS: {}\nDERROTAS: {}\n'.format(
        trainer.get('numWins'),
        trainer.get('numLosses')
    )
    oak_response += 'BATALHAS DISPUTADAS: {}\n'.format(
        trainer.get('numBattles')
    )
    oak_response += 'INSÍGNIAS CONQUISTADAS: \n{}\n\n'.format(
        badges
    )

    await ctx.send(oak_response)

@client.command()
async def score(ctx):
    '''
    Mostra o placar da liga
    '''
    payload = "{\"query\":\"query{\\n  abpScoreBoard{\\n    trainers{\\n      nickname\\n      numWins\\n      numLosses\\n      numBattles\\n      badges{\\n        reference\\n      }\\n    }\\n  }\\n}\"}"
    headers = {
        'content-type': "application/json"
        }

    response = requests.request("POST", LISA_URL, data=payload, headers=headers)
    response = json.loads(response.text)
    trainers = response['data']['abpScoreBoard'].get('trainers')

    trainers = sorted(trainers, key=lambda t: len(t['badges']), reverse=True)

    headers = ["Nick", 'Wins', 'Loss', 'Battles', 'Badges']

    table = []
    for trainer in trainers:
        row = [
            trainer.get('nickname'),
            '',
            trainer.get('numWins'),
            trainer.get('numLosses'),
            trainer.get('numBattles'),
            len(trainer.get('badges'))
        ]
        table.append(row)
    design = 'rst'
    res = tabulate(
      table,
      tablefmt=design,
      headers=headers,
      numalign="right",
    )
    await ctx.send(res)
