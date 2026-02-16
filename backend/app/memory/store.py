import chromadb
from chromadb.config import Settings
from ..config import config


class MemoryStore:
    def __init__(self):
        try:
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=config.CHROMA_PATH
            ))
            self.collection = self.client.get_or_create_collection(
                name="memories"
            )
            self.available = True
        except:
            self.available = False
            self.collection = None

    def add(self, agent_id: str, text: str, emotion: str):
        if not self.available:
            return
        try:
            self.collection.add(
                documents=[text],
                metadatas=[{"agent_id": agent_id, "emotion": emotion}],
                ids=[f"{agent_id}_{datetime.now().timestamp()}"]
            )
        except:
            pass

    def search(self, agent_id: str, query: str, n: int = 3):
        if not self.available:
            return []
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n,
                where={"agent_id": agent_id}
            )
            return results['documents'][0] if results['documents'] else []
        except:
            return []


memory_store = MemoryStore()