"""
Security Patterns Repository

Repository для хранения security patterns и rules.
"""

from typing import Any, Dict, List


class SecurityPatternsRepository:
    """
    Repository для базы знаний security patterns

    Хранит:
    - Vulnerability patterns
    - Secret patterns (regex)
    - Compliance rules
    - CVE data (mock)
    """

    def __init__(self):
        """Initialize repository with default data"""
        self._vulnerability_patterns = self._load_vulnerability_patterns()
        self._secret_patterns = self._load_secret_patterns()
        self._compliance_rules = self._load_compliance_rules()
        self._cve_database = self._load_cve_database()

    def get_vulnerability_patterns(self) -> Dict[str, Any]:
        """Получить vulnerability patterns"""
        return self._vulnerability_patterns

    def get_secret_patterns(self) -> Dict[str, Any]:
        """Получить secret patterns"""
        return self._secret_patterns

    def get_compliance_rules(self) -> Dict[str, List[Dict]]:
        """Получить compliance rules"""
        return self._compliance_rules

    def get_cve_database(self) -> Dict[str, Dict]:
        """Получить CVE database"""
        return self._cve_database

    def _load_vulnerability_patterns(self) -> Dict[str, Any]:
        """Load vulnerability patterns"""
        return {
            "sql_injection": {
                "pattern": r'(execute|query|sql)\s*\(\s*["\'].*?\+',
                "severity": "critical",
            },
            "xss": {"pattern": r"(innerHTML|outerHTML)\s*=", "severity": "high"},
        }

    def _load_secret_patterns(self) -> Dict[str, Any]:
        """Load secret patterns"""
        return {
            "api_key": {
                "pattern": r'(api[_-]?key|apikey)\s*=\s*["\'][a-zA-Z0-9]{20,}',
                "confidence": 0.9,
            },
            "password": {
                "pattern": r'(password|pwd)\s*=\s*["\'][^"\']{8,}',
                "confidence": 0.7,
            },
            "token": {
                "pattern": r'(token|auth)\s*=\s*["\'][a-zA-Z0-9]{32,}',
                "confidence": 0.85,
            },
            "aws_key": {"pattern": r"AKIA[0-9A-Z]{16}", "confidence": 0.95},
        }

    def _load_compliance_rules(self) -> Dict[str, List[Dict]]:
        """Load compliance rules"""
        return {
            "owasp": [
                {
                    "id": "A01:2021",
                    "description": "Broken Access Control",
                    "severity": "high",
                    "pattern": r"(admin|superuser)\s*=\s*True",
                },
                {
                    "id": "A02:2021",
                    "description": "Cryptographic Failures",
                    "severity": "critical",
                    "pattern": r"(md5|sha1)\s*\(",
                },
                {
                    "id": "A03:2021",
                    "description": "Injection",
                    "severity": "critical",
                    "pattern": r"execute\s*\(.*?\+.*?\)",
                },
            ],
            "cwe": [
                {
                    "id": "CWE-89",
                    "description": "SQL Injection",
                    "severity": "critical",
                    "pattern": r"(execute|query)\s*\(.*?\+.*?\)",
                },
                {
                    "id": "CWE-79",
                    "description": "Cross-site Scripting",
                    "severity": "high",
                    "pattern": r"innerHTML\s*=",
                },
            ],
        }

    def _load_cve_database(self) -> Dict[str, Dict]:
        """Load CVE database (mock)"""
        return {
            "requests:2.25.0": {
                "cve_id": "CVE-2023-32681",
                "severity": "high",
                "description": "Proxy-Authorization header leak",
                "fixed_version": "2.31.0",
            },
            "django:3.0.0": {
                "cve_id": "CVE-2023-24580",
                "severity": "critical",
                "description": "SQL injection vulnerability",
                "fixed_version": "3.2.18",
            },
        }


__all__ = ["SecurityPatternsRepository"]
