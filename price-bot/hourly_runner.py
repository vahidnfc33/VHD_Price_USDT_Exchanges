import os
import asyncio
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from price import build_message
from telegram import Bot
from telegram.error import TelegramError

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ.get("CHAT_ID", "@usdtyab")
DURATION = 3300  # 55 minutes in seconds
INTERVAL = 300   # 5 minutes


async def send_once(bot):
    for attempt in range(3):
        try:
            message = await asyncio.to_thread(build_message)
            if message.startswith("❌"):
                print(f"[⚠ Attempt {attempt+1}/3: fetch failed, retrying...]")
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
            print(f"[❌ Error: {e}]")
            try:
                msg = await bot.send_message(
                    chat_id=CHAT_ID,
                    text=message,
                    disable_web_page_preview=True,
                )
                print(f"[✅ Sent plain! Message ID: {msg.message_id}]")
                return True
            except TelegramError as e2:
                print(f"[❌ Plain failed: {e2}]")
        await asyncio.sleep(5)
    return False


async def main():
    bot = Bot(token=BOT_TOKEN)
    try:
        me = await bot.get_me()
        print(f"[👤 Bot: @{me.username}]")
    except TelegramError as e:
        print(f"[❌ Invalid token: {e}]")
        return

    start = time.time()
    count = 0
    while time.time() - start < DURATION:
        loop_start = time.time()
        ok = await send_once(bot)
        if ok:
            count += 1
        elapsed = time.time() - loop_start
        wait = max(0, INTERVAL - elapsed)
        print(f"[⏳ Sent {count} so far. Waiting {wait:.0f}s...]")
        await asyncio.sleep(wait)

    print(f"[🏁 Done. {count} messages sent in this batch.]")


if __name__ == "__main__":
    asyncio.run(main())
