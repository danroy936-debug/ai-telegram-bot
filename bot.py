import time
from groq import Groq

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = "TELEGRAM_BOT_TOKEN_KAU"
GROQ_API_KEY = "GROQ_API_KEY_KAU"

client = Groq(api_key=GROQ_API_KEY)

user_mode = {}
user_cooldown = {}

def menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 Chat", callback_data="chat"),
            InlineKeyboardButton("💻 Coding", callback_data="coding")
        ],
        [
            InlineKeyboardButton("📚 Study", callback_data="study"),
            InlineKeyboardButton("📢 Content", callback_data="content")
        ]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI Bot Ready!",
        reply_markup=menu()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.message.chat_id

    await query.answer()

    user_mode[user_id] = query.data

    await query.edit_message_text(
        f"Mode: {query.data.upper()}"
    )

def ask_ai(text, mode):
    system = {
        "chat": "You are a helpful assistant.",
        "coding": "You are a programmer.",
        "study": "You are a teacher.",
        "content": "You are a marketing expert."
    }

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system.get(mode, "chat")},
            {"role": "user", "content": text}
        ],
        max_tokens=200
    )

    return res.choices[0].message.content

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id
    text = update.message.text

    mode = user_mode.get(user_id, "chat")

    now = time.time()
    if user_id in user_cooldown and now - user_cooldown[user_id] < 3:
        await update.message.reply_text("⏳ Cooldown 3s")
        return

    user_cooldown[user_id] = now

    try:
        reply = ask_ai(text, mode)
        await update.message.reply_text(reply, reply_markup=menu())
    except Exception as e:
        await update.message.reply_text(str(e))

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot running...")
app.run_polling()
