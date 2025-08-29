import requests
import json
import os

with open("config/config.json", "r") as f:
    config = json.load(f)

GROQ_API_KEYS = os.getenv("GROQ_API_KEYS")
LIST_GROQ_API_KEYS = GROQ_API_KEYS.split(";")



url = config["groq_url"]  # Groq API endpoint
model = config["model"] # or another Groq model

def choose_best_title(search_results, preferences=None):

    # Default preferences if none passed
    if preferences is None:
        preferences = """
        - Prefer 1080p over 720p over others
        - Prefer x265 over x264 over others
        - Prefer BluRay over BrRip over WEBRip over others
        - Prefer file sizes between 1GB and 5GB for movies, no restriction for shows.
        - If multiple options tie, prefer the most recent Upload date.
        """

    system_prompt = f"""
    You are a movie selector agent.
    You will receive a JSON array of movie search results.
    Your task: pick the most ideal movie option based on these preferences:
    {preferences}
    If preferences conflict or not available, use your best judgement.
    Ensure that the option you pick matches with the query:
    (for example, if the query is a TV show, pick a TV show, if the query has Season 1 ensure its first season).
    Return only the chosen magnet:? link, the movie_title and title_type associated with it (do not explain).
    Always return in this specific clean json format with no nextlines, tabs or extra text:
    "magnet_link": "<the chosen magnet link>",
    "movie_title": "<the chosen movie/show full title as it is>"
    "size": "<File size as text (e.g., '1.2GB') only upto single decimal point>",
    "title_type": "<Movie or Show>"
    """

    # Rotate API keys to avoid rate limits
    for GROQ_API_KEY in LIST_GROQ_API_KEYS:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        try:
            payload = {
                "model": model, #"mixtral-8x7b-32768",  # or another Groq model
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(search_results)}
                ],
                "temperature": 0.0
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                break  # Successful request, exit the loop
            else:   
                print(f"API key failed with status {response.status_code}: {response.text}")

        except Exception as e:
            print(f"Error with API key...: {e}")

    response.raise_for_status()
    data = response.json()
    #print(data)  # Debug: print full response
    content = data["choices"][0]["message"]["content"]
    parsed_content = json.loads(content)
    best_link = parsed_content["magnet_link"].strip()
    title = parsed_content["movie_title"].strip()
    size = parsed_content.get("size", "NA").strip()
    title_type = parsed_content.get("title_type", "NA").strip()
    #print(f"Magnet Link: {best_link}")
    #print(f"Title: {title}")
    return {"magnet_link": best_link, "title": title, "size":size, "title_type": title_type}


def get_title_list(search_results):

    # Default preferences if none passe

    system_prompt = f"""
    You are a data formatting agent.
    Your task is to take scraped torrent search results received in JSON form and return a List of Python dictionary with the following structure of dictionary:
        "title": "<Exact Movie or Show Title>",
        "short_title": "<Shortened Title without extra tags>",
        "resolution": "<Resolution like 1080p or 720p>",
        "encoding": "<Encoding like x265 or x264> if available else keep blank",'",
        "source": "<Source like BluRay or WEBRip> if available else keep blank",
        "release_year": "<Release date in YYYY format> if available else keep blank",
        "magnet_link": "<Magnet link string>"
        "size": "<File size as text (e.g., '1.2GB') only upto single decimal point>",
        "title_type": "<Movie or Show>"
    
    The same dictionary structure should be repeated for each entry in the JSON (Example - If there are 5 movie titles in the JSON, return 5 dictionaries for each title in the list).    
    Return only the List of dictionaries in valid Python syntax with no extra text, no explanation, no nextlines, no tabs.
    """
    # Rotate API keys to avoid rate limits
    for GROQ_API_KEY in LIST_GROQ_API_KEYS:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        try:
            payload = {
                "model": model, #"mixtral-8x7b-32768",  # or another Groq model
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(search_results)}
                ],
                "temperature": 0.0
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                break  # Successful request, exit the loop
            else:   
                print(f"API key failed with status {response.status_code}: {response.text}")

        except Exception as e:
            print(f"Error with API key...: {e}")
    
    response.raise_for_status()
    data = response.json()
    #print(data)  # Debug: print full response
    content = data["choices"][0]["message"]["content"]
    print("DEBUG formatted_result type:", type(content))
    print("DEBUG first element:", content[0] if content else None)
    parsed_content = json.loads(content)
    #print(f"Title List: {content}")
    return parsed_content