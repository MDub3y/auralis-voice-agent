import os
import logging
import certifi
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cloud-test")
logging.getLogger("pymongo").setLevel(logging.WARNING)

load_dotenv()

def test_cloud_connection():
    uri = os.getenv("MONGO_URI")
    
    if "localhost" in uri or "127.0.0.1" in uri:
        logger.error("❌ ERROR: Your .env is still pointing to Localhost.")
        logger.error("👉 Please comment out the local URI and uncomment the Cloud URI in .env")
        return

    logger.info(f"☁️  Attempting connection to Cloud...")

    try:
        client = MongoClient(
            uri, 
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsCAFile=certifi.where()
        )
        
        client.admin.command('ping')
        logger.info("✅ SUCCESS: Connected to MongoDB Atlas!")
        
        db = client.get_database("dealership_core")
        result = db.test_collection.insert_one({
            "status": "cloud_active", 
            "source": "python_script",
            "timestamp": datetime.now()
        })
        logger.info(f"✅ SUCCESS: Wrote to Cloud DB. ID: {result.inserted_id}")
        logger.info("👉 You can now check 'dealership_core' -> 'test_collection' in Compass.")
        
    except Exception as e:
        logger.error(f"❌ FAILURE: {e}")

if __name__ == "__main__":
    test_cloud_connection()