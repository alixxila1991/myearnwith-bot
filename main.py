import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiohttp import web
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN") or "PUT_YOUR_FALLBACK_BOT_TOKEN_HERE"
WEBHOOK_URL = os.getenv("WEBHOOK_URL") or "https://your-render-url.onrender.com/webhook"
GROUP_ID = -1002730916091  # Your Telegram Group ID

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
Bot.set_current(bot)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# User wallet memory
user_wallet = {}

# --- /start ---
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    uid = str(message.from_user.id)
    if uid not in user_wallet:
        user_wallet[uid] = {"wallet": 0, "step": "group_join"}
    join_btn = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Join Telegram Group", url="https://t.me/Amazon_Flipkart_Loot_Alerts"),
        InlineKeyboardButton("✅ I Have Joined", callback_data="verify_join")
    )
    await message.answer(
        "👋 Welcome to the ₹50 Giveaway Bot!\n\n💸 Earn ₹50 directly to your UPI — just follow a few simple steps.\n\n🎯 Step 1: Join our group below.",
        reply_markup=join_btn
    )

# --- Group join verification ---
@dp.callback_query_handler(lambda c: c.data == "verify_join")
async def verify_group_join(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    uid = str(user_id)
    member = await bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)

    if member.status in ["member", "administrator", "creator"]:
        user_wallet[uid]["wallet"] += 20
        user_wallet[uid]["step"] = "referral"
        btn = InlineKeyboardMarkup().add(
            InlineKeyboardButton("💼 Check Balance", callback_data="check_balance")
        )
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(user_id, "🎉 Joined verified!\n₹20 added to your wallet.", reply_markup=btn)
    else:
        await bot.answer_callback_query(callback_query.id, text="❌ You have not joined the group.", show_alert=True)

# --- Balance check ---
@dp.callback_query_handler(lambda c: c.data == "check_balance")
async def show_wallet(callback_query: CallbackQuery):
    uid = str(callback_query.from_user.id)
    balance = user_wallet[uid]["wallet"]
    referral_btn = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ I’ve Shared in 5 Groups", callback_data="verify_referral")
    )
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
        f"💼 Wallet Balance: ₹{balance}\n\n🔓 To unlock ₹30 more:\nShare your link in 5 active groups:\n\n📎 Your Link:\nhttps://t.me/YourBot?start={uid}",
        reply_markup=referral_btn
    )

# --- Fake referral verification ---
@dp.callback_query_handler(lambda c: c.data == "verify_referral")
async def fake_verification(callback_query: CallbackQuery):
    uid = str(callback_query.from_user.id)
    user_wallet[uid]["wallet"] += 30
    user_wallet[uid]["step"] = "withdraw"
    withdraw_btn = InlineKeyboardMarkup().add(
        InlineKeyboardButton("💸 Withdraw ₹50", callback_data="withdraw")
    )
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
        f"✅ Verified!\n₹30 added.\n\n💼 Total: ₹50\n\n🔓 Withdrawal unlocked!",
        reply_markup=withdraw_btn
    )

# --- Fake withdraw ---
@dp.callback_query_handler(lambda c: c.data == "withdraw")
async def withdraw_handler(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
        "✍️ Enter your UPI ID to receive ₹50 (e.g. 9876543210@okaxis):")

@dp.message_handler(lambda message: "@" in message.text and len(message.text) < 50)
async def handle_upi(message: types.Message):
    await message.answer("✅ UPI ID received.\n\n💸 ₹50 will be credited in 2 hours.\n🧾 TXN: TXN12345UPAY")

# --- Webhook handler ---
async def handle_webhook(request):
    Bot.set_current(bot)
    data = await request.json()
    update = types.Update.to_object(data)
    await dp.process_update(update)
    return web.Response(text="OK")

# --- Health check ---
async def handle_health(request):
    return web.Response(text="OK")

# --- Startup & Shutdown ---
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    print("🚀 Webhook set to:", WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()
    await storage.close()
    await storage.wait_closed()

# --- App ---
app = web.Application()
app.router.add_post('/webhook', handle_webhook)
app.router.add_get('/', handle_health)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == '__main__':
    web.run_app(app, port=int(os.environ.get("PORT", 8080)))
