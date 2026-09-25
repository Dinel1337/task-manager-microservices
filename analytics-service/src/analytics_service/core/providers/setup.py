"""Dishka DI providers."""

from dishka import Provider, Scope, make_async_container, provide

from analytics_service.core.config import settings
from analytics_service.domain.use_cases.process_task_event import ProcessTaskEventUseCase
from analytics_service.infrastructure.postgres.database import Database
from analytics_service.infrastructure.postgres.repository import AnalyticsRepository


class InfrastructureProvider(Provider):
    scope = Scope.APP

    @provide
    def get_database(self) -> Database:
        return Database(settings.postgres_url)


class RepositoryProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_repository(self) -> AnalyticsRepository:
        return AnalyticsRepository()


class UseCaseProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_process_event(
        self, database: Database, repository: AnalyticsRepository
    ) -> ProcessTaskEventUseCase:
        return ProcessTaskEventUseCase(database, repository)


container = make_async_container(
    InfrastructureProvider(),
    RepositoryProvider(),
    UseCaseProvider(),
)
