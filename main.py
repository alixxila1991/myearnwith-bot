from aiogram import Bot, Dispatcher, executor, types
import json
import os
from threading import Timer
from dotenv import load_dotenv  # ✅ Load .env file

load_dotenv()  # ✅ Activate .env reading

API_TOKEN = os.getenv("BOT_TOKEN")  # ✅ Securely get token
GROUP_ID = -1002730916091  # Replace with your actual group ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

if os.path.exists("user.json"):
    with open("user.json", "r") as f:
        user_wallet = json.load(f)
else:
    user_wallet = {}

def save_wallet():
    with open("user.json", "w") as f:
        json.dump(user_wallet, f)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    args = message.get_args()
    user_id = str(message.from_user.id)

    if user_id not in user_wallet:
        user_wallet[user_id] = {
            "wallet": 0, "joined": False, "verified": False,
            "ref_by": args if args else None, "referrals": []
        }

        if args and args != user_id and args in user_wallet:
            user_wallet[args]["referrals"].append(user_id)

        save_wallet()

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🚀 Start Earning", callback_data="start_earning"))
    await message.reply("💸 Welcome! Earn ₹50 in just a few simple steps!", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "start_earning")
async def ask_to_join_group(callback_query: types.CallbackQuery):
    join_keyboard = types.InlineKeyboardMarkup()
    join_keyboard.add(
        types.InlineKeyboardButton("📢 Join Telegram Group", url="https://t.me/Amazon_Flipkart_Loot_Alerts"),
        types.InlineKeyboardButton("✅ I've Joined", callback_data="joined_done")
    )
    await bot.send_message(callback_query.from_user.id, "🔓 Please join our group to unlock your reward:", reply_markup=join_keyboard)

@dp.callback_query_handler(lambda c: c.data == "joined_done")
async def joined_button_callback(callback_query: types.CallbackQuery):
    user = await bot.get_chat_member(GROUP_ID, callback_query.from_user.id)
    uid = str(callback_query.from_user.id)

    if user.status in ['member', 'creator', 'administrator']:
        user_wallet[uid]["wallet"] = 20
        user_wallet[uid]["joined"] = True
        save_wallet()
        await bot.send_message(uid, "🎉 ₹20 credited. Now complete the next step to get ₹30 more.")
        await ask_to_share(uid)
    else:
        await bot.send_message(uid, "❌ You haven’t joined the group yet.")

async def ask_to_share(user_id):
    share_message = (
        "📢 Share our link in 5 active Telegram groups to unlock your remaining ₹30 reward.\n\n"
        "👇 *Copy and share this message in 5 Telegram groups:*\n\n"
        "🔥 FREE Deals & Loots 🔥\n"
        "🛒 Amazon + Flipkart Offers, Price Errors & More!\n"
        "👉 https://t.me/+SL5K8_5Qfwk5MzE1\n\n"
        "_Once shared, click the button below to continue._"
    )

    share_keyboard = types.InlineKeyboardMarkup()
    share_keyboard.add(
        types.InlineKeyboardButton("✅ I've Shared in 5 Groups", callback_data="shared_done")
    )

    await bot.send_message(
        user_id,
        share_message,
        parse_mode="Markdown",
        reply_markup=share_keyboard
    )

@dp.callback_query_handler(lambda c: c.data == "shared_done")
async def shared_button_callback(callback_query: types.CallbackQuery):
    uid = str(callback_query.from_user.id)
    if user_wallet.get(uid, {}).get("wallet", 0) >= 50:
        await bot.send_message(uid, "✅ You've already completed all steps.")
        return

    user_wallet[uid]["wallet"] += 30
    save_wallet()
    await bot.send_message(
        uid,
        "🎊 ₹30 more added! Wallet = ₹50\n\n💸 Click below to withdraw your reward.",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("💸 Withdraw ₹50", callback_data="withdraw_start")
        )
    )

@dp.callback_query_handler(lambda c: c.data == "withdraw_start")
async def withdraw_button_handler(callback_query: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("📱 Join WhatsApp Group", url="https://chat.whatsapp.com/ExampleLink")
    )
    await bot.send_message(callback_query.from_user.id, "🚨 Join WhatsApp and earn extra ₹20!", reply_markup=keyboard)
    await bot.send_message(callback_query.from_user.id, "📷 Please upload a screenshot to continue.")

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def verify_screenshot(message: types.Message):
    uid = str(message.from_user.id)
    if user_wallet.get(uid, {}).get("wallet", 0) < 50:
        await message.reply("❗ You haven’t completed the steps yet.")
        return

    user_wallet[uid]["verified"] = True
    save_wallet()
    await message.reply("✅ Screenshot received. Now enter your UPI ID.")

@dp.message_handler(lambda message: "@" in message.text or "upi" in message.text.lower())
async def get_upi(message: types.Message):
    uid = str(message.from_user.id)
    if not user_wallet.get(uid, {}).get("verified", False):
        await message.reply("❗ Screenshot is required before withdrawal.")
        return

    user_wallet[uid]["upi"] = message.text.strip()
    save_wallet()

    await message.reply("⏳ ₹70 will be credited to your UPI in 2 hours.")

    def confirm_payment():
        bot.loop.create_task(bot.send_message(uid, "✅ ₹70 has been successfully sent to your UPI ID. Thank you!"))

    Timer(3600, confirm_payment).start()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
