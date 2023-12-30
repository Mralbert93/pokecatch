from datetime import datetime
from embeds import get_found_embed, get_attempt_embed, get_run_embed, get_regions_embed, get_region_selected_embed
from interactions import Client, Intents, listen, slash_command, SlashContext, OptionType, slash_option, ActionRow, Button, ButtonStyle, Guild, Embed, File
from interactions.api.events import Component, Startup, MessageCreate
from interactions.ext.paginators import Paginator
import json
from level import calculate_level
import os
from pokemon import get_all_pokemon, load_all_pokemon, get_random_pokemon
from pymongo.mongo_client import MongoClient
import random
from regions import get_all_regions, assign_levels_to_regions, get_available_regions
from throw import attempt


database_url = os.environ.get("DATABASE_URL")
token= os.environ.get("DISCORD_TOKEN")

mongo = MongoClient(database_url)
bot = Client(intents=Intents.DEFAULT)

db = mongo.pokecatch
encounters = db["encounters"]
pokedex = db["pokemon"]
users = db["users"]

all_pokemon = {}
pokemon_channels = {}
regions = {'kanto': 0, 'johto': 5, 'hoenn': 10, 'sinnoh': 15, 'unova': 20, 'kalos': 25, 'alola': 30, 'galar': 35, 'paldea': 40}

def get_encounter_by_post_id(post_id):
    return encounters.find_one({"post": post_id})

def get_pokemon_by_id(pokemon_id):
    return pokedex.find_one({"pokemon_id": pokemon_id})

async def get_level(ctx):
    user_data = users.find_one({"user_id": ctx.user.id})

    user_pokemon = user_data.get('pokemon',[])
    grouped_pokemon = [user_pokemon[i:i + 1] for i in range(0, len(user_pokemon), 1)]

    total_unique_pokemon_caught = len(user_pokemon)
    total_pokemon_caught = sum(pokemon['count'] for pokemon in user_pokemon)
    total_balls_thrown = user_data.get('thrown')
    accuracy = "{:.2f}%".format(float(total_pokemon_caught) / float(total_balls_thrown) * 100)

    level, total_score = calculate_level(total_balls_thrown, total_pokemon_caught, total_unique_pokemon_caught)

    return user_data, total_balls_thrown, total_pokemon_caught, total_unique_pokemon_caught, level, total_score, accuracy, grouped_pokemon

async def get_region(user_id):
    return users.find_one({"user_id": user_id})['region'].capitalize()

async def set_region(user_id, region):
    users.update_one(
        {"user_id": user_id},
        {"$set": {"region": str(region)}}
    )

async def select_region(ctx, region):
    user_data, total_balls_thrown, total_pokemon_caught, total_unique_pokemon_caught, level, total_score, accuracy, grouped_pokemon = await get_level(ctx)

    current_region = await get_region(ctx.user.id)
    available_regions = get_available_regions(level, regions)

    if region in available_regions:
        await set_region(ctx.user.id, region)
        embed = await get_region_selected_embed(ctx, region)
        await ctx.edit_origin(embed=embed, components=[])
    else:
        await ctx.send(f"{ctx.user.mention}, sorry this region is not available based on your level.", ephemeral=True)

async def create_encounter(guild):
    random_pokemon = get_random_pokemon(all_pokemon)

    pokemon_id = random_pokemon['id']
    pokemon_name = str(random_pokemon['name']).capitalize()
    pokemon_image = random_pokemon['sprites']['front_default']

    embed, buttons = await get_found_embed(pokemon_name, pokemon_image)

    channel = pokemon_channels[guild]
    post = await channel.send(embed=embed, components=[buttons])
    
    encounters.insert_one(
        {"post": post.id, "pokemon_id": pokemon_id}
    )

    pokedex.update_one(
        {"pokemon_id": pokemon_id},
        {"$push": {"name": pokemon_name,"image": pokemon_image}},
        upsert=True
    )

@slash_command(
    name = "region",
    description = "Choose your region"
)
async def region(ctx: SlashContext): 
    try:
        user_data, total_balls_thrown, total_pokemon_caught, total_unique_pokemon_caught, level, total_score, accuracy, grouped_pokemon = await get_level(ctx)
    except Exception as e:
        await ctx.send(f"{ctx.user.mention}, you cannot switch regions until Level 5. Go catch some Pokemon!", ephemeral=True)
        return
    current_region = await get_region(ctx.user.id)
    embed, action_rows = await get_regions_embed(ctx, regions, level, current_region)
    await ctx.send(embed=embed, components=action_rows, ephemeral=True)

