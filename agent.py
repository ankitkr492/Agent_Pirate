import requests
import json
import os

def choose_best_with_groq(search_results, preferences=None):

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"

    # Default preferences if none passed
    if preferences is None:
        preferences = """
        - Prefer 1080p over 720p over others
        - Prefer x265 over x264 over others
        - Prefer BluRay over BrRip over WEBRip over others
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
    Return only the chosen magnet:? link and the movie_title associated with it (do not explain).
    Always return in this specific clean json format with no nextlines, tabs or extra text:
    "magnet_link": "<the chosen magnet link>",
    "movie_title": "<the chosen movie/show title>"
    "title_type": "<Movie or Show>"
    """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile", #"mixtral-8x7b-32768",  # or another Groq model
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(search_results)}
        ],
        "temperature": 0.0
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    #print(data)  # Debug: print full response
    content = data["choices"][0]["message"]["content"]
    parsed_content = json.loads(content)
    best_link = parsed_content["magnet_link"].strip()
    title = parsed_content["movie_title"].strip()
    title_type = parsed_content.get("title_type", "Unknown").strip()
    #print(f"Magnet Link: {best_link}")
    #print(f"Title: {title}")
    return {"magnet_link": best_link, "movie_title": title, "title_type": title_type}