"""
Módulo para configurações
"""
from decouple import config

TOKEN = config('TOKEN')
ADMIN_CHANNEL = config('ADMIN_CHANNEL')

POKE_API_URL = 'https://pokeapi.co/api/v2/pokemon/'
ITEM_API_URL = 'https://pokeapi.co/api/v2/item/'
ABILITY_API_URL = 'https://pokeapi.co/api/v2/ability/'
EFFECTIVENESS_API_URL = 'https://raw.githubusercontent.com/pokeweak/pokeweak.github.io/master/pokemon.json'

LISA_URL = config('LISA')
RANKED_SPREADSHEET_ID = '1E2cQBWeQc9JkCKv3BUPClGwulPXXg-4hTYotuUKmoJI'
SCORE_INDEX = 4
SD_NAME_INDEX = 1
COLOR_INDEX = 1
ELO_IMG_INDEX = 2

__version__ = '0.0.1'
