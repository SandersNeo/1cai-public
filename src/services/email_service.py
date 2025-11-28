# [NEXUS IDENTITY] ID: -6143009017350627894 | DATE: 2025-11-23

"""
Email Service for Alerting and Notifications
Версия: 1.0.0

Поддерживает:
- SMTP email отправку (Gmail, SendGrid, AWS SES)
- HTML и plain text форматы
- Model drift alerts
- Rate limiting для предотвращения спама
- Graceful degradation если email не настроен
"""

import logging
import os
import re
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications"""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
    ):
        """
        Initialize Email Service

        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: Sender email address
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("FROM_EMAIL", self.smtp_user)

        # Rate limiting
        self.last_alert_time: Dict[str, float] = {}
        self.min_alert_interval = int(
            os.getenv("EMAIL_RATE_LIMIT_SECONDS", "3600"))  # 1 hour default

        # Validate configuration
        if not all([self.smtp_user, self.smtp_password]):
            logger.warning(
                "Email service not configured - alerts will be logged only. "
                "Set SMTP_USER and SMTP_PASSWORD environment variables."
            )
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Email service initialized: {self.smtp_host}:{self.smtp_port}")

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """
        Send email notification

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body_html: HTML body
            body_text: Plain text body (fallback)

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.warning(
                f"Email not sent (service disabled): {subject}",
                extra={"recipients": len(to_emails)},
            )
            return False

        # Validate email addresses
        valid_emails = self._validate_emails(to_emails)
        if not valid_emails:
            logger.error("No valid email addresses provided")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = ", ".join(valid_emails)
            msg["Subject"] = subject

            # Add plain text version
            if body_text:
                part1 = MIMEText(body_text, "plain", "utf-8")
                msg.attach(part1)

            # Add HTML version
            part2 = MIMEText(body_html, "html", "utf-8")
            msg.attach(part2)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(
                f"Email sent successfully",
                extra={
                    "subject": subject,
                    "recipients": len(valid_emails),
                    "to": valid_emails,
                },
            )
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(
                f"SMTP authentication failed: {e}. Check SMTP_USER and SMTP_PASSWORD.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return False

    def send_drift_alert(self, drift_models: List[Dict], to_emails: List[str]) -> bool:
        """
        Send model drift alert with rate limiting

        Args:
            drift_models: List of models with drift info
                Example: [{"model": "classification", "drift_score": 0.18}]
            to_emails: Recipients

        Returns:
            True if sent successfully
        """
        # Check rate limit
        alert_key = "drift_alert"
        if not self._check_rate_limit(alert_key):
            logger.info(
                f"Drift alert skipped due to rate limiting " f"(min interval: {self.min_alert_interval}s)")
            return False

        subject = f"🚨 Model Drift Alert - {len(drift_models)} models affected"

        # HTML body
        html_body = self._generate_drift_alert_html(drift_models)

        # Plain text fallback
        text_body = self._generate_drift_alert_text(drift_models)

        result = self.send_email(to_emails, subject, html_body, text_body)

        if result:
            self.last_alert_time[alert_key] = time.time()

        return result

    def _check_rate_limit(self, alert_key: str) -> bool:
        """Check if alert can be sent (rate limiting)"""
        if alert_key not in self.last_alert_time:
            return True

        elapsed = time.time() - self.last_alert_time[alert_key]
        return elapsed >= self.min_alert_interval

    def _validate_emails(self, emails: List[str]) -> List[str]:
        """Validate email addresses"""
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        valid_emails = []
        for email in emails:
            email = email.strip()
            if re.match(email_regex, email):
                valid_emails.append(email)
            else:
                logger.warning("Invalid email address: %s", email)

        return valid_emails

    def _generate_drift_alert_html(self, drift_models: List[Dict]) -> str:
        """Generate HTML for drift alert"""
        models_html = ""
        for model in drift_models:
            drift_pct = model["drift_score"] * 100
            models_html += f"""
            <tr>
                <td style="padding: 12px; border: 1px solid #ddd;">{model['model']}</td>
                <td style="padding: 12px; border: 1px solid #ddd; color: #d32f2f; font-weight: bold;">
                    {drift_pct:.1f}%
                </td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="background-color: #d32f2f; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h2 style="margin: 0; font-size: 24px;">🚨 Model Drift Detected</h2>
                </div>

                <div style="padding: 20px;">
                    <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                        The following models have exceeded the drift threshold (15%):
                    </p>

                    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                        <thead>
                            <tr style="background-color: #f5f5f5;">
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: left; font-weight: 600;">Model</th>
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: left; font-weight: 600;">Drift Score</th>
                            </tr>
                        </thead>
                        <tbody>
                            {models_html}
                        </tbody>
                    </table>

                    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0 0 10px 0; font-weight: 600; color: #856404;">⚠️ Action Required:</p>
                        <ul style="margin: 0; padding-left: 20px; color: #856404;">
                            <li>Review model performance metrics in MLflow</li>
                            <li>Consider retraining affected models</li>
                            <li>Check for data distribution changes</li>
                            <li>Investigate potential data quality issues</li>
                        </ul>
                    </div>

                    <p style="color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                        This is an automated alert from <strong>1C AI Stack ML Pipeline</strong><br>
                        Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    def _generate_drift_alert_text(self, drift_models: List[Dict]) -> str:
        """Generate plain text for drift alert"""
        models_text = "\n".join(
            [f"  - {m['model']}: {m['drift_score']*100:.1f}%" for m in drift_models])

        return f"""
MODEL DRIFT ALERT
================

The following models have exceeded the drift threshold (15%):

{models_text}

Action Required:
- Review model performance metrics in MLflow
- Consider retraining affected models
- Check for data distribution changes
- Investigate potential data quality issues

---
This is an automated alert from 1C AI Stack ML Pipeline
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}
        """

    def get_stats(self) -> Dict:
        """Get email service statistics"""
        return {
            "enabled": self.enabled,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "from_email": self.from_email,
            "rate_limit_seconds": self.min_alert_interval,
            "last_alerts": {
                key: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
                for key, timestamp in self.last_alert_time.items()
            },
        }


# Global instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get singleton email service"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
