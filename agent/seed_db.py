import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Connect
uri = os.getenv("MONGO_URI")
client = MongoClient(uri)
db = client.get_database("dealership_core")

def seed():
    print("🗑️  Cleaning old data...")
    db.bookings.delete_many({})
    db.customers.delete_many({})
    db.availability.delete_many({})

    print("🌱 Seeding Customers...")
    customers = [
        {
            "name": "Christina Yang",
            "phone": "9876543213",
            "email": "christina@grey-sloan.com",
            "vehicle": "Rolls-Royce Ghost",
            "vehicle_no": "KA-01-EQ-9999",
            "last_service": "2025-01-15",
            "vip_status": True
        },
        {
            "name": "Meredith Grey",
            "phone": "9876543210",
            "email": "meredith@grey-sloan.com",
            "vehicle": "Rolls-Royce Phantom",
            "vehicle_no": "DL-02-AB-0001",
            "last_service": "2024-11-20",
            "vip_status": True
        },
        {
            "name": "Derek Sheperd",
            "phone": "9876543211",
            "email": "derek@grey-sloan.com",
            "vehicle": "Rolls-Royce Spectre",
            "vehicle_no": "DL-02-AB-0002",
            "last_service": "2024-11-20",
            "vip_status": True
        },
        {
            "name": "Mark Sloan",
            "phone": "9876543212",
            "email": "mark@grey-sloan.com",
            "vehicle": "Rolls-Royce Cullinan",
            "vehicle_no": "DL-02-AB-0002",
            "last_service": "2024-11-20",
            "vip_status": True
        }
    ]
    db.customers.insert_many(customers)

    print("📅 Seeding Schedule...")
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    print("✅ Database Seeded!")
    print(f"👉 Setup: {len(customers)} customers created.")
    print(f"👉 Rule: Max capacity is set to 1 booking per day.")

if __name__ == "__main__":
    seed()