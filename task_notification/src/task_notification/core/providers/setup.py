from typing import AsyncIterator

from dishka import Provider, Scope, make_async_container, make_container, provide

from task_notification.core.config import settings
from task_notification.core.providers.config_provider import ConfigProvider
from task_notification.domain.metrics.use_case import GetNotificationsMetricsUseCase
from task_notification.domain.use_cases.create_notification import CreateNotificationUseCase
from task_notification.domain.use_cases.get_notification_by_id import GetNotificationByIdUseCase
from task_notification.domain.use_cases.get_notifications import GetNotificationsUseCase
from task_notification.domain.use_cases.send_pending_notifications import SendPendingNotificationsUseCase
from task_notification.domain.use_cases.update_notification_status import UpdateNotificationStatusUseCase
from task_notification.infrastructure.email.email_service import EmailService
from task_notification.infrastructure.postgres.database import Database
from task_notification.infrastructure.postgres.repository import NotificationRepository


# Config container для RabbitMQ
config_container = make_container(ConfigProvider())


class InfrastructureProvider(Provider):
    scope = Scope.APP

    @provide
    def get_database(self) -> Database:
        return Database(settings.postgres_url)


class RepositoryProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_notification_repository(self) -> NotificationRepository:
        return NotificationRepository()


class ServiceProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_email_service(self) -> EmailService:
        return EmailService()


class UseCaseProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_create_notification(
        self,
        database: Database,
        repository: NotificationRepository,
    ) -> CreateNotificationUseCase:
        return CreateNotificationUseCase(database, repository)

    @provide
    def get_get_notification_by_id(
        self,
        database: Database,
        repository: NotificationRepository,
    ) -> GetNotificationByIdUseCase:
        return GetNotificationByIdUseCase(database, repository)

    @provide
    def get_update_notification_status(
        self,
        database: Database,
        repository: NotificationRepository,
    ) -> UpdateNotificationStatusUseCase:
        return UpdateNotificationStatusUseCase(database, repository)

    @provide
    def get_get_notifications(
        self,
        database: Database,
        repository: NotificationRepository,
    ) -> GetNotificationsUseCase:
        return GetNotificationsUseCase(database, repository)

    @provide
    def get_send_pending_notifications(
        self,
        database: Database,
        repository: NotificationRepository,
        email_service: EmailService,
    ) -> SendPendingNotificationsUseCase:
        return SendPendingNotificationsUseCase(database, repository, email_service)


class MetricsProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_notifications_metrics(
        self,
        database: Database,
        repository: NotificationRepository,
    ) -> GetNotificationsMetricsUseCase:
        return GetNotificationsMetricsUseCase(database, repository)


container = make_async_container(
    InfrastructureProvider(),
    RepositoryProvider(),
    ServiceProvider(),
    UseCaseProvider(),
    MetricsProvider(),
)
