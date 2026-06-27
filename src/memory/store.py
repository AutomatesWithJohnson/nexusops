"""Memory store with Redis (short-term) and PostgreSQL+pgvector (long-term)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Optional

import redis.asyncio as redis
import structlog

from src.config import settings

logger = structlog.get_logger()


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    content: str
    category: str  # customer, interaction, preference, fact
    source_agent: str
    customer_id: Optional[str] = None
    embedding: Optional[list[float]] = None
    score: float = 1.0
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    metadata: dict = field(default_factory=dict)


class MemoryStore:
    """Dual-layer memory: Redis for short-term, PostgreSQL+pgvector for long-term.

    Short-term (Redis):
    - Current conversation context
    - Recent interactions (last 24h)
    - Active task state

    Long-term (PostgreSQL + pgvector):
    - Customer profiles
    - Historical interactions with embeddings
    - Learned preferences and patterns
    - Semantic search across all memories
    """

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.db_pool = None  # asyncpg pool, initialized in setup()
        self._initialized = False

    async def setup(self):
        """Initialize connections."""
        # Redis connection
        self.redis = redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        # Verify connection
        try:
            await self.redis.ping()
            logger.info("redis_connected")
        except Exception as e:
            logger.warning("redis_connection_failed", error=str(e))

        # PostgreSQL connection (asyncpg)
        try:
            import asyncpg
            self.db_pool = await asyncpg.create_pool(
                dsn=settings.postgres_url.replace("+asyncpg", ""),
                min_size=2,
                max_size=10,
            )
            await self._ensure_tables()
            logger.info("postgres_connected")
        except Exception as e:
            logger.warning("postgres_connection_failed", error=str(e))

        self._initialized = True

    async def _ensure_tables(self):
        """Create tables if they don't exist."""
        if not self.db_pool:
            return

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    source_agent TEXT NOT NULL,
                    customer_id TEXT,
                    embedding vector(1024),
                    score FLOAT DEFAULT 1.0,
                    created_at DOUBLE PRECISION NOT NULL,
                    accessed_at DOUBLE PRECISION NOT NULL,
                    access_count INT DEFAULT 0,
                    metadata JSONB DEFAULT '{}'
                );
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_customer
                ON memories (customer_id);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_category
                ON memories (category);
            """)

    async def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry in both Redis (short-term) and PostgreSQL (long-term)."""
        entry_id = entry.id or f"mem_{int(time.time())}_{hash(entry.content) % 10000}"
        entry.id = entry_id

        # Store in Redis with TTL (24h)
        if self.redis:
            try:
                key = f"memory:{entry_id}"
                data = json.dumps({
                    "id": entry.id,
                    "content": entry.content,
                    "category": entry.category,
                    "source_agent": entry.source_agent,
                    "customer_id": entry.customer_id,
                    "score": entry.score,
                    "created_at": entry.created_at,
                })
                await self.redis.setex(key, 86400, data)

                # Also add to customer timeline
                if entry.customer_id:
                    await self.redis.lpush(
                        f"customer:{entry.customer_id}:timeline",
                        entry_id,
                    )
                    await self.redis.ltrim(
                        f"customer:{entry.customer_id}:timeline",
                        0,
                        99,  # Keep last 100 interactions
                    )
            except Exception as e:
                logger.warning("redis_store_failed", error=str(e))

        # Store in PostgreSQL with embedding
        if self.db_pool and entry.embedding:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO memories (id, content, category, source_agent,
                            customer_id, embedding, score, created_at, accessed_at, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8, $9, $10)
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            score = EXCLUDED.score,
                            accessed_at = EXCLUDED.accessed_at
                        """,
                        entry.id,
                        entry.content,
                        entry.category,
                        entry.source_agent,
                        entry.customer_id,
                        str(entry.embedding),
                        entry.score,
                        entry.created_at,
                        entry.accessed_at,
                        json.dumps(entry.metadata),
                    )
            except Exception as e:
                logger.warning("postgres_store_failed", error=str(e))

        return entry_id

    async def search(
        self,
        query: str,
        limit: int = 5,
        customer_id: Optional[str] = None,
        category: Optional[str] = None,
        min_score: float = 0.3,
    ) -> list[dict]:
        """Search memories using semantic similarity.

        Falls back to Redis recent entries if PostgreSQL is unavailable.
        """
        results = []

        # Try semantic search via pgvector
        if self.db_pool:
            try:
                # Generate embedding for query
                query_embedding = await self._get_embedding(query)
                if query_embedding:
                    async with self.db_pool.acquire() as conn:
                        rows = await conn.fetch(
                            """
                            SELECT id, content, category, customer_id, score,
                                   created_at, 1 - (embedding <=> $1::vector) as similarity
                            FROM memories
                            WHERE 1 - (embedding <=> $1::vector) > $2
                            ORDER BY embedding <=> $1::vector
                            LIMIT $3
                            """,
                            str(query_embedding),
                            min_score,
                            limit,
                        )
                        for row in rows:
                            results.append({
                                "id": row["id"],
                                "content": row["content"],
                                "category": row["category"],
                                "customer_id": row["customer_id"],
                                "score": float(row["similarity"]),
                                "created_at": row["created_at"],
                            })
            except Exception as e:
                logger.warning("semantic_search_failed", error=str(e))

        # Fallback: recent entries from Redis
        if not results and self.redis and customer_id:
            try:
                timeline = await self.redis.lrange(
                    f"customer:{customer_id}:timeline", 0, limit - 1
                )
                for mem_id in timeline:
                    data = await self.redis.get(f"memory:{mem_id}")
                    if data:
                        results.append(json.loads(data))
            except Exception as e:
                logger.warning("redis_search_failed", error=str(e))

        return results

    async def get_customer_context(self, customer_id: str, max_memories: int = 10) -> dict:
        """Get full context for a customer from memory."""
        context = {
            "customer_id": customer_id,
            "recent_interactions": [],
            "preferences": {},
            "total_interactions": 0,
        }

        if self.redis:
            try:
                # Get recent interactions
                timeline = await self.redis.lrange(
                    f"customer:{customer_id}:timeline", 0, max_memories - 1
                )
                for mem_id in timeline:
                    data = await self.redis.get(f"memory:{mem_id}")
                    if data:
                        context["recent_interactions"].append(json.loads(data))

                # Get interaction count
                count = await self.redis.llen(f"customer:{customer_id}:timeline")
                context["total_interactions"] = count

                # Get stored preferences
                prefs = await self.redis.hgetall(f"customer:{customer_id}:prefs")
                context["preferences"] = prefs
            except Exception as e:
                logger.warning("customer_context_failed", error=str(e))

        return context

    async def _get_embedding(self, text: str) -> Optional[list[float]]:
        """Get embedding vector for text using Qwen embedding model."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                base_url=settings.dashscope_base_url,
                api_key=settings.dashscope_api_key,
            )
            response = await client.embeddings.create(
                model=settings.model_embedding,
                input=text[:2000],  # Truncate for embedding
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning("embedding_failed", error=str(e))
            return None

    async def close(self):
        """Close all connections."""
        if self.redis:
            await self.redis.aclose()
        if self.db_pool:
            await self.db_pool.close()
