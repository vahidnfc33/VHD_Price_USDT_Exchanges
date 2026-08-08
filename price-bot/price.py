import asyncio
import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import re

ALLOWED_CHANNELS = ['@usdtyab']
ALLOWED_ADMINS = []

referral_links = {
    "آبان تتر": "https://abantether.com/register?code=wwHr",
    "اترکس": "https://app.eterex.com/register?ref=170695",
    "ارز پلاس": "https://panel.arzplus.net/auth/register?rewards=babydoge&referral=296139",
    "افکس": "https://efex.pro/fa/sign-up?ref=392773045109",
    "اکسکوینو": "https://excoino.com/panel/auth/register?referral_code=945206",
    "او ام پی فینکس": "https://omp.exchange/referral/ET5AJYDV2",
    "بیت ایمن": "https://trade.bitimen.com/signup?ref_code=990257",
    "تاپ ارز": "https://my.topchnge.net/",
    "تبدیل": "https://tabdeal.org/auth/register-req?ref=1fifw0",
    "تترلند": "https://tetherland.com/register?ref=XGX0YG",
    "رمزینکس": "https://ramzinex.com/app/login?ref-code=570617",
    "سرمایکس": "https://sarmayex.com/authentication/init?reagent_code=1135330034",
    "صرافکس": "https://sarrafex.com/account/signup?referral=lppp9",
    "کوین کده": "https://coinkade.com/?ref=28082",
    "ملّی چنج": "https://mellichange.com/account/ref/MC4X7LGcoH2j/",
    "نوبیتکس": "https://nobitex.ir/signup/?refcode=13108",
    "ایرانیکارت": "https://panel.iranicard.ir/register?referralCode=29936688",
    "بیت پین": "https://bitpin.ir/signup/?refcode=uepd2bmvjo",
    "والکس": "https://wallex.ir/signup?ref=RKna",
}

MAIN_EXCHANGES = [
    "آبان تتر",
    "نوبیتکس",
    "والکس",
    "تترلند",
    "بیت پین",
    "ایرانیکارت",
]


def is_authorized_chat(chat_id, chat_username=None):
    if chat_username:
        return f"@{chat_username}" in ALLOWED_CHANNELS
    return False

def is_authorized_user(user_id):
    return user_id in ALLOWED_ADMINS if ALLOWED_ADMINS else False

async def check_authorization(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type in ['channel', 'supergroup']:
        if is_authorized_chat(chat.id, chat.username):
            return True
        else:
            await update.message.reply_text("❌ این بات فقط در کانال @usdtyab فعال است.")
            return False
    elif chat.type == 'private':
        if is_authorized_user(user.id):
            return True
        else:
            await update.message.reply_text("❌ شما مجاز به استفاده از این بات نیستید.")
            return False

    await update.message.reply_text("❌ این بات فقط در کانال @usdtyab فعال است.")
    return False

def fa_to_en(text):
    fa_digits = '۰۱۲۳۴۵۶۷۸۹'
    en_digits = '0123456789'
    return text.translate(str.maketrans(fa_digits, en_digits))

farsi_order = " آابپتثجچحخدذرزسشصضطظعغفقکگلمنوهی"
def farsi_sort_key(text):
    return [farsi_order.index(ch) if ch in farsi_order else ord(ch) for ch in text.strip()]

def fetch_prices():
    url = "https://mihanblockchain.com/cryptocurrency-prices/tether/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table")
        header_cells = [th.text.strip() for th in table.find("thead").find_all("th")]
        data = []
        seen_names = set()
        for row in table.find("tbody").find_all("tr"):
            values = [td.text.strip() for td in row.find_all("td")]
            entry = dict(zip(header_cells, values))
            name = entry.get('صرافی', '')

            if not name:
                continue

            excluded = ["فرهاد اکسچنج", "جیبیتکس", "ملّی چنج", "ملی چنج", "اکسکوینو", "ارزینجا", "کوین کده"]
            if any(ex in name for ex in excluded):
                continue

            if name in seen_names:
                continue
            seen_names.add(name)

            data.append(entry)
        return sorted(data, key=lambda x: farsi_sort_key(x.get('صرافی', '')))
    except Exception as e:
        print(f"[خطا در دریافت قیمت‌ها]: {e}")
        return []


