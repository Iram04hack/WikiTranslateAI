# -*- coding: utf-8 -*-
"""
Cache manager for WikiTranslateAI - Multi-level caching system
"""

import json
import sqlite3
import threading
import time
import hashlib
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheManager:
    """Multi-level cache manager with L1 (memory) + L3 (SQLite)"""
    
    def __init__(self, cache_dir: str = "data/cache", max_memory_items: int = 1000, default_ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_memory_items = max_memory_items
        self.default_ttl = default_ttl
        
        # L1 Cache - Memory
        self._memory_cache: Dict[str, Dict] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        
        # L3 Cache - SQLite
        self._sqlite_db = self.cache_dir / "cache.db"
        self._init_sqlite()
        
        # Stats
        self.stats = {'l1_hits': 0, 'l3_hits': 0, 'misses': 0, 'sets': 0}
    
    def _init_sqlite(self):
        """Initialize SQLite cache database"""
        with sqlite3.connect(self._sqlite_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
    
    def _generate_key(self, key: Union[str, Dict]) -> str:
        """Generate normalized cache key"""
        if isinstance(key, dict):
            key_str = json.dumps(key, sort_keys=True)
            return hashlib.md5(key_str.encode()).hexdigest()
        return str(key)
    
    def get(self, key: Union[str, Dict], default: Any = None) -> Any:
        """Get value from multi-level cache"""
        cache_key = self._generate_key(key)
        
        # L1 Cache - Memory
        with self._lock:
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                if not self._is_expired(entry):
                    self._access_times[cache_key] = time.time()
                    self.stats['l1_hits'] += 1
                    return entry['value']
                else:
                    del self._memory_cache[cache_key]
                    self._access_times.pop(cache_key, None)
        
        # L3 Cache - SQLite
        try:
            with sqlite3.connect(self._sqlite_db) as conn:
                cursor = conn.execute(
                    "SELECT value, expires_at FROM cache_entries WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)",
                    (cache_key, datetime.now().isoformat())
                )
                row = cursor.fetchone()
                if row:
                    value = json.loads(row[0])
                    entry = {'value': value, 'expires_at': row[1]}
                    
                    # Promote to L1
                    self._set_l1(cache_key, entry)
                    self.stats['l3_hits'] += 1
                    return value
        except Exception as e:
            logger.error(f"SQLite get error: {e}")
        
        # Cache miss
        self.stats['misses'] += 1
        return default
    
    def set(self, key: Union[str, Dict], value: Any, ttl: Optional[int] = None) -> bool:
        """Store value in multi-level cache"""
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        entry = {
            'value': value,
            'expires_at': expires_at.isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        success = True
        success &= self._set_l1(cache_key, entry)
        success &= self._set_l3(cache_key, entry)
        
        if success:
            self.stats['sets'] += 1
        
        return success
    
    def _set_l1(self, cache_key: str, entry: Dict) -> bool:
        """Store in L1 cache with LRU eviction"""
        try:
            with self._lock:
                if len(self._memory_cache) >= self.max_memory_items:
                    self._evict_lru()
                
                self._memory_cache[cache_key] = entry
                self._access_times[cache_key] = time.time()
            return True
        except Exception as e:
            logger.error(f"L1 set error: {e}")
            return False
    
    def _set_l3(self, cache_key: str, entry: Dict) -> bool:
        """Store in L3 SQLite cache"""
        try:
            with sqlite3.connect(self._sqlite_db) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, value, created_at, expires_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    cache_key,
                    json.dumps(entry['value']),
                    entry['created_at'],
                    entry['expires_at']
                ))
            return True
        except Exception as e:
            logger.error(f"L3 set error: {e}")
            return False
    
    def _evict_lru(self):
        """Evict least recently used item from L1"""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        self._memory_cache.pop(lru_key, None)
        self._access_times.pop(lru_key, None)
    
    def _is_expired(self, entry: Dict) -> bool:
        """Check if cache entry is expired"""
        if 'expires_at' not in entry or entry['expires_at'] is None:
            return False
        
        try:
            expires_at = datetime.fromisoformat(entry['expires_at'])
            return datetime.now() > expires_at
        except:
            return True
    
    def clear(self):
        """Clear all cache levels"""
        with self._lock:
            self._memory_cache.clear()
            self._access_times.clear()
        
        try:
            with sqlite3.connect(self._sqlite_db) as conn:
                conn.execute("DELETE FROM cache_entries")
        except Exception as e:
            logger.error(f"SQLite clear error: {e}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = sum([self.stats['l1_hits'], self.stats['l3_hits'], self.stats['misses']])
        hit_rate = 0
        if total_requests > 0:
            hits = self.stats['l1_hits'] + self.stats['l3_hits']
            hit_rate = hits / total_requests
        
        return {
            **self.stats,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'l1_size': len(self._memory_cache)
        }


# Global instance for simple usage
_default_cache = None

def get_cache() -> CacheManager:
    """Get default cache instance"""
    global _default_cache
    if _default_cache is None:
        _default_cache = CacheManager()
    return _default_cache