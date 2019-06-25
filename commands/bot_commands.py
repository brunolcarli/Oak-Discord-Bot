from random import choice
import discord
from discord.ext import commands
from util.general_tools import get_similar_pokemon
from util.get_api_data import (dex_information, get_pokemon_data, 
                            get_item_data, item_information,
                            get_ability_data, ability_information)   

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
async def leaders(ctx):
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
    quoted = ' '.join(word for word in phrase)
    with open('files/quotes.txt', 'a') as f:
        f.writelines(quoted + '\n')
    await ctx.send(quoted)

@client.command()
async def random_quote(ctx):
    '''
    Retorna um quote aleatório
    '''
    with open('files/quotes.txt', 'r') as f:
        quotes = f.readlines()
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
