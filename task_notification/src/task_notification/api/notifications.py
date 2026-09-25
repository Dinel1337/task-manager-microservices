from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from task_notification.core.exceptions.notifications import NotificationNotFoundException
from task_notification.core.logger import get_logger, log
from task_notification.domain.use_cases.get_notifications import GetNotificationsUseCase
from task_notification.schemas.api.notifications import NotificationResponse, NotificationsRequest
from task_notification.schemas.api.pagination import Pagination
from task_notification.schemas.notification import NotificationFilters

logger = get_logger(__name__)

notifications_router = APIRouter(prefix="/notifications")


@notifications_router.get(
    "",
    response_model=Pagination[NotificationResponse],
)
@inject
@log(logger)
async def get_all_notifications(
    use_case: FromDishka[GetNotificationsUseCase],
    request: NotificationsRequest = Depends(),
) -> Pagination[NotificationResponse]:
    """Получить список уведомлений с фильтрацией и пагинацией."""
    records, total = await use_case.execute(
        filters=NotificationFilters.model_validate(request.model_dump()),
    )
    return Pagination(limit=request.limit, offset=request.offset, items=records, total=total)


@notifications_router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
@inject
@log(logger)
async def get_notification(
    notification_id: int,
    use_case: FromDishka[GetNotificationsUseCase],
) -> NotificationResponse:
    """Получить уведомление по ID."""
    try:
        return NotificationResponse.model_validate(await use_case.get_by_id(notification_id))
    except NotificationNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@notifications_router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
@inject
@log(logger)
async def mark_notification_as_read(
    notification_id: int,
    use_case: FromDishka[GetNotificationsUseCase],
) -> NotificationResponse:
    """Пометить уведомление как прочитанное."""
    try:
        return NotificationResponse.model_validate(await use_case.mark_as_read(notification_id))
    except NotificationNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
