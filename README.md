# Agent_Pirate
Agent to pirate and torrent movies and shows automatically by getting the name.


Agent_Pirate is a Telegram bot that allows users to search for and request movies or TV shows for automatic downloading via torrents magnet which gets added to the Jellefin Media Server Library.

## Features

- Search for movies and TV shows by name and find its torrent magnet link.
- Request downloads directly from Telegram.
- Restricted access to allowed users.

## Setup Instructions

1. **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/Agent_Pirate.git
    cd Agent_Pirate
    ```

2. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

    Install bittorrent
    Go to Download settings and disable the checkbox "Display torrent content and some options"

3. **Set environment variables**

    Create a `.env` file or set the following variables in your environment:
    - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
    - `TELEGRAM_USER_ID`: Your Telegram user ID (for access control).
    **You can use userinfobot in telegram to get your telegram id

4. **Download Start/Finish Alerts**
    Automatic alerts can be sent to the configured Telegram ID whenver torrent starts or finishes downloading the file.

    In the Downloads Settings of qbittorrent scroll to "Run External Program"
    
    Check "Run on torrent added" and write the command
    - <YOUR_VENV>/python3  <PROJECT_PATH>/notify_add.py "%F" "%N" "TELEGRAM_BOT_TOKEN" "TELEGRAM_USER_ID"

    Check "Run on torrent finished" and write the command
    - <YOUR_VENV>/python3 <PROJECT_PATH>/notify_finish.py "%F" "%N" "TELEGRAM_BOT_TOKEN" "TELEGRAM_USER_ID"

    Example:
    YOUR_VENV: /Users/ankit/Documents/Agent_Pirate/.venv/bin 
    PROJECT_PATH: /Users/ankit/Documents/Agent_Pirate

4. **Run the bot**
    ```bash
    python bot.py
    ```

## Usage

- `/start` – Start the bot and check authorization.
- `/request <MovieName>` – Search and request a movie or TV show.
- `/help` – Show usage instructions.

## Example

```
/request Inception
```

## ⚠️ Disclaimer

This project is for educational purposes only.
