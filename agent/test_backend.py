import logging
from database import DealershipDB
from knowledge import KnowledgeBase

# Configure simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-suite")

def test_rag():
    print("\n--- TESTING RAG (Vector Search) ---")
    kb = KnowledgeBase()
    
    # query matches one of the sentences we just seeded
    query = "What are your financing rates?"
    print(f"Query: {query}")
    
    result = kb.search(query)
    print(f"Result:\n{result}")
    
    if "2.9%" in result:
        print("✅ SUCCESS: Retrieved correct financing info.")
    else:
        print("❌ FAILURE: Could not find financing info.")

def test_db():
    print("\n--- TESTING MONGODB (Booking System) ---")
    db = DealershipDB()
    
    # 1. Test Availability
    date = "tomorrow at 10am"
    service = "Oil Change"
    is_free = db.check_availability(service, date)
    print(f"Slot '{date}' available? {is_free}")
    
    # 2. Test Booking (Write to DB)
    if is_free:
        booking_id = db.create_booking("Test User", "555-0199", service, date)
        print(f"Booking created with ID: {booking_id}")
        
        if booking_id and "mock" not in booking_id:
             print("✅ SUCCESS: Wrote to MongoDB Atlas.")
        elif "mock" in booking_id:
             print("⚠️ NOTE: Running in mock mode (Check MONGO_URI).")
        else:
             print("❌ FAILURE: Could not create booking.")

if __name__ == "__main__":
    test_rag()
    test_db()