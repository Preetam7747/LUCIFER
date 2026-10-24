import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def get_route(client, keywords):
    rules = []

    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint.lower()
        path = str(rule).lower()

        if any(keyword in endpoint or keyword in path for keyword in keywords):
            if "GET" in rule.methods:
                rules.append(str(rule))

    return rules


def test_auth_routes_exist():
    routes = get_route(None, ["auth", "login", "register", "signup"])

    assert routes, "No authentication route was found."


def test_login_page(client):
    routes = get_route(client, ["login"])

    if routes:
        response = client.get(routes[0])
        assert response.status_code in (200, 302)


def test_register_page(client):
    routes = get_route(client, ["register", "signup"])

    if routes:
        response = client.get(routes[0])
        assert response.status_code in (200, 302)