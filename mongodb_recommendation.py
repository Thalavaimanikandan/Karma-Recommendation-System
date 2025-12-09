import os
import logging
import pandas as pd
import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBRecommendationSystem:
    """
    Recommendation system using MongoDB data and sentence transformers
    """
    
    def __init__(self, 
                 mongo_uri='mongodb://localhost:27017/',
                 database_name='gorse_app',
                 collection_name='posts',
                 model_name='all-MiniLM-L6-v2'):
        """
        Initialize the recommendation system with MongoDB
        
        Args:
            mongo_uri (str): MongoDB connection string
            database_name (str): Database name
            collection_name (str): Collection name
            model_name (str): Sentence transformer model name
        """
        self.mongo_uri = mongo_uri
        self.database_name = database_name
        self.collection_name = collection_name
        self.model_name = model_name
        
        self.client = None
        self.db = None
        self.collection = None
        self.model = None
        self.df = None
        self.embeddings = None
        
        logger.info(f"🔧 Initializing MongoDB Recommendation System")
        logger.info(f"📊 Database: {database_name}")
        logger.info(f"📁 Collection: {collection_name}")
        
        # Connect to MongoDB
        self._connect_mongodb()
        
        # Load model
        self._load_model()
        
        # Load data from MongoDB
        self._load_data_from_mongodb()
    
    def _connect_mongodb(self):
        """Connect to MongoDB"""
        try:
            logger.info(f"🔌 Connecting to MongoDB: {self.mongo_uri}")
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.server_info()
            
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # Get collection count
            count = self.collection.count_documents({})
            logger.info(f"✅ Connected to MongoDB - Found {count} documents")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            logger.info(f"📥 Loading model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("✅ Model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def _load_data_from_mongodb(self):
        """Load data from MongoDB collection"""
        try:
            logger.info(f"📂 Loading data from MongoDB collection: {self.collection_name}")
            
            # Fetch all documents
            cursor = self.collection.find({})
            documents = list(cursor)
            
            if not documents:
                logger.warning("⚠️ No documents found in collection")
                self.df = pd.DataFrame()
                return
            
            # Convert to DataFrame
            self.df = pd.DataFrame(documents)
            logger.info(f"✅ Loaded {len(self.df)} documents")
            
            # Show columns
            logger.info(f"📋 Available columns: {list(self.df.columns)}")
            
            # Create text field for embedding
            self._create_text_field()
            
            # Generate embeddings
            self._generate_embeddings()
            
        except Exception as e:
            logger.error(f"❌ Failed to load data from MongoDB: {e}")
            raise
    
    def _create_text_field(self):
        """Create a combined text field for embedding"""
        try:
            # Common field names to combine
            text_fields = []
            
            # Check which fields exist and combine them
            possible_fields = ['title', 'content', 'description', 'body', 'text', 
                             'caption', 'post', 'message', 'category', 'tags']
            
            for field in possible_fields:
                if field in self.df.columns:
                    text_fields.append(field)
            
            if not text_fields:
                # If no text fields found, use all string columns
                text_fields = self.df.select_dtypes(include=['object']).columns.tolist()
                # Exclude _id and other system fields
                text_fields = [f for f in text_fields if f not in ['_id', 'id', 'created_at', 'updated_at']]
            
            logger.info(f"📝 Using fields for embedding: {text_fields}")
            
            # Combine text fields
            self.df['combined_text'] = self.df[text_fields].fillna('').astype(str).agg(' '.join, axis=1)
            
            # Clean text
            self.df['combined_text'] = self.df['combined_text'].str.strip()
            
            logger.info("✅ Combined text field created")
            
        except Exception as e:
            logger.error(f"❌ Failed to create text field: {e}")
            raise
    
    def _generate_embeddings(self):
        """Generate embeddings for all texts"""
        try:
            logger.info("🔄 Generating embeddings...")
            
            # Get texts
            texts = self.df['combined_text'].tolist()
            
            # Generate embeddings
            self.embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            
            logger.info(f"✅ Generated embeddings with shape: {self.embeddings.shape}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embeddings: {e}")
            raise
    
    def get_recommendations(self, query_text, top_k=5, filter_dict=None):
        """
        Get recommendations based on query text
        
        Args:
            query_text (str): Query text
            top_k (int): Number of recommendations to return
            filter_dict (dict): MongoDB filter for pre-filtering results
            
        Returns:
            pd.DataFrame: Top-k recommendations with similarity scores
        """
        try:
            if self.embeddings is None or len(self.embeddings) == 0:
                logger.error("❌ No embeddings available")
                return pd.DataFrame()
            
            # Apply MongoDB filter if provided
            df_filtered = self.df
            if filter_dict:
                # Convert filter to pandas query
                mask = pd.Series([True] * len(self.df))
                for key, value in filter_dict.items():
                    if key in self.df.columns:
                        mask &= (self.df[key] == value)
                df_filtered = self.df[mask]
                embeddings_filtered = self.embeddings[mask]
            else:
                embeddings_filtered = self.embeddings
            
            if len(df_filtered) == 0:
                logger.warning("⚠️ No documents match the filter")
                return pd.DataFrame()
            
            # Generate query embedding
            logger.info(f"🔍 Processing query: '{query_text}'")
            query_embedding = self.model.encode([query_text], convert_to_numpy=True)
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, embeddings_filtered)[0]
            
            # Get top-k indices
            top_k = min(top_k, len(similarities))
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            # Create result dataframe
            result_df = df_filtered.iloc[top_indices].copy()
            result_df['similarity_score'] = similarities[top_indices]
            
            # Convert ObjectId to string for JSON serialization
            if '_id' in result_df.columns:
                result_df['_id'] = result_df['_id'].astype(str)
            
            # Reset index
            result_df = result_df.reset_index(drop=True)
            
            logger.info(f"✅ Found {len(result_df)} recommendations")
            
            return result_df
            
        except Exception as e:
            logger.error(f"❌ Error in get_recommendations: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def recommend(self, text, top_k=5, category=None):
        """
        Alias for get_recommendations
        
        Args:
            text (str): Query text
            top_k (int): Number of recommendations
            category (str): Category filter (optional)
            
        Returns:
            pd.DataFrame: Recommendations
        """
        filter_dict = {'category': category} if category else None
        return self.get_recommendations(text, top_k, filter_dict)
    
    def refresh_data(self):
        """Refresh data from MongoDB"""
        logger.info("🔄 Refreshing data from MongoDB...")
        self._load_data_from_mongodb()
        logger.info("✅ Data refreshed successfully")
    
    def get_categories(self):
        """Get unique categories from the data"""
        if 'category' in self.df.columns:
            return self.df['category'].unique().tolist()
        return []
    
    def get_stats(self):
        """Get system statistics"""
        stats = {
            'total_documents': len(self.df) if self.df is not None else 0,
            'embedding_dimension': self.embeddings.shape[1] if self.embeddings is not None else 0,
            'model_name': self.model_name,
            'database': self.database_name,
            'collection': self.collection_name,
            'categories': self.get_categories(),
            'available_fields': list(self.df.columns) if self.df is not None else []
        }
        return stats
    
    def save_embeddings(self, filepath='models/mongodb_embeddings.pkl'):
        """Save embeddings to file"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            data = {
                'embeddings': self.embeddings,
                'df': self.df,
                'model_name': self.model_name,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"✅ Embeddings saved to: {filepath}")
        except Exception as e:
            logger.error(f"❌ Failed to save embeddings: {e}")
    
    def load_embeddings(self, filepath='models/mongodb_embeddings.pkl'):
        """Load embeddings from file"""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.embeddings = data['embeddings']
            self.df = data['df']
            self.model_name = data['model_name']
            
            logger.info(f"✅ Embeddings loaded from: {filepath}")
            logger.info(f"📅 Saved at: {data.get('timestamp', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load embeddings: {e}")
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("🔌 MongoDB connection closed")


# Test function
def test_mongodb_recommendation():
    """Test the MongoDB recommendation system"""
    try:
        # Initialize system - UPDATE THESE VALUES!
        recommender = MongoDBRecommendationSystem(
            mongo_uri='mongodb://localhost:27017/',
            database_name='test_db',      # ⚠️ Change this to your database name
            collection_name='posts'       # ⚠️ Change this to your collection name
        )
        
        # Get stats
        stats = recommender.get_stats()
        print("\n" + "="*70)
        print("📊 System Statistics:")
        print("="*70)
        for key, value in stats.items():
            if isinstance(value, list) and len(value) > 5:
                print(f"{key}: {value[:5]}... (showing first 5)")
            else:
                print(f"{key}: {value}")
        print("="*70)
        
        # Test recommendation
        query = "technology"
        print(f"\n🔍 Testing query: '{query}'")
        results = recommender.get_recommendations(query, top_k=5)
        
        print("\n" + "="*70)
        print(f"📋 Top 5 Recommendations for: '{query}'")
        print("="*70)
        
        if not results.empty:
            # Show only relevant columns
            display_cols = [col for col in results.columns 
                          if col not in ['combined_text', 'embeddings']]
            display_cols = display_cols[:5] + ['similarity_score']  # Show first 5 columns + score
            
            for idx, row in results.iterrows():
                print(f"\n#{idx + 1} (Score: {row['similarity_score']:.4f})")
                for col in display_cols:
                    if col in row and col != 'similarity_score':
                        value = str(row[col])[:100]  # Limit length
                        print(f"  {col}: {value}")
        else:
            print("❌ No results found")
        
        print("="*70)
        
        # Close connection
        recommender.close()
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("="*70)
    print("🚀 MongoDB Recommendation System - Test Mode")
    print("="*70)
    print("\n⚠️  Before running, update these values in the code:")
    print("   - database_name")
    print("   - collection_name")
    print("   - mongo_uri (if different)\n")
    
    test_mongodb_recommendation()