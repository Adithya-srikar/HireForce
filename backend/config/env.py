from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    db_url = os.getenv("DB_URL")
    db_name = os.getenv("DB_NAME")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    environment = os.getenv("ENVIRONMENT")
    apify_token = os.getenv("APIFY_TOKEN")
