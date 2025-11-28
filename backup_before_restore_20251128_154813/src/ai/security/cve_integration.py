"""
CVE Database Integration for Security Agent

Provides integration with CVE databases for vulnerability checking.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp


class CVEIntegration:
    """
    Integration with CVE (Common Vulnerabilities and Exposures) databases.

    Supports:
    - NVD (National Vulnerability Database)
    - CVE.org
    - GitHub Security Advisories
    """

    def __init__(self):
        self.logger = logging.getLogger("cve_integration")
        self.nvd_api_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.cache = {}  # Simple in-memory cache

    async def check_dependencies(
        self,
        dependencies: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Check dependencies against CVE database.

        Args:
            dependencies: List of {"name": str, "version": str}

        Returns:
            List of vulnerabilities found
        """
        vulnerabilities = []

        for dep in dependencies:
            cves = await self.search_cve(
                product=dep["name"],
                version=dep.get("version")
            )

            if cves:
                vulnerabilities.append({
                    "dependency": dep,
                    "cves": cves,
                    "severity": self._get_max_severity(cves),
                    "count": len(cves)
                })

        return vulnerabilities

    async def search_cve(
        self,
        product: str,
        version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search CVE database for product vulnerabilities.

        Args:
            product: Product name
            version: Optional version

        Returns:
            List of CVEs
        """
        # Check cache
        cache_key = f"{product}:{version or 'all'}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
