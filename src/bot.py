from src.bot.libs.events import *
from dotenv import load_dotenv

load_dotenv()

TARGET_GUILD_ID = ""
USER_ID = ""
BOT_TOKEN = os.getenv("API_KEY")
LOG_FILE = ""

bot.run(
    BOT_TOKEN
)

