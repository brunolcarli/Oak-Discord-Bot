"""
Módulo para comandos do bot. Neste arquivo deverão conter apenas funções de
chamada dos comandos que o bot responde. Demais algoritmos, mesmo contendo
o processamento destas funções devem estar em um outro módulo dedicado e
importá-lo neste escopo, deixando este módulo o mais limpo possível e
facilitando a identificação e manutenção dos comandos.
"""

# std libs
from base64 import b64decode, b64encode
from ast import literal_eval
from sys import stdout
from random import choice, randint
from datetime import datetime
import json
import requests

# 3rd Party libs usefull tools
from dateutil import parser

# Discord tools
import discord
from discord.ext import commands

# settings constants
from settings import (BACKEND_URL, SCORE_INDEX, ADMIN_CHANNEL,
                      COLOR_INDEX, ELO_IMG_INDEX, BILL_API_URL)

# general tools
from util.showdown_battle import load_battle_replay
from util.elos import get_elo, get_elo_name, validate_elo_battle, ELOS_MAP

# TODO talvez muitas destas funções pudessem ser encapsuladas em uma classe
from util.general_tools import (get_trainer_rank, get_emoji,
                                get_ranked_spreadsheet, get_form_spreadsheet,
                                get_trainer_database_spreadsheet,
                                get_trainer_db_table, get_random_profile,
                                compare_insensitive, get_embed_output,
                                get_table_output, get_trainer_rank_row,
                                get_initial_ranked_table, find_trainer,
                                find_db_trainer, get_discord_member,
                                get_value_or_default, get_gql_client,
                                get_badge_icon)

# requests tools
from util.get_api_data import (dex_information, get_pokemon_data)
from util.oak_errors import CommandErrors
from commands.queries import Query
from commands.mutations import Mutations

client = commands.Bot(command_prefix='/')


@client.event
async def on_ready():
    """
    Imprime uma mensagem no console informando que o bot, a princípio executou
    corretamente.
    """
    print("The bot is ready!")


@client.command()
async def ping(ctx):
    """
    Verifica se o bot está executando. Responde com "pong" caso positivo.
    """
    await ctx.send('pong')


@client.command()
async def quote(ctx, *phrase):
    """
    Salva uma mensagem como quote para ser eternamente lembrado
    """
    if phrase:
        quoted = ' '.join(word for word in phrase)

        # TODO build the query in another dedicated module and import here
        part_1 = "{\"query\":\"mutation{\\n  createAbpQuote(input:{\\n quote: \\\" "
        part_2 = "\\\"\\n  }){\\n    response\\n  }\\n}\"}"
        headers = {
            'content-type': "application/json"
            }
        payload = part_1 + quoted + part_2
        response = requests.request("POST", BACKEND_URL, data=payload, headers=headers)
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
    response = requests.request("POST", BACKEND_URL, data=payload, headers=headers)
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


##########################################
# Comandos Ranked
##########################################

@client.command(aliases=['top', 'rt', 'ranked_top'])
async def top_ranked(ctx, *args):
    """
    Informa os 20 primeiros colocados da Ranked ABP.
    """
    data = get_ranked_spreadsheet()
    table = get_initial_ranked_table()

    view_types = [
        ["list", "lista", "elos"],
        ["table", "tabela"]
    ]
    is_table = len(args) > 0 and args[0].strip().lower() in view_types[1]
    is_list = not is_table

    for i, trainer in enumerate(data[:20], start=1):
        trainer = get_trainer_rank_row(trainer, i)
        table.append(trainer)

    if is_list:
        descript = "**__Top Players__**"
        output = get_embed_output(table, client)
        await ctx.send(descript, embed=output)

    else:
        output = get_table_output(table)
        await ctx.send(output)


@client.command(aliases=['trainer', 'trainer_ranked'])
async def ranked_trainer(ctx, *trainer_nickname):
    """
    Busca o score de um trainer na ranked pelo nick do caboclo.
    """
    if not trainer_nickname:
        await ctx.send('Forneça um nick\nUso: `/ranked_trainer <nickname>`')

    else:
        trainer_nickname = ' '.join(word for word in trainer_nickname)
        trainer = find_trainer(trainer_nickname)

        if not trainer:
            await ctx.send('Treinador não encontrado')

        else:
            # lookup for the trainer elo data
            nick = "**__" + trainer[1] + "__**"
            elo_rank = get_trainer_rank(trainer[SCORE_INDEX])
            elo = get_elo_name(elo_rank)
            elo_data = [item for item in ELOS_MAP if item[0] == elo][0]

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


@client.command(aliases=['elo', 'elo_ranked'])
async def ranked_elo(ctx, *elo_arg):
    """
    Retorna todos os treinadores que estão no Rank Elo solicitado.
    """
    if not elo_arg:
        await ctx.send('Forneça um Rank Elo\nUso: `/ranked_elo <elo>`')

    else:
        elo = ' '.join(word for word in elo_arg)
        data = get_ranked_spreadsheet()
        table = get_initial_ranked_table()

        for i, trainer in enumerate(data, start=1):
            rank = get_trainer_rank(trainer[SCORE_INDEX])
            is_target_elo = compare_insensitive(rank, elo)
            if is_target_elo:
                trainer = get_trainer_rank_row(trainer, i)
                table.append(trainer)

        # only table header
        if len(table) == 1:
            await ctx.send('Treinadores não encontrados para o Elo: ' + elo)

        # when too big table, shows just the first 20
        elif len(table) > 20:
            table = table[:21]
            await ctx.send('Top 20 treinadores do Elo: ' + elo)

            output = get_table_output(table)
            await ctx.send(output)