@slash_command(
    name = "user",
    description = "Show your Pokemon"
)
async def user(ctx: SlashContext):
    try:
        user_data, total_balls_thrown, total_pokemon_caught, total_unique_pokemon_caught, level, total_score, accuracy, grouped_pokemon = await get_level(ctx)
    except Exception as e:
        await ctx.send(f"{ctx.user.mention}, no data to display. You haven't caught any pokemon. Get out there and start catching!", ephemeral=True)
        return
    
    embeds = []
    
    embed = Embed(title="Your Pokemon - Summary", color="#FF0000")
    embed.add_field(name=f"Level {level}", value=f"{total_score} EXP", inline=True)
    embed.add_field(name="Caught", value=str(total_pokemon_caught) + " Pokemon", inline=True)
    embed.add_field(name="Uniques", value=str(total_unique_pokemon_caught) + " Pokemon", inline=True)
    embed.add_field(name="Thrown", value=str(total_balls_thrown) + " Pokeballs", inline=True)
    embed.add_field(name="Throw Accuracy", value=accuracy, inline=True)
    embed.set_thumbnail(url=ctx.user.avatar_url)
    embeds.append(embed)

    for i, group in enumerate(grouped_pokemon):
        embed = Embed(title=f"Your Pokemon - Page {i + 1}", color="#FF0000")

        for pokemon in group:
            pokemon_id = pokemon.get('pokemon_id')
            count = pokemon.get('count')
            first_encountered = pokemon.get('first_encountered')

            result = get_pokemon_by_id(pokemon_id)
            pokemon_name = result['name'][0]
            pokemon_image = result['image'][0]

            embed.add_field(
                name=f"ID: {pokemon_id}",
                value=f"**Name**: {pokemon_name}\n**Caught:** {count}x\n**First Caught:** {first_encountered.strftime('%m-%d-%Y %H:%M')}",
                inline=False
            )
            embed.set_image(url=pokemon_image)

        embeds.append(embed)

    paginator = Paginator.create_from_embeds(bot, *embeds)
    await paginator.send(ctx)

@listen(Component)
async def on_component(event: Component):
    ctx = event.ctx

    match ctx.custom_id:
        case "catch":
            encounter = get_encounter_by_post_id(ctx.message_id)
            
            pokemon_id = encounter['pokemon_id']
            pokemon_data = get_pokemon_by_id(pokemon_id)

            caught, escaped = await attempt()
            
            embed, buttons = await get_attempt_embed(ctx, pokemon_data, caught, escaped)

            current_date = datetime.utcnow()

            if caught:
                data = users.find_one({"user_id": ctx.user.id, "pokemon.pokemon_id": pokemon_id})
                if data is None:
                    users.update_one(
                        {"user_id": ctx.user.id},
                        {"$push": {"pokemon": {"pokemon_id": pokemon_id, "count": 1, "first_encountered": current_date}},"$set": {"region": "kanto"}, "$inc": {"thrown": 1}},
                        upsert=True
                    )
                    encounters.delete_one(
                        {"post": ctx.message_id}
                    )
                else:
                    users.update_one(
                        {"user_id": ctx.user.id, "pokemon.pokemon_id": pokemon_id},
                        {"$inc": {"pokemon.$.count": 1},"$inc": {"thrown": 1}}
                    )
                    encounters.delete_one(
                        {"post": ctx.message_id}
                    )
            if escaped:
                encounters.delete_one(
                        {"post": ctx.message_id}
                    )
                users.update_one(
                        {"user_id": ctx.user.id},
                        {"$inc": {"thrown": 1}}
                    )
            
            await ctx.edit_origin(embed=embed, components=buttons)

        case "run":
            encounter = get_encounter_by_post_id(ctx.message_id)
            
            pokemon_id = encounter['pokemon_id']
            pokemon_data = get_pokemon_by_id(pokemon_id)

            embed, buttons = await get_run_embed(ctx, pokemon_data)
            await ctx.edit_origin(embed=embed, components=buttons)

        case "kanto":
            await select_region(ctx, "kanto")
        case "johto":
            await select_region(ctx, "johto")
        case "hoenn":
            await select_region(ctx, "hoenn")
        case "sinnoh":
            await select_region(ctx, "sinnoh")
        case "unova":
            await select_region(ctx, "unova")
        case "kalos":
            await select_region(ctx, "kalos")
        case "alola":
            await select_region(ctx, "alola")
        case "galar":
            await select_region(ctx, "galar")
        case "paldea":
            await select_region(ctx, "paldea")

@listen(MessageCreate)
async def on_message_create(event: MessageCreate):
    if event.message.author.bot:
        return
    random_number = random.randint(0, 5)
    if random_number == 1:
        await create_encounter(event.message.guild.id)

@listen(Startup)
async def startup_func():
    print(f"We have logged in as {bot.user}")

    for guild in bot.guilds:
        channels = await guild.fetch_channels()
        for channel in channels:
            if channel.name == "pokemon":
                pokemon_channels[guild.id] = channel
                break

    global all_pokemon
    global regions

    # all_pokemon = pokemon.get_all_pokemon()
    
    # with open('pokemon.json', 'w') as json_file:
    #     json.dump(all_pokemon, json_file)

    all_pokemon = load_all_pokemon()

bot.start(token)
