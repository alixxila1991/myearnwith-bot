import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
GROUP_ID = -1002730916091

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

user_data = {}

class Form(StatesGroup):
    awaiting_screenshot = State()
    awaiting_upi = State()

# --- /start Command ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    uid = str(message.from_user.id)
    user_data[uid] = {'wallet': 0, 'shared_groups': 0, 'referred': False, 'whatsapp_done': False}

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ Join Telegram Group", url="https://t.me/Amazon_Flipkart_Loot_Alerts"),
        InlineKeyboardButton("➡️ I Have Joined", callback_data="verify_join")
    )
    await message.answer("👋 Welcome!\n\n💸 Earn ₹50 by completing simple steps!\n\n👇 Step 1: Join the Telegram group below:", reply_markup=keyboard)

# --- Verify Group Join ---
@dp.callback_query_handler(lambda c: c.data == 'verify_join')
async def verify_join(callback_query: types.CallbackQuery):
    uid = str(callback_query.from_user.id)
    member = await bot.get_chat_member(GROUP_ID, callback_query.from_user.id)
    if member.status in ['member', 'creator', 'administrator']:
        user_data[uid]['wallet'] = 20
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("💼 Check Balance", callback_data="check_balance"))
        await callback_query.message.edit_text("🎉 Congratulations! You have successfully joined the group.\n\n₹20 added to your wallet.", reply_markup=kb)
    else:
        await callback_query.message.edit_text("❌ You haven't joined the group yet. Please join and try again.")

# --- Check Balance & Share Link ---
@dp.callback_query_handler(lambda c: c.data == 'check_balance')
async def check_balance(callback_query: types.CallbackQuery):
    uid = str(callback_query.from_user.id)
    balance = user_data[uid]['wallet']
    keyboard = InlineKeyboardMarkup()
    if balance == 20:
        keyboard.add(InlineKeyboardButton("📤 Share Referral Link in 5 Groups", callback_data="share_link"))
    elif balance >= 50 and not user_data[uid]['whatsapp_done']:
        keyboard.add(InlineKeyboardButton("💬 Join WhatsApp Channel", url="https://wa.me/yourwhatsapplink"))
        keyboard.add(InlineKeyboardButton("📸 I Joined WhatsApp & Have Screenshot", callback_data="upload_ss"))
    elif balance == 70:
        keyboard.add(InlineKeyboardButton("💳 Withdraw ₹70", callback_data="withdraw"))

    await callback_query.message.answer(f"💼 Wallet Balance: ₹{balance}", reply_markup=keyboard)

# --- Share Link Step ---
@dp.callback_query_handler(lambda c: c.data == 'share_link')
async def share_link_step(callback_query: types.CallbackQuery):
    uid = str(callback_query.from_user.id)
    link = f"https://t.me/YourBotUsername?start={uid}"
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ I've Shared in 5 Groups", callback_data="verify_share"))
    await callback_query.message.answer(f"📎 Your Referral Link:\n{link}\n\n📢 Share this in 5 active Telegram groups.\nThen click the button below.", reply_markup=kb)

# --- Verify Shared Link ---
@dp.callback_query_handler(lambda c: c.data == 'verify_share')
async def verify_share(callback_query: types.CallbackQuery):
    uid = str(callback_query.from_user.id)
    if user_data[uid]['shared_groups'] >= 5:
        await callback_query.message.answer("✅ Already verified. You earned ₹30.")
        return

    # Simulate verifying shared groups (you can add actual logic)
    user_data[uid]['shared_groups'] = 5
    user_data[uid]['wallet'] += 30
    await callback_query.message.answer("🎉 Verified! You earned ₹30 more.")
    await check_balance(callback_query)

# --- Screenshot Upload Prompt ---
@dp.callback_query_handler(lambda c: c.data == 'upload_ss')
async def ask_screenshot(callback_query: types.CallbackQuery, state: FSMContext):
    await Form.awaiting_screenshot.set()
    await callback_query.message.answer("📸 Please send a screenshot showing you joined the WhatsApp group.")

@dp.message_handler(content_types=['photo'], state=Form.awaiting_screenshot)
async def handle_screenshot(message: types.Message, state: FSMContext):
    await state.finish()
    await Form.awaiting_upi.set()
    await message.answer("✅ Screenshot verified. Now send your UPI ID (e.g., 98765@upi)")

@dp.message_handler(state=Form.awaiting_upi)
async def get_upi_id(message: types.Message, state: FSMContext):
    uid = str(message.from_user.id)
    user_data[uid]['wallet'] = 70
    user_data[uid]['whatsapp_done'] = True
    await state.finish()
    await message.answer("✅ UPI ID received.\n\n💸 Your ₹70 will be credited within 1 hour.\n🧾 Transaction ID: TXN{}UPAY".format(uid[-4:]))
    # Send fake confirmation after delay
    await asyncio.sleep(3600)
    await message.answer(f"🎉 ₹70 successfully credited to your UPI!\nThanks for participating.")

# --- Withdraw Handler ---
@dp.callback_query_handler(lambda c: c.data == 'withdraw')
async def withdraw_handler(callback_query: types.CallbackQuery):
    uid = str(callback_query.from_user.id)
    if user_data[uid]['wallet'] == 70:
        await callback_query.message.answer("💰 You've earned ₹70. Please wait while we process your withdrawal.")
    else:
        await callback_query.message.answer("⚠️ You have not yet completed all steps.")

# --- Webhook Setup ---
async def handle_webhook(request):
    data = await request.json()
    update = types.Update.to_object(data)
    await dp.process_update(update)
    return web.Response(text="OK")

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()
    await storage.close()
    await storage.wait_closed()

app = web.Application()
app.router.add_post('/webhook', handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == '__main__':
    web.run_app(app, port=int(os.environ.get("PORT", 8080)))
