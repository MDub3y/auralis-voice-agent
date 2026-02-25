import os
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger("auralis-db")

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        
        self.uri = os.getenv("MONGO_URI")
        self.client = None
        self.db = None
        
        if self.uri:
            self.client = AsyncIOMotorClient(
                self.uri, 
                maxPoolSize=10, 
                minPoolSize=1,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client.get_database("dealership_core")
            self._initialized = True
            logger.info("✅ Async DB Connection Pool Initialized")
        else:
            logger.error("❌ Critical: MONGO_URI missing")

    async def health_check(self):
        try:
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False

    async def get_customer_by_lookup(self, identifier: str):
        # 🛡️ FIX: Explicit None check prevents the crash
        if self.db is None: return None
        
        return await self.db.customers.find_one({
            "$or": [
                {"phone": identifier},
                {"name": {"$regex": f"^{identifier}$", "$options": "i"}}
            ]
        })

    async def check_availability(self, date: str):
        if self.db is None: return False
        
        # 📅 LOGIC UPDATE: Allow up to 2 slots per day
        count = await self.db.bookings.count_documents({"date": date})
        
        logger.info(f"📅 Checking {date}: {count}/2 slots booked.")
        return count < 2

    async def create_booking(self, booking_data: dict):
        if self.db is None: return None
        
        idempotency_key = f"{booking_data['phone']}_{booking_data['date']}"
        booking_data['_id'] = idempotency_key 
        booking_data['created_at'] = datetime.utcnow()

        try:
            await self.db.bookings.insert_one(booking_data)
            return {"success": True, "id": idempotency_key}
        except DuplicateKeyError:
            return {"success": False, "error": "BOOKING_EXISTS"}
        except Exception as e:
            return {"success": False, "error": "DB_WRITE_FAILURE"}
        

    async def queue_booking_request(self, booking_data: dict):
        """
        Pushes the appointment payload to a staging collection (Queue).
        This does NOT touch the official 'bookings' calendar.
        """
        if self.db is None: return {"success": False, "error": "DB_DISCONNECTED"}
        
        # Enforce 'Pending' status
        booking_data['status'] = 'pending_validation'
        booking_data['submission_timestamp'] = datetime.utcnow()
        
        try:
            # We treat this collection as a FIFO queue
            result = await self.db.pending_requests.insert_one(booking_data)
            return {"success": True, "reference_id": str(result.inserted_id)}
        except Exception as e:
            logger.error(f"Queue push failed: {e}")
            return {"success": False, "error": "QUEUE_FAILURE"}