@client.command(aliases=['valid', 'rv'])
async def ranked_validate(ctx):
    """
    Valida as entradas pendentes do formulário de registro de batalhas
    """
    if ctx.message.channel.name == ADMIN_CHANNEL:

        data = get_form_spreadsheet()
        ranked_data = get_ranked_spreadsheet()
        errors = [
            ["Ln.", "Error"]
        ]

        # TIP: Encurte links grandes no bit.ly
        ok = [
            'http://i.imgur.com/dTysUHw.jpg',
            'http://bit.ly/chuck_approve',
            'https://i.kym-cdn.com/photos/images/original/001/092/497/a30.jpg',
            'https://media.giphy.com/media/111ebonMs90YLu/giphy.gif'
        ]

        for i, row in enumerate(data, start=2):
            # validate trainers
            trainers_result = ""
            winner_data = find_trainer(row[2], ranked_data)
            loser_data = find_trainer(row[3], ranked_data)

            if not winner_data:
                trainers_result += "Winner not found; "

            if not loser_data:
                trainers_result += "Loser not found; "

            if trainers_result:
                errors.append([i, trainers_result])

            # validate elos
            winner_elo = get_elo(get_trainer_rank(winner_data[SCORE_INDEX]))
            loser_elo = get_elo(get_trainer_rank(loser_data[SCORE_INDEX]))
            valid_elos = validate_elo_battle(winner_elo, loser_elo)

            if not valid_elos:
                error = f"Invalid elos matchup \
                    ({winner_elo.name} vs {loser_elo.name})"
                errors.append([i, error])

            # validate showdown replay
            result = load_battle_replay(row[4])  # 4 is the replay

            if not result.success:
                errors.append([i, "Não foi possivel carregar o replay"])

            # validate replay metadata
            battle_result = result.battle.validate(
                row[2],
                row[3],
                datetime.strptime(row[0], "%d/%m/%Y %H:%M:%S")
            )

            if not battle_result.success:
                errors.append([i, battle_result.error])

        # only table header
        if len(errors) == 1:
            await ctx.send('All good! 👍 ' + ok[randint(0, len(ok)-1)])

        else:
            # when too big errors table, split into smaller data
            chunks = [errors[x:x+10] for x in range(0, len(errors), 10)]
            for err in chunks:
                output = get_table_output(err)
                await ctx.send(output)
    else:
        await ctx.send("Comando restrito!")


@client.command(aliases=['db', 'bd', 'abp-db', 'trainer_db', 'trainer_names'])
async def abp_db(ctx, *trainer_arg):
    """
    Retorna todos os treinadores que estão cadastrados na ABP.
    """
    if trainer_arg:
        trainer_nickname = ' '.join(word for word in trainer_arg)
        trainer = find_db_trainer(trainer_nickname)

        if not trainer:
            return await ctx.send('Treinador não encontrado')

        # lookup for the trainer as discord member
        nick = "**__" + trainer[0] + "__**"
        trainer_discord = get_discord_member(client, trainer[1])

        rnd_profile = get_random_profile()
        color = (trainer_discord.color) if trainer_discord is not None else rnd_profile[0]
        avatar = (trainer_discord.avatar_url) if trainer_discord is not None else rnd_profile[1]

        # setup embed data
        embed = discord.Embed(color=color, type="rich")
        embed.set_thumbnail(url=avatar)

        embed.add_field(name="Discord", value=get_value_or_default(trainer, 1), inline=False)
        embed.add_field(name="Switch FC", value=get_value_or_default(trainer, 2), inline=False)
        embed.add_field(name="Showdown", value=get_value_or_default(trainer, 3), inline=False)

        await ctx.send(nick, embed=embed)

    else:
        max_data = 10
        data = get_trainer_database_spreadsheet()
        table = get_trainer_db_table()

        if len(data) > max_data:
            for _ in range(1, max_data):
                pos = randint(0, len(data)-1)
                table.append(data[pos])
                del data[pos]
        else:
            table.extend(data)

        # only table header
        if len(table) == 1:
            return await ctx.send('Treinadores não encontrados!')

        # show list of trainers
        embed = discord.Embed(color=0x1E1E1E, type="rich")
        embed.set_thumbnail(url="http://bit.ly/abp_logo")

        for _, trainer in enumerate(table[1:max_data+1], start=1):
            title = "{0} - {1}".format(trainer[0], get_value_or_default(trainer, 1, "n/a"))
            details = "FC: `{0}` | SD: `{1}`".format(get_value_or_default(trainer, 2),
                                                     get_value_or_default(trainer, 3))

            embed.add_field(name=title, value=details, inline=False)

        description = "**__Players__** - Você pode executar de novo e ver outros jogadores..."
        await ctx.send(description, embed=embed)


##########################################
# Comandos de interação com Bill
##########################################

# TODO Retornar erro ao nao enviar um id valido
@client.command(aliases=['ligas', 'liga'])
async def view_leagues(bot, league_id=None):
    """
    Consulta as ligas cadastradas.

    Para consultar uma lista de todas as ligas:

    /view_leagues

    Para consultar dados de uma liga específica pode-se fornecer o id da liga:

    /view_leagues liga1

    Aliases:
        ligas
        liga
    """
    # busca todas as ligas
    if not league_id:
        payload = Query.get_leagues()
        client = get_gql_client(BILL_API_URL)
        response = client.execute(payload)

        leagues = [edge.get('node') for edge in response['leagues'].get('edges')]

        embed = discord.Embed(color=0x1E1E1E, type="rich")
        embed.set_thumbnail(url="http://bit.ly/abp_logo")

        for league in leagues:
            league_hash_id = league.get('id', '?')
            reference = league.get('reference', '?')
            start_date = league.get('startDate', '?')
            end_date = league.get('endDate', '?')

            # desfaz a hash da liga
            _, league_id = b64decode(league_hash_id).decode('utf-8').split(':')

            body = f'ID: `liga{league_id}` | Data: de `{start_date}` a `{end_date}`\n'

            embed.add_field(name=reference, value=body, inline=False)

        description = 'Ligas Pokémon ABP'
        return await bot.send(description, embed=embed)

    # faz a hash da liga
    try:
        _, int_id = league_id.lower().split('liga')
    except Exception:
        return await bot.send('ID inválido!')  # TODO retornar Oak error

    # Garante que o id é realmente integer
    if not int_id.isdigit():
        return await bot.send('ID inválido!')  # TODO retornar Oak error

    league_hash = b64encode(f'LeagueType:{int_id}'.encode('utf-8')).decode('utf-8')
    payload = Query.get_leagues(id=league_hash)
    client = get_gql_client(BILL_API_URL)
    response = client.execute(payload)

    leagues = response['leagues']['edges']
    if not leagues:
        return #erro

    league = leagues[0]

    # desfaz a hash da liga
    league_hash_id = league['node'].get('id')
    _, league_id = b64decode(league_hash_id).decode('utf-8').split(':')

    embed = discord.Embed(color=0x1E1E1E, type="rich")
    embed.set_thumbnail(url="http://bit.ly/abp_logo")
    embed.add_field(name='ID', value=f'liga{league_id}', inline=True)
    embed.add_field(name='Referência', value=league['node'].get('reference'), inline=True)
    embed.add_field(name='Início', value=league['node'].get('startDate'), inline=True)
    embed.add_field(name='Fim', value=league['node'].get('endDate'), inline=True)
    embed.add_field(
        name='Competidores',
        value=len(league['node']['competitors'].get('edges')),
        inline=False
    )

    return await bot.send('Aqui', embed=embed)


