'''
Módulo para ferramentas genéricas.
'''
import difflib
import string
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from settings import (RANKED_SPREADSHEET_ID, SCORE_INDEX, SD_NAME_INDEX)

def get_similar_pokemon(pokemon):
    '''
    Identifica se o pokémon solicitado com nome errado
    pelo usuário pode ser um dentre os existentes,
    devolvendo uma sugestão com o nome correto.

    param : pokemon : <str> : Nome do pokémon
    return : <str>
    '''
    with open('files/pokes.txt', 'r') as f:
        pokes = f.readlines()
    closest_pokemon = difflib.get_close_matches(pokemon, pokes)
    return ', '.join(poke for poke in closest_pokemon)

def get_trainer_rank(pts):
    '''
    Retorna o rank (elo) do treinador baseado
    na sua pontuação:
    Retardatário 0 - 99
    Bronze 100 - 299
    Prata 300 - 499
    Ouro 500 - 749
    Platina 750 - 849
    Diamante 850 - 949
    Mestre 950- 999
    Grand mestre 1000
    '''
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
        rank = 'Grande Mestre'
    return rank

def sort_trainers(data):
    '''
    ordena uma lista filtrada de trainers pelos pontos.
    '''    
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
    data = get_spreadsheet_data(RANKED_SPREADSHEET_ID, 'Rank!A1:F255')
    return sort_trainers(data)

def get_form_spreadsheet():
    data = get_spreadsheet_data(RANKED_SPREADSHEET_ID, 'Respostas ao formulário 2!A2:E255')
    return data

def get_spreadsheet_data(spreadSheetId, cellRange):
    scope = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'oak_ss_api_keys.json',
        scope
    )
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadSheetId, range=cellRange).execute()
    values = result.get('values', [])

    return values

def compare_insensitive(s1, s2):
    # TODO: improve it to ignore all special characters
    return s1.strip().lower().replace("á", "a") == s2.strip().lower().replace("á", "a")


def get_embed_output(ranked_table):
    """
    Processa uma mensagem embed bonita e formatada.

    param : ranked_table : <list> :

    return : <class 'discord.embeds.Embed'> :
    """

    rank_index = ranked_table[0].index("Rank")
    trainer1_elo_data = [item for item in elos_map if item[0] == ranked_table[1][rank_index].lower().replace("á", "a")][0]
    pts_size = len(str(ranked_table[1][4]))
    
    embed = discord.Embed(color=trainer1_elo_data[COLOR_INDEX], type="rich")
    embed.set_thumbnail(url="https://uploaddeimagens.com.br/images/002/296/393/original/abp_logo.png")
    
    for i, trainer in enumerate(ranked_table[1:21], start=1):
        elo = trainer[rank_index].lower().replace("á", "a")
        emoji = get(client.emojis, name=elo)

        title = "{0} {1}º - {2}".format(str(emoji), str(i), trainer[1])
        details = "Wins: `{0:0>3}` | Bts: `{1:0>3}` | Pts: **`{2:0>{pts_size}}`**".format(trainer[2], trainer[3], trainer[4], pts_size=pts_size)
        embed.add_field(name=title, value=details, inline=True)

    return embed
