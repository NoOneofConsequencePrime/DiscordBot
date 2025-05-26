import asyncio
import discord
import datetime
import os
import json
from discord.ext import commands
from discord.types.channel import VoiceChannel

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

#write these into a file to make the bot restart-proof
pending_role_setup = {}
monitored_roles = {}

TARGET_GUILD_ID = ""
USER_ID = ""
BOT_TOKEN = ""
LOG_FILE = ""

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


@bot.command(name="join", help="Joins the channel you (invoker of the command) are currently in.")
async def vc_connect(ctx):
    if ctx.guild.id in monitored_roles.keys() or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
        check_role = monitored_roles[ctx.guild.id]
        if check_role in ctx.author.roles or ctx.author.guild_permissions.manage_guild or ctx.author.guild_permissions.administrator:
            if ctx.author.voice.channel:
                vc = ctx.author.voice.channel
                await vc.connect()
                await ctx.send("Joined channel!")
            else:
                await ctx.send("Please join a channel first!")
        else:
            await ctx.send("Improper Permissions! Please contact a server admin to setup role permissions")
    else:
        await ctx.send("Please setup role permissions first!")


@bot.command(name="change_role_permissions", help="Changes what roles the bot listens to, aside from those with administrator permissions or manage server permissions.")
async def change_perms(ctx):
    if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
        author = ctx.author
        guild = ctx.guild
        if author:
            pending_role_setup[author.id] = guild.id
            try:
                await author.send(f"Hello! Thanks for adding me to **{author.name}**.\n"
                                 "Please mention the role I should monitor (e.g., @Admin):")
            except discord.Forbidden:
                if guild.system_channels:
                    await guild.system_channel.send(
                        f"{author.mention}, please mention the role I should monitor (e.g., @Admin):")
        else:
            return
    else:
        await ctx.send("You need administrator or manage server permissions to execute this command.")


@bot.event
async def on_guild_join(guild):
    owner = guild.owner
    if owner:
        pending_role_setup[owner.id] = guild.id
        try:
            await owner.send(f"Hello! Thanks for adding me to **{guild.name}**.\n"
                             "Please mention the role I should monitor (e.g., @Admin):")
        except discord.Forbidden:
            if guild.system_channels:
                await guild.system_channel.send(f"{owner.mention}, please mention the role I should monitor (e.g., @Admin):")
    else:
        return

@bot.event
async def on_message(message):
    if not (message.author == bot.user):
        if message.guild is None and message.author.id in pending_role_setup:
            guild_id = pending_role_setup[message.author.id]
            guild = bot.get_guild(guild_id)
            if guild is None:
                return
        if message.role_mentions:
            role = message.role_mentions[0]
            monitored_roles[guild.id] = role.id
            await message.channel.send(f"Great! I'll monitor the **{role.name}** role.")
            del pending_role_setup[message.author.id]

@bot.event
async def on_ready():
        
    await bot.close()

bot.run(
    BOT_TOKEN
)

# bot.run(
#     BOT_TOKEN,
#     log_handler=None,
#     log_level=None
# )