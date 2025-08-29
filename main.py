import webbrowser
from scraper import scrape_tpb
from agent import choose_best_with_groq
import json
import os

with open("config/config.json", "r") as f:
    config = json.load(f)

ACTIVE_REQUESTS_FILE = config["ACTIVE_REQUESTS_FILE"]

def update_json(title, title_type):
    """Add or update entry in classified.json"""
    data = []
    if os.path.exists(ACTIVE_REQUESTS_FILE):
        with open(ACTIVE_REQUESTS_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    # overwrite if title already exists
    updated = False
    for entry in data:
        if entry["title"] == title:
            entry["type"] = title_type
            updated = True
            break
    if not updated:
        data.append({"title": title, "type": title_type})

    with open(ACTIVE_REQUESTS_FILE, "w") as f:
        json.dump(data, f, indent=2)



def movie_agent(query, scraper="tpb"):
    top_n = 10
    print(f"Searching for: {query}")

    if scraper == "tpb":
        search_results = scrape_tpb(query)
        truncated_results = search_results[:top_n]
    else:
        raise ValueError(f"Unknown scraper: {scraper}")

    if not search_results:
        print("No results found.")
        return None

    print("Choosing best option with Groq...")
    result = choose_best_with_groq(truncated_results)
    magnet_link = result["magnet_link"]
    title = result["movie_title"]
    title_type = result["title_type"]

    print(f"Chosen title: {title}")
    print(f"Classification: {title_type}")
    print(f"Chosen Magnet link: {magnet_link}")
    if magnet_link.startswith("magnet:?"):
        print("Opening magnet link...")
        webbrowser.open(magnet_link)
        update_json(title, title_type)
        return title
    else:
        print("No valid magnet link returned.")



if __name__ == "__main__":
    movie_agent(input("Enter movie or TV show name: "))