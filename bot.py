import os
import time
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
# ENV VARIABLES
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found")

client = Groq(api_key=GROQ_API_KEY)

# =========================
# MEMORY
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
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 AI Bot Ready!\n\nSelect a mode below:",
        reply_markup=menu()
    )

# =========================
# BUTTON
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id
    selected_mode = query.data

    user_mode[user_id] = selected_mode

    await query.edit_message_text(
        f"✅ Mode selected: {selected_mode.upper()}"
    )

# =========================
# AI
# =========================

def ask_ai(text, mode):

    system_prompts = {
        "chat": "You are a helpful AI assistant.",
        "coding": "You are an expert software engineer.",
        "study": "You are an experienced teacher.",
        "content": "You are a professional content creator and marketer."
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

    if (
        user_id in user_cooldown
        and now - user_cooldown[user_id] < 3
    ):
        await update.message.reply_text(
            "⏳ Please wait 3 seconds before sending another message."
        )
        return

    user_cooldown[user_id] = now

    mode = user_mode.get(user_id, "chat")

    try:

        reply = ask_ai(text, mode)

        if not reply:
            reply = "No response generated."

        await update.message.reply_text(
            reply,
            reply_markup=menu()
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Error:\n{str(e)}"
        )

# =========================
# MAIN
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

    print("🤖 Bot running...")

    app.run_polling()

if __name__ == "__main__":
    main()
