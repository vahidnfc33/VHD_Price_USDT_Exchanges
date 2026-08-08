import os
import asyncio
import sys
import traceback

sys.path.insert(0, os.path.dirname(__file__))
from price import build_message
from telegram import Bot
from telegram.error import TelegramError

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ.get("CHAT_ID", "@usdtyab")


async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
        me = await bot.get_me()
        print(f"[👤 Bot: @{me.username} | ID: {me.id}]")
    except TelegramError as e:
        print(f"[❌ Invalid token or bot blocked: {e}]")
        return

    try:
        message = await asyncio.to_thread(build_message)
        print(f"[📝 Message length: {len(message)} chars]")
        msg = await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        print(f"[✅ Sent! Message ID: {msg.message_id}]")
    except TelegramError as e:
        print(f"[❌ Send failed: {e}]")
        print(f"[🔄 Retrying without HTML parse_mode...]")
        try:
            msg = await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                disable_web_page_preview=True,
            )
            print(f"[✅ Sent as plain text! Message ID: {msg.message_id}]")
        except TelegramError as e2:
            print(f"[❌ Plain text also failed: {e2}]")
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
