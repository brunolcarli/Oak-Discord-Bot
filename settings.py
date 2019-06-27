'''
Módulo para configurações
'''
from decouple import config


TOKEN = config('TOKEN')

POKE_API_URL = 'https://pokeapi.co/api/v2/pokemon/'
ITEM_API_URL = 'https://pokeapi.co/api/v2/item/'
ABILITY_API_URL = 'https://pokeapi.co/api/v2/ability/'
EFFECTIVENESS_API_URL = 'https://raw.githubusercontent.com/pokeweak/pokeweak.github.io/master/pokemon.json'

LISA_URL = config('LISA')
