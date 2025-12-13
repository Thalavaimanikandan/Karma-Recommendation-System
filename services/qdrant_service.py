import logging
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)


class QdrantService:
    """Qdrant vector database service"""
    
    def __init__(self, host: str = 'localhost', port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        logger.info(f"✅ Qdrant connected: {host}:{port}")
    
    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 384,
        distance: Distance = Distance.COSINE
    ):
        """Create a collection"""
        try:
            self.client.get_collection(collection_name)
            logger.info(f"Collection '{collection_name}' already exists")
        except:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance)
            )
            logger.info(f"✅ Created collection: {collection_name}")
    
    def upsert_points(
        self,
        collection_name: str,
        points: List[PointStruct]
    ):
        """Insert or update points"""
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """Search for similar vectors"""
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )
        return results
    
    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        self.client.delete_collection(collection_name)
    
    def close(self):
        """Close connection"""
        if self.client:
            self.client.close()