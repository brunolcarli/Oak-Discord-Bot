"""
Módulo para ferramentas genéricas.
"""
import difflib
import discord
from discord.utils import get
from tabulate import tabulate
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from settings import (RANKED_SPREADSHEET_ID, SCORE_INDEX, SD_NAME_INDEX,
                      COLOR_INDEX)
from util.elos import (ELOS_MAP, get_elo_name)


def get_similar_pokemon(pokemon):
    """
    Identifica se o pokémon solicitado com nome errado
    pelo usuário pode ser um dentre os existentes,
    devolvendo uma sugestão com o nome correto.

    param : pokemon : <str> : Nome do pokémon
    return : <str>
    """
    with open('files/pokes.txt', 'r') as f:
        pokes = f.readlines()

    closest_pokemon = difflib.get_close_matches(pokemon, pokes)
    return ', '.join(poke for poke in closest_pokemon)


def get_trainer_rank(pts):
    """
    Retorna o rank (elo) do treinador baseado
    na sua pontuação:
    Retardatário 0 - 99
    Bronze 100 - 299
    Prata 300 - 499
    Ouro 500 - 749
    Platina 750 - 849
    Diamante 850 - 949
    Mestre 950- 999
    Grão mestre 1000
    """
    pts = int(pts)
    if pts < 100:
        rank = 'Retardatário'
    elif pts >= 100 and pts < 300:
        rank = 'Bronze'
    elif pts >= 300 and pts < 500:
        rank = 'Prata'
    elif pts >= 500 and pts < 750:
        rank = 'Ouro'
    elif pts >= 750 and pts < 850:
        rank = 'Platina'
    elif pts >= 850 and pts < 950:
        rank = 'Diamante'
    elif pts >= 950 and pts < 1000:
        rank = 'Mestre'
    elif pts >= 1000:
        rank = 'Grão Mestre'
    return rank


def sort_trainers(data):
    """
    Ordena uma lista filtrada de trainers pelos pontos.

    param : data : <list>
    returns : <list>
    """
    trainers = []
    for trainer in data:
        try:
            trainer_has_points = int(trainer[SCORE_INDEX])
        except ValueError:
            pass
        else:
            trainers.append(trainer)
    return sorted(trainers, key=lambda i: int(i[SCORE_INDEX]), reverse=True)


def get_ranked_spreadsheet():
    """
    Retorna os dados da planilha do ranked.
    """
    data = get_spreadsheet_data(RANKED_SPREADSHEET_ID, 'Rank!A1:F255')
    return sort_trainers(data)


def get_form_spreadsheet():
    """
    Retorna os dados de formulário da planilha do ranked.
    """
    data = get_spreadsheet_data(RANKED_SPREADSHEET_ID, 'Respostas ao formulário 2!A2:E255')
    return data


def get_spreadsheet_data(spreadsheet_id, cell_range):
    scope = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'oak_ss_api_keys.json',
        scope
    )
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    result = sheet.values().get(
        spreadsheetId=spreadsheet_id, range=cell_range
    ).execute()

    values = result.get('values', [])

    return values

def compare_insensitive(s1, s2):
    # TODO: improve it to ignore all special characters
    s1 = s1.strip().lower().replace("á", "a").replace("ã", "a").replace(" ", "")
    s2 = s2.strip().lower().replace("á", "a").replace("ã", "a").replace(" ", "")

    return s1 == s2


def get_embed_output(ranked_table, client):
    """
    Processa uma mensagem embed bonita e formatada.

    param : ranked_table : <list> :
    param : client : Bot client instance :

    return : <class 'discord.embeds.Embed'> :
    """
    rank_index = ranked_table[0].index("Rank")
    trainer1_elo_data = [item for item in ELOS_MAP \
        if item[0] == get_elo_name(ranked_table[1][rank_index])][0]

    pts_size = len(str(ranked_table[1][4]))

    embed = discord.Embed(color=trainer1_elo_data[COLOR_INDEX], type="rich")
    embed.set_thumbnail(url="http://bit.ly/abp_logo")

    for i, trainer in enumerate(ranked_table[1:21], start=1):
        elo = get_elo_name(trainer[rank_index])
        emoji = get(client.emojis, name=elo)

        title = "{0} {1}º - {2}".format(str(emoji), str(i), trainer[1])
        details = "Wins: `{0:0>3}` | Bts: `{1:0>3}` | \
            Pts: **`{2:0>{pts_size}}`**".format(
                trainer[2],
                trainer[3],
                trainer[4],
                pts_size=pts_size
            )

        embed.add_field(name=title, value=details, inline=True)

    return embed


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
    rank = get_trainer_rank(trainer[SCORE_INDEX])
    trainer.append(rank)

    return trainer


def get_initial_ranked_table():
    """
    Retorna uma lista contendo uma lista com as colunas a serem exibidas
    no placar da Ranked.

    params : None :
    return : <list> :
    """
    return [
        ['Pos', 'Nick', 'Wins', 'Bts', 'Pts', 'Rank'],
    ]


def find_trainer(trainer_nickname, data=None):
    """
    Procura por um treinador específico na tabela de treinadores da ranked.

    param : trainer_nickname : <str>
    param : data : <list> : param data default value : None

    return : <list>
    """
    data = data if data is not None else get_ranked_spreadsheet()
    pos = 0

    for trainer in data:
        pos += 1
        trainer_found = compare_insensitive(
            trainer[SD_NAME_INDEX],
            trainer_nickname
        )

        if trainer_found:
            trainer.append(pos)
            return trainer

    return None
