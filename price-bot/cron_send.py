import os
import asyncio
import sys

sys.path.insert(0, os.path.dirname(__file__))
from price import build_message
from telegram import Bot

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ.get("CHAT_ID", "@usdtyab")


async def main():
    bot = Bot(token=BOT_TOKEN)
    message = await asyncio.to_thread(build_message)
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML", disable_web_page_preview=True)
    print("[✅ Sent]")


if __name__ == "__main__":
    asyncio.run(main())
