import difflib
from telegram import Bot
import asyncio
import sys
import os
import json
from dotenv import load_dotenv


load_dotenv()

with open(os.getenv("AGENT_PIRATE_CONFIG_PATH"), "r") as f:
    config = json.load(f)

REQUESTS_FILE = config["REQUESTS_FILE"]

torrent_path = sys.argv[1]   # %F
torrent_name = sys.argv[2]  # %N


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

#CHAT_ID = sys.argv[4]

ADMINS = os.getenv("ADMINS_TELEGRAM_USER_ID").split(",")

async def main(CHAT_IDS):
    bot = Bot(token=BOT_TOKEN)
    for CHAT_ID in CHAT_IDS:
        await bot.send_message(chat_id=CHAT_ID, text=f"🔔 Alert!!!\nStarted Downloading:\n{torrent_name}\n")

def load_requests():
    if not os.path.exists(REQUESTS_FILE):
        return []
    with open(REQUESTS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def get_user_id(title):
    data = load_requests()
    if not data:
        return None

    for entry in data:
        if entry["title"].lower() in title.lower():
            return entry.get("user_id")
    
    # If no exact match, fuzzy match
    titles = [entry["title"] for entry in data]
    best_match = difflib.get_close_matches(title, titles, n=1, cutoff=0.6)

    if best_match:
        matched_title = best_match[0]
        for entry in data:
            if entry["title"] == matched_title:
                return entry.get("user_id")

    return None


if __name__ == "__main__":
    user_id = get_user_id(torrent_name)

    if not user_id:
        print(f"⚠️ No requester found for {torrent_name}.\nSending notification to ADMINS only.")
        users = ADMINS
    else:
        print(f"✅ Found user_id {user_id} for {torrent_name}")
        if user_id not in ADMINS:
            print(f"User ID {user_id} not in ADMINS, sending notification to user + ADMINS.")
            users = ADMINS + [user_id]
        else:
            print(f"User ID {user_id} is already in ADMINS, sending notification from ADMINS list only.")
            users = ADMINS    

    asyncio.run(main(users))