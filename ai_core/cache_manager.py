import time
from typing import Any, Optional, Dict

class SimpleTTLCache:
    """
    Tezkor xotira keshi (In-Memory TTL Cache).
    Katta zaproslar oqimida ma'lumotlar bazasini ortiqcha yuklamaslik va
    server qotib qolmasligini ta'minlash uchun xizmat qiladi.
    """
    def __init__(self, default_ttl: int = 60):
        self._cache: Dict[str, dict] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        item = self._cache.get(key)
        if not item:
            return None
        if time.time() > item["expires_at"]:
            del self._cache[key]
            return None
        return item["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        expires_at = time.time() + (ttl if ttl is not None else self.default_ttl)
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at
        }

    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        self._cache.clear()

# Global kesh instansiyasi
analytics_cache = SimpleTTLCache(default_ttl=45)
search_cache = SimpleTTLCache(default_ttl=300)
