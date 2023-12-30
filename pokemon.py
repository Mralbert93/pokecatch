import json
import requests
import random
    
def get_all_pokemon():
    response = requests.get('https://pokeapi.co/api/v2/pokemon-species/')
    all_pokemon = response.json()
    return all_pokemon

def load_all_pokemon():
    with open('pokemon.json', 'r') as json_file:
        return json.load(json_file)

def get_random_pokemon(all_pokemon):
    total_pokemon = all_pokemon['count']

    random_pokemon_id = random.randint(1, total_pokemon)

    pokemon_url = f'https://pokeapi.co/api/v2/pokemon/{random_pokemon_id}/' 
    pokemon_response = requests.get(pokemon_url)
    pokemon_data = pokemon_response.json()

    return pokemon_data
