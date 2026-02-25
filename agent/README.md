- *Connection Pooling* (AsyncIOMotorClient) for MongoDB to handle high concurrency safely.

- *Idempotency Keys* (phone_date) to prevent double-booking race conditions.

- *State Management* (SessionManager) to act as a source of truth, preventing the LLM from hallucinating user details.

- *Local Embeddings* (SentenceTransformer) to reduce latency by avoiding an external API call for vector generation.