from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

# In a real scenario, we'd import: from langchain_community.vectorstores.pgvector import PGVector
# For this build, we implement the interface and a mock-capable structure.

logger = logging.getLogger(__name__)

class MemoryStore(ABC):
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]):
        pass
    
    @abstractmethod
    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        pass

class PGVectorMemory(MemoryStore):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        # self.vector_store = PGVector(connection_string=..., embedding_function=...)
        logger.info(f"Initialized PGVectorMemory with {connection_string}")

    async def add_documents(self, documents: List[Dict[str, Any]]):
        logger.info(f"Storing {len(documents)} documents to PGVector.")
        # Actual implementation:
        # texts = [d['content'] for d in documents]
        # metadatas = [d['metadata'] for d in documents]
        # self.vector_store.add_texts(texts, metadatas)
        pass

    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"Searching PGVector for: {query}")
        # Actual implementation:
        # docs = self.vector_store.similarity_search(query, k=k)
        # return [{"content": d.page_content, "metadata": d.metadata} for d in docs]
        return []

class LocalMemory(MemoryStore):
    """Simple in-memory list for testing/fallback."""
    def __init__(self):
        self.docs = []

    async def add_documents(self, documents: List[Dict[str, Any]]):
        self.docs.extend(documents)
        logger.info(f"Stored {len(documents)} docs locally.")

    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        # Naive keyword search
        results = []
        for d in self.docs:
            if query.lower() in d.get('content', '').lower():
                results.append(d)
        return results[:k]
