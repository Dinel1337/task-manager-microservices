"""Email service for sending notifications."""

from email.message import EmailMessage
from typing import Final

from aiosmtplib import SMTP, SMTPException
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt

from task_notification.core.config import settings
from task_notification.core.exceptions.base import BaseServiceException
from task_notification.core.logger import get_logger, log

logger = get_logger(__name__)


class EmailSendError(BaseServiceException):
    """Ошибка отправки email."""

    def __init__(self, recipient: str, error: str):
        super().__init__(f"Failed to send email to {recipient}: {error}")


class EmailService:
    """Сервис для отправки email уведомлений через SMTP."""

    _MAX_RETRIES: Final[int] = 3
    _SMTP_ERRORS: Final[tuple] = (SMTPException, ConnectionError, TimeoutError, OSError)

    def __init__(self):
        self._smtp_host = settings.SMTP_HOST
        self._smtp_port = settings.SMTP_PORT
        self._smtp_username = settings.SMTP_USERNAME
        self._smtp_password = settings.SMTP_PASSWORD
        self._from_email = settings.SMTP_FROM_EMAIL
        self._use_tls = settings.SMTP_USE_TLS
        self._start_tls = settings.SMTP_START_TLS

    @log(logger)
    async def send_task_notification(
        self,
        recipient: str,
        task_id: int,
        task_title: str,
        task_description: str,
        event_type: str,
        task_status: str | None = None,
        task_priority: str | None = None,
    ) -> None:
        """
        Отправить email уведомление о событии задачи.

        Args:
            recipient: Email получателя
            task_id: ID задачи
            task_title: Название задачи
            task_description: Описание задачи
            event_type: Тип события (created, updated, deleted)
            task_status: Статус задачи (опционально)
            task_priority: Приоритет задачи (опционально)

        Raises:
            EmailSendError: Если не удалось отправить письмо
        """
        message = self._build_message(
            recipient=recipient,
            task_id=task_id,
            task_title=task_title,
            task_description=task_description,
            event_type=event_type,
            task_status=task_status,
            task_priority=task_priority,
        )

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self._MAX_RETRIES),
            retry=retry_if_exception_type(self._SMTP_ERRORS),
            reraise=True,
        ):
            with attempt:
                try:
                    await self._send_email(message)
                    logger.info(
                        f"Email sent successfully to {recipient} "
                        f"for task {task_id} ({event_type})"
                    )
                except self._SMTP_ERRORS as e:
                    error_msg = str(e)
                    logger.error(f"SMTP error: {error_msg}")
                    raise EmailSendError(recipient, error_msg)

    async def _send_email(self, message: EmailMessage) -> None:
        """Отправить email через SMTP."""
        smtp = SMTP(
            hostname=self._smtp_host,
            port=self._smtp_port,
            username=self._smtp_username,
            password=self._smtp_password,
            use_tls=self._use_tls,
            start_tls=self._start_tls,
        )

        async with smtp:
            await smtp.send_message(message)

    def _build_message(
        self,
        recipient: str,
        task_id: int,
        task_title: str,
        task_description: str,
        event_type: str,
        task_status: str | None = None,
        task_priority: str | None = None,
    ) -> EmailMessage:
        """Сформировать email сообщение."""
        message = EmailMessage()
        message["From"] = self._from_email
        message["To"] = recipient
        message["Subject"] = self._build_subject(event_type, task_title)

        # Plain text content
        text_content = self._build_text_content(
            task_id=task_id,
            task_title=task_title,
            task_description=task_description,
            event_type=event_type,
            task_status=task_status,
            task_priority=task_priority,
        )
        message.set_content(text_content)

        # HTML content
        html_content = self._build_html_content(
            task_id=task_id,
            task_title=task_title,
            task_description=task_description,
            event_type=event_type,
            task_status=task_status,
            task_priority=task_priority,
        )
        message.add_alternative(html_content, subtype="html")

        return message

    def _build_subject(self, event_type: str, task_title: str) -> str:
        """Сформировать тему письма."""
        event_labels = {
            "created": "📝 New Task Created",
            "updated": "✏️ Task Updated",
            "deleted": "🗑️ Task Deleted",
        }
        label = event_labels.get(event_type, f"Task {event_type.title()}")
        return f"{label}: {task_title}"

    def _build_text_content(
        self,
        task_id: int,
        task_title: str,
        task_description: str,
        event_type: str,
        task_status: str | None,
        task_priority: str | None,
    ) -> str:
        """Сформировать текстовое содержимое письма."""
        lines = [
            f"Task {event_type.upper()}",
            "",
            f"Task ID: {task_id}",
            f"Title: {task_title}",
            "",
            "Description:",
            task_description,
            "",
        ]

        if task_status:
            lines.append(f"Status: {task_status}")
        if task_priority:
            lines.append(f"Priority: {task_priority}")

        lines.extend([
            "",
            "---",
            "Task Manager Notification System",
        ])

        return "\n".join(lines)

    def _build_html_content(
        self,
        task_id: int,
        task_title: str,
        task_description: str,
        event_type: str,
        task_status: str | None,
        task_priority: str | None,
    ) -> str:
        """Сформировать HTML содержимое письма."""
        event_colors = {
            "created": "#4CAF50",
            "updated": "#2196F3",
            "deleted": "#F44336",
        }
        color = event_colors.get(event_type, "#9E9E9E")

        status_html = f'<p><strong>Status:</strong> {task_status}</p>' if task_status else ""
        priority_html = f'<p><strong>Priority:</strong> {task_priority}</p>' if task_priority else ""

        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: {color}; border-bottom: 2px solid {color}; padding-bottom: 10px;">
                        Task {event_type.title()}
                    </h2>
                    <div style="margin: 20px 0;">
                        <p><strong>Task ID:</strong> {task_id}</p>
                        <p><strong>Title:</strong> {task_title}</p>
                        <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid {color}; margin: 15px 0;">
                            <strong>Description:</strong><br>
                            <span style="white-space: pre-wrap;">{task_description}</span>
                        </div>
                        {status_html}
                        {priority_html}
                    </div>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        Task Manager Notification System
                    </p>
                </div>
            </body>
        </html>
        """

