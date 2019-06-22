import requests
import json
from settings import (POKE_API_URL, EFFECTIVENESS_API_URL, ITEM_API_URL,
                    ABILITY_API_URL)

def get_immunities(pokemon_types):
    '''
    Determina se um pokémon é imune à um determinado
    tipo.

    param : pokemon_types : <list> : Tipos do pokémon
    return : <list>
    '''
    immunities = []
    if 'ghost' in pokemon_types:
        immunities.append('fighting')
        immunities.append('normal')
    if 'dark' in pokemon_types:
        immunities.append('psychic')
    if 'fairy' in pokemon_types:
        immunities.append('dragon')
    if 'steel' in pokemon_types:
        immunities.append('poison')
    if 'flying' in pokemon_types:
        immunities.append('ground')
    if 'normal' in pokemon_types:
        immunities.append('ghost')
    if 'ground' in pokemon_types:
        immunities.append('electric')
    return immunities

def validate(response):
    '''
    Valida a resposta de uma requisição.

    param : response : <requests.models.Response>
    return : <dict>
    '''
    if response.status_code == 200:
        data = json.loads(response.content)
        return data
    return {}

def get_pokemon_data(pokemon):
    '''
    Faz uma requisição à Poke API buscando
    pelos dados de um pokémon fornecido como
    parâmetro.

    param : pokemon : <str> : Nome do pokémon
    return : <dict>
    '''
    url = POKE_API_URL + pokemon + '/'
    response = requests.get(url)
    return validate(response)

def get_pokemon_effectiveness(dex_num):
    '''
    Faz uma requisição web buscando
    pelos dados de efetividade do pokemon pelo
    seu id (número na pokedex).
    A efetividade contempla:
    - Fraquezas
    - Resistência
    - Imunidade

    param : dex_num : <int> Número do pokémon na PokeDex
    return : <dict>
    '''
    response = requests.get(EFFECTIVENESS_API_URL)
    data = validate(response)
    # a resposta da requsição retorna uma lista
    # por iniciar do zero chamamos o pokémon pelo
    # ID - 1
    try:
        effectivness = data[dex_num - 1]
    except:
        effectivness = {}

    return effectivness

def get_item_data(item_name):
    '''
    Realiza uma requisição à Poke API solicitando
    pelos dados de um item fornecido por parâmetro.

    param : item_name : <str> : Nome do item

    return : <dict>
    '''
    url = ITEM_API_URL + item_name + '/'
    response = requests.get(url)
    return validate(response)

def get_ability_data(ability_name):
    '''
    Realiza uma requisição à Poke API solicitando
    por dados de uma habilidade fornecida por parâmetro.

    param : ability_name : <str> : Nome da habilidade
    return : <dict>
    '''
    url = ABILITY_API_URL + ability_name + '/'
    response = requests.get(url)
    return validate(response)

def parse_effectiveness(data):
    '''
    Realiza um parsing em um dicionário contendo as
    efetividades de um pokémon.

    param : data : <dict> : Dados de efetividade do pokémon
    return : <str>
    '''
    if not data:
        response = 'Dados de efetividade desconhecidos!'
    else:
        weakness = ', '.join(w for w in data.get('weaknesses'))
        resistance = ', '.join(r for r in data.get('strengths'))

        # Como a requisição não apresenta as imunidades
        # tenho que fazer isso 'na mão'
        immunities = ', '.join(i for i in get_immunities(data.get('types')))

        # monta a string com os dados
        response = 'Weakness: {}\nResistance: {}\nImmune: {}'.format(
            weakness, resistance, immunities
        )
    return response

def dex_information(data):
    '''
    Realiza um parsing em um dicionário de dados
    pokémon traduzindo para uma string de informações
    gerais sobre o monstrinho.

    param : data : <dict>  dicionário de dados pokémon
    return : <str>
    '''
    if not data:
        # dex_response = 'Pokémon não registrado na PokeDex!'
        dex_response = None

    else:
        # monta uma resposta com os dados do pokémon
        name = data.get('name')
        dex_num = data.get('id')
        picture = data['sprites'].get('front_default')
        height = data.get('height')
        weight = data.get('weight')
        types = ', '.join(t['type']['name'] for t in data.get('types'))

        # monta um dicionário de stats a partir dos dados da requisição
        stats = [{i['stat']['name']:i['base_stat']} for i in data.get('stats')]

        # monta uma string contendo os stats a partir do dicionário
        stats = '\n'.join(
            '{} :{}'.format(k,v) for i in stats for (k, v) in i.items()
        )

        # define as efetividades do pokémon
        effectiveness = parse_effectiveness(get_pokemon_effectiveness(dex_num))

        # monta a string de resposta
        response = 'Name: {}\nPokedex: {}\nType: {}\nHeight: {} Weight: {}\n'.format(
            name.capitalize(), dex_num, types, height, weight    
        )
        response += '\nBase Stats:\n{} \n'.format(stats)

        dex_response = picture + ' \n' +response + effectiveness
        
    return dex_response

def item_information(data):
    '''
    Realiza a leitura de um dicionário de items, traduzindo
    para uma string contendo as informações do item.

    param : data : <dict> : Dados do item.

    return : <str>
    '''
    if not data:
        item_response = 'Item desconhecido.'

    else:
        name = data.get('name')
        picture = data['sprites'].get('default')
        effect = data['effect_entries'][0].get('effect')
        category = data['category'].get('name')
        fling_power = data.get('fling_power')
        fling_effect = data.get('fling_effect')
        if fling_effect:
            fling_effect = fling_effect['name']

        # monta a string de resposta
        item_response = '{}\nName: {}\nEffect: \n{}\n\nCategory: {}\n'.format(
            picture, name.capitalize(), effect, category.capitalize()
        )
        item_response += 'Fling effect: {}\nFling Power: {}\n'.format(
            fling_effect, fling_power
        )

    return item_response

def ability_information(data):
    '''
    Realiza a leitura de um dicionário de dados
    contendo informações sobre uma habildiade.

    param : data : <dict> : Dados da habilidade
    return : <str>
    '''
    if not data:
        ability_response = 'Habilidade desconhecida.'

    else:
        name = data.get('name')
        effect = data['effect_entries'][0].get('effect')
        pokemon = ', '.join(
            i['pokemon'].get('name').capitalize() for i in data.get('pokemon')
        )

        ability_response = '\nName: {}\nEffect: {}\n\n'.format(
            name.capitalize(), effect
        )
        ability_response += 'Ability found in the following Pokémon:\n{}'.format(
            pokemon
        )

    return ability_response
