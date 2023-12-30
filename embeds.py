from interactions import Client, Intents, listen, slash_command, SlashContext, OptionType, slash_option, ActionRow, Button, ButtonStyle, Guild, Embed, File

async def get_found_embed(pokemon_name, pokemon_image):
    embed = Embed(title="Pokemon Found", description=f"A wild **{pokemon_name}** has been found!\n\nWould you like to try to catch it?", color="#FF0000")
    embed.set_image(url=pokemon_image)

    catch_button = Button(label="Catch", custom_id="catch", style=ButtonStyle.GREEN)
    run_button = Button(label="Run", custom_id="run", style=ButtonStyle.DANGER)

    buttons = [catch_button, run_button]
    
    return embed, buttons

async def get_attempt_embed(ctx, pokemon_data, caught, escaped):
    pokemon_name = pokemon_data['name'][0]
    pokemon_image = pokemon_data['image'][0]

    if caught:
        embed = Embed(title="Pokemon Caught", description=f"{ctx.user.mention} has successfully caught **{pokemon_name}**!", color="#FF0000")
        embed.set_image(url=pokemon_image)
        buttons = []
    elif escaped:
        embed = Embed(title="Pokemon Escaped", description=f"Oh no! {ctx.user.mention} tried to catch **{pokemon_name}** and it escaped!", color="#FF0000")
        embed.set_image(url="https://media.tenor.com/w31RJzlRkowAAAAM/pokemon-go-run.gif")
        buttons = []
    else:
        embed = Embed(title="Catch Failed", description=f"{ctx.user.mention} attempted to catch **{pokemon_name}** and failed.\n\nWould you like to try again?", color="#FF0000")
        embed.set_image(url=pokemon_image)
        
        catch_button = Button(label="Catch", custom_id="catch", style=ButtonStyle.GREEN)
        run_button = Button(label="Run", custom_id="run", style=ButtonStyle.DANGER)
        buttons = [catch_button, run_button]
    
    return embed, buttons

async def get_run_embed(ctx, pokemon_data):
    pokemon_name = pokemon_data['name'][0]
    pokemon_image = pokemon_data['image'][0]

    embed = Embed(title="Run Away", description=f"{ctx.user.mention} has chosen to run away from **{pokemon_name}**.", color="#FF0000")
    embed.set_image(url=pokemon_image)

    buttons = []

    return embed, buttons

async def get_regions_embed(ctx, regions, user_level, current_region):
    embed = Embed(title="Region Selection", description=f"Your current region is **{current_region}**.\nYour level is **{user_level}**.\n\nPlease choose any region available for your level.\n\n{ctx.user.mention}", color="#FF0000")
    embed.set_thumbnail(url=ctx.user.avatar_url)

    async def render_region(region):
        if region == "kanto":
            return "Kanto\u00A0\u00A0\u00A0"
        if region == "alola":
            return "Alola\u00A0\u00A0"
        if region == "johto":
            return "Johto\u00A0\u00A0\u00A0\u00A0"
        if region == "kalos":
            return "Kalos\u00A0\u00A0\u00A0"
        if region == "galar":
            return "Galar\u00A0\u00A0"
        if region == "hoenn":
            return "Hoenn\u00A0"
        else:
            return region.capitalize()
    
    buttons = [
        Button(
            style=ButtonStyle.GREEN if user_level >= level else ButtonStyle.RED,
            label=f"{await render_region(region)} (Lvl {level})",
            custom_id=region
        )
        for region, level in regions.items()
    ]

    action_rows = [ActionRow(*buttons[i:i + 3]) for i in range(0, len(buttons), 3)]

    return embed, action_rows

async def get_region_selected_embed(ctx, region):
    embed = Embed(title="Region Selected", description=f"You have selected **{region.capitalize()}** as your region.\n\nYou may switch regions at any time by reusing this command.\n\n{ctx.user.mention}", color="#FF0000")
    embed.set_thumbnail(url=ctx.user.avatar_url)
    return embed
