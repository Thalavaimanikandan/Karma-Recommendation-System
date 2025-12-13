import logging
from typing import List, Dict, Optional
from pymongo import MongoClient

logger = logging.getLogger(__name__)

class MongoDBService:
    """MongoDB connection and basic CRUD operations"""

    def __init__(self, mongo_uri: str, db_name: str):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        logger.info(f"✅ MongoDB connected: {db_name}")

    def get_collection(self, collection_name: str):
        """Return MongoDB collection"""
        return self.db[collection_name]

    # ---------- CRUD ----------
    
    def insert_one(self, collection: str, document: Dict) -> str:
        result = self.db[collection].insert_one(document)
        return str(result.inserted_id)

    def insert_many(self, collection: str, documents: List[Dict]) -> List[str]:
        result = self.db[collection].insert_many(documents)
        return [str(_id) for _id in result.inserted_ids]

    def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        return self.db[collection].find_one(query)

    def find(self, collection: str, query: Dict, limit: int = 100) -> List[Dict]:
        return list(self.db[collection].find(query).limit(limit))

    def update_one(self, collection: str, query: Dict, update: Dict):
        return self.db[collection].update_one(query, update)

    def delete_one(self, collection: str, query: Dict):
        return self.db[collection].delete_one(query)

    def close(self):
        if self.client:
            self.client.close()
