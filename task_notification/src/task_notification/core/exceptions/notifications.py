from typing import Final

from task_notification.core.exceptions.base import BaseServiceException, EntityNotFoundException


class NotificationNotFoundException(EntityNotFoundException):
    """Уведомление не найдено."""

    def __init__(self, notification_id: int) -> None:
        super().__init__(entity="Notification", entity_id=notification_id)


class NotificationValidationError(BaseServiceException):
    """Ошибка валидации уведомления."""
    pass


class NotificationSendError(BaseServiceException):
    """Ошибка отправки уведомления."""

    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Не удалось отправить уведомление {notification_id}: {detail}"

    def __init__(self, notification_id: int, detail: str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(
            notification_id=notification_id,
            detail=detail,
        )
        super().__init__(self.message)


class InvalidNotificationTypeError(BaseServiceException):
    """Неверный тип уведомления."""

    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Неверный тип уведомления: {notification_type}"

    def __init__(self, notification_type: str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(notification_type=notification_type)
        super().__init__(self.message)



