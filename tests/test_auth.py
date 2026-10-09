"""회원가입 / 로그인 happy-path + 주요 에러 케이스."""

import pytest
from httpx import AsyncClient

SIGNUP_PAYLOAD = {
    "email": "student@example.com",
    "password": "supersecret",
    "full_name": "홍길동",
    "role": "student",
    "grade": "9",
}


@pytest.mark.asyncio
async def test_signup_creates_pending_user(client: AsyncClient) -> None:
    res = await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    assert res.status_code == 201
    body = res.json()
    assert body["email"] == SIGNUP_PAYLOAD["email"]
    assert body["role"] == "student"
    assert body["approval_status"] == "pending"  # 항상 승인 대기로 시작
    assert "id" in body
    assert "hashed_password" not in body  # 비밀번호는 응답에 노출되지 않음


@pytest.mark.asyncio
async def test_signup_duplicate_email_conflict(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    res = await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    assert res.status_code == 409
    assert res.json()["error"]["code"] == "email_already_exists"


@pytest.mark.asyncio
async def test_login_returns_tokens(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    res = await client.post(
        "/api/v1/auth/login",
        json={"email": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_login_wrong_password_unauthorized(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    res = await client.post(
        "/api/v1/auth/login",
        json={"email": SIGNUP_PAYLOAD["email"], "password": "wrong-password"},
    )

    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_credentials"
