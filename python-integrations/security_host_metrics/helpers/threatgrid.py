from helpers.cacheable_api_handler import CacheableApiHandler
import logging


class ThreatGrid(CacheableApiHandler):
    def __init__(self, api_key, allow_local=False, rate_limiters: dict = None, logger= None):
        self.api_base = "https://panacea.threatgrid.com"
        super().__init__(api_key, allow_local, rate_limiters, logger)

    def get_domain_report(self, domain: str, use_cache: bool = True) -> dict:
        # https://ciscosecurity-tg-00-integration-workflows.readthedocs-hosted.com/en/latest/tg/query.html#querying-for-an-observable-or-entity
        url = f"{self.api_base}/api/v2/search/submissions?q={domain}"
        response = self.make_api_request(
            "GET",
            url,
            headers=self.get_auth_headers(),
            payload=None,
            use_cache=use_cache,
        )
        if "error" in response:
            raise Exception(f"Error fetching domain report for {domain}: {response['error']}")

        # even if `use_cache` is false (to read from the cache), we still want to make
        # sure we cache the response for future use
        if not use_cache:
            self.add_to_cache(url, None, response)

        return response

    def get_auth_headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    def extract_threatgrid_data(self, report):
        items = report.get("data", {}).get("items", [])
        max_threat_score = 0
        behaviors = []

        for item in items:
            analysis = item["item"].get("analysis", {})
            item_threat_score = analysis.get("threat_score", 0)
            item_behaviors = analysis.get("behaviors", [])

            if item_threat_score > max_threat_score:
                max_threat_score = item_threat_score

            behaviors.extend(item_behaviors)

        # sort behaviors by threat score (which will cause it to not be in the same order as in the UI)
        behaviors.sort(key=lambda x: x.get("threat", 0), reverse=True)

        return {"threat_score": max_threat_score, "behaviors": behaviors}

    def get_latest_sample_hash(self, domain, report):
        items = report.get("data", {}).get("items", [])

        if len(items) == 0:
            return ""

        # look for a sample with a filename matching `^{domain}_`; if none, return the first sample
        for item in items:
            if item["item"].get("filename", "").startswith(f"{domain}_"):
                return item["item"].get("sample", "")

        return items[0].get("item", {}).get("sample", "")
