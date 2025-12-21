import logging

from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    path="",
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK,
)
async def ping() -> PlainTextResponse:
    """
    Simple health check endpoint.
    """
    logger.debug("ping")
    return PlainTextResponse("pong\n")
