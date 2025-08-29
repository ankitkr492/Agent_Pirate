from telegram import Bot
import asyncio
import sys
import os
import json
import shutil
import difflib

torrent_path = sys.argv[1]   # %F
torrent_name = sys.argv[2]  # %N

# torrent_path = sys.argv[1]   # %F
# torrent_name = sys.argv[2]  # %N


BOT_TOKEN = sys.argv[3]
CHAT_ID = sys.argv[4]

async def finished():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=f"🔔 Alert!!!\nFinished Downloading: {torrent_name}\n")

async def error(error_msg):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=f"❌ Error Moving File: {error_msg}\n")

async def moved():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=f"🔔 Alert!!!\n Moved the file to media server: {torrent_name}\n")


with open("C:/Users/ankit/OneDrive/Documents/Agent_Pirate/config/config.json", "r") as f:
    config = json.load(f)

ACTIVE_REQUESTS_FILE = config["ACTIVE_REQUESTS_FILE"]

MOVIES_DIR = config["MOVIES_DIR"]
SHOWS_DIR = config["SHOWS_DIR"]

def load_classifications():
    if not os.path.exists(ACTIVE_REQUESTS_FILE):
        return []
    with open(ACTIVE_REQUESTS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_classifications(data):
    with open(ACTIVE_REQUESTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_type_and_cleanup(title):
    data = load_classifications()
    if not data:
        return None

    # Exact match first
    for entry in data:
        if entry["title"].lower() in title.lower():
            result = entry["type"]
            # cleanup → remove from json
            new_data = [e for e in data if e != entry]
            save_classifications(new_data)
            return result

    # If no exact match, fuzzy match
    titles = [entry["title"] for entry in data]
    best_match = difflib.get_close_matches(title, titles, n=1, cutoff=0.6)

    if best_match:
        matched_title = best_match[0]
        for entry in data:
            if entry["title"] == matched_title:
                result = entry["type"]
                # cleanup → remove from json
                new_data = [e for e in data if e != entry]
                save_classifications(new_data)
                return result

    return None



if __name__ == "__main__":
    asyncio.run(finished())

    title_type = get_type_and_cleanup(torrent_name)

    if not title_type:
        print(f"⚠️ No classification found for {torrent_name}. Leaving file in place.")
        asyncio.run(error(f"No classification found for {torrent_name}. Leaving file in place."))
        sys.exit(0)

    # Determine destination
    if title_type == "Movie":
        dest_dir = MOVIES_DIR
    elif title_type == "Show":
        dest_dir = SHOWS_DIR
    else:
        print(f"⚠️ Unknown type '{title_type}' for {torrent_name}")
        asyncio.run(error(f"Unknown type '{title_type}' for {torrent_name}"))
        sys.exit(1)

    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, os.path.basename(torrent_path))

    # Move file/folder
    try:
        shutil.move(torrent_path, dest_path)
        print(f"✅ Moved {torrent_name} → {dest_dir}")
        asyncio.run(moved())
    except Exception as e:
        print(f"❌ Failed to move {torrent_name}: {e}")
        asyncio.run(error(f"Failed to move {torrent_name}: {e}"))