# TODO review
@client.command(aliases=['vt', 't', 'trainers'])
async def view_trainers(bot, discord_id=None):
    """
    Visualiza dados de treiandores cadastrados

    Exemplo de uso, ver listagem de treinadores:
        /view_trainers

    Exemplo de uso, ver dados de um treinador:
        /view_trainers @Username

    Alaises:
        vt
        t
        trainers
    """
    embed = discord.Embed(color=0x1E1E1E, type="rich")

    if not discord_id:
        payload = Query.get_trainers()
        client = get_gql_client(BILL_API_URL)
        response = client.execute(payload)

        trainers = [edge.get('node') for edge in response['trainers'].get('edges')]

        for trainer in trainers:
            discord_id = trainer.get('discordId', '?')
            battle_counter = trainer.get('battleCounter', '?')
            lv = trainer.get('lv', '?')

            embed.add_field(name="Discord", value=discord_id, inline=True)
            embed.add_field(name="Lv", value=lv, inline=True)
            embed.add_field(name="Batalhas", value=battle_counter, inline=True)
            embed.add_field(name='_', value='__', inline=False)

        description = 'Treinadores ABP'
        embed.set_thumbnail(url="http://bit.ly/abp_logo")
        return await bot.send(description, embed=embed)

    # Caso seja fornecido um ID discord
    guild_member = next(
        iter(
            [member for member in bot.guild.members if member.id == int(discord_id[2:-1])]
            ),
        None  # default
    )
    if not guild_member:
        return await bot.send('Treinador inválido!')  # TODO Retornar Oak Error

    payload = Query.get_trainers(id=discord_id)
    client = get_gql_client(BILL_API_URL)
    response = client.execute(payload)

    trainers = [edge.get('node') for edge in response['trainers'].get('edges')]
    if not trainers:
        return await bot.send('Treinador não registrado!')

    embed = discord.Embed(color=0x1E1E1E, type="rich")

    discord_id = trainers[0].get('discordId', '?')
    battle_counter = trainers[0].get('battleCounter', '?')
    badge_counter = trainers[0].get('badgeCounter', '?')
    leagues_counter = trainers[0].get('leaguesCounter', '?')
    loose_percentage = trainers[0].get('loosePercentage', '?')
    join_date = parser.parse(trainers[0].get('joinDate')).strftime('%d/%m/%Y')
    win_percentage = trainers[0].get('winPercentage', '?')
    lv = trainers[0].get('lv', '?')
    exp = trainers[0].get('exp', '?')
    next_lv = trainers[0].get('nextLv', '?')
    fc = trainers[0].get('fc', '?')
    sd_id = trainers[0].get('sdId', '?')

    description = f'Trainer Card de {discord_id}'

    embed.set_thumbnail(url=guild_member.avatar_url._url)
    embed.add_field(name="Registrado em", value=parser.parse(join_date), inline=True)
    embed.add_field(name="Lv", value=lv, inline=True)
    embed.add_field(name="Próximo Lv", value=next_lv, inline=True)
    embed.add_field(name="Exp", value=exp, inline=True)
    embed.add_field(name="Insígnias", value=badge_counter, inline=True)
    embed.add_field(name="Batalhas", value=battle_counter, inline=True)
    embed.add_field(name="% Vitorias", value='%.2f'%win_percentage, inline=True)
    embed.add_field(name="% Derrotas", value='%.2f'%loose_percentage, inline=True)
    embed.add_field(name="Ligas", value=leagues_counter, inline=True)
    embed.add_field(name='FC', value=fc, inline=True)
    embed.add_field(name='ID Showdown', value=sd_id, inline=True)

    return await bot.send(description, embed=embed)


@client.command(aliases=['vl', 'leaders', 'lideres', 'lider', 'leader'])
async def view_leaders(bot, discord_id=None):
    """
    Visualiza dados de líderes

    Exemplo de uso, ver lista de líderes:
        /view_leaders

    Exemplo de uso, ver dados de um líder:
        /view_leaders @Username

    Aliases:
        vl
        leaders
        lideres
        lider
        leader
    """
    embed = discord.Embed(color=0x1E1E1E, type="rich")

    if not discord_id:
        payload = Query.get_leaders()
        client = get_gql_client(BILL_API_URL)
        response = client.execute(payload)

        leaders = [edge.get('node') for edge in response['leaders'].get('edges')]

        for leader in leaders:
            discord_id = leader.get('discordId', '?')
            lv = leader.get('lv', '?')
            fc = leader.get('fc', '?')

            embed.add_field(name="Discord", value=discord_id, inline=True)
            embed.add_field(name="Lv", value=lv, inline=True)
            embed.add_field(name="FC", value=fc, inline=True)
            embed.add_field(name='_', value='__', inline=False)

        description = 'Líderes ABP'
        embed.set_thumbnail(url="http://bit.ly/abp_logo")
        return await bot.send(description, embed=embed)

    # TODO fazer um wrapper
    # Caso seja fornecido um ID discord
    guild_member = next(
        iter(
            [member for member in bot.guild.members if member.id == int(discord_id[2:-1])]
            ),
        None  # default
    )
    if not guild_member:
        return await bot.send('Treinador inválido!')  # TODO Retornar Oak Error

    payload = Query.get_leaders(id=discord_id)
    client = get_gql_client(BILL_API_URL)
    response = client.execute(payload)

    leaders = [edge.get('node') for edge in response['leaders'].get('edges')]
    if not leaders:
        return await bot.send('Líder não registrado!')

    embed = discord.Embed(color=0x1E1E1E, type="rich")

    discord_id = leaders[0].get('discordId', '?')
    battle_counter = leaders[0].get('battleCounter', '?')
    loose_percentage = leaders[0].get('loosePercentage', '?')
    win_percentage = leaders[0].get('winPercentage', '?')
    lv = leaders[0].get('lv', '?')
    exp = leaders[0].get('exp', '?')
    next_lv = leaders[0].get('nextLv', '?')
    fc = leaders[0].get('fc', '?')
    sd_id = leaders[0].get('sdId', '?')
    role = leaders[0].get('role', '?')
    poke_type = leaders[0].get('pokemonType', '?')

    description = f'Leader Card de {discord_id}'

    embed.set_thumbnail(url=guild_member.avatar_url._url)
    embed.add_field(name="Tipo Pokémon", value=poke_type, inline=True)
    embed.add_field(name="Cargo", value=role, inline=True)
    embed.add_field(name="Lv", value=lv, inline=True)
    embed.add_field(name="Próximo Lv", value=next_lv, inline=True)
    embed.add_field(name="Exp", value=exp, inline=True)
    embed.add_field(name="Batalhas", value=battle_counter, inline=True)
    embed.add_field(name="% Vitorias", value='%.2f'%win_percentage, inline=True)
    embed.add_field(name="% Derrotas", value='%.2f'%loose_percentage, inline=True)
    embed.add_field(name='FC', value=fc, inline=True)
    embed.add_field(name='ID Showdown', value=sd_id, inline=True)

    return await bot.send(description, embed=embed)


