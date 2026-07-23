from fastapi import status
from httpx import AsyncClient


async def test_healthcheck_returns_200(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/healthcheck")

    assert response.status_code == status.HTTP_200_OK, (
        "Healthcheck endpoint must return 200 OK"
    )
