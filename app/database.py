from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING


MONGO_URL = "mongodb://sampleuser:samplepass@localhost:27017/sampledb"

client = AsyncIOMotorClient(MONGO_URL)
database = client.sampledb

user_collection = database.get_collection("user")
user_collection.create_index([("email", ASCENDING)], unique=True)
user_collection.create_index([("username", ASCENDING)], unique=True)

company_collection = database.get_collection("company")
company_collection.create_index([("user_id", ASCENDING)])