#!/usr/bin/env python3
"""
Sync MongoDB data to Gorse recommendation system
Fully corrected version
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict

import requests
from pymongo import MongoClient

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "recommendation_db"

USERS_COLLECTION = "users"
POSTS_COLLECTION = "posts"
INTERACTIONS_COLLECTION = "interactions"

GORSE_URL = "http://localhost:8087"
GORSE_API_KEY = os.getenv("GORSE_API_KEY", None)  # Optional

# ---------------------------------------------------------
# LOGGER
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# MONGO CLIENT
# ---------------------------------------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def send_post(endpoint: str, payload: Dict):
    headers = {"Content-Type": "application/json"}
    if GORSE_API_KEY:
        headers["X-API-Key"] = GORSE_API_KEY
    try:
        response = requests.post(f"{GORSE_URL}{endpoint}", json=payload, headers=headers, timeout=10)
        return response
    except Exception as e:
        logger.error(f"Failed POST {endpoint}: {e}")
        return None

def iso_timestamp(ts):
    if isinstance(ts, datetime):
        return ts.isoformat()
    return datetime.utcnow().isoformat()

# ---------------------------------------------------------
# USER SYNC
# ---------------------------------------------------------
def sync_users():
    users = list(db[USERS_COLLECTION].find())
    logger.info(f"📌 Found {len(users)} users in MongoDB")

    success = 0
    failed = 0

    for u in users:
        user_id = str(u.get("_id") or u.get("user_id"))
        labels = u.get("interests", [])

        payload = {
            "UserId": user_id,
            "Labels": labels,
            "Comment": "Synced from MongoDB"
        }

        r = send_post("/api/user", payload)
        if r and r.status_code in (200, 201):
            logger.info(f"✅ Synced user {user_id}")
            success += 1
        else:
            logger.error(f"❌ Failed user {user_id}: {r.text if r else 'No response'}")
            failed += 1

    logger.info(f"✔ USER SYNC DONE → {success} success / {failed} failed")

# ---------------------------------------------------------
# POST / ITEM SYNC
# ---------------------------------------------------------
def sync_posts():
    posts = list(db[POSTS_COLLECTION].find())
    logger.info(f"📝 Found {len(posts)} posts")

    success = 0
    failed = 0

    for post in posts:
        post_id = str(post["_id"])
        category = post.get("category", "general")
        ts = iso_timestamp(post.get("created_at"))

        payload = {
            "ItemId": post_id,
            "Categories": [category],
            "Labels": [category],
            "Timestamp": ts,
            "Comment": post.get("title", "")[:200]
        }

        r = send_post("/api/item", payload)
        if r and r.status_code in (200, 201):
            success += 1
            logger.info(f"📌 Item synced {post_id}")
        else:
            logger.error(f"❌ Failed item {post_id}: {r.text if r else 'No response'}")
            failed += 1

    logger.info(f"✔ ITEM SYNC DONE → {success} success / {failed} failed")

# ---------------------------------------------------------
# FEEDBACK / INTERACTIONS SYNC
# ---------------------------------------------------------
def sync_feedback(batch_size: int = 100):
    interactions = list(db[INTERACTIONS_COLLECTION].find())
    total_events = 0
    batch: List[Dict] = []

    for inter in interactions:
        total_events += 1
        user_id = str(inter.get("user_id"))
        item_id = str(inter.get("post_id") or inter.get("item_id"))
        if not user_id or not item_id:
            continue

        itype = inter.get("interaction_type", "view")
        ftype = {"view": "read", "click": "read", "like": "star"}.get(itype, "read")
        ts = iso_timestamp(inter.get("timestamp"))

        batch.append({
            "FeedbackType": ftype,
            "UserId": user_id,
            "ItemId": item_id,
            "Timestamp": ts
        })

        if len(batch) >= batch_size:
            send_post("/api/feedback", batch)
            batch = []

    if batch:
        send_post("/api/feedback", batch)

    logger.info(f"✔ FEEDBACK SYNC DONE → {total_events} events")

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    logger.info("="*60)
    logger.info("🚀 Starting MongoDB → Gorse sync")
    logger.info("="*60)

    sync_users()
    sync_posts()
    sync_feedback()

    logger.info("🎉 All sync completed successfully!")

if __name__ == "__main__":
    main()
