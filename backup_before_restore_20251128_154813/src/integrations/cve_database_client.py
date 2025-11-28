"""
CVE Database Client - Multi-Source Vulnerability Database Integration

Integrates with multiple CVE sources:
- NVD (National Vulnerability Database)
- Snyk
- GitHub Security Advisories
- OSV (Open Source Vulnerabilities)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CVE:
    """CVE vulnerability information"""
    cve_id: str
    description: str
    severity: str  # low, medium, high, critical
    cvss_score: float
    published_date: datetime
    affected_versions: List[str]
    fixed_versions: List[str]
    source: str  # nvd, snyk, github, osv
    references: List[str]


class CVEDatabaseClient:
    """
    Multi-source CVE database client

    Aggregates vulnerability data from:
    - NVD API
    - Snyk API
    - GitHub Security Advisories API
    - OSV API
    """

    def __init__(
        self,
        nvd_api_key: Optional[str] = None,
        snyk_api_key: Optional[str] = None,
        github_token: Optional[str] = None
    ):
        """
        Initialize CVE database client

        Args:
            nvd_api_key: NVD API key
            snyk_api_key: Snyk API token
            github_token: GitHub personal access token
        """
        self.nvd_api_key = nvd_api_key
        self.snyk_api_key = snyk_api_key
        self.github_token = github_token
        self.logger = logging.getLogger("cve_database_client")

        # Initialize clients
        self.nvd_client = None
        self.snyk_client = None
        self.github_client = None
        self.osv_client = None

        self._init_clients()

    def _init_clients(self):
        """Initialize API clients"""
        # NVD Client
        if self.nvd_api_key:
            try:
