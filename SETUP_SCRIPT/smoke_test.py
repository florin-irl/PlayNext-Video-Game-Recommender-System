import os, requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

cid = os.getenv("TWITCH_CLIENT_ID")
sec = os.getenv("TWITCH_CLIENT_SECRET")
assert cid and sec, "Missing TWITCH_CLIENT_ID/SECRET in .env"

tok = requests.post("https://id.twitch.tv/oauth2/token",
    params={"client_id": cid, "client_secret": sec, "grant_type": "client_credentials"},
    timeout=30).json()["access_token"]

q = """fields id,name,cover.image_id;
       sort total_rating_count desc;
       where cover != null;
       limit 5;"""
resp = requests.post("https://api.igdb.com/v4/games", data=q,
                     headers={"Client-ID": cid, "Authorization": f"Bearer {tok}"}, timeout=60)
print(resp.status_code)
print(resp.json())
