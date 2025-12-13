import logging
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Embedding generation utility using sentence transformers
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedding generator
        
        Popular models:
        - all-MiniLM-L6-v2 (384 dims, fast)
        - all-mpnet-base-v2 (768 dims, accurate)
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"✅ Embedding model loaded: {model_name} ({self.dimension}D)")
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text or list of texts
            normalize: Whether to normalize embeddings (for cosine similarity)
            batch_size: Batch size for processing
        
        Returns:
            numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100
        )
        
        return embeddings
    
    def encode_single(self, text: str, normalize: bool = True) -> List[float]:
        """Encode a single text and return as list"""
        embedding = self.encode(text, normalize=normalize)
        return embedding[0].tolist()
    
    def similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts"""
        emb1 = self.encode(text1, normalize=True)
        emb2 = self.encode(text2, normalize=True)
        
        # Cosine similarity (dot product of normalized vectors)
        similarity = float(np.dot(emb1[0], emb2[0]))
        
        return similarity
    
    def batch_similarity(
        self,
        query: str,
        candidates: List[str]
    ) -> List[float]:
        """Calculate similarity between query and multiple candidates"""
        query_emb = self.encode(query, normalize=True)
        candidate_embs = self.encode(candidates, normalize=True)
        
        # Dot product for cosine similarity
        similarities = np.dot(candidate_embs, query_emb[0])
        
        return similarities.tolist()