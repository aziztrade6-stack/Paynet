import asyncio
import logging
import sqlite3
import re
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Botingiz tokeni
API_TOKEN = "8823420781:AAHUt1Aero1zdNb2c46N8BcYWJUQ2-wlC9w"  # <-- BotFather bergan haqiqiy tokenni yozing

logging.basicConfig(level=logging.INFO)

conn = sqlite3.connect("kassa.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

def add_transaction(user_id: int, amount: float, note: str = ""):
    cursor.execute("INSERT INTO transactions (user_id, amount, note) VALUES (?, ?, ?)", (user_id, amount, note))
    conn.commit()

def get_total(user_id: int) -> float:
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()[0]
    return res if res else 0.0

def get_count(user_id: int) -> int:
    cursor.execute("SELECT COUNT(id) FROM transactions WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()[0]
    return res if res else 0

def reset_transactions(user_id: int):
    cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    conn.commit()

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Xush kelibsiz!\n\n"
        "Pul qabul qilganda shunchaki summani yozib yuboring (masalan: `50000` yoki `35000 karta`).\n\n"
        "Buyruqlar:\n"
        "/stat - Jami tushum va qabul qilingan to'lovlar soni\n"
        "/reset - Hisobni noldan boshlash",
        parse_mode="Markdown"
    )

@dp.message(Command("stat"))
async def stat_handler(message: types.Message):
    total = get_total(message.from_user.id)
    count = get_count(message.from_user.id)
    await message.answer(
        f"📊 **Hisob-kitob holati:**\n\n"
        f"Jami yig'ilgan: **{total:,.2f}**\n"
        f"To'lovlar soni: **{count} ta**",
        parse_mode="Markdown"
    )

@dp.message(Command("reset"))
async def reset_handler(message: types.Message):
    reset_transactions(message.from_user.id)
    await message.answer("🔄 Barcha hisob-kitoblar tozalandi.")

@dp.message()
async def process_income(message: types.Message):
    text = message.text.strip().replace(",", ".")
    match = re.match(r"^(\d+(\.\d+)?)(\s+(.*))?$", text)
    if match:
        amount = float(match.group(1))
        note = match.group(4) if match.group(4) else "Izohsiz"
        user_id = message.from_user.id

        add_transaction(user_id, amount, note)
        total = get_total(user_id)

        await message.answer(
            f"✅ **Qabul qilindi:** +{amount:,.2f}\n"
            f"📝 **Izoh:** {note}\n"
            f"💰 **Jami hisob:** **{total:,.2f}**",
            parse_mode="Markdown"
        )
    else:
        await message.answer("Iltimos, summani raqam bilan yozing (masalan: `50000`).")

# Server doim ochiq turishi uchun dummy web server
async def handle_ping(request):
    return web.Response(text="Bot ishlayapti!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
