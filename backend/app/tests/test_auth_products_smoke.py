from fastapi.testclient import TestClient
from app.main import app


def test_register_and_login_and_list_products(monkeypatch):
    client = TestClient(app)
    # Use sqlite for tests by monkeypatching settings if needed
    # Minimal smoke: register and login
    r = client.post('/auth/register', json={
        'email': 'owner@test.com',
        'password': 'secret',
        'role': 'owner',
        'tenant_name': 'T',
        'tenant_slug': 't'
    })
    assert r.status_code == 200
    tokens = r.json()
    assert 'access_token' in tokens

    # Login against the same tenant
    r = client.post('/auth/login', json={
        'email': 'owner@test.com',
        'password': 'secret'
    }, headers={'X-Tenant-ID': 't'})
    assert r.status_code == 200
    access = r.json()['access_token']

    # List products
    r = client.get('/products/', headers={'Authorization': f'Bearer {access}', 'X-Tenant-ID': 't'})
    assert r.status_code == 200





