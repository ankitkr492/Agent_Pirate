import os, json
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import webbrowser
from dotenv import load_dotenv
from scraper import scrape_tpb
from agent import choose_best_title, get_title_list

load_dotenv()

with open(os.getenv("AGENT_PIRATE_CONFIG_PATH"), "r") as f:
    config = json.load(f)

REQUESTS_FILE = config["REQUESTS_FILE"]

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- Load ENV ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Allowed users (Telegram user IDs)
ADMINS = [os.getenv("TELEGRAM_USER_ID")]
ALLOWED_USERS = config["ALLOWED_USERS"].split(",")    # Add more IDs as needed


# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ALLOWED_USERS:
        await update.message.reply_text("🚫 You are not authorized to use this bot.")
        print("Unauthorised access: "+ str(update.effective_user.id))
        return
    await update.message.reply_text("👋 Welcome! Use /request <MovieName> to search.")
    print("/start usage by: "+str(update.effective_user.id))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ALLOWED_USERS:
        await update.message.reply_text("🚫 You are not authorized to use this bot.")
        print("Unauthorised access: "+ str(update.effective_user.id))
        return
    await update.message.reply_text("ℹ️ Use /request <MovieName> to download a movie or TV show.\nYou can also select from the provided options or let the bot choose the best one for you.")
    print("/help usage by: "+str(update.effective_user.id))

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ALLOWED_USERS:
        await update.message.reply_text("🚫 You are not authorized to use this bot.")
        print("Unauthorised access: "+ str(update.effective_user.id))
        return
    await update.message.reply_text("❓ Unknown command. Use /help to see available commands.")
    print("unknown message: " + " ".join(context.args) + "by: "+str(update.effective_user.id))

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    await update.message.reply_text("⚠️ An error occurred. Please try again later.")

def movie_agent(results, auto_decide: bool):
    if auto_decide:
        print("Choosing best option with LLM...")
        result = choose_best_title(results)
    else:
        result = results[0]
    
    # magnet_link = result["magnet_link"]
    title = result["title"]
    size = result["size"]
    title_type = result["title_type"]

    print(f"Chosen title: {title}")
    print(f"File Size: {size}")
    print(f"Classification: {title_type}")
    # print(f"Chosen Magnet link: {magnet_link}")
    
    return result
    
def title_list_agent(results):
    print("Getting List of titles in List<Dictionary> Format.")
    result = get_title_list(results)
    #print("Result:", result)
    print("-------------------------Result Titles---------------------------")
    for item in result:
        print(f"Title: {item['title']} | Size: {item['size']}")
    return result

