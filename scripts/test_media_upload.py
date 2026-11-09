import io
import os
from fastapi.testclient import TestClient
from app.main import app

png = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)

client = TestClient(app)
r = client.post(
    "/login",
    data={"email": os.environ.get("TEST_LOGIN_EMAIL", ""), "password": os.environ.get("TEST_LOGIN_PASSWORD", "")},
    follow_redirects=False,
)
print("login", r.status_code)
r = client.post(
    "/api/media/upload",
    files={"file": ("test.png", io.BytesIO(png), "image/png")},
    data={"title": "Demo", "kind": "image"},
)
print("upload", r.status_code, r.text[:220])
assert r.status_code == 201, r.text
url = r.json()["url"]
g = client.get("/api/media")
print("list", g.status_code, len(g.json()))
m = client.get(url)
print("serve", m.status_code, m.headers.get("content-type"), len(m.content))
assert m.status_code == 200
print("OK")
