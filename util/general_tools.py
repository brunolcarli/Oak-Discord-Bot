'''
Módulo para ferramentas genéricas.
'''
import difflib
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
            trainer_has_points = int(trainer.get('Pontuação'))
        except ValueError:
            pass
        else:
            trainers.append(trainer)
    return sorted(trainers, key=lambda i: int(i['Pontuação']), reverse=True)

def get_ranked_spreadsheet():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'oak_ss_api_keys.json',
        scope
    )
    client = gspread.authorize(creds)
    sheet = client.open('Rankeadas ABP').sheet1

    data = sheet.get_all_records()
    return sort_trainers(data)
