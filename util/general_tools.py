'''
Módulo para ferramentas genéricas.
'''
import difflib

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
