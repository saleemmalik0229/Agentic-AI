from abc import ABC, abstractmethod
from typing import Optional
import json
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

class BaseHistory(ABC):
    @abstractmethod
    async def get(self, query: str) -> Optional[str]:
        pass

    @abstractmethod
    async def set(self, query: str, answer: str):
        pass

class FileHistory(BaseHistory):
    """Legacy JSON implementation (Async wrapper)."""
    def __init__(self, storage_file: str = "query_history.json"):
        self.storage_file = storage_file
        # In-memory cache for speed
        self._cache = self._load()

    def _load(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        try:
            with open(self.storage_file, "w") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.error(f"Save failed: {e}")

    async def get(self, query: str) -> Optional[str]:
        return self._cache.get(query.strip().lower())

    async def set(self, query: str, answer: str):
        self._cache[query.strip().lower()] = answer
        self._save()

class PostgresHistory(BaseHistory):
    """Production-grade PostgreSQL implementation."""
    def __init__(self, connection_string: str):
        self.dsn = connection_string
        self.pool = None

    async def connect(self):
        import asyncpg
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(self.dsn)
                # Ensure table exists
                async with self.pool.acquire() as conn:
                    await conn.execute('''
                        CREATE TABLE IF NOT EXISTS query_history (
                            query_hash TEXT PRIMARY KEY,
                            query_text TEXT,
                            answer TEXT,
                            created_at TIMESTAMP DEFAULT NOW()
                        )
                    ''')
            except Exception as e:
                logger.error(f"Postgres connection failed: {e}")

    async def get(self, query: str) -> Optional[str]:
        if not self.pool:
            await self.connect()
        
        if not self.pool: return None
        
        q_hash = query.strip().lower() # Simple hash for now
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT answer FROM query_history WHERE query_hash = $1", q_hash)
            return row['answer'] if row else None

    async def set(self, query: str, answer: str):
         if not self.pool: return
         
         q_hash = query.strip().lower()
         async with self.pool.acquire() as conn:
             await conn.execute('''
                INSERT INTO query_history (query_hash, query_text, answer)
                VALUES ($1, $2, $3)
                ON CONFLICT (query_hash) DO UPDATE SET answer = $3
             ''', q_hash, query, answer)

# Factory
def get_history_manager(db_url: str = None) -> BaseHistory:
    if db_url and "postgres" in db_url:
        return PostgresHistory(db_url)
    return FileHistory()
