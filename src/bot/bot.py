import asyncio
import discord
import datetime
import os
import json
from discord.ext import commands
from discord import VoiceChannel
import gtts
import uuid
import threading
import queue as thread_queue
import time
# import PyNaCl


intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
# intents.members = True
intents.guild_messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

#write these into a file to make the bot restart-proof
pending_role_setup = {}
monitored_roles = {}

TARGET_GUILD_ID = ""
USER_ID = ""
BOT_TOKEN = ""
LOG_FILE = ""

queue = thread_queue.Queue()

async def ratelimit_safe(coro):
    try:
        return await coro
    except discord.HTTPException as e:
        if e.status == 429:
            reset_after = float(e.response.headers.get('x-ratelimit-reset-after', 1))
            print(f"Rate limited. Retrying after {reset_after} seconds.")
            await asyncio.sleep(reset_after)
            return await ratelimit_safe(coro)
        raise


def generate_tts(text:str, filename:str):
    tts = gtts.gTTS(text=text, lang='en')
    tts.save(filename)

def clear_queue(q):
    while not q.empty():
        try:
            q.get_nowait()
            q.task_done()
        except Exception:
            break

def queue_run():
    while True:
        ctx, tts_input = queue.get()
        if ctx.voice_client:
            filename = f"tts_{uuid.uuid4().hex}.mp3"
            generate_tts(tts_input, filename)

            def after_playing(error):
                try:
                    os.remove(filename)
                    print("Temporary TTS file deleted.")
                except Exception as e:
                    print(f"Error deleting file: {e}")
                if error:
                    print(f"Error during playback: {error}")

            audio = discord.FFmpegPCMAudio(filename, executable="../../dependencies/ffmpeg/bin/ffmpeg.exe", options="-filter:a 'atempo=1.4'")
            ctx.voice_client.play(audio, after=after_playing)
            while ctx.voice_client.is_playing():
                time.sleep(1)
        queue.task_done()

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
        clear_queue(queue)

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

bot.run(
    BOT_TOKEN
)

# bot.run(
#     BOT_TOKEN,
#     log_handler=None,
#     log_level=None
# )