from telegram import Bot
import asyncio
import sys

torrent_path = sys.argv[1]   # %F
torrent_name = sys.argv[2]  # %N

# file_path = "/Users/ankit/Documents/Agent_Pirate/output.txt"
# with open(file_path, "a") as f:
#     f.write(f"Started Downloading: {torrent_name} at {torrent_path}\n")

BOT_TOKEN = sys.argv[3]
CHAT_ID = sys.argv[4]

async def main():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=f"🔔 Alert!!!\nStarted Downloading: {torrent_name}\n")

if __name__ == "__main__":
    asyncio.run(main())