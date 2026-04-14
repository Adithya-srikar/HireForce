from pymongo import MongoClient
from config.env import Config

client = MongoClient(Config.db_url)
db = client[Config.db_name]

def get_db():
    print("connected to db")
    return db