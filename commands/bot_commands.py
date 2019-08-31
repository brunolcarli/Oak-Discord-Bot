"""
Módulo para comandos do bot. Neste arquivo deverão conter apenas funções de
chamada dos comandos que o bot responde. Demais algoritmos, mesmo contendo
o processamento destas funções devem estar em um outro módulo dedicado e
importá-lo neste escopo, deixando este módulo o mais limpo possível e
facilitando a identificação e manutenção dos comandos.
"""
from random import choice
import discord
from discord.ext import commands
from discord.utils import get
from settings import (LISA_URL, RANKED_SPREADSHEET_ID, SCORE_INDEX, SD_NAME_INDEX, ADMIN_CHANNEL)
from util.general_tools import (get_similar_pokemon, get_trainer_rank,
                                get_ranked_spreadsheet, get_form_spreadsheet, compare_insensitive, get_embed_output)
from util.get_api_data import (dex_information, get_pokemon_data, 
                               get_item_data, item_information,
                               get_ability_data, ability_information)
from util.showdown_battle import load_battle_replay
from util.elos import (Elos, get_elo, validate_elo_battle)
import requests
import json
from tabulate import tabulate
import random
from datetime import datetime

# TODO - move this to a constants, settings or config file
class ErrorResponses:
    E404 = 'Não encontrei esta informação! (E404)'
    E111 = 'Agora estou ocupado. A Lisa está dodói. (E111)'


client = commands.Bot(command_prefix='/')
COLOR_INDEX = 1
ELO_IMG_INDEX = 2

