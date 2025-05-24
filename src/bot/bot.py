import asyncio
import discord
import datetime
import os
import json
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)
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