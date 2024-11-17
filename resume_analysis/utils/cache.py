from typing import Any, Optional
from datetime import datetime, timedelta

class Cache:
    def __init__(self, ttl: Optional[int] = None):
        self._cache = {}
        self._expiry = {}
        self._default_ttl = timedelta(hours=1 if ttl is None else ttl/3600)
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self._cache:
            return None
            
        if datetime.now() > self._expiry[key]:
            self.delete(key)
            return None
            
        return self._cache[key]
        
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """Set value in cache with expiry"""
        self._cache[key] = value
        self._expiry[key] = datetime.now() + (ttl or self._default_ttl)
        
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        self._cache.pop(key, None)
        self._expiry.pop(key, None) 