# TODO move this to another module. Declare within a set/tuple in UPPER_CASE
elos_map = [
    [ "grand mestre", 0x303030, "https://lh3.googleusercontent.com/q7DbMaDc-E0fpgBGy8-B4cvjJ-CTSuCuNYUU1BTLNVtb60vpmTBA0atUKnYmMMzbSgmZdx9t9WwbtI5dtXiEqqqKA9EyHDK7QC_RTI3psIuM0a5xxZJTcwn4EAq6vz_xEJEMdRn5On8HbnFqemtA_O8CYQhHntyAT97j6zseTncL0UT5hC_Qb6ZLqiEcvhNawAJgz2dbfEjvq1z-KmYEc7kU-i6ko9bgChwm1NSUTGSSp96Rkg0qJO7uptGCjUuvkNl9Jfev4HJDa9JgC6rtQMPRXZUCJ46ncAaPcyToyaVi1aj1szhSo5t3taMYLGJeNJJ-Ig125ukLkK9LvOblFYngvx0xpdlk_G4rKLRZRvLbtE2T3z9fmZzrJ8vhIsdEsj1mdKsB9tGn9r1ZIIjJaeFZLGcZXXlvFnytiOhIgYeHJbInils3L5ufVJNdynC5-W8Bckm7fpgVmtbHz-LVu4BOjG1T6QTxwahmivWxU6kst-QKPNoJE2WNejHSWxpu6Zx5wGqlPndilJfdrw6LoKGzV3aoM3m2W9swJKzpAPjWBcsEW-qGbPzCD1DBRklRgUmhSV5ejoiGcbRfcgcgPGmO-a7PFeg22SnYJKy0E9mwSiTLSSu__cGg-EQiQQZ11zD2XjrGbGX9oEN5umuzOYE47qLuQAutSbafrH7_VcG4bfJt-7UpTvfg9heGzoVIpeI2asUTJXRINwCgKgaRdlw=w857-h858-no" ],
    [ "mestre",       0x80e891, "https://lh3.googleusercontent.com/AiSEFZIbBlprCeSw2tC7Wa3_FsU17T3JOQ3WRXnkzSrgK4kcNZposVAGW0EVOd2BFh1R7ggxvyliYTL1Aa2Tl2zkVtlIFYfsJs3Ses1WVu0TQ_9uMlyp76n4sqndeNuZivqU5bw7oAwxbr5wdoCdtJpcFgXoC81XFLkQjhhdSrsKxpNN-SO30oo7Nq-4mxR3FGE1Tb6ujYa-3eCQmidxMJ5DXgDwzg2TLClQFwDeuf1MFtRYMWbXjBXJCS4hbsqufEVnDprbyiWoJsK1RejH4hAPgP4b0WnO0qheX-ewEcPM-BsLVrOm3eti4At7729eSlxQEj0C8hVGcSzX-gLiq8TrbDJDu6NuTFLDfd9JbZYR9LAtTZ4DoM0muA7twY515sQhTaX-SknbrrrjSYOzKqSt-LPi-HM-tICkBWDRy97Gb0rhHRqnblEQv4WhSfCxybv8vsMz9yUrwy53niUIrX6WSB1_V8k5ihMph529gnITRQKWEnIwvqFg37kZzZ5ImUqOiNGXEuKUV9hGbqGgKNTEyq5Cauy_zunJIp5zT9KJfV0XVF7A3lM5gjNeWwMkP-O-LG4qjlbyPlJWnkfbYVMpWY04FLiun_QB67-0O_ypAz8lw0zWEn9eU3KPwAkBI88vTTDdY1dghIKdgWDTAsxsOuUXCA7Yf5-pjI61v4UOFRTQeXxMPNEzU3WLRvn8WEpwbu4f9b2kkcomxBHEB0Q=s834-no" ],
    [ "diamante",     0x59d0e4, "https://uploaddeimagens.com.br/images/002/278/683/original/Diamante.png" ],
    [ "platina",      0xd7d7d7, "https://lh3.googleusercontent.com/hQifT74Pr0Trza6dQ3_ERzc_ZXkpqjdGTny2uiEUzg_iknxql4ArzmF4aUPiLplcHTbQBuV9lF8qkuU4ZxfDzjVwWk_MDQrZe5D35zwqjtsJIsgP4KRiOwXGkv5RbmxwPnW6w24fvewbViVRWeIUioFz-M2yImPfBEcUmOwF8WCvDw17BnxiHkTjRZkl-N3U1ZG_gqf8jWqUXIPssuJDtVyMkiKp8eixtxyYj_OC-gf5LlaLv4UQdonAeYt20MtpNuPa6r_-wXQ09zM8xv-oWeDnSdrqdRbcZ1JmtmkjaJQpgPdRJ9nt-mg39WxM58avap6kCVlvqwSeB-oX9_eJF_wOex1nnKK0CC06RksUc9FshiN3CRA9ekW8FOzfq0L9ufREGJkgjrRzRnc-A-D8cvLpgAXg6Sa54Q8rwxq-3ojGwPWB_xtFz_1LoPPO4J1ZCocQoheNZnrMifqbXJyQ0i9ce6MZ6fOmUnrdBcZxsyOsh16skzocDRI2XFO2krsgi1I4kSTbHhCS3VkWwOYeRr_EUMr9MZ7xWmqDH3jI7DNjHnbyKkTjsz6Nj3kTsb8a9GJzDjqvExXd6JYsB8OTjy3DtRVFKR5THLfO4d8FryQjnCQY6uJBYduu0t4e6ACKmoh0Ladu2ywQQHG0-EwYDQ6ioYx2DpRUIMB8FAWnN2eMDlafF0BU5Ob0AduV2cKznM47eZCM5yf592n5jl70QwM=s834-no" ],
    [ "ouro",         0xbfa617, "https://lh3.googleusercontent.com/rENAkMDu3Mdgi_l0XH2anhKmAVAYmVEBJvxnos8XJGu-WXOKH5akOvHoqntNj4Vz6MxKjAWA6mGxpT9Uo2aq6TpY-vZax_zLawXX5kNlIEkePaIMiMVaF_LJYgUdXqEoZ4U_MlDK9_Au7kHS_bPJugNho0saBdS0Bz2kG0idwRPlUozKEIycLMlrwb9x9Cjqci_b7tyHk_zHU6e5GdDwpzi9KPgP0LEss9j6qorFBvwKUx0CLyQ5zK7Nhj3F4OjZvUEFf6NVKrl-sZrua3eYbY7gbUAPKp20vIY7c3YbNbfWRO6G3doyAGyRUM2XBp3s9c5G2bBGobpjXoabA6HEKscnTWRr2JIdrkvXPUorYRmnekXgXLhL_OWn_ADhL38aMltIV5GnW8FfeoP5aQEGmGlaC0lQJWxU09eT4_eaEKDwqUqBAbjhTy2iB8ggHSqh1N7qYnTcSuhvulHwb_Gnm-NQYuf1heyq9vVxh4Caran6EcnD-FRXZ1Dj4ddaU_ZIoow05Fvl23Kr4LZ1bZ7_6kc1szxce3IbM2BRxTRDzZ6IKOuCx9c9Ttn3rDiRKJB6-14cNjaQHtQ269cie7bV0X5JyRy7sMma5inNmeAeF7PFTpspg9ePOBYerndbOcaAlXE36RRAM2Yqp8Q_n3PUd5FSW922M13pNQjTk5OIrT0e4nPFqtHmnH0aUp0PgjhtiTSYDqwuesLVZYgcY--fpS8=s834-no" ],
    [ "prata",        0x8e8e8e, "https://lh3.googleusercontent.com/5l38BR08J-lJCQkRuXn69t4qbDZmOZM9yk0sMZzAdO4SY0FVa0KP127rrnsd2OUV-SDzkmySHyRuQjoRzcWRt35XEM-q091anUcVTple-fyAaBc26JFFBI9z4ycz2V5IFx8KgrXWMkKHRsB4hKYS_sl1tQtS9HT7Vak9kd5CgafkHoTvogNu3rE_taXfsePJrRYemNWxoe_tMZ0rtZgxNQ1OKqtBf3Kgak1KIF0XlVBx8ZQdxzadSk0yuNT6wANOa58aAxmgizLeliPSbWm7QcrJyzotcliMbYUs73lU_kf7NYVcL1109cRcGq5NgXM8MH81VDKI2cGpz1Phj51Htzl9R4FuSXKPqdh4fiSUwYI9V-rpoc9sA5NkOsAznr13jlYqMF_cMLB8885E3QmMxsaR0YDq28QrMucB5Uq0NXqQdDPA7-4bF8DI4uK9cP6nOD7ehaDf_nsb2o8YvI_pjpRooSKM9D0bGLi6-vj7cwNsmkiK7WGp0-xiYhQZVKf3zZUth2ZHsKnTpR6XobKMhky-Lfe9Z4GvqwPk3IhZUg6YvMQD61mg4X3rkYvujtQgbCbC0Wrj4_-ZOJ0_pV-Hs5QC_mJrRnY-SxJG9pYD6S0qrQmVqd-sytllP2d3LwRhdckrYd9l6aTa3oahS9hg55wC9SIeVtyjUy8EHjzxlcOdAqXfGutX42eKPa4D206wiTbLY0HHwKNf7fiBogyCILQ=w841-h834-no" ],
    [ "bronze",       0xc0702d, "https://lh3.googleusercontent.com/xuxJIlFO7v9X1-CBgyTEfTAsRqLqjGXE_z8Po1KroHuvhs4JsP0IpzJ_SsqBAC33_3SnBErojk0C8wViI4rmVwi3Dlz644wyHTIRF3GDz1hUMDib4poKcJ4N46syMuyT_9iKmzRfYT_Maz0o-uq4t0-yBrzAroihDIb4X5eexKEwPOTajBngQFOx_AzH1TA7M846deV92BpbNi7VisHq2NB_eaZVf1cVrwU__dX-pr0aEn_RCPCZduyq14mNo0-TrOIKyV6zXZY6Rhd9WaD4nO9qSrp-2DSg0dn0rSocsSOPeSpac75izEh49zt1ld1e3FQtnh_HTasQf4OXdPo8QinThjL8C12KkiqfLsmUMmE12pq24B5zGndslw9Xmz-NE9-99Tp5HvA9-tZe13wqqSCpXpN8ua1vWTrLcveh9W47QPR-gzK9xkjKQbbyNF9Etp35TxESVCBzYGngddvcTunZGdrZa_pAA0_1ALC1nEZ_Hr5ps3s97RyGLT5tId9mHygBnoej6GEcpL2Iirk1ktsksrsL2xTdw0I0rzUbLlkKZHbfg5OVjVc32qKQ1Vl5yPeIsjudSC64hmhn-vWK2GCoZMdblNwigV9ECLVwMwiU3mVwDoBkXgxK_NFL_YDogt66FnLLfbnLjM4cx8hWlP18dmmfEWy6OuqRIlZ92ESSc8bOtzyZbHNKgjyKRh5as_1RlLWmAIugOhD-m3eVdArN=w829-h834-no" ],
    [ "retardatario", 0xb73232, "https://lh3.googleusercontent.com/pFWZesmDmhDYx2nk_Fb1ziuPxCSsC4nq7fAXvNfjpWcHcSspMazQhrvJirYwYTtrTL36zRYuX1jSObDhEXjURxd3oCrGk8dBKexrLOLBTDgJTWzXygiR6htlvhkNpPob8Lr9aoBeg8M-DIJdEZUV5PfkCRmZPvhiz1QBZgKAWdTserRbSR5ZEyboUaCS7lQVydv2b0r1YXavv6uF9VaXUbMPJM_Q0ChIbwTz23s9aaa_L0g4ffJHs2RxLvwwNfwnGISTXN-QD47Gfk3Y_HKLVD7-nF3I-ubQnRSz8GY_nDSe1nbm6gbZQ-nzpSZHxDfLQK2pYRMLGCy1l3beX0HC5nNt7PpeRKH94DdvKgTrxv9cHBK1eVDV0aBOoSQEvT3rh8ja_dyiO6ABcuWPVzNno5KLDe6g1GcOPQWKI8FVoz5iibn7Y4GAE5QWxR1FHulyNHQMFfzAljPaUFG9q1ZRYZNaMWNKEXj4FV9FQjk3xFnGBsYaMuJWJW3VWsFWSBT3-m4XRRdFXPTjZA1GSQlKxcnyPI6dM_ZjmMpPjdG1z12LfKMA7fHuHtmWLfdaD23vrr7ucsr7mYB83YIq2iJqdlZPIhwua91uiucefW_KjY1cHyoSw4Y2Cu04mmZU3AsEvPsavx9MVAqMU6N4xvgl3rlfWsFK2kulR6GY35GcktSIYL8zfjzfghgtiwlFAoDFe3L8_Y7GMgEFqUxp2zG0XO4=w832-h834-no" ]
]

