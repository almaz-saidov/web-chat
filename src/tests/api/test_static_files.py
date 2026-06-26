from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient


async def test_static_pages_are_served_by_existing_urls(test_app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://testserver") as client:
        for path in ["/login.html", "/register.html", "/chat.html"]:
            response = await client.get(path)

            assert response.status_code == status.HTTP_200_OK, f"Static page {path} must be served"


async def test_static_assets_are_served_by_existing_urls(test_app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://testserver") as client:
        for path in ["/css/auth.css", "/css/chat.css", "/js/login.js", "/js/register.js", "/js/chat.js"]:
            response = await client.get(path)

            assert response.status_code == status.HTTP_200_OK, f"Static asset {path} must be served"
