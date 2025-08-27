import requests
from bs4 import BeautifulSoup

#thepiratebay
def scrape_tpb(query):
    """
    Scraper for mymovies.com search results.
    Returns JSON-like list of rows.
    """
    url = f"https://thepiratebay11.com/search/{query}/1/99/200"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", {"id": "searchResult"})
    if not table:
        return []

    rows = []
    for tr in table.find_all("tr"):
        cells = []
        for td in tr.find_all(["td", "th"]):
            text = td.get_text(strip=True)
            links = [a["href"] for a in td.find_all("a", href=True)]
            cells.append({"text": text, "links": links})
        if cells:
            rows.append(cells)
    return rows

# Future scrapers can be added here:
# def scrape_other_site(query): ...