@client.event
async def on_ready():
    """
    Imprime uma mensagem no console informando que o bot, a princípio executou
    corretamente.
    """
    print("The bot is ready!")

@client.event
async def on_member_join(member):
    # TODO I think this should be removed, since is is unused, or, adapt to
    # send an welcome text on member join ...
    # maybe thats the real reason for this piece of code to exist ¯\(°_o)/¯
    print('{} entrou no rolê!'.format(member))

@client.event
async def on_member_remove(member):
    # TODO I think this should be removed, since is is unused, or, adapt to
    # send an welcome text on member join ...
    # maybe thats the real reason for this piece of code to exist ¯\(°_o)/¯
    print('{} saiu do rolê!'.format(member))

@client.command()
async def ping(ctx):
    """
    Verifica se o bot está executando. Responde com "pong" caso positivo.
    """
    await ctx.send('pong')

@client.command()
async def dex(ctx, pokemon):
    """
    Responde informações sobre um pokemon.
    """
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
    """
    Responde informações sobre um item.
    """
    data = get_item_data(item.lower())
    response = item_information(data)
    await ctx.send(response)

@client.command()
async def ability(ctx, ability):
    """
    Responde informações sobre uma habilidade
    """
    data = get_ability_data(ability.lower())
    response = ability_information(data)
    await ctx.send(response)

