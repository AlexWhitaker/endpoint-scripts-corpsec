import os
import json
import logging
from pymemcache.client.base import Client as MemcachedClient


# custom serializer/deserializer for memcached,
# re: https://pymemcache.readthedocs.io/en/latest/getting_started.html#serialization
class JsonSerde(object):
    def serialize(self, key, value):
        if isinstance(value, str):
            return value.encode("utf-8"), 1
        return json.dumps(value).encode("utf-8"), 2

    def deserialize(self, key, value, flags):
        if flags == 1:
            return value.decode("utf-8")
        if flags == 2:
            return json.loads(value.decode("utf-8"))
        raise Exception("Unknown serialization format")


def ensure_memcached_client(method):
    def wrapper(self, *args, **kwargs):
        # if the memcached client is not initialized (e.g., `None`, not `False`), initialize it
        if not hasattr(self, "memcached_client") or self.memcached_client is None:
            self.init_memcached_client()
        return method(self, *args, **kwargs)

    return wrapper


class CacheHelper:
    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)

        self.local_cache = {}
        self.memcached_client = None

    def init_memcached_client(self):
        try:
            self.memcached_client = MemcachedClient(
                os.getenv("SECURITY_SERVICES_MEMCACHED"), connect_timeout=1, timeout=30, serde=JsonSerde()
            )
        except Exception as e:
            self.logger.info(f"Error connecting to memcached: {e}")
            self.memcached_client = False

    @ensure_memcached_client
    def set(self, key: str, value):
        if self.memcached_client:
            self.memcached_client.set(key, value)
        else:
            self.local_cache[key] = value

    @ensure_memcached_client
    def get(self, key: str, default=None):
        if self.memcached_client:
            return self.memcached_client.get(key)
        else:
            return self.local_cache.get(key, default)

    @ensure_memcached_client
    def delete(self, key: str):
        if self.memcached_client:
            self.memcached_client.delete(key)
        elif key in self.local_cache:
            del self.local_cache[key]

    @ensure_memcached_client
    def clear(self):
        if self.memcached_client:
            self.memcached_client.flush_all()
        else:
            self.local_cache.clear()