def linkify(name):
    for ref_name, link in referral_links.items():
        if name.startswith(ref_name):
            suffix = name[len(ref_name):].strip()
            if suffix:
                suffix = f" ({suffix})"
            return f'<a href="{link}"><b>{ref_name}</b></a>{suffix}'
    return name

def extract_name_suffix(full_name):
    for ref_name in referral_links:
        if full_name.startswith(ref_name):
            suffix = full_name[len(ref_name):].strip()
            if suffix:
                return f"{ref_name} ({suffix})"
            return ref_name
    return full_name

def is_main_exchange(name):
    return any(name.startswith(m) for m in MAIN_EXCHANGES)


def build_message():
    prices = fetch_prices()
    prices = sorted(prices, key=lambda x: farsi_sort_key(x.get('صرافی', '')))

    if not prices:
        return "❌ خطا در دریافت قیمت‌ها از سایت."

    message = (
        "💵 <b>جدیدترین قیمت تتر (USDT):</b>\n"
        "🔄 <i>بروزرسانی هر ۵ دقیقه</i>\n\n"
    )

    valid_prices = []
    main_block = ""
    other_block = ""

    for p in prices:
        name = p.get('صرافی', '❓').strip()
        name_linked = linkify(name)

        price_str = "❌"
        price_val = None

        price_raw = fa_to_en(p.get('قیمت', '').replace("تومان", "").replace(",", "").strip())

        try:
            price_val = float(price_raw)
            price_str = f"{int(price_val):,}"
            valid_prices.append((name, price_val))
        except:
            pass

        entry_text = f"🔰 {name_linked}\n💰 قیمت: {price_str}\n\n"

        if is_main_exchange(name):
            main_block += entry_text
        else:
            other_block += entry_text

    message += main_block

    if other_block:
        message += (
            "<blockquote expandable>"
            "📋 <b>سایر صرافی‌ها</b>\n\n"
            f"{other_block.strip()}"
            "</blockquote>\n\n"
        )

    message += "━━━━━━━━━━━━━━━\n"

    if valid_prices:
        best_buy = min(valid_prices, key=lambda x: x[1])
        best_sell = max(valid_prices, key=lambda x: x[1])
        message += (
            f"<blockquote>🟢 بهترین قیمت برای خرید:\n"
            f"<b>{int(best_buy[1]):,}</b> از <b>{extract_name_suffix(best_buy[0])}</b>\n\n"
            f"🔴 بهترین قیمت برای فروش:\n"
            f"<b>{int(best_sell[1]):,}</b> از <b>{extract_name_suffix(best_sell[0])}</b></blockquote>\n"
        )


    message += "\n📌 <i>منبع: میهن بلاکچین .</i>"

    return message.strip()


async def usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update, context):
        return
    message = await asyncio.to_thread(build_message)
    await update.message.reply_text(message, parse_mode="HTML", disable_web_page_preview=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update, context):
        return
    await update.message.reply_text(
        "🤖 سلام! این بات فقط در کانال @usdtyab فعال است.\n"
        "برای دریافت قیمت تتر از دستور /usdt استفاده کنید."
    )

async def auto_send(bot: Bot):
    while True:
        try:
            message = await asyncio.to_thread(build_message)
            await bot.send_message(chat_id='@usdtyab', text=message, parse_mode="HTML", disable_web_page_preview=True)
            print("[✅ Successfully sent to authorized channel]")
        except Exception as e:
            print(f"[❌ Auto-send error]: {e}")
        await asyncio.sleep(300)

if __name__ == '__main__':
    bot_token = os.environ["BOT_TOKEN"]
    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usdt", usdt))

    async def on_startup(app):
        asyncio.create_task(auto_send(app.bot))

    app.post_init = on_startup

    print("🤖 Bot is up and restricted to @usdtyab channel only!")
    app.run_polling()
