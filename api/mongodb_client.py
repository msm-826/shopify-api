from pymongo import MongoClient
from decouple import config
from django.conf import settings
import os

if settings.DEBUG:
    client = MongoClient(config('MONGODB_URL'))
else:
    client = MongoClient(os.environ.get("MONGODB_URL"))
db = client['RQ_Analytics']

def get_collection(collection_name):
    return db[collection_name]