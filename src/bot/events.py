from commands import *

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)

    if voice_client and len(voice_client.channel.members) == 1:
        await voice_client.disconnect()
        print(f"Disconnected from {voice_client.channel} due to inactivity.")

@bot.event
async def on_guild_join(guild):
    owner = guild.owner
    if owner:
        pending_role_setup[owner.id] = guild.id
        try:
            await owner.send(f"Hello! Thanks for adding me to **{guild.name}**.\n" 
                             "On top of this role, anyone with administrator or manage server permissions can still access me. \n"
                             "Please mention the role I should monitor (e.g., @Admin):")
        except discord.Forbidden:
            if guild.system_channel:
                await guild.system_channel.send(f"{owner.mention}, please mention the role I should monitor (e.g., @Admin): \n"
                                                "On top of this role, anyone with administrator or manage server permissions can still access me. \n")
    else:
        return

@bot.event
async def on_message(message):
    if not (message.author == bot.user):
        if message.author.id in pending_role_setup:
            guild_id = pending_role_setup[message.author.id]
            guild = bot.get_guild(guild_id)
            if guild is None:
                return

            role_name = message.content.strip().lstrip("@")
            role = discord.utils.find(lambda r: r.name == role_name, guild.roles)

            if role:
                monitored_roles[guild.id] = role.id
                await message.channel.send(f"Great! I'll monitor the **{role.name}** role.")
                del pending_role_setup[message.author.id]
            else:
                await message.channel.send(
                    f"Sorry, I couldn't find a role named '{role_name}'. Make sure you typed it exactly.")

    await bot.process_commands(message)


@bot.hybrid_command(description="Check bot latency.")
async def ping(ctx):
    await ctx.send("Pong!")
    await ctx.send(monitored_roles)

@bot.command()
async def sync(ctx):
    if ctx.author.id == 649782084847665195:
        await bot.tree.sync()
        await bot.tree.sync(guild = ctx.guild)
        await ctx.send("Commands synced!")
    else:
        await ctx.send("You do not have permission to use this command.")


@bot.event
async def on_ready():
    pass
    # await bot.close()
