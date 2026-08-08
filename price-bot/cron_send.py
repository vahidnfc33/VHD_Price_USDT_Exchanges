import os
import asyncio
import sys
import traceback

sys.path.insert(0, os.path.dirname(__file__))
from price import build_message, fetch_prices
from telegram import Bot
from telegram.error import TelegramError

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ.get("CHAT_ID", "@usdtyab")


async def send_price(bot):
    for attempt in range(3):
        try:
            message = await asyncio.to_thread(build_message)
            if message.startswith("❌"):
                print(f"[⚠ Attempt {attempt+1}/3: fetch returned error, retrying...]")
                await asyncio.sleep(5)
                continue
            msg = await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            print(f"[✅ Sent! Message ID: {msg.message_id}]")
            return True
        except TelegramError as e:
            print(f"[❌ Telegram error: {e}]")
            try:
                msg = await bot.send_message(
                    chat_id=CHAT_ID,
                    text=message,
                    disable_web_page_preview=True,
                )
                print(f"[✅ Sent as plain text! Message ID: {msg.message_id}]")
                return True
            except TelegramError as e2:
                print(f"[❌ Plain text also failed: {e2}]")
                traceback.print_exc()
        await asyncio.sleep(5)
    return False


async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
        me = await bot.get_me()
        print(f"[👤 Bot: @{me.username} | ID: {me.id}]")
    except TelegramError as e:
        print(f"[❌ Invalid token or bot blocked: {e}]")
        return

    await send_price(bot)


if __name__ == "__main__":
    asyncio.run(main())
