import base64
import json
import time
from helpers.cacheable_api_handler import CacheableApiHandler
import logging


class NoUmbrellaCategoriesError(Exception):
    pass


class Umbrella(CacheableApiHandler):
    def __init__(self, api_key: str, allow_local=False, rate_limiters: dict = None, logger= None):
        self.api_base = "https://api.umbrella.com"
        self.access_token = None
        self.categories = []
        super().__init__(api_key, allow_local, rate_limiters, logger)

    def get_categories(self, use_cache: bool = True) -> list:
        if len(self.categories) > 0:
            return self.categories

        cached_results = self.get_from_cache("umbrella-categories")
        if cached_results:
            if "data" in cached_results:
                self.logger.info(f"[Umbrella] Using {len(cached_results)} cached categories")
                cached_results = cached_results["data"]
            self.categories = cached_results
            return cached_results

        url = f"{self.api_base}/reports/v2/categories"
        payload = None
        response = self.make_api_request(
            "GET",
            url,
            headers=self.get_auth_headers(),
            payload=payload,
            use_cache=use_cache,
        )
        if "error" in response:
            raise NoUmbrellaCategoriesError(f"Error fetching global Umbrella categories: {response['error']}")

        categories = response["data"] if "data" in response else []
        self.logger.info(f"[Umbrella] Fetched {len(categories)} categories")

        # even if `use_cache` is false (to read from the cache), we still want to make
        # sure we cache the response for future use
        if not use_cache:
            self.add_to_cache(url, payload, categories)

        return categories

    def get_risk_score(self, domain: str, use_cache: bool = True) -> dict:
        url = f"{self.api_base}/investigate/v2/domains/risk-score/{domain}"
        payload = None
        response = self.make_api_request(
            "GET",
            url,
            headers=self.get_auth_headers(),
            payload=payload,
            use_cache=use_cache,
        )

        # even if `use_cache` is false (to read from the cache), we still want to make
        # sure we cache the response for future use
        if not use_cache:
            self.add_to_cache(url, payload, response)

        return response

    def extract_umbrella_risk_score(self, data):
        indicators = data.get("indicators", [])
        risk_score = data.get("risk_score", 0)
        return {"risk_score": risk_score, "indicators": indicators}

    def get_domain_status_and_categorization(self, domain: str, use_cache: bool = True) -> dict:
        url = f"{self.api_base}/investigate/v2/domains/categorization/{domain}"
        payload = None
        response = self.make_api_request(
            "GET",
            url,
            headers=self.get_auth_headers(),
            payload=payload,
            use_cache=use_cache,
        )

        # even if `use_cache` is false (to read from the cache), we still want to make
        # sure we cache the response for future use
        if not use_cache:
            self.add_to_cache(url, payload, response)

        return response

    def extract_umbrella_categories(self, domain: str, data: dict) -> dict:
        extracted_categories = {"content_categories": [], "security_categories": []}

        categories = self.get_categories()
        if len(categories) == 0:
            return extracted_categories

        if domain not in data:
            return extracted_categories

        domain_data = data[domain]
        if "content_categories" in domain_data:
            extracted_categories["content_categories"] = [
                x["label"] for x in categories if str(x["id"]) in domain_data["content_categories"]
            ]

        if "security_categories" in domain_data:
            extracted_categories["security_categories"] = [
                x["label"] for x in categories if str(x["id"]) in domain_data["security_categories"]
            ]

        return extracted_categories

    def get_dns_activity(self, payload: dict, use_cache: bool = True) -> dict:
        url = f"{self.api_base}/reports/v2/activity/dns"
        return self.make_api_request(
            "GET",
            url,
            headers=self.get_auth_headers(),
            payload=payload,
            use_cache=use_cache,
        )

    def is_access_token_valid(self) -> bool:
        if self.access_token is None:
            return False

        # check if the access token is still valid (it's a JWT w/ an `exp` field in the payload!)
        payload = self.access_token.split(".")[1]
        if len(payload) % 4 != 0:
            payload += "=" * (4 - len(payload) % 4)
        payload_json = json.loads(base64.b64decode(payload))

        time_padding = 60
        if "exp" not in payload_json or payload_json["exp"] < (time.time() - time_padding):
            return False

        return True

    def fetch_access_token(self) -> None:
        if self.api_key is None:
            raise Exception("No Cisco Umbrella API key provided")

        url = f"{self.api_base}/auth/v2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Authorization": f"Basic {self.api_key}",
        }

        allow_local = self.allow_local
        self.allow_local = False  # we don't want this cached to disk
        response = self.make_api_request("POST", url, headers=headers, payload=None, use_cache=False)
        self.allow_local = allow_local

        if "access_token" not in response:
            raise Exception("Failed to fetch Umbrella access token")

        self.access_token = response["access_token"]

    def get_auth_headers(self):
        if not self.is_access_token_valid():
            self.fetch_access_token()

        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
