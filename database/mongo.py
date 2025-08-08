import os
from pymongo.mongo_client import MongoClient

uri = os.getenv("MongoDB_URI")

client = MongoClient(uri)

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client['baobab_tech']