# TODO Remove this it is irrelevant, and the guys dont use it anymore ¯\(°_o)/¯
@client.command()
async def frase_do_sidney(ctx):
    options = ['VAI SER EMOCIONANTE!', 'manicaca']
    await ctx.send(choice(options))

@client.command()
async def quote(ctx, *phrase):
    """
    Salva uma mensagem como quote para ser eternamente lembrado
    """
    if phrase:
        quoted = ' '.join(word for word in phrase)

        # TODO build the query in another dedicated module and import here
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
    """
    Retorna um quote aleatório
    """
    # TODO build the query in another dedicated module and import here
    payload = "{\"query\":\"query{\\n  abpQuotes\\n}\"}"
    headers = {
        'content-type': "application/json"
        }

    # TODO Exchange requests for gql module
    response = requests.request("POST", LISA_URL, data=payload, headers=headers)
    response = json.loads(response.text)
    quotes = response['data'].get('abpQuotes')

    await ctx.send(choice(quotes))

@client.command()
async def random_pokemon(ctx):
    """
    Responde com um pokémon aleatório
    """
    with open('files/pokes.txt', 'r') as f:
        pokes = f.readlines()

    i_choose_you = choice(pokes).split('\n')[0]
    poke = get_pokemon_data(i_choose_you.lower())
    response = dex_information(poke)
    await ctx.send(response)