# TODO encapsulate the algorithm inside this func to a dedicated module
@client.command(aliases=['nt'])
async def new_trainer(bot, discord_id=None):
    """
    Solicita a criação de um novo treinador ao banco de dados.

    Exemplo de uso:
        /nt @Username

    Aliases:
        nt
    """
    embed = discord.Embed(color=0x1E1E1E, type="rich")

    # Se não fornecer o discord ID
    if not discord_id:
        title = 'Por favor marque o treinador a ser registrado!'
        embed.add_field(name='Exemplo', value='`/new_trainer @username`', inline=False)
        return await bot.send(title, embed=embed)

    # Verifica se é administrador ou auto registro
    is_adm = 'ADM' in [r.name for r in bot.author.roles]
    is_self_registering = discord_id == f'<@{bot.author.id}>'

    # Somente adms criam treinador e ou o proprio treinador pode se registrar
    if not is_adm and not is_self_registering:
        title = ':octagonal_sign:'
        embed.add_field(
            name='Pemissão negada',
            value='Você não tem permissão para registrar um treinador!',
            inline=False
        )
        return await bot.send(title, embed=embed)

    # Verifica que o discord_id fornecido é um usuário do servidor
    guild_member = next(
        iter(
            [member for member in bot.guild.members if member.id == int(discord_id[2:-1])]
            ),
        None  # default
    )
    if not guild_member:
        return await bot.send('Treinador inválido!')  # TODO Retornar Oak Error

    payload = Mutations.create_trainer(discord_id)
    client = get_gql_client(BILL_API_URL)

    try:
        response = client.execute(payload)
    except Exception as err:
        stdout.write(f'Erro: {str(err)}\n\n')

        is_unique = literal_eval(err.args[0]).get('message').startswith('UNIQUE')
        if is_unique:
            return await bot.send('Este treinador já está registrado!')
        return await bot.send(
            'Sinto muito. Não pude processar esta operação.\n'\
            'Por favor, tente novamente mais tarde'
        )  # TODO retornar Oak error

    trainer = response['createTrainer'].get('trainer')
    join_date = parser.parse(trainer.get('joinDate')).strftime('%d/%m/%Y')

    # retorna usuario registrado
    embed.set_thumbnail(url=guild_member.avatar_url._url)
    description = 'Bem vindo Vindo a liga ABP.\nAqui está seu Trainer Card:'
    embed.add_field(name='ID Discord:', value=trainer.get('discordId'), inline=True)
    embed.add_field(name='Nome:', value=guild_member.name, inline=True)
    embed.add_field(name='Registro:', value=join_date, inline=False)
    embed.add_field(name='Lv:', value=trainer.get('lv'), inline=True)
    embed.add_field(name='Next:', value=trainer.get('nextLv'), inline=True)
    embed.add_field(name='Exp.:', value=trainer.get('exp'), inline=True)
    embed.add_field(name='Batalhas:', value=trainer.get('battleCounter'), inline=True)
    embed.add_field(name='Insígnias:', value=trainer.get('badgeCounter'), inline=True)
    embed.add_field(name='Ligas:', value=trainer.get('leaguesCounter'), inline=True)
    embed.add_field(name='% Vitórias:', value=trainer.get('winPercentage'), inline=True)
    embed.add_field(name='% Derrotas:', value=trainer.get('loosePercentage'), inline=True)

    await bot.send(description, embed=embed)


@client.command(aliases=['nliga', 'cliga'])
async def new_league(bot, *reference):
    """
    Envia uma requisição solicitando a criação de uma nova liga.

    Exemplo de uso:
        /new_league Liga 2089 Pokemon Galaxy & Universe

    Aliases:
        nliga
        cliga
    """
    embed = discord.Embed(color=0x1E1E1E, type="rich")

    # somente administradores podem registrar ligas
    is_adm = 'ADM' in [r.name for r in bot.author.roles]  # TODO fazer um wrapper

    if not is_adm:
        title = ':octagonal_sign:'
        embed.add_field(
            name='Pemissão negada',
            value='Você não tem permissão para registrar uma liga!',
            inline=False
        )
        return await bot.send(title, embed=embed)

    # Se não fornecer o discord ID
    if not reference:
        title = 'Por favor insira um nome ou referência para esta Liga!'
        embed.add_field(name='Exemplo', value='`/new_league Liga 2020`', inline=False)
        return await bot.send(title, embed=embed)

    reference = ' '.join(word for word in reference)

    payload = Mutations.create_league(reference)
    client = get_gql_client(BILL_API_URL)

    try:
        response = client.execute(payload)
    except Exception as err:
        stdout.write(f'Erro: {str(err)}\n\n')

        is_unique = literal_eval(err.args[0]).get('message').startswith('UNIQUE')
        if is_unique:
            return await bot.send('Esta liga já está registrada!')
        return await bot.send(
            'Sinto muito. Não pude processar esta operação.\n'\
            'Por favor, tente novamente mais tarde'
        )  # TODO retornar Oak error

    league = response['createLeague'].get('league')

    # desfaz a hash da liga
    league_hash_id = league.get('id')
    _, league_id = b64decode(league_hash_id).decode('utf-8').split(':')

    description = 'Liga Registrada com sucesso!'
    embed.add_field(name='ID:', value=f'liga{league_id}', inline=True)
    embed.add_field(name='Referência:', value=league.get('reference'), inline=True)
    return await bot.send(description, embed=embed)


