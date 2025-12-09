import os
import logging
import pandas as pd
import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
from collections import Counter
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedMongoDBRecommendationSystem:
    def __init__(self, mongo_uri='mongodb://localhost:27017/', database_name='gorse_app', collection_name='posts', model_name='all-MiniLM-L6-v2'):
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
        self.category_keywords = {}
        self.stop_words = {'the','is','at','which','on','a','an','and','or','but','in','with','to','for','of','as','by','from','that','this','these','those','are','was','were','been','be','have','has','had','do','does','did','will','would','should','could','may','might','can','it','its','about','into','through','during','before','after','above','below','up','down','out','off','over','under','again','further','then','once','here','there','when','where','why','how','all','both','each','few','more','most','other','some','such','no','nor','not','only','own','same','so','than','too','very','just','now'}
        logger.info("🔧 Initializing Advanced MongoDB Recommendation System")
        self._connect_mongodb()
        self._load_sentence_model()
        self._load_data_from_mongodb()
        self._build_category_index()
    
    def _connect_mongodb(self):
        try:
            logger.info("🔌 Connecting to MongoDB...")
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.client.server_info()
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            count = self.collection.count_documents({})
            logger.info(f"✅ Connected - Found {count} documents")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    def _load_sentence_model(self):
        try:
            logger.info(f"📥 Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("✅ Embedding model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def _load_data_from_mongodb(self):
        try:
            logger.info(f"📂 Loading data from collection: {self.collection_name}")
            cursor = self.collection.find({})
            documents = list(cursor)
            if not documents:
                logger.warning("⚠️ No documents found")
                self.df = pd.DataFrame()
                return
            self.df = pd.DataFrame(documents)
            logger.info(f"✅ Loaded {len(self.df)} documents")
            logger.info(f"📋 Columns: {list(self.df.columns)}")
            self._create_text_field()
            self._generate_embeddings()
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            raise
    
    def _create_text_field(self):
        try:
            text_fields = []
            priority_fields = ['title','body','content','description','category','tags']
            for field in priority_fields:
                if field in self.df.columns:
                    text_fields.append(field)
            logger.info(f"📝 Combining fields: {text_fields}")
            if 'tags' in self.df.columns:
                self.df['tags_str'] = self.df['tags'].apply(lambda x: ' '.join(x) if isinstance(x, list) else str(x))
                if 'tags_str' not in text_fields:
                    text_fields.append('tags_str')
            self.df['combined_text'] = self.df[text_fields].fillna('').astype(str).agg(' '.join, axis=1)
            self.df['combined_text'] = self.df['combined_text'].str.strip()
            logger.info("✅ Combined text field created")
        except Exception as e:
            logger.error(f"❌ Failed to create text field: {e}")
            raise
    
    def _generate_embeddings(self):
        try:
            logger.info("🔄 Generating embeddings...")
            texts = self.df['combined_text'].tolist()
            self.embeddings = self.model.encode(texts, batch_size=32, show_progress_bar=True, convert_to_numpy=True)
            logger.info(f"✅ Embeddings generated: {self.embeddings.shape}")
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            raise
    
    def extract_keywords(self, text, top_n=10):
        try:
            text = text.lower()
            words = re.findall(r'\b[a-z]{3,}\b', text)
            keywords = [w for w in words if w not in self.stop_words]
            word_freq = Counter(keywords)
            top_keywords = [word for word, _ in word_freq.most_common(top_n)]
            return top_keywords
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            return []
    
    def _build_category_index(self):
        try:
            if 'category' not in self.df.columns:
                logger.warning("⚠️ No category column")
                return
            logger.info("🔨 Building category keyword index...")
            for category in self.df['category'].unique():
                if pd.isna(category):
                    continue
                category_posts = self.df[self.df['category'] == category]
                all_keywords = []
                for _, post in category_posts.iterrows():
                    text = post['combined_text']
                    keywords = self.extract_keywords(text)
                    all_keywords.extend(keywords)
                keyword_freq = Counter(all_keywords)
                top_keywords = [word for word, _ in keyword_freq.most_common(20)]
                self.category_keywords[category] = top_keywords
                logger.info(f"  {category}: {', '.join(top_keywords[:5])}...")
            logger.info("✅ Category index built")
        except Exception as e:
            logger.error(f"❌ Failed to build category index: {e}")
    
    def detect_category(self, query):
        try:
            query_keywords = self.extract_keywords(query)
            if not query_keywords:
                return None
            category_scores = {}
            for category, keywords in self.category_keywords.items():
                matches = sum(1 for qk in query_keywords if qk in keywords)
                if matches > 0:
                    category_scores[category] = matches / len(query_keywords)
            if category_scores:
                best_category = max(category_scores, key=category_scores.get)
                if category_scores[best_category] > 0.3:
                    logger.info(f"🎯 Detected category: {best_category}")
                    return best_category
            return None
        except Exception as e:
            logger.error(f"Category detection error: {e}")
            return None
    
    def smart_search(self, query, top_k=5, auto_detect_category=True, category_filter=None):
        try:
            if self.embeddings is None or len(self.embeddings) == 0:
                logger.error("❌ No embeddings available")
                return pd.DataFrame(), [], None
            logger.info(f"🔍 Smart search: '{query}'")
            keywords = self.extract_keywords(query)
            logger.info(f"📝 Keywords: {keywords}")
            detected_category = None
            if auto_detect_category and not category_filter:
                detected_category = self.detect_category(query)
            final_category = category_filter or detected_category
            enhanced_query = ' '.join(keywords) if keywords else query
            df_filtered = self.df
            embeddings_filtered = self.embeddings
            if final_category and 'category' in self.df.columns:
                logger.info(f"🎯 Filtering by: {final_category}")
                mask = self.df['category'] == final_category
                df_filtered = self.df[mask]
                embeddings_filtered = self.embeddings[mask]
            if len(df_filtered) == 0:
                return pd.DataFrame(), keywords, final_category
            query_embedding = self.model.encode([enhanced_query], convert_to_numpy=True)
            similarities = cosine_similarity(query_embedding, embeddings_filtered)[0]
            for idx, row in df_filtered.iterrows():
                text = row['combined_text'].lower()
                boost = sum(0.1 for kw in keywords if kw in text)
                similarities[df_filtered.index.get_loc(idx)] += boost
            top_k = min(top_k, len(similarities))
            top_indices = similarities.argsort()[-top_k:][::-1]
            result_df = df_filtered.iloc[top_indices].copy()
            result_df['similarity_score'] = similarities[top_indices]
            result_df['matched_keywords'] = result_df['combined_text'].apply(lambda x: [kw for kw in keywords if kw in x.lower()])
            if '_id' in result_df.columns:
                result_df['_id'] = result_df['_id'].astype(str)
            result_df = result_df.reset_index(drop=True)
            logger.info(f"✅ Found {len(result_df)} results")
            return result_df, keywords, final_category
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame(), [], None
    
    def recommend(self, text, top_k=5, category=None, auto_detect=True):
        results, keywords, detected_cat = self.smart_search(text, top_k=top_k, auto_detect_category=auto_detect, category_filter=category)
        return results, keywords, detected_cat
    
    def get_recommendations(self, query_text, top_k=5, filter_dict=None):
        results, _, _ = self.smart_search(query_text, top_k)
        return results
    
    def refresh_data(self):
        logger.info("🔄 Refreshing...")
        self._load_data_from_mongodb()
        self._build_category_index()
    
    def get_categories(self):
        if 'category' in self.df.columns:
            return self.df['category'].unique().tolist()
        return []
    
    def get_stats(self):
        return {'total_documents':len(self.df) if self.df is not None else 0,'embedding_dimension':self.embeddings.shape[1] if self.embeddings is not None else 0,'model_name':self.model_name,'database':self.database_name,'collection':self.collection_name,'categories':self.get_categories(),'category_keywords':{k:v[:5] for k,v in self.category_keywords.items()},'available_fields':list(self.df.columns) if self.df is not None else []}
    
    def close(self):
        if self.client:
            self.client.close()
            logger.info("🔌 Connection closed")

def test_advanced_system():
    try:
        recommender = AdvancedMongoDBRecommendationSystem(mongo_uri='mongodb://localhost:27017/',database_name='gorse_app',collection_name='posts')
        test_queries = ["yoga is a meditation and health exercise","bat cricket sports","python programming technology","event news update"]
        print("\n"+"="*70)
        print("🧪 Testing Advanced Recommendation System")
        print("="*70)
        for query in test_queries:
            print(f"\n📝 Query: '{query}'")
            results, keywords, category = recommender.smart_search(query, top_k=3)
            print(f"🔑 Keywords: {keywords}")
            print(f"🎯 Category: {category or 'Not detected'}")
            print(f"📊 Results: {len(results)}")
            if not results.empty:
                for idx, row in results.iterrows():
                    print(f"  #{idx+1} {row['title']} (Score: {row['similarity_score']:.3f})")
                    if row['matched_keywords']:
                        print(f"      Matched: {row['matched_keywords']}")
        print("="*70)
        print("\n✅ Test completed successfully!")
        recommender.close()
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_advanced_system()
