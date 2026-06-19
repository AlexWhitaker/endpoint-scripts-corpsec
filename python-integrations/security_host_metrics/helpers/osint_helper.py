class OSINTHelper:
    def __init__(self):
        self.reputation_tools = [
            {
                "tool": "Google Safe Browsing",
                "url": "https://transparencyreport.google.com/safe-browsing/search?url=<domain>",
            },
            {
                "tool": "CloudFlare Radar",
                "url": "https://radar.cloudflare.com/domains/feedback/<domain>",
            },
            {
                "tool": "Cisco Talos",
                "url": "https://talosintelligence.com/reputation_center/lookup?search=<domain>",
            },
            {
                "tool": "Sucuri SiteCheck",
                "url": "https://sitecheck.sucuri.net/results/<domain>",
            },
            {
                "tool": "Comodo Valkyrie Verdict",
                "url": "https://verdict.valkyrie.comodo.com/url/domain/result?domain=<domain>",
            },
            {
                "tool": "Symantec WebPulse Site Review",
                "url": "https://sitereview.symantec.com/#/lookup-result/<domain>",
            },
            {
                "tool": "McAfee WebAdvisor",
                "url": "https://www.siteadvisor.com/sitereport.html?url=<domain>",
            },
        ]

        self.research_tools = [
            {"tool": "urlscan.io", "url": "https://urlscan.io/domain/<domain>"},
            {
                "tool": "AlientVault OTX",
                "url": "https://otx.alienvault.com/indicator/domain/<domain>",
            },
            {
                "tool": "Wayback Machine",
                "url": "https://web.archive.org/web/*/<domain>",
            },
            {"tool": "DomainTools", "url": "https://whois.domaintools.com/<domain>"},
            {"tool": "PublicWWW", "url": 'https://publicwww.com/websites/"<domain>"/'},
            {
                "tool": "MXToolBox",
                "url": "https://mxtoolbox.com/SuperTool.aspx?action=mx%3a<domain>",
            },
            {
                "tool": "Censys",
                "url": "https://search.censys.io/search?resource=certificates&q=labels%3D%60unexpired%60+and+names%3A+<domain>",
            },
            {"tool": "Shodan", "url": "https://www.shodan.io/search?query=<domain>"},
        ]

    def get_osint_urls(self, domain: str) -> list:
        return [
            {
                "tool": tool["tool"],
                "url": tool["url"].replace("<domain>", domain),
                "type": "reputation",
            }
            for tool in self.reputation_tools
        ] + [
            {
                "tool": tool["tool"],
                "url": tool["url"].replace("<domain>", domain),
                "type": "research",
            }
            for tool in self.research_tools
        ]