@client.command(aliases=['nl'])
async def new_leader(bot, *args):
    """
    Envia uma requisição solicitando a criação de um novo líder.

    Exemplo de uso:
        /new_leader @Username fire elite_four

    Cargos aceitos:
        gym_leader
        elite_four
        champion

    Tipos aceitos:
        Normal
        Fire
        Water
        Grass
        Electric
        Ice
        Fighting
        Poison
        Ground
        Flying
        Psychic
        Bug
        Rock
        Ghost
        Dark
        Dragon
        Steel
        Fairy
        All

    Aliases:
        nl
    """
    embed = discord.Embed(color=0x1E1E1E, type="rich")

    # somente administradores podem registrar ligas
    is_adm = 'ADM' in [r.name for r in bot.author.roles]  # TODO fazer um wrapper

    if not is_adm:
        title = ':octagonal_sign:'
        embed.add_field(
            name='Pemissão negada',
            value='Você não tem permissão para registrar um Líder!',
            inline=False
        )
        return await bot.send(title, embed=embed)

    if len(args) is not 3:
        title = 'Preciso que me informe **três** parâmetros '\
                '**exatamente** nesta ordem!'
        embed.add_field(
            name='Exemplo 1',
            value='`/new_leader @fulano fire gym_leader`',
            inline=False
        )
        embed.add_field(
            name='Exemplo 2',
            value='`/new_leader @ciclano fairy elite_four`',
            inline=False
        )
        embed.add_field(
            name='Exemplo 3',
            value='`/new_leader @fulano grass champion`',
            inline=False
        )
        return await bot.send(title, embed=embed)

    discord_id, poke_type, role = args
    # Verifica que o discord_id fornecido é um usuário do servidor
    guild_member = next(
        iter(
            [member for member in bot.guild.members if member.id == int(discord_id[2:-1])]
        ),
        None  # default
    )
    if not guild_member:
        return await bot.send('Trainador inválido!')  # TODO Retornar Oak Error

    payload = Mutations.create_leader(
        discord_id,
        poke_type.upper(),
        role.upper()
    )
    client = get_gql_client(BILL_API_URL)

    try:
        response = client.execute(payload)
    except Exception as err:
        stdout.write(f'Erro: {str(err)}\n\n')

        is_unique = literal_eval(err.args[0]).get('message').startswith('UNIQUE')
        if is_unique:
            return await bot.send('Este líder já está registrado!')
        return await bot.send(
            'Sinto muito. Não pude processar esta operação.\n'\
            'Por favor, tente novamente mais tarde'
        )  # TODO retornar Oak error

    leader = response['createLeader'].get('leader')

    # retorna usuario registrado
    embed.set_thumbnail(url=guild_member.avatar_url._url)
    description = 'Registro de líder sucedido:'
    embed.add_field(name='ID Discord:', value=leader.get('discordId'), inline=True)
    embed.add_field(name='Nome:', value=guild_member.name, inline=True)
    embed.add_field(name='Lv:', value=leader.get('lv'), inline=True)
    embed.add_field(name='Next:', value=leader.get('nextLv'), inline=True)
    embed.add_field(name='Exp.:', value=leader.get('exp'), inline=True)
    embed.add_field(name='Batalhas:', value=leader.get('battleCounter'), inline=True)
    embed.add_field(name='% Vitórias:', value=leader.get('winPercentage'), inline=True)
    embed.add_field(name='% Derrotas:', value=leader.get('loosePercentage'), inline=True)
    return await bot.send(description, embed=embed)


# TODO review
@client.command(aliases=['lr', 'registro_liga', 'rl'])
async def league_register(bot, *args):
    """
    Solicita a API a inscrição de um jogador em uma liga pokemon.
    Deve-se fornecer um parâmetro informando se o jogador é um treinador
    que irá competir na liga ou um líder que irá defender a liga.
    Params:
                -t : Treinador
                -l : Líder

    Em caso de registro de treinador fornecer o parâmetro seguido do id discord:
    Ex:
                -t @Username liga1

    Em caso de registro de líder:
    Ex:
                -l @Username liga1

    Aliases:
        registro_liga
        rl
        lr
    """

    embed = discord.Embed(color=0x1E1E1E, type="rich")

    # somente administradores podem registrar jogadores nas ligas
    is_adm = 'ADM' in [r.name for r in bot.author.roles]  # TODO fazer um wrapper

    if not is_adm:
        title = ':octagonal_sign:'
        embed.add_field(
            name='Pemissão negada',
            value='Você não tem permissão para isso!',
            inline=False
        )
        return await bot.send(title, embed=embed)

    if len(args) < 3:
        title = 'Parâmetros ausêntes :octagonal_sign:'
        example = 'Por favor forneça os parâmetros corretamente!\n'\
                  '\nPara registrar um treinador em uma liga:\n'\
                  '`/league_register -t @username id_liga`'\
                  '\n\nPara registrar um líder em uma liga:\n'\
                  '`/league_register -l @username id_liga\n`'\
                  '\n\nVocê pode enviar `/help league_register` para mais ajuda!\n'
        embed.add_field(
            name='Exemplo',
            value=example,
            inline=False
        )
        return await bot.send(title, embed=embed)

    option, discord_id, league, *_ = args

    # Tenta iniciar a sequência de fabricacnao da hash base64
    try:
        _, int_id = league.lower().split('liga')
    except Exception:
        return await bot.send('ID de liga inválido!')  # TODO retornar Oak error

    # Garante que o id é realmente integer
    if not int_id.isdigit():
        return await bot.send('ID de liga inválido!')  # TODO retornar Oak error

    # faz a hash da liga
    league = b64encode(f'LeagueType:{int_id}'.encode('utf-8')).decode('utf-8')

    options = {'-t': True, '-l': False}
    if not option in options.keys():
        return await bot.send('Aceito somente as opções `-t` e `-l`')

    payload = Mutations.league_registration(discord_id, league, options[option])
    client = get_gql_client(BILL_API_URL)

    try:
        response = client.execute(payload)
    except Exception as err:
        stdout.write(f'Erro: {str(err)}\n\n')
        error_message = literal_eval(err.args[0]).get('message')
        is_unique = 'already registered' in error_message
        if is_unique:
            return await bot.send('Este usuário já foi registrado!')

        does_not_exist = 'does not exist' in error_message
        if does_not_exist:
            return await bot.send(
                'Este usuário não foi registrado!\n\nDica: `/help new_trainer`'
            )

        return await bot.send(
            'Sinto muito. Não pude processar esta operação.\n'\
            'Por favor, tente novamente mais tarde'
        )  # TODO retornar Oak error

    return await bot.send(response['leagueRegistration'].get('registration'))


