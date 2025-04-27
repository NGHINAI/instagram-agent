import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Instagram credentials
IGusername = os.getenv("IGusername") or "default_IGusername"
IGpassword = os.getenv("IGpassword") or "default_IGpassword"

# Twitter credentials
Xusername = os.getenv("Xusername") or "default_Xusername"
Xpassword = os.getenv("Xpassword") or "default_Xpassword"

# Twitter API credentials
TWITTER_API_CREDENTIALS = {
    "appKey": os.getenv("TWITTER_API_KEY") or "default_TWITTER_API_KEY",
    "appSecret": os.getenv("TWITTER_API_SECRET") or "default_TWITTER_API_SECRET",
    "accessToken": os.getenv("TWITTER_ACCESS_TOKEN") or "default TWITTER_ACCESS_TOKEN",
    "accessTokenSecret": os.getenv("TWITTER_ACCESS_SECRET") or "default_TWITTER_ACCESS_SECRET",
    "bearerToken": os.getenv("TWITTER_BEARER_TOKEN") or "default_TWITTER_BEARER_TOKEN",
}

# Gemini API keys
gemini_api_keys = [
    os.getenv("GEMINI_API_KEY_1") or "API_KEY_1",
    os.getenv("GEMINI_API_KEY_2") or "API_KEY_2",
    os.getenv("GEMINI_API_KEY_3") or "API_KEY_3",
    os.getenv("GEMINI_API_KEY_4") or "API_KEY_4",
    os.getenv("GEMINI_API_KEY_5") or "API_KEY_5",
]