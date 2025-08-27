import webbrowser
from scraper import scrape_tpb
from agent import choose_best_with_groq

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
        return

    print("Choosing best option with Groq...")
    magnet_link = choose_best_with_groq(truncated_results)

    print(f"Chosen link: {magnet_link}")
    if magnet_link.startswith("magnet:?"):
        print("Opening magnet link in browser...")
        webbrowser.open(magnet_link)
    else:
        print("No valid magnet link returned.")

if __name__ == "__main__":
    movie_agent("Severance S01")