# TODO review
@client.command(aliases=['br', 'new_battle', 'battle', 'rb'])
async def battle_register(bot, *args):
    """
    Registra uma batalha entre um treinador e um líder

    Exemplo de uso:
        /battle_register liga1 @trainer @leader @winner

    Aliases:
        new_battle
        battle
        br
        rb
    """
    embed = discord.Embed(color=0x1E1E1E, type="rich")

    # somente administradores podem registrar jogadores nas ligas
    is_adm = 'ADM' in [r.name for r in bot.author.roles]  # TODO fazer um wrapper

    if not is_adm:
        title = ':octagonal_sign:'
        return await bot.send(title, embed=embed)

    if len(args) < 4:
        title = 'Parâmetros incorretos :octagonal_sign:'
        embed.add_field(
            name='Exemplo de uso:',
            value='`/battle_register HashD4l1g4== @treinador @lider @vencedor`',
            inline=False
        )
        return await bot.send(title, embed=embed)  # TODO retornar Oak param error

    league, trainer, leader, winner, *_ = args

    # Tenta iniciar a sequência de fabricacnao da hash base64
    try:
        _, int_id = league.lower().split('liga')
    except Exception:
        return await bot.send('ID de liga inválido!')  # TODO retornar Oak error

    # Garante que o id é realmente integer
    if not int_id.isdigit():
        return await bot.send('ID de liga inválido!')  # TODO retornar Oak error

    # faz a hash da liga
    league = b64encode(f'LeagueType:{int_id}'.encode('utf-8')).decode('utf-8')

    payload = Mutations.battle_registration(league, trainer, leader, winner)
    client = get_gql_client(BILL_API_URL)

    try:
        response = client.execute(payload)
    except Exception as err:
        stdout.write(f'Erro: {str(err)}\n\n')

        err_message = literal_eval(err.args[0]).get('message')
        if 'trainer is in standby' in err_message:
            return await bot.send(
                'Este treinador está de molho e não pode batalhar!'
            )

        return await bot.send('Desculpe! Não pude realizar esta operação')

    # TODO tratar possíveis erros
    battle_date = response['battleRegister']['battle'].get('battleDatetime')
    winner = next(
        iter(
            [member for member in bot.guild.members \
                if member.id == int(response['battleRegister']['battle'].get('winner')[2:-1])]
            ),
        response['battleRegister']['battle'].get('winner')  # default
    )
    embed.set_thumbnail(url=winner.avatar_url._url)
    embed.add_field(name='Data da batalha:', value=battle_date, inline=False)
    embed.add_field(name='Vancedor:', value=winner.name, inline=False)
    # TODO mostrar quem X quem

    return await bot.send('Batalha registrada!', embed=embed)


@client.command(aliases=['ab', 'add', 'addb'])
async def add_badge(bot, discord_id=None, badge=None, league=None):
    """
    Adiciona uma insígnia à um treinador

    Exemplo de uso:
        /add_badge @Username fire liga1

    Insígnias aceitas:
        Normal
        Fire
        Water
        Grass
        Electric
        Ice
        Fighting
        Poison
        Ground
        Flying
        Psychic
        Bug
        Rock
        Ghost
        Dark
        Dragon
        Steel
        Fairy

    Aliases:
        add
        addb
        ab
    """
    a_valid_intention = discord_id and badge and league
    is_adm = 'ADM' in [r.name for r in bot.author.roles]  # TODO fazer um wrapper
    is_gym_leader = 'GYM LEADER' in [r.name for r in bot.author.roles]

    if not is_adm and not is_gym_leader:
        return await bot.send('Você não tem permissão para fazer isso')

    # TODO Adicionar verificação que valida se o gym leader é do tipo da insígnia

    if not a_valid_intention:
        return await bot.send(
            'Formato inválido!\nExemplo de uso:'\
            '\n`/add_badge @username dragon liga1`'
        )

    badges = set([
        'Normal', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Fighting',
        'Poison', 'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost',
        'Dark', 'Dragon', 'Steel', 'Fairy'
    ])

    a_valid_badge = badge.title() in badges
    if not a_valid_badge:
        return await bot.send('Insígnia inválida!')  # TODO retornar Oak error

    valid_member = next(
        iter(
            [member for member in bot.guild.members \
                if member.id == int(discord_id[2:-1])]
            ),
        None,  # default
    )

    if not valid_member:
        return await bot.send('Usuário inválido!')  # TODO retornar oak error

    # Tenta iniciar a sequência de fabricacnao da hash base64
    try:
        _, int_id = league.lower().split('liga')
    except Exception:
        return await bot.send('ID de liga inválido!')  # TODO retornar Oak error

    # Garante que o id é realmente integer
    if not int_id.isdigit():
        return await bot.send('ID de liga inválido!')  # TODO retornar Oak error

    # faz a hash da liga
    league = b64encode(f'LeagueType:{int_id}'.encode('utf-8')).decode('utf-8')

    payload = Mutations.add_badge(discord_id, badge, league)
    client = get_gql_client(BILL_API_URL)

    try:
        response = client.execute(payload)
    except Exception as err:
        stdout.write(f'Erro: {str(err)}\n\n')
        error_message = literal_eval(err.args[0]).get('message')

        if error_message == 'This trainer already have this badge!':
            return await bot.send('Esse treinador ja possui esta insígnia!')

        return await bot.send('Desculpe! Não pude realizar esta operação')

    response = response['addBadgeToTrainer'].get('response')
    if 'received' in response and 'badge' in response:
        emoji_name = get_badge_icon(badge.title())
        emoji_badge = ''.join(
            '<:{}:{}>'.format(e.name, e.id) for e in bot.guild.emojis if e.name == emoji_name
        )
        text = f'{discord_id} recebeu a insígnia {emoji_badge} !'

        return await bot.send(text)

    return await bot.send('Desculpe! Não pude realizar esta operação')


