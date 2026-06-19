import requests
import json
import os
from hashlib import md5
from helpers.cache_helper import CacheHelper
import logging


class CacheableApiHandler:
    def __init__(self, api_key: str, allow_local: bool = False, rate_limiters: dict = None, logger= None):
        self.api_base = self.api_base if hasattr(self, "api_base") else ""
        self.api_key = api_key
        self.allow_local = allow_local
        self.cache = CacheHelper()
        self.rate_limiters = rate_limiters or {}
        self.logger = logger or logging.getLogger(type(self).__name__)

    def make_api_request(
        self,
        method: str,
        url: str,
        headers: dict = None,
        payload: dict = None,
        use_cache: bool = True,
    ) -> dict:
        if self.api_key is None:
            return {"error": "No API key provided"}

        if use_cache:
            response = self.get_from_cache(url, payload)
            if response:
                self.logger.info(f"[{type(self).__name__}] Using cached response for {url}")
                return response

        self.logger.info(f"[{type(self).__name__}] API {method}: {url}")

        if "per_minute" in self.rate_limiters:
            self.rate_limiters["per_minute"].record_hit(sleep_if_needed=True)

        if "per_hour" in self.rate_limiters:
            self.rate_limiters["per_hour"].record_hit(sleep_if_needed=True)

        if "per_day" in self.rate_limiters:
            self.rate_limiters["per_day"].record_hit(sleep_if_needed=True)

        if method == "GET":
            response = requests.get(url, headers=headers, params=payload)
        else:
            payload = json.dumps(payload) if headers.get("Content-Type", "") == "application/json" else payload
            response = requests.request(method, url, headers=headers, data=payload)

        if "json" in response.headers.get("Content-Type", ""):
            response_data = response.json()
        else:
            response_data = response.text

        if response.status_code != 200:
            return {"error": response_data, "status_code": response.status_code}

        response = response_data
        if use_cache:
            self.add_to_cache(url, payload, response)
        return response

    def get_from_cache(self, url: str, payload: dict = None) -> dict:
        cache_key = self.get_cache_key(url, payload)

        if self.cache.get(cache_key):
            return self.cache.get(cache_key)

        local_filename = self.get_local_filename(cache_key)
        if self.allow_local and os.path.exists(local_filename):
            with open(local_filename, "r") as f:
                return json.load(f)

        return None

    def add_to_cache(self, url: str, url_payload: dict = None, data: dict = None):
        cache_key = self.get_cache_key(url, url_payload)

        if self.allow_local:
            local_filename = self.get_local_filename(cache_key)
            with open(local_filename, "w") as f:
                f.write(json.dumps(data))

        self.cache.set(cache_key, data)

    def get_cache_key(self, input: str, extra_input: dict = None) -> str:
        input_hash = md5(input.encode()).hexdigest()

        if extra_input is None:
            return input_hash

        extra_input_hash = md5(json.dumps(extra_input).encode()).hexdigest()
        return f"{input_hash}-{extra_input_hash}"

    def get_local_filename(self, cache_key: str) -> str:
        return f"data/{type(self).__name__}-{cache_key}.json"
