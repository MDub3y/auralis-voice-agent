import os
import logging
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("auralis-rag")

class KnowledgeBase:
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX", "dealership-knowledge")
        self.pc = None
        self.index = None
        
        # 1. Initialize Local Embedding Model
        # This downloads the model (approx 80MB) on first run and runs on CPU.
        # It's fast enough for real-time voice latency.
        try:
            logger.info("Loading local embedding model...")
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedder = None

        # 2. Initialize Pinecone
        if self.api_key:
            try:
                self.pc = Pinecone(api_key=self.api_key)
                self.index = self.pc.Index(self.index_name)
                logger.info("Connected to Pinecone.")
            except Exception as e:
                logger.error(f"Pinecone connection failed: {e}")

    def search(self, query: str):
        """
        Generates local embedding and searches Pinecone.
        """
        if not self.index or not self.embedder:
            return "I currently don't have access to the detailed policy manuals."

        try:
            # 1. Generate Embedding Locally (No API Call)
            # .tolist() is required because Pinecone expects a list, not a numpy array
            xb = self.embedder.encode(query).tolist()

            # 2. Query Pinecone
            results = self.index.query(
                vector=xb,
                top_k=3,
                include_metadata=True
            )

            # 3. Format Context
            matches = [match['metadata']['text'] for match in results['matches'] if 'text' in match['metadata']]
            
            if not matches:
                return "No specific policies found."
                
            return "\n".join(matches)

        except Exception as e:
            logger.error(f"RAG Error: {e}")
            return "Information currently unavailable."