# TODO Remove this it is irrelevant, and the guys dont use it anymore ¯\(°_o)/¯
@client.command()
async def gugasaur(ctx):
    """
    Responde com o pokemon do guga
    """
    poke = get_pokemon_data('tyrantrum')
    response = dex_information(poke)

    await ctx.send(response)

@client.command()
async def top_ranked(ctx, *args):
    """
    Informa os 20 primeiros colocados da Ranked ABP.
    """
    data = get_ranked_spreadsheet()
    table = get_initial_ranked_table()
    
    view_types = [
        [ "list", "lista", "elos" ],
        [ "table", "tabela" ]
    ]
    is_list = len(args) > 0 and args[0].strip().lower() in view_types[0]

    for i, trainer in enumerate(data[:20], start=1):
        trainer = get_trainer_rank_row(trainer, i)
        table.append(trainer)

    if is_list:
        descript = "**__Top Players__**"
        output = get_embed_output(table) 
        await ctx.send(descript, embed=output)
    else:
        output = get_table_output(table)
        await ctx.send(output)

@client.command()
async def ranked_trainer(ctx, *trainer_nickname):
    """
    Busca o score de um trainer na ranked pelo nick do caboclo.
    """
    if not trainer_nickname:
        await ctx.send('Forneça um nick\nUso: `/ranked_trainer <nickname>`')
        return
    
    trainer_nickname = ' '.join(word for word in trainer_nickname)
    trainer = find_trainer(trainer_nickname)

    if not trainer:
        await ctx.send('Treinador não encontrado')
        return

    # lookup for the trainer elo data
    nick = "**__"+ trainer[1] +"__**"
    elo_rank = get_trainer_rank(trainer[SCORE_INDEX])
    elo = elo_rank.lower().replace("á", "a")
    elo_data = [item for item in elos_map if item[0] == elo][0]

    # setup embed data
    embed = discord.Embed(color=elo_data[COLOR_INDEX], type="rich")
    embed.set_thumbnail(url=elo_data[ELO_IMG_INDEX])
    
    embed.add_field(name="Pos", value=trainer[6], inline=True)
    embed.add_field(name="Elo", value=elo_rank, inline=True)
    embed.add_field(name="Wins", value=trainer[2], inline=True)
    embed.add_field(name="Losses", value=trainer[3], inline=True)
    embed.add_field(name="Battles", value=trainer[5], inline=True)
    embed.add_field(name="Points", value=trainer[4], inline=True)
    
    await ctx.send(nick, embed=embed)

@client.command()
async def ranked_elo(ctx, *elo_arg):
    """
    Retorna todos os treinadores que estão no Rank Elo solicitado.
    """
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

