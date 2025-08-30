from telegram import Bot
import asyncio
import sys
import os
import json
import shutil
import difflib
from dotenv import load_dotenv

load_dotenv()

with open(os.getenv("AGENT_PIRATE_CONFIG_PATH"), "r") as f:
    config = json.load(f)

REQUESTS_FILE = config["REQUESTS_FILE"]

torrent_path = sys.argv[1]   # %F
torrent_name = sys.argv[2]  # %N

MOVIES_DIR = config["MOVIES_DIR"]
SHOWS_DIR = config["SHOWS_DIR"]

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# CHAT_ID = sys.argv[4]

ADMINS = os.getenv("ADMINS_TELEGRAM_USER_ID").split(",")

async def finished(CHAT_IDS):
    bot = Bot(token=BOT_TOKEN)
    for CHAT_ID in CHAT_IDS:
        await bot.send_message(chat_id=CHAT_ID, text=f"🔔 Alert!!!\nFinished Downloading: {torrent_name}\n")

async def error(error_msg, CHAT_IDS):
    bot = Bot(token=BOT_TOKEN)
    for CHAT_ID in CHAT_IDS:
        await bot.send_message(chat_id=CHAT_ID, text=f"❌ Error\n{error_msg}\n")

async def moved(CHAT_IDS):
    bot = Bot(token=BOT_TOKEN)
    for CHAT_ID in CHAT_IDS:
        await bot.send_message(chat_id=CHAT_ID, text=f"🔔 Alert!!!\n Moved the file to media server: {torrent_name}\nIt might take 15-30 mins to refresh the Media Library")


def load_request_data():
    if not os.path.exists(REQUESTS_FILE):
        return []
    with open(REQUESTS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_request_data(data):
    with open(REQUESTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_type_and_user(title):
    data = load_request_data()
    if not data:
        return None, None

    # Exact match first
    for entry in data:
        if entry["title"].lower() in title.lower():
            return entry["type"], entry.get("user_id")

    # If no exact match, fuzzy match
    titles = [entry["title"] for entry in data]
    best_match = difflib.get_close_matches(title, titles, n=1, cutoff=0.6)

    if best_match:
        matched_title = best_match[0]
        for entry in data:
            if entry["title"] == matched_title:
                return entry["type"], entry.get("user_id")

    return None, None


if __name__ == "__main__":
    
    title_type, user_id = get_type_and_user(torrent_name)

    if not user_id:
        print(f"⚠️ No user_id found for {torrent_name}.\nSending notification to ADMINS only.")
        users = ADMINS
    else:
        print(f"✅ Found user_id {user_id} for {torrent_name}")
        if user_id not in ADMINS:
            print(f"User ID {user_id} not in ADMINS, sending notification to user + ADMINS.")
            users = ADMINS + [user_id]
        else:
            print(f"User ID {user_id} is already in ADMINS, sending notification from ADMINS list only.")

    asyncio.run(finished(users))


    if not title_type:
        print(f"⚠️ No media classification found for {torrent_name}. Leaving file in place.")
        asyncio.run(error(f"No media classification found for {torrent_name}. Leaving file in place.\nContact Admins to move the file to Media Library.", users))
        sys.exit(0)

    print(f"✅ Found media classification for {torrent_name}: {title_type}, requested by user {user_id}")


    # Determine destination
    if title_type == "Movie":
        dest_dir = MOVIES_DIR
    elif title_type == "Show":
        dest_dir = SHOWS_DIR
    else:
        print(f"⚠️ Unknown type '{title_type}' for {torrent_name}")
        asyncio.run(error(f"Unknown media type '{title_type}' for {torrent_name}\nContact Admins to move the file to Media Library.", users))
        sys.exit(1)

    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, os.path.basename(torrent_path))

    # Move file/folder
    try:
        shutil.move(torrent_path, dest_path)
        print(f"✅ Moved {torrent_name} → {dest_dir}")
        asyncio.run(moved(users))
    except Exception as e:
        print(f"❌ Failed to move {torrent_name}: {e}")
        asyncio.run(error(f"Failed to move {torrent_name}: {e}\nContact Admins to move the file to Media Library.", users))
