"""
Support service for handling support requests and email notifications.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.support import SupportRequest
from app.schemas.support import SupportRequestCreate


class SupportService:
    """Service for handling support requests."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_support_request(
        self,
        user_id: UUID,
        support_data: SupportRequestCreate,
        user_email: str,
        user_name: str,
    ) -> SupportRequest:
        """Create a new support request and send email notification."""

        # Create support request in database
        support_request = SupportRequest(
            user_id=user_id,
            type=support_data.type,
            description=support_data.description,
        )

        self.db.add(support_request)
        await self.db.commit()
        await self.db.refresh(support_request)

        # Send email notification (fire and forget - don't fail if email fails)
        try:
            await self._send_support_email(
                support_request=support_request,
                user_email=user_email,
                user_name=user_name,
            )
        except Exception as e:
            logger.error(
                f"Failed to send support email for request {support_request.id}: {e}"
            )
            # Don't raise the exception - we still want to return the created support request

        return support_request

    async def _send_support_email(
        self,
        support_request: SupportRequest,
        user_email: str,
        user_name: str,
    ) -> None:
        """Send email notification to support team."""

        # TODO: Implement email sending
        # For now, we'll just log the email content
        # In production, you would integrate with an email service like SendGrid, AWS SES, etc.

        #         subject = f"[Support] {support_request.type.title()} - {support_request.id}"

        #         email_body = f"""
        # New support request received:

        # Request ID: {support_request.id}
        # Type: {support_request.type.title()}
        # User: {user_name} ({user_email})
        # User ID: {support_request.user_id}
        # Created: {support_request.created_at}

        # Description:
        # {support_request.description}

        # ---
        # This is an automated message from Promptly Social Scribe.
        #         """.strip()

        # TODO: Implement actual email sending
        # Example with SMTP (you would need to configure SMTP settings):
        # await self._send_smtp_email(
        #     to_email="support@promptly.social",
        #     subject=subject,
        #     body=email_body,
        # )
        pass

    async def _send_smtp_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
    ) -> None:
        """Send email via SMTP (placeholder implementation)."""

        # This is a placeholder implementation
        # You would need to configure SMTP settings in your environment

        if not from_email:
            from_email = "noreply@promptly.social"

        # Create message
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # This would require SMTP configuration
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.starttls()
        # server.login(smtp_username, smtp_password)
        # text = msg.as_string()
        # server.sendmail(from_email, to_email, text)
        # server.quit()

        logger.info(f"Email would be sent from {from_email} to {to_email}")
