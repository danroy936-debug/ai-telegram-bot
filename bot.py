import os
import time
import asyncio
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

# =========================
# ENV VARIABLES
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing")

client = Groq(api_key=GROQ_API_KEY)

# =========================
# MEMORY (simple in-memory)
# =========================

user_mode = {}
user_cooldown = {}

# =========================
# MENU
# =========================

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

# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI Bot Ready!\nSelect a mode:",
        reply_markup=menu()
    )

# =========================
# BUTTON HANDLER
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_mode[user_id] = query.data

    await query.edit_message_text(
        f"✅ Mode selected: {query.data.upper()}"
    )

# =========================
# AI FUNCTION
# =========================

def ask_ai(text, mode):

    system_prompts = {
        "chat": "You are a helpful assistant.",
        "coding": "You are a senior software engineer.",
        "study": "You are a teacher explaining clearly.",
        "content": "You are a marketing and content expert."
    }

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": system_prompts.get(mode, "You are a helpful assistant.")
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0.7,
        max_tokens=500
    )

    return response.choices[0].message.content

# =========================
# MESSAGE HANDLER
# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    now = time.time()

    # cooldown 3 sec
    if user_id in user_cooldown:
        if now - user_cooldown[user_id] < 3:
            await update.message.reply_text("⏳ Please wait 3 seconds")
            return

    user_cooldown[user_id] = now

    mode = user_mode.get(user_id, "chat")

    try:
        reply = ask_ai(text, mode)
        await update.message.reply_text(reply, reply_markup=menu())

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# =========================
# MAIN (FIX FOR RENDER + PYTHON 3.14)
# =========================

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

async def main():
    print("🤖 Bot starting...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
