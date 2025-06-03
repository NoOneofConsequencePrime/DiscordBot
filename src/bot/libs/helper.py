import discord
import asyncio
import gtts
import uuid
import os
import time
import queue as thread_queue
from discord.ext import commands

queue = thread_queue.Queue()

#write these into a file to make the bot restart-proof
pending_role_setup = {}
monitored_roles = {}

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
# intents.members = True
intents.guild_messages = True
bot = commands.Bot(command_prefix="!", intents=intents)


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

def clear_queue():
    while not queue.empty():
        try:
            queue.get_nowait()
            queue.task_done()
        except Exception:
            break

def try_remove(file_path, retries=3, delay=1):
    for _ in range(retries):
        try:
            os.remove(file_path)
            return
        except PermissionError:
            time.sleep(delay)

def queue_run():
    while True:
        ctx, tts_input = queue.get()
        if ctx.voice_client:
            filename = f"tts_{uuid.uuid4().hex}.mp3"
            filename = "temp_files/" + filename
            generate_tts(tts_input, filename)

            def after_playing(error):
                try:
                    try_remove(filename)
                    print("Temporary TTS file deleted.")
                except Exception as e:
                    print(f"Error deleting file: {e}")
                if error:
                    print(f"Error during playback: {error}")

            BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # This will point to libs/
            FFMPEG_PATH = os.path.join(BASE_DIR, "dependencies", "ffmpeg", "bin", "ffmpeg.exe")
            audio = discord.FFmpegPCMAudio(filename, executable=FFMPEG_PATH, options="-filter:a 'atempo=1.4'")
            ctx.voice_client.play(audio, after=after_playing)
            while ctx.voice_client.is_playing():
                time.sleep(1)
        queue.task_done()