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
    return s1.lower().replace("á", "a") == s2.lower().replace("á", "a")