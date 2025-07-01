import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=API_TOKEN)
Bot.set_current(bot) 
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

user_wallet = {}

# --- Start command ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    uid = str(message.from_user.id)
    if uid not in user_wallet:
        user_wallet[uid] = {"wallet": 0}
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Join Group", url="https://t.me/yourgroupname", callback_data="joined"))
    await message.answer("💸 Earn ₹50 in just a few simple steps!\nClick below to join our group and get rewarded!", reply_markup=keyboard)

# --- Join group callback ---
@dp.callback_query_handler(lambda c: c.data == "joined")
async def joined_button_callback(callback_query: CallbackQuery):
    uid = str(callback_query.from_user.id)
    if uid not in user_wallet:
        user_wallet[uid] = {"wallet": 0}
    user_wallet[uid]["wallet"] = 20
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(uid, "🎉 Congratulations! ₹20 has been credited to your wallet.")

# --- Webhook handler ---
async def handle_webhook(request):
    data = await request.json()
    update = types.Update.to_object(data)
    await dp.process_update(update)
    return web.Response()

# --- On startup ---
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    print("🚀 Webhook set!")

# --- On shutdown ---
async def on_shutdown(app):
    await bot.delete_webhook()
    await storage.close()
    await storage.wait_closed()

# --- App setup ---
app = web.Application()
app.router.add_post('/webhook', handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == '__main__':
    web.run_app(app, port=int(os.environ.get("PORT", 8080)))
