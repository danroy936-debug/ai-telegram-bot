import os
import time
import asyncio
import logging
from groq import Groq

from telegram import (
Update,
InlineKeyboardButton,
InlineKeyboardMarkup
)

from telegram.ext import (
Application,
CommandHandler,
MessageHandler,
CallbackQueryHandler,
ContextTypes,
filters
)

# =========================

LOGGING

#=========================

logging.basicConfig(
format="%(asctime)s - %(levelname)s - %(message)s",
level=logging.INFO
)

# =========================

ENV VARIABLES

# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
raise ValueError("BOT_TOKEN is missing")

if not GROQ_API_KEY:
raise ValueError("GROQ_API_KEY is missing")

client = Groq(api_key=GROQ_API_KEY)

# =========================

MEMORY

# =========================

user_mode = {}
user_cooldown = {}

# =========================

MENU

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

START

# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

await update.message.reply_text(
    "🤖 AI Bot Ready!\n\nSelect a mode:",
    reply_markup=menu()
)

# =========================

BUTTON

# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query

await query.answer()

user_id = query.from_user.id
user_mode[user_id] = query.data

await query.edit_message_text(
    f"✅ Mode selected: {query.data.upper()}",
    reply_markup=menu()
)

# =========================

AI FUNCTION

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
            "content": system_prompts.get(
                mode,
                "You are a helpful assistant."
            )
        },
        {
            "role": "user",
            "content": text
        }
    ],
    temperature=0.7,
    max_tokens=800
)

return response.choices[0].message.content

# =========================

MESSAGE HANDLER

# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

if not update.message:
    return

user_id = update.effective_user.id
text = update.message.text

now = time.time()

if user_id in user_cooldown:
    if now - user_cooldown[user_id] < 3:
        await update.message.reply_text(
            "⏳ Please wait 3 seconds before sending another message."
        )
        return

user_cooldown[user_id] = now

mode = user_mode.get(user_id, "chat")

try:

    loop = asyncio.get_running_loop()

    reply = await loop.run_in_executor(
        None,
        ask_ai,
        text,
        mode
    )

    if not reply:
        reply = "No response received."

    if len(reply) > 4000:
        reply = reply[:4000]

    await update.message.reply_text(
        reply,
        reply_markup=menu()
    )

except Exception as e:

    logging.exception("Error")

    await update.message.reply_text(
        f"❌ Error:\n{str(e)}"
    )

# =========================

MAIN

# =========================

def main():

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    CallbackQueryHandler(button)
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle
    )
)

logging.info("🤖 Bot started")

app.run_polling(
    drop_pending_updates=True
)

if name == "main":
main() 