#update active_requests.json for active requests
def update_json(title, title_type, user_id):
    data = []
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    # overwrite if title already exists for same user
    updated = False
    for entry in data:
        if entry["title"] == title and entry["user_id"] == user_id:
            entry["type"] = title_type
            updated = True
            break

    if not updated:
        data.append({"title": title, "type": title_type, "user_id": user_id})

    with open(REQUESTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

user_search_results = {}

async def request_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ALLOWED_USERS:
        await update.message.reply_text("🚫 You are not authorized to use this bot.")
        print("Unauthorised access: "+ str(update.effective_user.id))
        return
    
    print(f"/request usage by: {str(update.effective_user.id)} with args: {' '.join(context.args)}")

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /request <MovieName>")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔎 Searching for: {query} ...")

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, scrape_tpb, query)
    result_limit = config['result_limit']+1
    results = results[:result_limit]  # Limit to top n results

    # if result:
    #     await update.message.reply_text(f"🎬 Selected: {result}")
    #     await update.message.reply_text(f"🍿 Sit back and relax... Media will be added to server shortly.")
    if not results:
        await update.message.reply_text("❌ No valid results found.")
        return
    
    formatted_result = title_list_agent(results)
    # print(f"Formatted Result: {formatted_result}")
    
    if not formatted_result or len(formatted_result) == 0:
        await update.message.reply_text("❌ No valid results found.")
        return
    
    # Save results for user
    user_search_results[update.effective_user.id] = formatted_result

    # Prepare buttons for each result
    keyboard = [
        [InlineKeyboardButton(f"{item['size']}~{item['short_title'][:15]}~{item['resolution']}{item['release_year']}{item['encoding']}{item['source']}", callback_data=f"select_{idx}")]
        for idx, item in enumerate(formatted_result)
    ]
    keyboard.append([InlineKeyboardButton("🤖 Auto Choose Best", callback_data="auto_decide")])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a result or let the bot decide:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    results = user_search_results.get(user_id, [])

    if query.data.startswith("select_"):
        idx = int(query.data.split("_")[1])
        selected = results[idx]

        # Save pending selection
        context.user_data["pending_selection"] = selected
        context.user_data["all_results"] = results  # store all results for cancel re-render

        # Confirmation step
        confirm_keyboard = [
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm_selection")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(confirm_keyboard)
        
        await query.edit_message_text(
            f"🎬 You selected:\n\n<b>{selected['title']}</b>\n📦 Size: {selected['size']}\n\nDo you want to confirm?",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    elif query.data == "confirm_selection":
        selected = context.user_data.get("pending_selection")
        if not selected:
            await query.edit_message_text("❌ No pending selection found.")
            return
    

        llm_result = movie_agent([selected], False)
        if llm_result:
            await query.edit_message_text(f"🎬 Confirmed: {selected['title']}\n📦 Size: {selected['size']}\n🍿 Media will be added to server shortly.")
        else:
            await query.edit_message_text("❌ Failed to process the selected item. Please try again.")

        if selected['magnet_link'].startswith("magnet:?"):
            print("Opening magnet link...")
            webbrowser.open(selected['magnet_link'])
            update_json(selected['title'], selected['title_type'], str(update.effective_user.id))

        else:
            print("No valid magnet link returned.")
            await query.edit_message_text(f"❌ No valid magnet link returned for {selected['title']}. Please try again.")


    elif query.data == "auto_decide":
        # results = user_search_results.get(user_id, [])
        llm_result = movie_agent(results, True)

        # Save pending selection
        context.user_data["pending_selection"] = llm_result
        context.user_data["all_results"] = results  # store all results for cancel re-render

        if llm_result:
            context.user_data["auto_selected"] = llm_result
            keyboard = [
                [InlineKeyboardButton("✅ Confirm", callback_data="confirm_auto_decide")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🤖 Auto Selected:\n{llm_result['title']}\n📦 Size: {llm_result['size']}\n\nDo you want to confirm?",
                reply_markup=reply_markup
            )
            # await query.edit_message_text(f"🎬 Auto Selected: {llm_result}\n🍿 Media will be added to server shortly.")
        else:
            await query.edit_message_text("❌ Failed to process the request. Please try again.")
    
    elif query.data == "confirm_auto_decide":
        selected = context.user_data.get("auto_selected")
        if selected:
            # Do final processing here (magnet link, json, etc.)
            if selected['magnet_link'].startswith("magnet:?"):
                print("Opening magnet link...")
                webbrowser.open(selected['magnet_link'])
                update_json(selected['title'], selected['title_type'], str(update.effective_user.id))

            else:
                print("No valid magnet link returned.")
                await query.edit_message_text(
                f"❌ No valid magnet link returned for {selected['title']}. Please try again."
                )
            
            await query.edit_message_text(
                f"✅ Confirmed:\n\n🎬 {selected['title']}\n📦 Size: {selected['size']}\n🍿 Media will be added to server shortly."
            )
        else:
            await query.edit_message_text("❌ No auto-selected item found. Please try again.")


    elif query.data == "back":
        results = context.user_data.get("all_results", [])
        if not results:
            await query.edit_message_text("❌ Cancelled.")
            return

        # Rebuild original result list
        keyboard = [
        [InlineKeyboardButton(f"{item['size']}~{item['short_title'][:20]}~{item['resolution']}{item['release_year']}{item['encoding']}{item['source']}", callback_data=f"select_{idx}")]
        for idx, item in enumerate(results)
        ]
        keyboard.append([InlineKeyboardButton("🤖 Auto Choose Best", callback_data="auto_decide")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)

        #await query.edit_message_reply_markup(reply_markup=reply_markup)
        await query.edit_message_text(
            "🔙 Back to Results. Please choose again:",
            reply_markup=reply_markup
        )

    elif query.data == "cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Request cancelled.")


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
        # app.add_handler(MessageHandler(filters.COMMAND, unknown_command))  # Handle unknown commands
        app.add_error_handler(lambda update, context: logging.error(f"Update {update} caused error {context.error}"))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_command))
        app.add_handler(CallbackQueryHandler(button_callback))
    
    except Exception as e:
        print(f"Error in main: {e}")
        error_handler
    
    app.run_polling()

if __name__ == "__main__":
    main()