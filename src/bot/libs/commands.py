from .helper import *
import threading

@bot.hybrid_command(name="say", description="Say the following text string in voice channel.")
async def speak(ctx, *, args:str):
    if ctx.voice_client:
        queue.put((ctx, args))
    else:
        await ctx.send("Please use `/join` to have me join a voice channel first.")

@bot.hybrid_command(name="pause", description="Stops the current voice message")
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        clear_queue()
        for filename in os.listdir("temp_files/"):
            file_path = os.path.join("temp_files/", filename)
            if os.path.isfile(file_path):
                try_remove(file_path)

@bot.hybrid_command(name="join", description="Joins the channel you (invoker of the command) are currently in.")
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

@bot.hybrid_command(name="stop", description="Forces the bot to leave the voice channel it is in.")
async def vc_disconnect(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        ctx.send("Please execute this command from inside the voice channel the bot is in.")

@bot.hybrid_command(name="change_role_permissions", description="Changes roles the bot listens to, aside from administrator or manage server permissions.")
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