@client.command(aliases=['trainer_update', 'tupdate', 'tu'])
async def update_trainer(bot, discord_id=None, *tokens):
    """
    Atualiza dados de um treinador

    Exemplo de uso:
        /update_trainer @Username n Red

    Campos atualizáveis:
        n    :> Nome do Treinador
        fc   :> FC (Friend Code) do treinador
        sd   :> ID Showdown do treinador

    Aliases:
        trainer_update
        tupdate
        tu
    """
    embed = discord.Embed(color=0x1E1E1E, type="rich")

    # Somente pode-se atualizar os proprios dados
    self_update = discord_id == f'<@{bot.author.id}>'
    if not self_update:
        title = ':octagonal_sign:'
        embed.add_field(
            name='Pemissão negada',
            value='Você não tem permissão para isso!',
            inline=False
        )  # TODO retornar oak error
        return await bot.send(title, embed=embed)

    # Verifica que o discord_id fornecido é um usuário do servidor
    guild_member = next(
        iter(
            [member for member in bot.guild.members if member.id == int(discord_id[2:-1])]
            ),
        None  # default
    )
    if not guild_member:
        return await bot.send('Treinador inválido!')  # TODO Retornar Oak Error

    pairs = zip(*(iter(tokens),)*2)
    if not pairs:
        # TODO return oak error
        return await bot.send('Parâmetros ausentes')

    valid_options = {
        'n': 'name',
        'fc': 'fc',
        'sd': 'sd_id'
    }

    inputs = {}
    for pair in pairs:
        if pair[0].lower() in valid_options:
            inputs[valid_options[pair[0].lower()]] = pair[1]

    payload = Mutations.update_trainer(discord_id, **inputs)
    client = get_gql_client(BILL_API_URL)

    try:
        response = client.execute(payload)
    except Exception as err:
        stdout.write(f'Erro: {str(err)}\n\n')
        return # TODO retornar Oak error

    name = response['updateTrainer']['trainer'].get('name')
    fc = response['updateTrainer']['trainer'].get('fc')
    sd_id = response['updateTrainer']['trainer'].get('sdId')

    embed.set_thumbnail(url=guild_member.avatar_url._url)
    embed.add_field(name='Nome', value=name, inline=True)
    embed.add_field(name='FC', value=fc, inline=True)
    embed.add_field(name='ID Showdown', value=sd_id, inline=True)
    description = f'{discord_id} seus dados foram atualizados!'

    return await bot.send(description, embed=embed)


@client.command(aliases=['leader_update', 'lu', 'lupdate'])
async def update_leader(bot, discord_id=None, *tokens):
    """
    Atualiza dados de um líder

    Exemplo de uso:
        /update_leader @username fc 1234567890

    Campos atualizaveis:
        n     :> Nome do líder
        fc    :> FC (Friend Code) do líder
        sd    :> ID Showdown do líder
        role  :> Cargo (gym_leader, elite_four, chmpion)
        type  :> Tipo pokémon (fire, grass, dragon ... all)

    Aliases:
        leader_update
        lu
        lupdate
    """
    embed = discord.Embed(color=0x1E1E1E, type="rich")

    # Somente pode-se atualizar os proprios dados
    self_update = discord_id == f'<@{bot.author.id}>'
    if not self_update:
        title = ':octagonal_sign:'
        embed.add_field(
            name='Pemissão negada',
            value='Você não tem permissão para isso!',
            inline=False
        )  # TODO retornar oak error
        return await bot.send(title, embed=embed)

    # Verifica que o discord_id fornecido é um usuário do servidor
    guild_member = next(
        iter(
            [member for member in bot.guild.members if member.id == int(discord_id[2:-1])]
        ),
        None  # default
    )
    if not guild_member:
        return await bot.send('Líder inválido!')  # TODO Retornar Oak Error

    pairs = zip(*(iter(tokens),)*2)
    if not pairs:
        # TODO return oak error
        return await bot.send('Parâmetros ausentes')

    valid_options = {
        'n': 'name',
        'fc': 'fc',
        'sd': 'sd_id',
        'role': 'role',
        'type': 'poke_type'
    }

    inputs = {}
    for pair in pairs:
        if pair[0].lower() in valid_options:
            inputs[valid_options[pair[0].lower()]] = pair[1]

    payload = Mutations.update_leader(discord_id, **inputs)
    client = get_gql_client(BILL_API_URL)

    try:
        response = client.execute(payload)
    except Exception as err:
        stdout.write(f'Erro: {str(err)}\n\n')
        return await bot.send('Desculpe não pude realizar esta operação!')

    name = response['updateLeader']['leader'].get('name')
    fc = response['updateLeader']['leader'].get('fc')
    sd_id = response['updateLeader']['leader'].get('sdId')
    role = response['updateLeader']['leader'].get('role')
    poke_type = response['updateLeader']['leader'].get('pokemonType')

    embed.set_thumbnail(url=guild_member.avatar_url._url)
    embed.add_field(name='Nome', value=name, inline=True)
    embed.add_field(name='FC', value=fc, inline=True)
    embed.add_field(name='ID Showdown', value=sd_id, inline=True)
    embed.add_field(name='Tipo', value=poke_type, inline=True)
    embed.add_field(name='Cargo', value=role, inline=True)
    description = f'{discord_id} seus dados foram atualizados!'

    return await bot.send(description, embed=embed)


# TODO os parametros string precisam ser "joineds", ou seja, formar sentenças
# a partir dos tokens, pois se na descrição for fornecido "um lugar bonito"
# será salvo somente "um". Talvez substituir *tokens por dois parametros explcitos
# fazendo com que a função opera somente uma opção por vez.
@client.command(aliases=['atualiza_liga', 'al', 'ul'])
async def update_league(bot, league_id=None, *tokens):
    """
    Atualiza dados de uma liga

    Exemplo de uso:
        /update_league liga1 inicio 15-03-2020

    Campos atualizaveis:
        inicio :> Data de iníncio da liga
        fim    :> Data de encerramento da liga
        n      :> Nome da liga
        ref    :> Referencia da liga

    Aliases:
        atualiza_liga
        al
        ul
    """
    embed = discord.Embed(color=0x1E1E1E, type="rich")

    is_adm = 'ADM' in [r.name for r in bot.author.roles]  # TODO fazer um wrapper
    if not is_adm:
        return await bot.send('Você não tem permissão para fazer isso')

    if not league_id:
        title = 'Por favor marque forneça o ID da liga e os parâmetros!'
        embed.add_field(
            name='Exemplo',
            value='`/update_league liga1 inicio 15-03-2020`',
            inline=False
        )
        return await bot.send(title, embed=embed)

    # Tenta iniciar a sequência de fabricacnao da hash base64
    try:
        _, int_id = league_id.lower().split('liga')
    except Exception:
        return await bot.send('ID de liga inválido!')  # TODO retornar Oak error

    # Garante que o id é realmente integer
    if not int_id.isdigit():
        return await bot.send('ID de liga inválido!')  # TODO retornar Oak error

    # faz a hash da liga
    league_id = b64encode(f'LeagueType:{int_id}'.encode('utf-8')).decode('utf-8')

    pairs = zip(*(iter(tokens),)*2)
    if not pairs:
        # TODO return oak error
        return await bot.send('Parâmetros ausentes')

    valid_options = {
        'n': 'name',
        'ref': 'reference',
        'inicio': 'start_date',
        'fim': 'end_date',
    }

    inputs = {}
    for pair in pairs:
        if pair[0].lower() in valid_options:
            if pair[0] == 'inicio' or pair[0] == 'fim':
                inputs[valid_options[pair[0].lower()]] = datetime.strftime(
                    parser.parse(pair[1]), '%Y-%m-%d'
                )
            else:
                inputs[valid_options[pair[0].lower()]] = pair[1]

    payload = Mutations.update_league(league_id, **inputs)
    client = get_gql_client(BILL_API_URL)

    try:
        response = client.execute(payload)
    except Exception as err:
        stdout.write(f'Erro: {str(err)}\n\n')
        return await bot.send('Desculpe não pude realizar esta operação!')

    reference = response['updateLeague']['league'].get('reference') or '?'
    start_date = response['updateLeague']['league'].get('startDate') or '?'
    end_date = response['updateLeague']['league'].get('endDate') or '?'

    embed = discord.Embed(color=0x1E1E1E, type="rich")
    embed.set_thumbnail(url="http://bit.ly/abp_logo")
    embed.add_field(name='Referência', value=reference, inline=True)
    embed.add_field(name='Início', value=start_date, inline=True)
    embed.add_field(name='Fim', value=end_date, inline=True)

    return await bot.send('Liga atualizada!', embed=embed)


