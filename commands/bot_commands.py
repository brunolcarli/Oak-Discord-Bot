from random import choice
import discord
from discord.ext import commands
from util.general_tools import (get_similar_pokemon, get_trainer_rank,
                                get_ranked_spreadsheet)
from util.get_api_data import (dex_information, get_pokemon_data, 
                            get_item_data, item_information,
                            get_ability_data, ability_information)
from settings import (LISA_URL, RANKEADAS_SPREADSHEET_ID, PONTUACAO_INDEX, NOME_SD_INDEX)
import requests
import json
from tabulate import tabulate

# TODO - move this to a constants, settings or config file
class ErrorResponses:
    E404 = 'Não encontrei esta informação! (E404)'
    E111 = 'Agora estou ocupado. A Lisa está dodói. (E111)'


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


    '''
    Responde com a lista de lideres e elites
    '''
    with open('files/leaders.txt', 'r') as f:
        leaders_list = f.readlines()
    await ctx.send(''.join(line for line in leaders_list))

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
async def top_ranked(ctx):
    data = get_ranked_spreadsheet()
    table = get_initial_ranked_table()
    
    for trainer in data[:20]:
        trainer = get_trainer_rank_row(trainer)        
        table.append(trainer)

    output = get_table_output(table)
    await ctx.send(output)

@client.command()
async def ranked_trainer(ctx, *trainer_nickname):
    '''
    Busca o score de um trainer na ranked pelo nick do caboclo.
    '''
    if not trainer_nickname:
        await ctx.send('Forneça um nick\nUso: `/ranked_trainer <nickname>`')
        return
    
    trainer_nickname = ' '.join(word for word in trainer_nickname)
    trainer_data = None
    data = get_ranked_spreadsheet()
    for trainer in data:
        if trainer[NOME_SD_INDEX] == trainer_nickname:
            trainer_data = trainer

    if not trainer_data:
        await ctx.send('Treinador não encontrado')
        return

    table = get_initial_ranked_table()
    trainer = get_trainer_rank_row(trainer_data)
    table.append(trainer)

    output = get_table_output(table)
    await ctx.send(output)

def get_initial_ranked_table():
    return [
        [ 'Nick', 'Wins', 'Losses', 'Pts', 'Battles', 'Rank' ],
    ]

def get_trainer_rank_row(trainer):
    rank =  get_trainer_rank(trainer[PONTUACAO_INDEX])
    del trainer[0]
    trainer.append(rank)
    return trainer

def get_table_output(table):
    design = 'rst'
    response = tabulate(table, tablefmt=design)
    return '```{}```'.format(response)