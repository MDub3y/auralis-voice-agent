import os
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# 1. Connect
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Define Knowledge
knowledge_base = [
    "We offer financing rates starting at 2.9% APR for qualified buyers.",
    "The showroom is open Monday to Saturday from 9 AM to 7 PM, and Sunday from 10 AM to 4 PM.",
    "We offer a comprehensive 3-year warranty on all certified pre-owned vehicles.",
    "Service appointments can be cancelled up to 24 hours in advance without a fee.",
    "The Rolls-Royce Phantom features a 6.75-liter V12 engine delivering 563 horsepower.",
    "Our trade-in policy guarantees a fair market value assessment valid for 7 days."
]

# 3. Upload
print("Generating embeddings...")
vectors = []
for i, text in enumerate(knowledge_base):
    embedding = model.encode(text).tolist()
    vectors.append({
        "id": f"vec_{i}",
        "values": embedding,
        "metadata": {"text": text}
    })

print("Upserting to Pinecone...")
index.upsert(vectors=vectors)
print("Done! Knowledge base is live.")