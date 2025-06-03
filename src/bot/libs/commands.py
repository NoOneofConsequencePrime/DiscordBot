from .helper import *
import threading

@bot.hybrid_command(name="say", description="Say the following text string in voice channel.", help="Say the following text string in voice channel.")
async def speak(ctx, *, args:str):
    if ctx.voice_client:
        if ctx.guild.id in profanity_status:
            if not profanity_check(args):
                queue.put((ctx, args))
            else:
                await ctx.send("Profanity filter detected a bad word. If you believe this is an error, please screenshot and send to the bot developer.")
        else:
            queue.put((ctx, args))
    else:
        await ctx.send("Please use `/join` to have me join a voice channel first.")

@bot.hybrid_command(name="toggle_filter", description="Toggle the profanity filter.", help="Toggle the profanity filter.")
async def toggle(ctx):
    if ctx.guild.id not in profanity_status:
        profanity_status.append(ctx.guild.id)
        await ctx.send("Turned filter on.")
    else:
        profanity_status.remove(ctx.guild.id)
        await ctx.send("Turned filter off.")

    await save_on_exit_async()


@bot.hybrid_command(name="pause", description="Stops the current voice message.", help="Stops the current voice message and clears the voice queue. Any unread !say commands will not be read.")
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        clear_queue()
        for filename in os.listdir("temp_files/"):
            file_path = os.path.join("temp_files/", filename)
            if os.path.isfile(file_path):
                try_remove(file_path)

@bot.hybrid_command(name="join", description="Joins the channel you (invoker of the command) are currently in.", help="Joins the channel you (invoker of the command) are currently in.")
async def vc_connect(ctx):
    if ctx.guild.id in monitored_roles.keys() or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
        check_role = monitored_roles.get(ctx.guild.id)
        if discord.utils.get(ctx.guild.roles, id=check_role) or ctx.author.guild_permissions.manage_guild or ctx.author.guild_permissions.administrator:
            if ctx.author.voice and ctx.author.voice.channel:
                vc = ctx.author.voice.channel
                await vc.connect()
                threading.Thread(target=queue_run, daemon=True).start()
                # await ctx.send("Joined channel!")
            else:
                await ctx.send("Please join a channel first!")
        else:
            await ctx.send("Improper Permissions! Please contact a server admin to setup role permissions")
    else:
        await ctx.send("You do not have the proper permissions for this command, or setup role permissions first!")

@bot.hybrid_command(name="stop", description="Forces the bot to leave the voice channel it is in.", help="Forces the bot to leave the voice channel it is in.")
async def vc_disconnect(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("Please execute this command from inside the voice channel the bot is in.")

@bot.hybrid_command(name="change_role_permissions", description="Changes roles the bot listens to, aside from administrator or manage server permissions.", help="Changes roles the bot listens to, must be used by someone with administrator or manage server permissions. Users with administrator or manage server permissions retain their ability to use the command.")
async def change_perms(ctx):
    if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
        author = ctx.author
        guild = ctx.guild
        if author:
            pending_role_setup[author.id] = guild.id
            try:
                await author.send(f"Hello! Thanks for adding me to **{author.name}**.\n"
                                  "On top of this role, anyone with administrator or manage server permissions can still access me. \n"
                                 "Please mention the role I should monitor (e.g., @Admin):")
            except discord.Forbidden:
                if guild.system_channel:
                    await guild.system_channel.send(
                        f"{author.mention}, please mention the role I should monitor (e.g., @Admin): \n"
                        "On top of this role, anyone with administrator or manage server permissions can still access me. \n")
        else:
            return
    else:
        await ctx.send("You need administrator or manage server permissions to execute this command.")

@bot.hybrid_command(description="Check bot latency. Also for testing purposes.", help="Check bot latency. Also for testing purposes.")
async def ping(ctx):
    await ctx.send("Pong!")
    await ctx.send("My latency is: " + str(bot.latency*1000) + " ms")
    await ctx.send(profanity_status)

@bot.hybrid_command(description="For bot developer use only. Do not Invoke.", help="Syncs the tree across all discord guilds and the guild that the bot is in. The global sync can take up to an hour but the guild sync should only take minutes. Do not use unless your are a developer of the Bot.")
async def sync(ctx):
    if ctx.author.id == 649782084847665195:
        await bot.tree.sync()
        await bot.tree.sync(guild = ctx.guild)
        await ctx.send("Commands synced!")
    else:
        await ctx.send("You do not have permission to use this command.")