from httpx import AsyncClient

_USER = {"username": "alice", "email": "alice@example.com", "password": "secret123"}


async def test_register(client: AsyncClient):
    r = await client.post("/auth/register", json=_USER)
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "alice"
    assert "id" in data
    assert "hashed_password" not in data


async def test_login(client: AsyncClient):
    await client.post("/auth/register", json=_USER)
    r = await client.post("/auth/login", data={"username": "alice", "password": "secret123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


async def test_login_wrong_password(client: AsyncClient):
    await client.post("/auth/register", json=_USER)
    r = await client.post("/auth/login", data={"username": "alice", "password": "wrong"})
    assert r.status_code == 401


async def test_duplicate_registration(client: AsyncClient):
    await client.post("/auth/register", json=_USER)
    r = await client.post("/auth/register", json=_USER)
    assert r.status_code == 400
