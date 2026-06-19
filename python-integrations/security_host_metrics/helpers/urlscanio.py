from helpers.cacheable_api_handler import CacheableApiHandler
import logging


class UrlScanIO(CacheableApiHandler):
    def __init__(self, api_key: str, allow_local: bool = False, rate_limiters: dict = None, logger= None):
        self.api_base = "https://urlscan.io"
        super().__init__(api_key, allow_local, rate_limiters, logger)

    def get_domain_search(self, domain: str, use_cache: bool = True):
        url = f"{self.api_base}/api/v1/search/"
        params = {
            "q": f"domain:{domain} AND page.status:200 AND date:>now-2d",
            "size": 1,
        }
        response = self.make_api_request(
            "GET",
            url,
            headers=self.get_auth_headers(),
            payload=params,
            use_cache=use_cache,
        )

        # even if `use_cache` is false (to read from the cache), we still want to make
        # sure we cache the response for future use
        if not use_cache:
            self.add_to_cache(url, params, response)

        return response

    def submit_scan_request(self, domain: str):
        url = f"{self.api_base}/api/v1/scan/"
        payload = {
            "url": f"https://{domain}/",
            "public": "off",
            "visibility": "private",
        }

        headers = self.get_auth_headers()
        headers["Content-Type"] = "application/json"
        return self.make_api_request("POST", url, headers=headers, payload=payload, use_cache=False)

    def get_auth_headers(self):
        return {"API-Key": self.api_key}

    def extract_domain_search_results(self, domain: str, response: dict) -> dict:
        if "results" not in response or len(response["results"]) == 0:
            return None

        if len(response["results"]) > 1:
            self.logger.info(f"[UrlScanIO] Warning: more than one result found for domain {domain}")

        result = response["results"][0]
        return {
            "domain": result["task"]["domain"],
            "scan_time": result["task"]["time"],
            "scanned_ip": result["page"]["ip"],
            "page_status": result["page"]["status"],
            "page_title": result["page"]["title"] if "title" in result["page"] else None,
            "asn_name": result["page"]["asnname"] if "asnname" in result["page"] else None,
            "screenshot": result["screenshot"],
        }