@client.command()
async def ranked_validate(ctx):
    """
    Valida as entradas pendentes do formulário de registro de batalhas
    """
    if ctx.message.channel.name != ADMIN_CHANNEL:
        return

    data = get_form_spreadsheet()
    ranked_data = get_ranked_spreadsheet()
    errors = [
        [ "Ln.", "Error" ]
    ]
    ok = [ 'http://i.imgur.com/dTysUHw.jpg', 'https://media.tenor.com/images/4439cf6a16b577d81f6e06b9ba2fd278/tenor.gif', 'https://i.kym-cdn.com/photos/images/original/001/092/497/a30.jpg', 'https://i.kym-cdn.com/entries/icons/facebook/000/012/542/thumb-up-terminator_pablo_M_R.jpg', 'https://media.giphy.com/media/111ebonMs90YLu/giphy.gif' ]
    
    for i, row in enumerate(data, start=2):
        # validate trainers
        trainers_result = ""
        winner_data = find_trainer(row[2], ranked_data)
        loser_data  = find_trainer(row[3], ranked_data)
        if winner_data == None: trainers_result += "Winner not found; "
        if loser_data  == None: trainers_result += "Loser not found; "
        if trainers_result != "":
            errors.append([i, trainers_result])
            continue

        # validate elos
        winner_elo  = get_elo(get_trainer_rank(winner_data[SCORE_INDEX]))
        loser_elo   = get_elo(get_trainer_rank(loser_data[SCORE_INDEX]))
        valid_elos  = validate_elo_battle(winner_elo, loser_elo)
        if not valid_elos:
            errors.append([i, "Invalid elos matchup ({} vs {})".format(winner_elo.name, loser_elo.name)])
            continue
        
        # validate showdown replay
        result = load_battle_replay(row[4]) # 4 is the replay
        if not result.success:
            errors.append([i, "Não foi possivel carregar o replay" ])
            continue
        
        # validate replay metadata
        battle_result = result.battle.validate(row[2], row[3], datetime.strptime(row[0], "%d/%m/%Y %H:%M:%S"))
        if not battle_result.success:
            errors.append([i, battle_result.error])

    # only table header
    if len(errors) == 1:
        await ctx.send('All good! 👍 ' + ok[random.randint(0, len(ok)-1)])
        return

    # when too big errors table, split into smaller data
    chunks = [errors[x:x+10] for x in range(0, len(errors), 10)]
    for err in chunks:
        output = get_table_output(err)
        await ctx.send(output)

# TODO move this to an util or tools dedicated module
def get_initial_ranked_table():
    """
    Retorna uma lista contendo uma lista com as colunas a serem exibidas
    no placar da Ranked.

    params : None :
    return : <list> :
    """
    return [
        [ 'Pos', 'Nick', 'Wins', 'Bts', 'Pts', 'Rank' ],
    ]

# TODO move this to an util or tools dedicated module
def find_trainer(trainer_nickname, data = None):
    """
    Procura por um treinador específico na tabela de treinadores da ranked.

    param : trainer_nickname : <str>
    param : data : <list> : param data default value : None
                    TODO <- corrija-me se eu estiver errado Thiago Menezes
    return : <list>
    """
    data = data if data != None else get_ranked_spreadsheet()
    pos = 0
    for trainer in data:
        pos += 1
        trainer_found = compare_insensitive(trainer[SD_NAME_INDEX], trainer_nickname)
        if trainer_found:
            trainer.append(pos)
            return trainer

    return None

# TODO move this to an util or tools dedicated module
def get_trainer_rank_row(trainer, position):
    """
    Busca na planilha da Ranked a linha de dados contendo a informação
    do treinador, retornando um vetor de dados atualizados do treinador.

    param : trainer : <list> :
    param : position : <int> :

    return : <list> :
    """

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

# TODO move this to an util or tools dedicated module
def get_table_output(table):
    """
    Formata uma tabela com a lib tabulate, retornando a tabela formatada
    dentro de um bloco de código de Markdown.
    Exemplo:
    ```
        ===  ===============  ====  ===  ===  ========
        MARKDOWN CODE BLOCK WITHIN A TABULATE TABLE
        ===  ===============  ====  ===  ===  ========
    ```

    param : table : <list> :

    return : <str> :
    """
    design = 'rst'
    response = tabulate(table, tablefmt=design, numalign="right")

    return '```{}```'.format(response)
