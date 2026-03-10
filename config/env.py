from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    db_url = os.getenv("DB_URL")
    db_name = os.getenv("DB_NAME")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    environment = os.getenv("ENVIRONMENT")
    apify_token = os.getenv("APIFY_TOKEN")
