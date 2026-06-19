import base64
from hashlib import sha256
from datetime import datetime
from helpers.cacheable_api_handler import CacheableApiHandler
import logging


class VirusTotal(CacheableApiHandler):
    def __init__(self, api_key: str, allow_local: bool = False, rate_limiters: dict = None, logger= None):
        self.api_base = "https://www.virustotal.com"
        super().__init__(api_key, allow_local, rate_limiters, logger)

    def get_domain_report(self, domain: str, use_cache: bool = True):
        url = f"{self.api_base}/api/v3/domains/{domain}"
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

    def get_analysis(self, analysis_identifier: str, use_cache: bool = True):
        url = f"{self.api_base}/api/v3/analyses/{analysis_identifier}"
        payload = None
        response = self.make_api_request(
            "GET",
            url,
            headers=self.get_auth_headers(),
            payload=payload,
            use_cache=use_cache,
        )
        if "error" in response:
            raise Exception(f"Error fetching analysis for {analysis_identifier}: {response['error']}")

        # even if `use_cache` is false (to read from the cache), we still want to make
        # sure we cache the response for future use
        if not use_cache:
            self.add_to_cache(url, payload, response)

        return response

    def request_url_rescan(self, domain: str) -> dict:
        domain_id = self.get_url_identifier_b64(domain)
        url = f"{self.api_base}/api/v3/urls/{domain_id}/analyse"
        return self.make_api_request("POST", url, headers=self.get_auth_headers(), payload=None, use_cache=False)

    def get_auth_headers(self):
        return {"x-apikey": self.api_key}

    def extract_domain_info(self, report):
        if report is None:
            return {}

        domain_info = report.get("data", {}).get("attributes", {})
        dns_records = domain_info.get("last_dns_records", [])
        return {
            "domain": report.get("data", {}).get("id", "N/A"),
            "creation_date": domain_info.get("creation_date", "N/A"),
            "last_dns_record": dns_records[0].get("date", "N/A") if dns_records else "N/A",
            "last_dns_records_date": domain_info.get("last_dns_records_date", "N/A"),
            "whois_date": domain_info.get("whois_date", "N/A"),
        }

    def extract_reputation_analysis(self, report):
        if (
            "error" in report
            and not isinstance(report["error"], str)
            and report.get("error", {}).get("code", "") == "NotFoundError"
        ):
            return {"error": "NotFoundError"}
        elif "error" in report:
            return {"error": report["error"]}

        domain_info = report.get("data", {}).get("attributes", {})
        categories = domain_info.get("categories", {})
        last_analysis_stats = domain_info.get("last_analysis_stats", {})
        last_analysis_results = domain_info.get("last_analysis_results", {})

        reputation = {
            "total_votes": domain_info.get("total_votes", {}),
            "reputation_score": domain_info.get("reputation", "N/A"),
            "last_analysis_stats": last_analysis_stats,
            "categories": categories,
            "malicious_results": {k: v for k, v in last_analysis_results.items() if v.get("category") == "malicious"},
            "suspicious_results": {k: v for k, v in last_analysis_results.items() if v.get("category") == "suspicious"},
            "harmless_results": {k: v for k, v in last_analysis_results.items() if v.get("category") == "harmless"},
        }

        return reputation

    def extract_ssl_info(self, report):
        if report is None:
            return {}

        certificate = report.get("data", {}).get("attributes", {}).get("last_https_certificate", {})
        if not certificate:
            return {}

        cert_info = {}
        issuer = certificate.get("issuer", {})
        cert_info["Issuer"] = f"C={issuer.get('C')}, O={issuer.get('O')}, CN={issuer.get('CN')}"

        subject = certificate.get("subject", {})
        cert_info["Subject"] = f"C={subject.get('C')}, O={subject.get('O')}, CN={subject.get('CN')}"
        cert_info["Subject Alternative Names"] = certificate.get("extensions", {}).get("subject_alternative_name", [])

        validity = certificate.get("validity", {})
        cert_info["Validity Not Before"] = validity.get("not_before")
        cert_info["Validity Not After"] = validity.get("not_after")

        validity_not_before = (
            datetime.strptime(cert_info["Validity Not Before"], "%Y-%m-%d %H:%M:%S")
            if cert_info["Validity Not Before"]
            else datetime.now()
        )
        cert_info["Certificate Age (Days)"] = (datetime.now() - validity_not_before).days
        cert_info["SHA-256 Thumbprint"] = certificate.get("thumbprint_sha256")
        cert_info["Serial Number"] = certificate.get("serial_number")
        cert_info["Signature Algorithm"] = certificate.get("cert_signature", {}).get("signature_algorithm")

        return cert_info

    def extract_dns_records(self, report):
        dns_records = report.get("data", {}).get("attributes", {}).get("last_dns_records", [])
        records = {
            "A": [],
            "AAAA": [],
            "NS": [],
            "SOA": [],
        }

        for record in dns_records:
            record_type = record.get("type")
            if record_type in records:
                records[record_type].append(record.get("value"))

        return records

    def extract_all_dns_records(self, report):
        return report.get("data", {}).get("attributes", {}).get("last_dns_records", [])

    def get_url_identifier(self, domain: str, use_cache: bool = True) -> str:
        """
        The URL identifier is in the format `u-sha256(url)-$last_analysis_timestamp`,
        re: https://virustotal.readme.io/reference/url
        """
        # the URL identifier is a sha256 hash of the URL, which is typically `http://<domain>/`
        domain_id = sha256(f"http://{domain}/".encode("utf-8")).hexdigest()

        domain_report = self.get_domain_report(domain, use_cache)
        if "error" in domain_report:
            raise Exception(f"Error fetching domain report for {domain}: {domain_report['error']}")

        last_analysis_date = domain_report.get("data", {}).get("attributes", {}).get("last_analysis_date")
        if last_analysis_date is None:
            raise Exception(f"No last analysis date found for domain: {domain}")

        return f"u-{domain_id}-{last_analysis_date}"

    def get_url_identifier_b64(self, domain: str) -> str:
        """
        The URL identifier is typically a in the format `u-sha256(url)-$last_analysis_timestamp`,
        but they also accept a URL-Safe base64 version to cover the possibilities of differences,
        so that's what we're going with here! re: https://virustotal.readme.io/reference/url
        """
        return base64.urlsafe_b64encode(domain.encode()).decode().strip("=")
