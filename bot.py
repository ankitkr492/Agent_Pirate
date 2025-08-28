# bot.py
import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


from main import movie_agent

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- Load ENV ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Allowed users (Telegram user IDs)
ALLOWED_USERS = [int(os.getenv("TELEGRAM_USER_ID"))]    # Add more IDs as needed


# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("🚫 You are not authorized to use this bot.")
        return
    await update.message.reply_text("✅ Welcome! Use /request <MovieName> to search.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Use /request <MovieName> to download a movie or TV show.")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Unknown command. Use /help to see available commands.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    await update.message.reply_text("⚠️ An error occurred. Please try again later.")


async def request_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("🚫 You are not authorized to use this bot.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /request <MovieName>")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔎 Searching for: {query} ...")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, movie_agent, query)

    if result:
        await update.message.reply_text(f"🎬 Found: {result}")
        await update.message.reply_text(f"🍿 Sit back and relax... Movie will be added shortly.")
    else:
        await update.message.reply_text("❌ No valid results found.")


# --- Main ---
def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment variables!")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    #app = Application.builder().token(TELEGRAM_BOT_TOKEN).timezone(pytz.UTC).build()
    try:
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("request", request_movie))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.COMMAND, unknown_command))  # Handle unknown commands
        app.add_error_handler(lambda update, context: logging.error(f"Update {update} caused error {context.error}"))

    except Exception as e:
        print(f"Error in main: {e}")
        error_handler
    
    app.run_polling()

if __name__ == "__main__":
    main()