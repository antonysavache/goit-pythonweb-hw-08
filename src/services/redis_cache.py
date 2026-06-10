import json

import redis

from src.config import settings


class RedisCache:
    """Thin wrapper around Redis operations used by auth flow."""

    def __init__(self) -> None:
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password or None,
            decode_responses=True,
        )

    def get_user(self, email: str) -> dict | None:
        try:
            value = self.client.get(f"user:{email}")
        except redis.RedisError:
            return None
        return json.loads(value) if value else None

    def set_user(self, email: str, payload: dict) -> None:
        try:
            self.client.setex(f"user:{email}", settings.redis_cache_ttl, json.dumps(payload))
        except redis.RedisError:
            return

    def delete_user(self, email: str) -> None:
        try:
            self.client.delete(f"user:{email}")
        except redis.RedisError:
            return


cache = RedisCache()
