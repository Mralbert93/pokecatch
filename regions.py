import requests

def get_all_regions():
    regions_url = 'https://pokeapi.co/api/v2/region/'
    regions_response = requests.get(regions_url)

    regions_data = regions_response.json()
    return [region['name'] for region in regions_data['results']]

def assign_levels_to_regions(regions):
    levels = [index * 5 for index in range(len(regions))]
    
    region_levels = dict(zip(regions, levels))

    return region_levels

def get_available_regions(user_level, regions):
    available_regions = [region for region, level in regions.items() if level <= user_level]
    return available_regions
