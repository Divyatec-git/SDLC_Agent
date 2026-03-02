# db/connection.py

from pymongo import MongoClient

_client = None
_db = None

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "sdlc"


def get_client() -> MongoClient:
    """Returns a singleton MongoClient instance."""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client


def get_db():
    """Returns the 'sdlc' database handle."""
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db