@client.command(aliases=['sc', 'lscores', 'resumo_placar', 'rp'])
async def scores(bot, league_id=None):
    """
    Consulta o resumo dos scores de uma liga

    Exmplo de uso:
        /scores liga1

    Aliases:
        sc
        lscores
        resumo_placar
        rp
    """
    if not league_id:
        return await bot.send(
            'É preciso informar o id de uma liga!\nEx:\n`/scores liga1`'
        )  # TODO retornar Oak error

    embed = discord.Embed(color=0x1E1E1E, type="rich")
    embed.set_thumbnail(url="http://bit.ly/abp_logo")

    # faz a hash da liga
    try:
        _, int_id = league_id.lower().split('liga')
    except Exception:
        return await bot.send('ID inválido!')  # TODO retornar Oak error

    # Garante que o id é realmente integer
    if not int_id.isdigit():
        return await bot.send('ID inválido!')  # TODO retornar Oak error

    league_hash = b64encode(f'LeagueType:{int_id}'.encode('utf-8')).decode('utf-8')

    payload = Query.get_scores(league_id=league_hash)
    client = get_gql_client(BILL_API_URL)
    response = client.execute(payload)

    scores = response['scores']['edges']
    if not scores:
        return await bot.send('Não há scores nesta liga ainda!')  # TODO retornar Oak error

    for score in scores:
        trainer = score['node']['trainer'].get('discordId', '?')
        lv = score['node']['trainer'].get('lv', '?')
        wins = score['node'].get('wins', '?')
        losses = score['node'].get('losses', '?')
        badges = score['node'].get('badges', '?')
        standby = score['node'].get('standby')
        standby = ':exclamation:' if standby else ':white_check_mark:'

        body = f'{trainer} | **Lv**: `{lv}` | **Win**: `{wins}` | '\
               f'**Lose**: `{losses}` | **Insígnias**: `{len(badges)}` | '\
               f'**Molho**: {standby}'

        embed.add_field(name='Treinador', value=body, inline=False)

    return await bot.send('Scores', embed=embed)


@client.command(aliases=['tscore', 'ts', 'placar'])
async def trainer_score(bot, discord_id=None, league=None):
    """
    Informa o placar de um jogador em uma liga

    Exemplo de uso:
       /ts @username liga1

    Aliases:
        tscore
        ts
        placar
    """
    a_valid_intention = discord_id and league
    if not a_valid_intention:
        # TODO retornar oak error
        return await bot.send('Necessário marcar o treinador e informar a liga')

    # Verifica que o discord_id fornecido é um usuário do servidor
    guild_member = next(
        iter(
            [member for member in bot.guild.members if member.id == int(discord_id[2:-1])]
        ),
        None  # default
    )
    if not guild_member:
        return await bot.send('Treinador inválido!')  # TODO Retornar Oak Error

    # Tenta iniciar a sequência de fabricacnao da hash base64
    try:
        _, int_id = league.lower().split('liga')
    except Exception:
        return await bot.send('ID de liga inválido!')  # TODO retornar Oak error

    # Garante que o id é realmente integer
    if not int_id.isdigit():
        return await bot.send('ID de liga inválido!')  # TODO retornar Oak error

    # faz a hash da liga
    league_id = b64encode(f'LeagueType:{int_id}'.encode('utf-8')).decode('utf-8')

    payload = Query.get_trainer_score(discord_id, league_id)
    client = get_gql_client(BILL_API_URL)

    try:
        response = client.execute(payload)
    except Exception as err:
        stdout.write(f'Erro: {str(err)}\n\n')
        return # TODO retornar Oak error

    score_list = response['scores']['edges']

    if not score_list:
        return await bot.send('Nenhum score encontrado para esta combinação')

    score = next(iter(score_list)).get('node')

    # stats basicos
    trainer_lv = score['trainer'].get('lv')
    wins = score.get('wins')
    loses = score.get('losses')
    standby = score.get('standby')
    standby = ':exclamation:' if standby else ':white_check_mark:'
    stats = f'**Lv**: `{trainer_lv}` | **Vitórias**: `{wins}` | '\
            f'**Derrotas**: `{loses}` | **Molho**: {standby}'

    # insignas conquistadas
    badge_list = [get_badge_icon(badge) for badge in score.get('badges')]
    badges = ' '.join(get_emoji(bot, name) for name in badge_list)

    # última batalha do treinador
    have_battles = score['battles'].get('edges')
    if not have_battles:
        last_battle = 'Este treinador ainda não possui batalhas!'
    else:
        battle = next(iter(have_battles)).get('node')
        battle_datetime = parser.parse(battle.get('battleDatetime')).strftime('%d/%m/%Y')
        leader = battle['leader'].get('discordId')
        winner = battle.get('winner')
        last_battle = f'**Data**: `{battle_datetime}` | **Vs**: {leader} | '\
                      f'**Vencedor**: {winner}'

    embed = discord.Embed(color=0x1E1E1E, type='rich')
    embed.set_thumbnail(url=guild_member.avatar_url._url)
    embed.add_field(name='Stats', value=stats, inline=False)
    embed.add_field(name='Insígnias', value=badges, inline=False)
    embed.add_field(name='Última Batalha', value=last_battle, inline=False)

    msg = f'Placar de {discord_id} na {league}:'
    return await bot.send(msg, embed=embed)
