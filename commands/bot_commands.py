from random import choice
import discord
from discord.ext import commands
from util.general_tools import (get_similar_pokemon, get_trainer_rank,
                                get_ranked_spreadsheet, compare_insensitive)
from util.get_api_data import (dex_information, get_pokemon_data, 
                            get_item_data, item_information,
                            get_ability_data, ability_information)
from settings import (LISA_URL, RANKED_SPREADSHEET_ID, SCORE_INDEX, SD_NAME_INDEX)
import requests
import json
from tabulate import tabulate

# TODO - move this to a constants, settings or config file
class ErrorResponses:
    E404 = 'Não encontrei esta informação! (E404)'
    E111 = 'Agora estou ocupado. A Lisa está dodói. (E111)'


client = commands.Bot(command_prefix='/')
COLOR_INDEX = 1
ELO_IMG_INDEX = 2
elos_map = [
    [ "grand mestre", 0x303030, "https://uploaddeimagens.com.br/images/002/268/526/full/Grand-Mestre.png" ],
    [ "mestre",       0x80e891, "https://uploaddeimagens.com.br/images/002/268/524/full/Mestre.png" ],
    [ "diamante",     0x59d0e4, "https://uploaddeimagens.com.br/images/002/268/523/full/Diamante.png" ],
    [ "platina",      0xd7d7d7, "https://uploaddeimagens.com.br/images/002/268/477/full/Platina.png" ],
    [ "ouro",         0xbfa617, "https://uploaddeimagens.com.br/images/002/268/468/full/Ouro.png" ],
    [ "prata",        0x8e8e8e, "https://uploaddeimagens.com.br/images/002/268/474/full/Prata.png" ],
    [ "bronze",       0xc0702d, "https://uploaddeimagens.com.br/images/002/268/518/full/Bronze.png" ],
    [ "retardatario", 0xb73232, "https://uploaddeimagens.com.br/images/002/268/513/full/Retardatários.png" ]
]

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
    
    for i, trainer in enumerate(data[:20], start=1):
        trainer = get_trainer_rank_row(trainer, i)        
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
    pos = 0
    for trainer in data:
        pos += 1
        trainer_found = compare_insensitive(trainer[SD_NAME_INDEX], trainer_nickname)
        if trainer_found:
            trainer_data = trainer
            break

    if not trainer_data:
        await ctx.send('Treinador não encontrado')
        return

    # loock-up trainer elo data
    nick = "**__"+ trainer_data[1] +"__**"
    elo_rank = get_trainer_rank(trainer_data[SCORE_INDEX])
    elo = elo_rank.lower().replace("á", "a")
    elo_data = [item for item in elos_map if item[0] == elo][0]

    # setup embed data
    embed = discord.Embed(color=elo_data[COLOR_INDEX], type="rich")
    embed.set_thumbnail(url=elo_data[ELO_IMG_INDEX])
    
    embed.add_field(name="Pos", value=pos, inline=True)
    embed.add_field(name="Elo", value=elo_rank, inline=True)
    embed.add_field(name="Wins", value=trainer_data[2], inline=True)
    embed.add_field(name="Losses", value=trainer_data[3], inline=True)
    embed.add_field(name="Battles", value=trainer_data[5], inline=True)
    embed.add_field(name="Points", value=trainer_data[4], inline=True)
    
    await ctx.send(nick, embed=embed)

@client.command()
async def ranked_elo(ctx, *elo_arg):
    '''
    Retorna todos os treinadores que estão no Rank Elo solicitado.
    '''
    if not elo_arg:
        await ctx.send('Forneça um Rank Elo\nUso: `/ranked_elo <elo>`')
        return

    elo = ' '.join(word for word in elo_arg)
    data = get_ranked_spreadsheet()
    table = get_initial_ranked_table()
    
    for i, trainer in enumerate(data, start=1):
        rank =  get_trainer_rank(trainer[SCORE_INDEX])
        isTargetElo = compare_insensitive(rank, elo)
        if isTargetElo:
            trainer = get_trainer_rank_row(trainer, i)       
            table.append(trainer)
    
    # only table header
    if len(table) == 1:
        await ctx.send('Treinadores não encontrados para o Elo: ' + elo)
        return

    # when too big table, shows just the first 20
    if len(table) > 20:
        table = table[:21]
        await ctx.send('Top 20 treinadores do Elo: ' + elo)
    
    output = get_table_output(table)
    await ctx.send(output)

def get_initial_ranked_table():
    return [
        [ 'Pos', 'Nick', 'Wins', 'Bts', 'Pts', 'Rank' ],
    ]

def get_trainer_rank_row(trainer, position):    
    # remove name and insert the position in the front
    del trainer[0]
    trainer.insert(0, position)

    # limit nick size...
    trainer[1] = (trainer[1][:13] + '..') if len(trainer[1]) > 15 else trainer[1]

    # remove losses and swap battles with points
    del trainer[3]
    trainer[3], trainer[4] = trainer[4], trainer[3]
    
    # add rank
    rank =  get_trainer_rank(trainer[SCORE_INDEX])
    trainer.append(rank)
    
    return trainer

def get_table_output(table):
    design = 'rst'
    response = tabulate(table, tablefmt=design, numalign="right")
    return '```{}```'.format(response)