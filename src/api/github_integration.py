# [NEXUS IDENTITY] ID: 5086129874185795728 | DATE: 2025-11-19

"""
GitHub Integration
Версия: 2.1.0

Улучшения:
- Retry logic для GitHub API calls
- Улучшена обработка ошибок
- Structured logging
- Input validation и sanitization
"""

import asyncio
import hashlib
import hmac
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Header, HTTPException, Request

from src.ai.agents.code_review.ai_reviewer import AICodeReviewer
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

router = APIRouter(prefix="/api/github")


class GitHubIntegration:
    """Интеграция с GitHub для автоматического code review"""

    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
        self.reviewer = AICodeReviewer()

        if not self.github_token:
            logger.warning("GITHUB_TOKEN not set - GitHub integration disabled")

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Проверка подписи webhook от GitHub"""

        if not self.webhook_secret:
            logger.warning("Webhook secret not configured")
            return True  # В development можно пропустить

        mac = hmac.new(
            self.webhook_secret.encode(), msg=payload, digestmod=hashlib.sha256
        )

        expected_signature = "sha256=" + mac.hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    async def handle_pull_request_event(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обработка события Pull Request с input validation

        Triggers:
        - opened: PR создан
        - synchronize: новые commits
        - reopened: PR переоткрыт
        """
        # Input validation
        if not isinstance(event_data, dict):
            logger.warning(
                "Invalid event_data type in handle_pull_request_event",
                extra={"event_data_type": type(event_data).__name__},
            )
            return {"status": "error", "reason": "Invalid event data format"}

        action = event_data.get("action")

        if action not in ["opened", "synchronize", "reopened"]:
            return {"status": "skipped", "reason": f"Action {action} not handled"}

        # Validate required fields
        if "number" not in event_data:
            logger.warning("Missing 'number' field in event_data")
            return {"status": "error", "reason": "Missing PR number"}

        if "repository" not in event_data or not isinstance(
            event_data["repository"], dict
        ):
            logger.warning("Missing or invalid 'repository' field in event_data")
            return {"status": "error", "reason": "Missing repository information"}

        pr_number = event_data["number"]
        repo_full_name = event_data["repository"].get("full_name")

        if not isinstance(pr_number, int) or pr_number <= 0:
            logger.warning(
                "Invalid pr_number in handle_pull_request_event",
                extra={
                    "pr_number": pr_number,
                    "pr_number_type": type(pr_number).__name__,
                },
            )
            return {"status": "error", "reason": "Invalid PR number"}

        if not isinstance(repo_full_name, str) or not repo_full_name.strip():
            logger.warning(
                "Invalid repo_full_name in handle_pull_request_event",
                extra={"repo_full_name": repo_full_name},
            )
            return {"status": "error", "reason": "Invalid repository name"}

        # Sanitize repo name
        repo_full_name = repo_full_name.replace("..", "").replace("//", "/")

        pr_data = event_data.get("pull_request", {})

        logger.info(
            "Processing PR event",
            extra={"pr_number": pr_number, "repo": repo_full_name, "action": action},
        )

        # Получаем измененные файлы
        files_changed = await self._fetch_pr_files(repo_full_name, pr_number)

        # Выполняем AI review
        review_result = await self.reviewer.review_pull_request(files_changed)

        # Публикуем review в GitHub
        if self.github_token:
            await self._post_review_to_github(repo_full_name, pr_number, review_result)

        return {
            "status": "success",
            "pr_number": pr_number,
            "review_status": review_result["overall_status"],
            "issues_found": review_result["metrics"]["total_issues"],
        }

    async def _fetch_pr_files(
        self, repo_full_name: str, pr_number: int, max_retries: int = 3
    ) -> List[Dict[str, str]]:
        """
        Получение измененных файлов из PR с retry logic

        Args:
            repo_full_name: Repository full name (owner/repo)
            pr_number: Pull request number
            max_retries: Maximum retry attempts
        """
        # Input validation
        if not repo_full_name or not isinstance(repo_full_name, str):
            raise ValueError(f"Invalid repo_full_name: {repo_full_name}")
        if not isinstance(pr_number, int) or pr_number <= 0:
            raise ValueError(f"Invalid pr_number: {pr_number}")

        # Sanitize repo name (prevent path traversal)
        repo_full_name = repo_full_name.replace("..", "").replace("//", "/")

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Get PR files
        url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files"

        base_delay = 1.0
        last_exception = None

        for attempt in range(max_retries):
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0)
            ) as client:
                try:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    files = response.json()

                    if attempt > 0:
                        logger.info(
                            f"Successfully fetched PR files on attempt {attempt + 1}",
                            extra={
                                "repo": repo_full_name,
                                "pr_number": pr_number,
                                "attempt": attempt + 1,
                                "files_count": len(files),
                            },
                        )

                    break

                except httpx.HTTPStatusError as exc:
                    last_exception = exc
                    is_retryable = exc.response.status_code >= 500

                    if attempt == max_retries - 1 or not is_retryable:
                        logger.error(
                            f"Failed to fetch PR files: {exc.response.status_code} - {exc.response.text}",
                            extra={
                                "repo": repo_full_name,
                                "pr_number": pr_number,
                                "status_code": exc.response.status_code,
                                "attempt": attempt + 1,
                                "is_retryable": is_retryable,
                            },
                        )
                        return []

                    delay = base_delay * (2**attempt)
                    logger.warning(
                        f"GitHub API error, retrying in {delay}s (attempt {attempt + 1}/{max_retries})",
                        extra={
                            "repo": repo_full_name,
                            "pr_number": pr_number,
                            "status_code": exc.response.status_code,
                            "attempt": attempt + 1,
                            "delay": delay,
                        },
                    )
                    await asyncio.sleep(delay)

                except httpx.RequestError as exc:
                    last_exception = exc
                    if attempt == max_retries - 1:
                        logger.error(
                            f"GitHub request error: {exc}",
                            extra={
                                "repo": repo_full_name,
                                "pr_number": pr_number,
                                "error_type": type(exc).__name__,
                                "attempt": attempt + 1,
                            },
                            exc_info=True,
                        )
                        return []

                    delay = base_delay * (2**attempt)
                    logger.warning(
                        f"GitHub request error, retrying in {delay}s: {exc}",
                        extra={
                            "repo": repo_full_name,
                            "pr_number": pr_number,
                            "error_type": type(exc).__name__,
                            "attempt": attempt + 1,
                            "delay": delay,
                        },
                    )
                    await asyncio.sleep(delay)

        if last_exception:
            return []

        # Download content для .bsl файлов
        result = []

        for file in files:
            if not file["filename"].endswith(".bsl"):
                continue

            # Download raw content
            raw_url = file["raw_url"]

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0)
            ) as client:
                try:
                    content_response = await client.get(raw_url, headers=headers)
                    content_response.raise_for_status()
                except httpx.RequestError as exc:
                    logger.error("Failed to download %s: %s", raw_url, exc)
                    continue
                except httpx.HTTPStatusError as exc:
                    logger.error(
                        "Failed to download %s: %s", raw_url, exc.response.status_code
                    )
                    continue

                result.append(
                    {
                        "filename": file["filename"],
                        "content": content_response.text,
                        "status": file["status"],  # added, modified, removed
                        "additions": file["additions"],
                        "deletions": file["deletions"],
                    }
                )

        return result

    async def _post_review_to_github(
        self,
        repo_full_name: str,
        pr_number: int,
        review_result: Dict[str, Any],
        max_retries: int = 3,
    ):
        """Публикация review в GitHub с retry logic и input validation"""
        # Input validation
        if not repo_full_name or not isinstance(repo_full_name, str):
            logger.warning(
                "Invalid repo_full_name in _post_review_to_github",
                extra={
                    "repo_full_name_type": (
                        type(repo_full_name).__name__ if repo_full_name else None
                    )
                },
            )
            return

        if not isinstance(pr_number, int) or pr_number <= 0:
            logger.warning(
                "Invalid pr_number in _post_review_to_github",
                extra={
                    "pr_number": pr_number,
                    "pr_number_type": type(pr_number).__name__,
                },
            )
            return

        if not isinstance(review_result, dict):
            logger.warning(
                "Invalid review_result type in _post_review_to_github",
                extra={"review_result_type": type(review_result).__name__},
            )
            return

        # Sanitize repo name
        repo_full_name = repo_full_name.replace("..", "").replace("//", "/")

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/reviews"

        # Format comments
        try:
            comments = self._format_comments_for_github(
                review_result.get("file_reviews", [])
            )
        except Exception as e:
            logger.error(
                f"Error formatting comments: {e}",
                extra={"error_type": type(e).__name__},
                exc_info=True,
            )
            comments = []

        # Create review
        review_body = {
            "body": review_result.get("summary", "Code review completed"),
            "event": {
                "APPROVED": "APPROVE",
                "CHANGES_REQUESTED": "REQUEST_CHANGES",
                "COMMENTED": "COMMENT",
            }.get(review_result.get("overall_status", "COMMENTED"), "COMMENT"),
            "comments": comments,
        }

        base_delay = 1.0
        last_exception = None

        for attempt in range(max_retries):
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0)
            ) as client:
                try:
                    response = await client.post(url, headers=headers, json=review_body)
                    response.raise_for_status()

                    if attempt > 0:
                        logger.info(
                            f"Successfully posted review on attempt {attempt + 1}",
                            extra={
                                "repo": repo_full_name,
                                "pr_number": pr_number,
                                "attempt": attempt + 1,
                            },
                        )

                    return

                except httpx.HTTPStatusError as exc:
                    last_exception = exc
                    is_retryable = exc.response.status_code >= 500

                    if attempt == max_retries - 1 or not is_retryable:
                        logger.error(
                            f"Failed to post review: {exc.response.status_code} - {exc.response.text}",
                            extra={
                                "repo": repo_full_name,
                                "pr_number": pr_number,
                                "status_code": exc.response.status_code,
                                "attempt": attempt + 1,
                                "is_retryable": is_retryable,
                            },
                            exc_info=True,
                        )
                        return

                    delay = base_delay * (2**attempt)
                    logger.warning(
                        f"GitHub API error posting review, retrying in {delay}s (attempt {attempt + 1}/{max_retries})",
                        extra={
                            "repo": repo_full_name,
                            "pr_number": pr_number,
                            "status_code": exc.response.status_code,
                            "attempt": attempt + 1,
                            "delay": delay,
                        },
                    )
                    await asyncio.sleep(delay)

                except httpx.RequestError as exc:
                    last_exception = exc
                    if attempt == max_retries - 1:
                        logger.error(
                            f"GitHub request error posting review: {exc}",
                            extra={
                                "repo": repo_full_name,
                                "pr_number": pr_number,
                                "error_type": type(exc).__name__,
                                "attempt": attempt + 1,
                            },
                            exc_info=True,
                        )
                        return

                    delay = base_delay * (2**attempt)
                    logger.warning(
                        f"GitHub request error posting review, retrying in {delay}s: {exc}",
                        extra={
                            "repo": repo_full_name,
                            "pr_number": pr_number,
                            "error_type": type(exc).__name__,
                            "attempt": attempt + 1,
                            "delay": delay,
                        },
                    )
                    await asyncio.sleep(delay)

        if last_exception:
            logger.error(
                f"Failed to post review after {max_retries} attempts",
                extra={
                    "repo": repo_full_name,
                    "pr_number": pr_number,
                    "max_retries": max_retries,
                },
            )
        else:
            logger.info(
                f"Review posted successfully to PR #{pr_number}",
                extra={"repo": repo_full_name, "pr_number": pr_number},
            )

    async def post_pr_comment(
        self,
        repo: str,
        pr_number: int,
        comment: str,
        github_token: Optional[str] = None,
        max_retries: int = 3,
    ) -> bool:
        """
        Публикация одиночного комментария в PR с input validation и retry logic.
        Совместима с тестами, использующими заглушки httpx.AsyncClient.
        """
        # Input validation
        if not isinstance(repo, str) or not repo.strip():
            logger.warning(
                "Invalid repo in post_pr_comment",
                extra={"repo_type": type(repo).__name__ if repo else None},
            )
            return False

        if not isinstance(pr_number, int) or pr_number <= 0:
            logger.warning(
                "Invalid pr_number in post_pr_comment",
                extra={
                    "pr_number": pr_number,
                    "pr_number_type": type(pr_number).__name__,
                },
            )
            return False

        if not isinstance(comment, str) or not comment.strip():
            logger.warning(
                "Invalid comment in post_pr_comment",
                extra={"comment_type": type(comment).__name__ if comment else None},
            )
            return False

        # Limit comment length (prevent DoS)
        max_comment_length = 65536  # GitHub limit
        if len(comment) > max_comment_length:
            logger.warning(
                "Comment too long in post_pr_comment",
                extra={
                    "comment_length": len(comment),
                    "max_length": max_comment_length,
                },
            )
            comment = comment[:max_comment_length]

        # Sanitize repo name
        repo = repo.replace("..", "").replace("//", "/")

        token = github_token or self.github_token
        if not token:
            logger.warning("Skip PR comment: GITHUB_TOKEN not configured")
            return False

        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        base_delay = 1.0
        timeout_config = httpx.Timeout(10.0, connect=5.0)
        last_exception = None

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=timeout_config) as client:
                    response = await client.post(
                        url, headers=headers, json={"body": comment}
                    )

                if response.status_code in (200, 201):
                    if attempt > 0:
                        logger.info(
                            "Successfully posted PR comment on retry",
                            extra={
                                "repo": repo,
                                "pr_number": pr_number,
                                "attempt": attempt + 1,
                            },
                        )
                    return True

                if response.status_code >= 500 and attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    logger.warning(
                        f"GitHub API error posting comment, retrying in {delay}s (attempt {attempt + 1}/{max_retries})",
                        extra={
                            "repo": repo,
                            "pr_number": pr_number,
                            "status_code": response.status_code,
                            "attempt": attempt + 1,
                            "delay": delay,
                        },
                    )
                    await asyncio.sleep(delay)
                    continue

                logger.error(
                    "GitHub comment error",
                    extra={
                        "repo": repo,
                        "pr_number": pr_number,
                        "status_code": response.status_code,
                        "response_text": response.text[:500],
                    },
                )
                return False

            except httpx.TimeoutException as e:
                last_exception = e
                if attempt == max_retries - 1:
                    logger.error(
                        "Timeout posting PR comment after all retries",
                        extra={
                            "repo": repo,
                            "pr_number": pr_number,
                            "max_retries": max_retries,
                        },
                        exc_info=True,
                    )
                    return False

                delay = base_delay * (2**attempt)
                logger.warning(
                    f"Timeout posting PR comment, retrying in {delay}s (attempt {attempt + 1}/{max_retries})",
                    extra={
                        "repo": repo,
                        "pr_number": pr_number,
                        "attempt": attempt + 1,
                        "delay": delay,
                    },
                )
                await asyncio.sleep(delay)

            except httpx.RequestError as e:
                last_exception = e
                if attempt == max_retries - 1:
                    logger.error(
                        "Request error posting PR comment after all retries",
                        extra={
                            "repo": repo,
                            "pr_number": pr_number,
                            "error_type": type(e).__name__,
                            "max_retries": max_retries,
                        },
                        exc_info=True,
                    )
                    return False

                delay = base_delay * (2**attempt)
                logger.warning(
                    f"Request error posting PR comment, retrying in {delay}s (attempt {attempt + 1}/{max_retries})",
                    extra={
                        "repo": repo,
                        "pr_number": pr_number,
                        "error_type": type(e).__name__,
                        "attempt": attempt + 1,
                        "delay": delay,
                    },
                )
                await asyncio.sleep(delay)

        return False

    def _format_comments_for_github(self, file_reviews: List[Dict]) -> List[Dict]:
        """Форматирование комментариев для GitHub API"""

        comments = []

        for file_review in file_reviews:
            filename = file_review["filename"]

            # Собираем все issues
            all_issues = []
            for category in ["security", "performance", "best_practices"]:
                all_issues.extend(file_review.get("issues", {}).get(category, []))

            # Форматируем для GitHub
            for issue in all_issues:
                comment_body = self._format_issue_comment(issue)

                comments.append(
                    {
                        "path": filename,
                        "line": issue.get("line", 1),
                        "body": comment_body,
                    }
                )

        return comments

    def _format_issue_comment(self, issue: Dict) -> str:
        """Форматирование одного issue в Markdown"""

        severity_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}

        emoji = severity_emoji.get(issue.get("severity", "LOW"), "🔵")

        comment = f"{emoji} **{issue['type']}** ({issue['severity']})\n\n"
        comment += f"{issue['message']}\n"

        if issue.get("description"):
            comment += f"\n**Почему это проблема:**\n{issue['description']}\n"

        if issue.get("recommendation"):
            comment += f"\n**Рекомендация:**\n{issue['recommendation']}\n"

        if issue.get("performance_impact"):
            comment += f"\n**Performance Impact:** {issue['performance_impact']}\n"

        if issue.get("cwe_id"):
            comment += f"\n**CWE:** {issue['cwe_id']}\n"

        if issue.get("standard"):
            comment += f"\n📚 **Стандарт:** {issue['standard']}\n"

        return comment


