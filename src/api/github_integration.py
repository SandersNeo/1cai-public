"""
GitHub Integration
Автоматический code review для Pull Requests
"""

import os
import hmac
import hashlib
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Request, HTTPException, Header
import httpx

from src.ai.agents.code_review.ai_reviewer import AICodeReviewer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/github")


class GitHubIntegration:
    """Интеграция с GitHub для автоматического code review"""
    
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
        self.reviewer = AICodeReviewer()
        
        if not self.github_token:
            logger.warning("GITHUB_TOKEN not set - GitHub integration disabled")
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """Проверка подписи webhook от GitHub"""
        
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured")
            return True  # В development можно пропустить
        
        mac = hmac.new(
            self.webhook_secret.encode(),
            msg=payload,
            digestmod=hashlib.sha256
        )
        
        expected_signature = 'sha256=' + mac.hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def handle_pull_request_event(
        self,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обработка события Pull Request
        
        Triggers:
        - opened: PR создан
        - synchronize: новые commits
        - reopened: PR переоткрыт
        """
        
        action = event_data.get('action')
        
        if action not in ['opened', 'synchronize', 'reopened']:
            return {'status': 'skipped', 'reason': f'Action {action} not handled'}
        
        pr_number = event_data['number']
        repo_full_name = event_data['repository']['full_name']
        pr_data = event_data['pull_request']
        
        logger.info(f"Processing PR #{pr_number} from {repo_full_name}")
        
        # Получаем измененные файлы
        files_changed = await self._fetch_pr_files(repo_full_name, pr_number)
        
        # Выполняем AI review
        review_result = await self.reviewer.review_pull_request(files_changed)
        
        # Публикуем review в GitHub
        if self.github_token:
            await self._post_review_to_github(
                repo_full_name,
                pr_number,
                review_result
            )
        
        return {
            'status': 'success',
            'pr_number': pr_number,
            'review_status': review_result['overall_status'],
            'issues_found': review_result['metrics']['total_issues']
        }
    
    async def _fetch_pr_files(
        self,
        repo_full_name: str,
        pr_number: int
    ) -> List[Dict[str, str]]:
        """Получение измененных файлов из PR"""
        
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Get PR files
        url = f'https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files'
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Failed to fetch PR files: %s - %s",
                    exc.response.status_code,
                    exc.response.text,
                )
                return []
            except httpx.RequestError as exc:
                logger.error("GitHub request error: %s", exc)
                return []
            
            files = response.json()
        
        # Download content для .bsl файлов
        result = []
        
        for file in files:
            if not file['filename'].endswith('.bsl'):
                continue
            
            # Download raw content
            raw_url = file['raw_url']
            
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
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

                result.append({
                    'filename': file['filename'],
                    'content': content_response.text,
                    'status': file['status'],  # added, modified, removed
                    'additions': file['additions'],
                    'deletions': file['deletions']
                })
        
        return result
    
    async def _post_review_to_github(
        self,
        repo_full_name: str,
        pr_number: int,
        review_result: Dict[str, Any]
    ):
        """Публикация review в GitHub"""
        
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f'https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/reviews'
        
        # Format comments
        comments = self._format_comments_for_github(review_result['file_reviews'])
        
        # Create review
        review_body = {
            'body': review_result['summary'],
            'event': {
                'APPROVED': 'APPROVE',
                'CHANGES_REQUESTED': 'REQUEST_CHANGES',
                'COMMENTED': 'COMMENT'
            }.get(review_result['overall_status'], 'COMMENT'),
            'comments': comments
        }
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    json=review_body
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Failed to post review: %s - %s",
                    exc.response.status_code,
                    exc.response.text,
                )
            except httpx.RequestError as exc:
                logger.error("GitHub request error: %s", exc)
            else:
                logger.info(f"Review posted successfully to PR #{pr_number}")
    
    def _format_comments_for_github(
        self,
        file_reviews: List[Dict]
    ) -> List[Dict]:
        """Форматирование комментариев для GitHub API"""
        
        comments = []
        
        for file_review in file_reviews:
            filename = file_review['filename']
            
            # Собираем все issues
            all_issues = []
            for category in ['security', 'performance', 'best_practices']:
                all_issues.extend(file_review.get('issues', {}).get(category, []))
            
            # Форматируем для GitHub
            for issue in all_issues:
                comment_body = self._format_issue_comment(issue)
                
                comments.append({
                    'path': filename,
                    'line': issue.get('line', 1),
                    'body': comment_body
                })
        
        return comments
    
    def _format_issue_comment(self, issue: Dict) -> str:
        """Форматирование одного issue в Markdown"""
        
        severity_emoji = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }
        
        emoji = severity_emoji.get(issue.get('severity', 'LOW'), '🔵')
        
        comment = f"{emoji} **{issue['type']}** ({issue['severity']})\n\n"
        comment += f"{issue['message']}\n"
        
        if issue.get('description'):
            comment += f"\n**Почему это проблема:**\n{issue['description']}\n"
        
        if issue.get('recommendation'):
            comment += f"\n**Рекомендация:**\n{issue['recommendation']}\n"
        
        if issue.get('performance_impact'):
            comment += f"\n**Performance Impact:** {issue['performance_impact']}\n"
        
        if issue.get('cwe_id'):
            comment += f"\n**CWE:** {issue['cwe_id']}\n"
        
        if issue.get('standard'):
            comment += f"\n📚 **Стандарт:** {issue['standard']}\n"
        
        return comment


# FastAPI endpoints

github_integration = GitHubIntegration()


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None)
):
    """
    GitHub Webhook endpoint
    
    Принимает события от GitHub:
    - pull_request
    - push
    - etc.
    """
    
    # Read payload
    payload = await request.body()
    
    # Verify signature
    if x_hub_signature_256:
        if not github_integration.verify_webhook_signature(payload, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse JSON
    event_data = await request.json()
    
    # Handle event
    if x_github_event == 'pull_request':
        result = await github_integration.handle_pull_request_event(event_data)
        return result
    
    return {'status': 'event_not_handled', 'event_type': x_github_event}


@router.post("/review")
async def manual_review(
    code: str,
    filename: str = "code.bsl"
):
    """Manual code review endpoint (для testing)"""
    
    review_result = await github_integration.reviewer.review_code(code, filename)
    return review_result


