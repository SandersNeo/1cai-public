# [NEXUS IDENTITY] ID: -5756776353244742889 | DATE: 2025-11-19

"""
Secure Code Review AI Agent
Based on Agents Rule of Two: [BC] Configuration

[A] CANNOT process untrusted inputs (only trusted contributors)
[B] Can access sensitive data (source code)
[C] Can change state (post comments, suggest changes)
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.security.ai_security_layer import AISecurityLayer, AgentRuleOfTwoConfig


@dataclass
class TrustedContributor:
    """Trusted contributor definition"""

    github_id: str
    email: str
    name: str
    approved_prs: int = 0
    trusted_since: Optional[str] = None


class CodeReviewAISecure:
    """
    Secure Code Review AI - только для trusted contributors
    """

    # Доверенные домены email
    TRUSTED_EMAIL_DOMAINS = [
        "@company.com",
        "@1c-ai-stack.com",
        # Добавьте ваши домены
    ]

    def __init__(self):
        self.security = AISecurityLayer()

        # Конфигурация Rule of Two
        self.config = AgentRuleOfTwoConfig(
            can_process_untrusted=False,  # [A] - только trusted contributors
            can_access_sensitive=True,  # [B] - видит код
            can_change_state=True,  # [C] - может комментировать
        )

        # Список доверенных contributors
        self.trusted_contributors = self._load_trusted_contributors()

    def review_pull_request(
        self,
        pr_author: str,
        pr_author_email: str,
        pr_diff: str,
        pr_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Проверка PR с AI

        КРИТИЧНО: Только для trusted contributors!
        """
        context = context or {}

        # Проверка 1: Trusted contributor?
        trust_check = self._is_trusted_contributor(pr_author, pr_author_email)

        if not trust_check["trusted"]:
            # [A] ЗАЩИТА - блокируем untrusted
            self.security.audit_logger.log_security_concern(
                agent_id="code_review_ai_secure",
                concern_type="untrusted_contributor_pr",
                details={
                    "pr_author": pr_author,
                    "pr_id": pr_id,
                    "reason": trust_check["reason"],
                },
            )

            return {
                "auto_review": False,
                "message": "⚠️ External contributor - Manual review required",
                "reason": trust_check["reason"],
                "requires_maintainer_review": True,
                "trust_info": trust_check,
                "suggestion": (
                    f"This PR is from an external contributor. "
                    f"After {5 - trust_check['approved_prs']} more approved PRs, "
                    f"they will get automatic AI reviews!"
                ),
            }

        # Для trusted contributors - AI review
        return self._perform_ai_review(pr_diff, pr_id, pr_author, context)

    def _is_trusted_contributor(self, author: str, email: str) -> Dict[str, Any]:
        """
        Проверка доверенности contributor

        Критерии:
        1. Internal email (@company.com)
        2. В списке trusted contributors
        3. История approved PRs (>= 5)
        """
        # Проверка 1: Internal email domain
        for domain in self.TRUSTED_EMAIL_DOMAINS:
            if email.endswith(domain):
                return {
                    "trusted": True,
                    "reason": "Internal team member",
                    "level": "FULL",
                }

        # Проверка 2: В explicit trusted list
        if author in [c.github_id for c in self.trusted_contributors]:
            contributor = next(
                c for c in self.trusted_contributors if c.github_id == author
            )
            return {
                "trusted": True,
                "reason": "In trusted contributors list",
                "level": "FULL",
                "approved_prs": contributor.approved_prs,
            }

        # Проверка 3: История approved PRs
        contribution_history = self._get_contribution_history(author)

        if (
            contribution_history["approved_prs"] >= 5
            and contribution_history["no_security_issues"]
        ):
            # Auto-promote to trusted!
            self._add_to_trusted_list(author, email)

            return {
                "trusted": True,
                "reason": "Auto-promoted based on contribution history",
                "level": "FULL",
                "approved_prs": contribution_history["approved_prs"],
            }

        # Not trusted
        return {
            "trusted": False,
            "reason": "External contributor",
            "approved_prs": contribution_history["approved_prs"],
            "prs_until_trust": max(0, 5 - contribution_history["approved_prs"]),
        }

    def _perform_ai_review(
        self, diff: str, pr_id: str, author: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Выполняет AI review для trusted PR"""

        # [B] Доступ к sensitive code (OK - trusted contributor)
        # [C] Может комментировать (OK)

        # AI анализ
        review_result = self._analyze_code_with_ai(diff)

        # Audit logging
        self.security.audit_logger.log_ai_request(
            agent_id="code_review_ai_secure",
            user_id=author,
            input_hash=self.security._hash_input(diff),
            rule_of_two_config=self.config.get_config_code(),
            approved_by_human=True,  # Trusted contributor = human approved
        )

        return {
            "auto_review": True,
            "review": review_result,
            "pr_id": pr_id,
            "reviewer": "AI-Code-Review",
            "comments": review_result.get("comments", []),
            "approval_status": review_result.get("approval_status"),
            "security_concerns": review_result.get("security_concerns", []),
        }

    def _analyze_code_with_ai(self, diff: str) -> Dict[str, Any]:
        """AI анализ кода (placeholder)"""
        # В продакшене: вызов AI model
        return {
            "approval_status": "APPROVED",
            "comments": [
                {
                    "line": 10,
                    "severity": "INFO",
                    "message": "Consider adding error handling here",
                }
            ],
            "security_concerns": [],
            "quality_score": 0.85,
        }

    def _get_contribution_history(self, author: str) -> Dict[str, Any]:
        """Получает историю contributions (placeholder)"""
        # В продакшене: запрос к GitHub API или БД
        return {"approved_prs": 0, "rejected_prs": 0, "no_security_issues": True}

    def _add_to_trusted_list(self, author: str, email: str):
        """Добавляет contributor в trusted list"""
        contributor = TrustedContributor(
            github_id=author,
            email=email,
            name=author,
            approved_prs=5,
            trusted_since=datetime.now().isoformat(),
        )

        self.trusted_contributors.append(contributor)
        # В продакшене: сохранить в БД

    def _load_trusted_contributors(self) -> List[TrustedContributor]:
        """Загружает список trusted contributors"""
        # В продакшене: загрузка из БД
        return []