# FastAPI endpoints

github_integration = GitHubIntegration()


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
):
    """
    GitHub Webhook endpoint с input validation и timeout handling

    Принимает события от GitHub:
    - pull_request
    - push
    - etc.
    """
    try:
        # Read payload with timeout
        payload = await asyncio.wait_for(request.body(), timeout=30.0)

        # Input validation for payload size (prevent DoS)
        max_payload_size = 10 * 1024 * 1024  # 10 MB
        if len(payload) > max_payload_size:
            logger.warning(
                "Payload too large in github_webhook",
                extra={"payload_size": len(payload), "max_size": max_payload_size},
            )
            raise HTTPException(status_code=413, detail="Payload too large")

        # Verify signature
        if x_hub_signature_256:
            if (
                not isinstance(x_hub_signature_256, str)
                or not x_hub_signature_256.strip()
            ):
                logger.warning("Invalid signature header in github_webhook")
                raise HTTPException(status_code=401, detail="Invalid signature format")

            if not github_integration.verify_webhook_signature(
                payload, x_hub_signature_256
            ):
                logger.warning(
                    "Invalid webhook signature", extra={"event_type": x_github_event}
                )
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse JSON with timeout
        try:
            event_data = await asyncio.wait_for(request.json(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.error("Timeout parsing JSON in github_webhook")
            raise HTTPException(status_code=504, detail="Timeout parsing request")
        except Exception as e:
            logger.error(
                "Error parsing JSON in github_webhook",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # Validate event type
        if not x_github_event or not isinstance(x_github_event, str):
            logger.warning("Missing or invalid x_github_event header")
            return {"status": "error", "reason": "Missing event type"}

        # Limit event type length
        if len(x_github_event) > 100:
            logger.warning(
                "Event type too long in github_webhook",
                extra={"event_type_length": len(x_github_event)},
            )
            x_github_event = x_github_event[:100]

        # Handle event
        if x_github_event == "pull_request":
            result = await asyncio.wait_for(
                github_integration.handle_pull_request_event(event_data),
                timeout=60.0,  # 60 seconds for PR processing
            )
            return result

        logger.info("Unhandled GitHub event type", extra={"event_type": x_github_event})
        return {"status": "event_not_handled", "event_type": x_github_event}

    except HTTPException:
        raise
    except asyncio.TimeoutError:
        logger.error("Timeout in github_webhook")
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        logger.error(
            "Unexpected error in github_webhook",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "event_type": x_github_event,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/review")
async def manual_review(code: str, filename: str = "code.bsl"):
    """
    Manual code review endpoint с input validation и timeout handling (для testing)
    """
    # Input validation
    if not isinstance(code, str):
        logger.warning(
            "Invalid code type in manual_review",
            extra={"code_type": type(code).__name__},
        )
        raise HTTPException(status_code=400, detail="Code must be a string")

    # Limit code length (prevent DoS)
    max_code_length = 10 * 1024 * 1024  # 10 MB
    if len(code) > max_code_length:
        logger.warning(
            "Code too long in manual_review",
            extra={"code_length": len(code), "max_length": max_code_length},
        )
        raise HTTPException(status_code=413, detail="Code too large")

    if not isinstance(filename, str) or not filename.strip():
        logger.warning(
            "Invalid filename in manual_review",
            extra={"filename_type": type(filename).__name__ if filename else None},
        )
        filename = "code.bsl"

    # Sanitize filename (prevent path traversal)
    filename = filename.replace("..", "").replace("/", "_").replace("\\", "_")
    if len(filename) > 255:
        filename = filename[:255]

    try:
        # Timeout для review операции (60 секунд)
        review_result = await asyncio.wait_for(
            github_integration.reviewer.review_code(code, filename), timeout=60.0
        )

        logger.info(
            "Manual review completed",
            extra={
                "filename": filename,
                "code_length": len(code),
                "review_status": review_result.get("overall_status", "unknown"),
            },
        )

        return review_result

    except asyncio.TimeoutError:
        logger.error(
            "Timeout in manual_review",
            extra={"file_name": filename, "code_length": len(code)},
        )
        raise HTTPException(status_code=504, detail="Review operation timed out")
    except Exception as e:
        logger.error(
            "Error in manual_review",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "filename": filename,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred during code review"
        )
