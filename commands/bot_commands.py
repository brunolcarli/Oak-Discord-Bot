"""
Módulo para comandos do bot. Neste arquivo deverão conter apenas funções de
chamada dos comandos que o bot responde. Demais algoritmos, mesmo contendo
o processamento destas funções devem estar em um outro módulo dedicado e
importá-lo neste escopo, deixando este módulo o mais limpo possível e
facilitando a identificação e manutenção dos comandos.
"""

# std libs
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
from util.general_tools import (get_similar_pokemon, get_trainer_rank,
                                get_ranked_spreadsheet, get_form_spreadsheet,
                                get_trainer_database_spreadsheet, 
                                get_trainer_db_table, get_random_profile,
                                compare_insensitive, get_embed_output,
                                get_table_output, get_trainer_rank_row,
                                get_initial_ranked_table, find_trainer, 
                                find_db_trainer, get_discord_member,
                                get_value_or_default,
                                get_initial_ranked_table, find_trainer,
                                get_gql_client)

# requests tools
from util.get_api_data import (dex_information, get_pokemon_data,
                               get_item_data, item_information,
                               get_ability_data, ability_information)
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
@client.command()
async def view_leagues(bot, league_id=None):
    """
    Consulta as ligas cadastardas.

    Para consultar uma lista de todas as ligas:
    ```
    /view_leagues
    ```

    Para consultar dados de uma liga específica pode-se fornecer o id da liga:
    ```
    /view_leagues Ha5Hb4s364dAL1gA==
    ```

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
            league_id = league.get('id', '?')
            reference = league.get('reference', '?')
            start_date = league.get('startDate', '?')
            end_date = league.get('endDate', '?')
            league_description = league.get('description') or 'No description'

            body = f'ID: `{league_id}` | Data: de `{start_date}` a `{end_date}`\n'\
                f'`{league_description}`'

            embed.add_field(name=reference, value=body, inline=False)

        description = 'Ligas Pokémon ABP'
        return await bot.send(description, embed=embed)

    payload = Query.get_leagues(id=league_id)
    client = get_gql_client(BILL_API_URL)
    response = client.execute(payload)

    leagues = response['leagues']['edges']
    if not leagues:
        return #erro

    league = leagues[0]
    embed = discord.Embed(color=0x1E1E1E, type="rich")
    embed.set_thumbnail(url="http://bit.ly/abp_logo")
    embed.add_field(name='ID', value=league['node'].get('id'), inline=True)
    embed.add_field(name='Referência', value=league['node'].get('reference'), inline=True)
    embed.add_field(name='Início', value=league['node'].get('startDate'), inline=True)
    embed.add_field(name='Fim', value=league['node'].get('endDate'), inline=True)
    embed.add_field(
        name='Competidores',
        value=len(league['node']['competitors'].get('edges')),
        inline=False
    )

    return await bot.send('Aqui', embed=embed)

# @client.command()
# async def view_trainers(ctx):
#     payload = get_trainers()
#     client = get_gql_client(BILL_API_URL)
#     response = client.execute(payload)

#     trainers = [edge.get('node') for edge in response['trainers'].get('edges')]

#     embed = discord.Embed(color=0x1E1E1E, type="rich")
#     embed.set_thumbnail(url="http://bit.ly/abp_logo")

#     for trainer in trainers:
#         trainer_id = trainer.get('id', '?')
#         name = trainer.get('name', '?')
#         join_date = trainer.get('joinDate', '?')
#         battle_counter = trainer.get('battleCounter', '?')
#         win_percentage = trainer.get('winPercentage', '?')


#         body = f'ID: `{league_id}` | Data: de `{start_date}` a `{end_date}`\n'\
#                f'`{league_description}`'

#         embed.add_field(name=reference, value=body, inline=False)

#     description = 'Ligas Pokémon ABP'
#     await ctx.send(description, embed=embed)

# @client.command()
# async def foo(ctx, param=None, value=None):
#     a_valid_intention = param and value
#     if not a_valid_intention:
#         return await ctx.send('Chamada inválida ao comando!')


# TODO encapsulate the algorithm inside thos func to a dedicated module
@client.command()
async def new_trainer(bot, discord_id=None):
    """
    Solicita a criação de um novo treinador ao banco de dados.
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


@client.command()
async def new_league(bot, *reference):
    """
    Envia uma requisição solicitando a criação de uma nova liga.
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

    description = 'Liga Registrada com sucesso!'
    embed.add_field(name='ID:', value=league.get('id'), inline=True)
    embed.add_field(name='Referência:', value=league.get('reference'), inline=True)
    return await bot.send(description, embed=embed)


@client.command()
async def new_leader(bot, *args):
    """
    Envia uma requisição solicitando a criação de um novo líder.
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
        title = 'Preciso que me informe **três** parâmetros **exatamente** nesta ordem!'
        embed.add_field(name='Exemplo 1', value='`/new_leader @fulano fire gym_leader`', inline=False)
        embed.add_field(name='Exemplo 2', value='`/new_leader @ciclano fairy elite_four`', inline=False)
        embed.add_field(name='Exemplo 3', value='`/new_leader @fulano grass champion`', inline=False)
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

# TODO
@client.command()
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
                -t @Username HashIdDaLiga==

    Em caso de registro de líder deve-se fornecer também o tipo de pokemon e
    papel do líder, separados pelo caracter underscore (_)
    Ex:
                -l @Username HashIdDaLiga==

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
