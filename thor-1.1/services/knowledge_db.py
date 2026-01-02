"""
Knowledge Database - SQLite-based persistent storage for Thor's knowledge acquisition system.
Provides schema management, CRUD operations, and semantic search capabilities.
"""
import sqlite3
import os
import json
import pickle
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from contextlib import contextmanager
import hashlib

# Default database path
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge.db")


class KnowledgeDatabase:
    """
    SQLite-based knowledge storage with support for:
    - Knowledge items with embeddings
    - Topic queue management
    - Learning session tracking
    - User query recording for adaptive learning
    """
    
    _local = threading.local()
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._initialize_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
        return self._local.connection
    
    @contextmanager
    def _cursor(self):
        """Context manager for database cursor with automatic commit/rollback."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
    
    def _initialize_database(self):
        """Create database schema if it doesn't exist."""
        with self._cursor() as cursor:
            # Knowledge items table - core knowledge storage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    content_hash TEXT UNIQUE,
                    source TEXT DEFAULT 'wikipedia',
                    url TEXT,
                    embedding BLOB,
                    confidence REAL DEFAULT 0.5,
                    quality_score REAL DEFAULT 0.5,
                    word_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    is_verified INTEGER DEFAULT 0
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_topic 
                ON knowledge_items(topic)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_source 
                ON knowledge_items(source)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_created 
                ON knowledge_items(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_confidence 
                ON knowledge_items(confidence)
            """)
            
            # Topics table - queue of topics to learn
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT UNIQUE NOT NULL,
                    category TEXT,
                    source TEXT DEFAULT 'dictionary',
                    priority INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'pending',
                    last_crawled TIMESTAMP,
                    crawl_count INTEGER DEFAULT 0,
                    knowledge_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for topics
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_topics_status 
                ON topics(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_topics_priority 
                ON topics(priority DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_topics_source 
                ON topics(source)
            """)
            
            # Learning sessions table - track crawling sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    status TEXT DEFAULT 'running',
                    topics_crawled INTEGER DEFAULT 0,
                    knowledge_items_added INTEGER DEFAULT 0,
                    errors_encountered INTEGER DEFAULT 0,
                    avg_confidence REAL DEFAULT 0.0
                )
            """)
            
            # User queries table - for adaptive learning
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    query_hash TEXT,
                    extracted_topics TEXT,
                    knowledge_found INTEGER DEFAULT 0,
                    needs_research INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for user queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_queries_created 
                ON user_queries(created_at)
            """)
            
            # Related topics table - for topic graph
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS related_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_id INTEGER,
                    related_topic TEXT,
                    relationship_type TEXT DEFAULT 'related',
                    strength REAL DEFAULT 0.5,
                    FOREIGN KEY (topic_id) REFERENCES topics(id)
                )
            """)
            
            # Statistics table - aggregate stats
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_date DATE UNIQUE,
                    total_knowledge_items INTEGER DEFAULT 0,
                    total_topics_crawled INTEGER DEFAULT 0,
                    total_user_queries INTEGER DEFAULT 0,
                    avg_confidence REAL DEFAULT 0.0,
                    sources_breakdown TEXT
                )
            """)
    
    # ==================== Knowledge Items CRUD ====================
    
    def add_knowledge(
        self,
        topic: str,
        content: str,
        title: str = None,
        source: str = "wikipedia",
        url: str = None,
        embedding: bytes = None,
        confidence: float = 0.5
    ) -> Optional[int]:
        """
        Add a knowledge item to the database.
        Returns the ID of the inserted item, or None if duplicate.
        """
        # Generate content hash for deduplication
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        word_count = len(content.split())
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(content, title, source)
        
        try:
            with self._cursor() as cursor:
                cursor.execute("""
                    INSERT INTO knowledge_items 
                    (topic, title, content, content_hash, source, url, embedding, 
                     confidence, quality_score, word_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (topic, title, content, content_hash, source, url, 
                      embedding, confidence, quality_score, word_count))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Duplicate content
            return None
    
    def add_knowledge_batch(self, items: List[Dict]) -> Tuple[int, int]:
        """
        Add multiple knowledge items in a batch.
        Returns (successful_count, duplicate_count).
        """
        successful = 0
        duplicates = 0
        
        for item in items:
            result = self.add_knowledge(
                topic=item.get('topic', item.get('query', '')),
                content=item.get('content', ''),
                title=item.get('title'),
                source=item.get('source', 'wikipedia'),
                url=item.get('url'),
                embedding=item.get('embedding'),
                confidence=item.get('confidence', 0.5)
            )
            if result:
                successful += 1
            else:
                duplicates += 1
        
        return successful, duplicates
    
    def get_knowledge_by_topic(
        self,
        topic: str,
        limit: int = 10,
        min_confidence: float = 0.0
    ) -> List[Dict]:
        """Get knowledge items for a specific topic."""
        with self._cursor() as cursor:
            cursor.execute("""
                SELECT * FROM knowledge_items
                WHERE topic LIKE ? AND confidence >= ?
                ORDER BY confidence DESC, quality_score DESC
                LIMIT ?
            """, (f"%{topic}%", min_confidence, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def search_knowledge(
        self,
        query: str,
        limit: int = 10,
        min_confidence: float = 0.0,
        sources: List[str] = None
    ) -> List[Dict]:
        """
        Search knowledge items by query (searches topic, title, and content).
        """
        with self._cursor() as cursor:
            sql = """
                SELECT * FROM knowledge_items
                WHERE (topic LIKE ? OR title LIKE ? OR content LIKE ?)
                AND confidence >= ?
            """
            params = [f"%{query}%", f"%{query}%", f"%{query}%", min_confidence]
            
            if sources:
                placeholders = ",".join(["?" for _ in sources])
                sql += f" AND source IN ({placeholders})"
                params.extend(sources)
            
            sql += " ORDER BY confidence DESC, quality_score DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # Update access count for returned items
            ids = [row['id'] for row in rows]
            if ids:
                self._update_access_stats(ids)
            
            return [dict(row) for row in rows]
    
    def get_knowledge_count(self) -> int:
        """Get total count of knowledge items."""
        with self._cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM knowledge_items")
            return cursor.fetchone()[0]
    
    def get_knowledge_by_ids(self, ids: List[int]) -> List[Dict]:
        """Get knowledge items by their IDs."""
        if not ids:
            return []
        
        with self._cursor() as cursor:
            placeholders = ",".join(["?" for _ in ids])
            cursor.execute(f"""
                SELECT * FROM knowledge_items
                WHERE id IN ({placeholders})
            """, ids)
            return [dict(row) for row in cursor.fetchall()]
    
    def _update_access_stats(self, ids: List[int]):
        """Update access count and last_accessed for knowledge items."""
        if not ids:
            return
        
        with self._cursor() as cursor:
            placeholders = ",".join(["?" for _ in ids])
            cursor.execute(f"""
                UPDATE knowledge_items
                SET access_count = access_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
            """, ids)
    
    def _calculate_quality_score(
        self,
        content: str,
        title: str,
        source: str
    ) -> float:
        """Calculate quality score for knowledge content."""
        score = 0.0
        
        # Length score (0-0.3)
        word_count = len(content.split())
        if word_count >= 100:
            score += 0.3
        elif word_count >= 50:
            score += 0.2
        elif word_count >= 20:
            score += 0.1
        
        # Source score (0-0.3)
        source_scores = {
            'wikipedia': 0.3,
            'google': 0.25,
            'duckduckgo': 0.2,
            'bing': 0.2,
            'brave': 0.25,
            'structured': 0.15
        }
        score += source_scores.get(source.lower(), 0.1)
        
        # Title score (0-0.2)
        if title and len(title) > 5:
            score += 0.2
        
        # Completeness score (0-0.2)
        if content.strip().endswith(('.', '!', '?')):
            score += 0.1
        if '\n' in content or len(content.split('.')) > 2:
            score += 0.1
        
        return min(score, 1.0)
    
    # ==================== Topics Management ====================
    
    def add_topic(
        self,
        topic: str,
        category: str = None,
        source: str = "dictionary",
        priority: int = 5
    ) -> Optional[int]:
        """Add a topic to the queue. Returns topic ID or None if exists."""
        try:
            with self._cursor() as cursor:
                cursor.execute("""
                    INSERT INTO topics (topic, category, source, priority)
                    VALUES (?, ?, ?, ?)
                """, (topic.lower().strip(), category, source, priority))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def add_topics_batch(self, topics: List[Dict]) -> Tuple[int, int]:
        """
        Add multiple topics in a batch.
        Returns (added_count, existing_count).
        """
        added = 0
        existing = 0
        
        for topic_data in topics:
            if isinstance(topic_data, str):
                topic_data = {'topic': topic_data}
            
            result = self.add_topic(
                topic=topic_data.get('topic', ''),
                category=topic_data.get('category'),
                source=topic_data.get('source', 'dictionary'),
                priority=topic_data.get('priority', 5)
            )
            if result:
                added += 1
            else:
                existing += 1
        
        return added, existing
    
    def get_next_topic(self) -> Optional[Dict]:
        """
        Get the next topic to crawl based on priority and status.
        Returns the topic with highest priority that hasn't been crawled recently.
        """
        with self._cursor() as cursor:
            # Get pending topic with highest priority
            cursor.execute("""
                SELECT * FROM topics
                WHERE status = 'pending'
                OR (status = 'crawled' AND 
                    (last_crawled IS NULL OR last_crawled < datetime('now', '-7 days')))
                ORDER BY 
                    CASE WHEN status = 'pending' THEN 0 ELSE 1 END,
                    priority DESC,
                    crawl_count ASC,
                    created_at ASC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_topics_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get topics by their status."""
        with self._cursor() as cursor:
            cursor.execute("""
                SELECT * FROM topics
                WHERE status = ?
                ORDER BY priority DESC
                LIMIT ?
            """, (status, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_topic_status(
        self,
        topic_id: int,
        status: str,
        knowledge_count: int = 0,
        error: str = None
    ):
        """Update topic status after crawling."""
        with self._cursor() as cursor:
            if error:
                cursor.execute("""
                    UPDATE topics
                    SET status = ?,
                        last_crawled = CURRENT_TIMESTAMP,
                        crawl_count = crawl_count + 1,
                        error_count = error_count + 1,
                        last_error = ?
                    WHERE id = ?
                """, (status, error, topic_id))
            else:
                cursor.execute("""
                    UPDATE topics
                    SET status = ?,
                        last_crawled = CURRENT_TIMESTAMP,
                        crawl_count = crawl_count + 1,
                        knowledge_count = knowledge_count + ?
                    WHERE id = ?
                """, (status, knowledge_count, topic_id))
    
    def get_topics_count(self, status: str = None) -> int:
        """Get count of topics, optionally filtered by status."""
        with self._cursor() as cursor:
            if status:
                cursor.execute(
                    "SELECT COUNT(*) FROM topics WHERE status = ?",
                    (status,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM topics")
            return cursor.fetchone()[0]
    
    def boost_topic_priority(self, topic: str, boost: int = 2):
        """Boost priority of a topic (e.g., when user asks about it)."""
        with self._cursor() as cursor:
            cursor.execute("""
                UPDATE topics
                SET priority = MIN(priority + ?, 10)
                WHERE topic = ?
            """, (boost, topic.lower().strip()))
    
    # ==================== User Queries ====================
    
    def record_user_query(
        self,
        query: str,
        extracted_topics: List[str],
        knowledge_found: bool,
        needs_research: bool
    ):
        """Record a user query for adaptive learning."""
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        topics_json = json.dumps(extracted_topics)
        
        with self._cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_queries 
                (query, query_hash, extracted_topics, knowledge_found, needs_research)
                VALUES (?, ?, ?, ?, ?)
            """, (query, query_hash, topics_json, 
                  1 if knowledge_found else 0,
                  1 if needs_research else 0))
            
            # If needs research, add extracted topics to queue with high priority
            if needs_research and extracted_topics:
                for topic in extracted_topics:
                    self.add_topic(
                        topic=topic,
                        source='user_query',
                        priority=8  # High priority for user-requested topics
                    )
    
    def get_unanswered_topics(self, limit: int = 50) -> List[str]:
        """Get topics that users asked about but we couldn't answer."""
        with self._cursor() as cursor:
            cursor.execute("""
                SELECT extracted_topics FROM user_queries
                WHERE needs_research = 1
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            topics = []
            for row in cursor.fetchall():
                try:
                    topic_list = json.loads(row['extracted_topics'])
                    topics.extend(topic_list)
                except:
                    pass
            
            return list(set(topics))
    
    # ==================== Learning Sessions ====================
    
    def start_learning_session(self) -> int:
        """Start a new learning session. Returns session ID."""
        with self._cursor() as cursor:
            cursor.execute("""
                INSERT INTO learning_sessions (status)
                VALUES ('running')
            """)
            return cursor.lastrowid
    
    def update_learning_session(
        self,
        session_id: int,
        topics_crawled: int = 0,
        knowledge_added: int = 0,
        errors: int = 0
    ):
        """Update learning session statistics."""
        with self._cursor() as cursor:
            cursor.execute("""
                UPDATE learning_sessions
                SET topics_crawled = topics_crawled + ?,
                    knowledge_items_added = knowledge_items_added + ?,
                    errors_encountered = errors_encountered + ?
                WHERE id = ?
            """, (topics_crawled, knowledge_added, errors, session_id))
    
    def end_learning_session(self, session_id: int):
        """End a learning session."""
        with self._cursor() as cursor:
            # Calculate average confidence for this session
            cursor.execute("""
                SELECT AVG(confidence) FROM knowledge_items
                WHERE created_at >= (
                    SELECT started_at FROM learning_sessions WHERE id = ?
                )
            """, (session_id,))
            avg_conf = cursor.fetchone()[0] or 0.0
            
            cursor.execute("""
                UPDATE learning_sessions
                SET ended_at = CURRENT_TIMESTAMP,
                    status = 'completed',
                    avg_confidence = ?
                WHERE id = ?
            """, (avg_conf, session_id))
    
    def get_session_stats(self, session_id: int) -> Optional[Dict]:
        """Get statistics for a learning session."""
        with self._cursor() as cursor:
            cursor.execute("""
                SELECT * FROM learning_sessions WHERE id = ?
            """, (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== Related Topics ====================
    
    def add_related_topic(
        self,
        topic_id: int,
        related_topic: str,
        relationship_type: str = "related",
        strength: float = 0.5
    ):
        """Add a related topic discovered during crawling."""
        # First, ensure the related topic exists in topics table
        self.add_topic(
            topic=related_topic,
            source='discovered',
            priority=4  # Lower priority than dictionary topics
        )
        
        with self._cursor() as cursor:
            cursor.execute("""
                INSERT OR IGNORE INTO related_topics 
                (topic_id, related_topic, relationship_type, strength)
                VALUES (?, ?, ?, ?)
            """, (topic_id, related_topic.lower().strip(), 
                  relationship_type, strength))
    
    def get_related_topics(self, topic: str, limit: int = 10) -> List[str]:
        """Get topics related to the given topic."""
        with self._cursor() as cursor:
            # First get topic ID
            cursor.execute(
                "SELECT id FROM topics WHERE topic = ?",
                (topic.lower().strip(),)
            )
            row = cursor.fetchone()
            if not row:
                return []
            
            topic_id = row['id']
            
            cursor.execute("""
                SELECT related_topic FROM related_topics
                WHERE topic_id = ?
                ORDER BY strength DESC
                LIMIT ?
            """, (topic_id, limit))
            
            return [row['related_topic'] for row in cursor.fetchall()]
    
    # ==================== Statistics ====================
    
    def get_database_stats(self) -> Dict:
        """Get overall database statistics."""
        with self._cursor() as cursor:
            stats = {}
            
            # Knowledge items stats
            cursor.execute("SELECT COUNT(*) FROM knowledge_items")
            stats['total_knowledge_items'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(confidence) FROM knowledge_items")
            stats['avg_confidence'] = cursor.fetchone()[0] or 0.0
            
            cursor.execute("SELECT AVG(quality_score) FROM knowledge_items")
            stats['avg_quality_score'] = cursor.fetchone()[0] or 0.0
            
            # Source breakdown
            cursor.execute("""
                SELECT source, COUNT(*) as count 
                FROM knowledge_items 
                GROUP BY source
            """)
            stats['sources'] = {row['source']: row['count'] 
                               for row in cursor.fetchall()}
            
            # Topics stats
            cursor.execute("SELECT COUNT(*) FROM topics")
            stats['total_topics'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM topics 
                GROUP BY status
            """)
            stats['topics_by_status'] = {row['status']: row['count'] 
                                         for row in cursor.fetchall()}
            
            # User queries stats
            cursor.execute("SELECT COUNT(*) FROM user_queries")
            stats['total_user_queries'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM user_queries WHERE needs_research = 1
            """)
            stats['unanswered_queries'] = cursor.fetchone()[0]
            
            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) FROM knowledge_items
                WHERE created_at >= datetime('now', '-24 hours')
            """)
            stats['knowledge_added_24h'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM topics
                WHERE last_crawled >= datetime('now', '-24 hours')
            """)
            stats['topics_crawled_24h'] = cursor.fetchone()[0]
            
            return stats
    
    def cleanup_old_data(self, days: int = 365):
        """Remove old, low-quality, or unused knowledge items."""
        with self._cursor() as cursor:
            # Remove items that are old, never accessed, and low confidence
            cursor.execute("""
                DELETE FROM knowledge_items
                WHERE created_at < datetime('now', ? || ' days')
                AND access_count = 0
                AND confidence < 0.3
            """, (f"-{days}",))
            
            deleted = cursor.rowcount
            print(f"[KnowledgeDB] Cleaned up {deleted} old low-quality items")
            return deleted


# Global instance
_knowledge_db = None


def get_knowledge_db(db_path: str = None) -> KnowledgeDatabase:
    """Get or create the global knowledge database instance."""
    global _knowledge_db
    if _knowledge_db is None:
        _knowledge_db = KnowledgeDatabase(db_path)
    return _knowledge_db

