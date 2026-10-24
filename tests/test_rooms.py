import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def find_room_routes():
    routes = []

    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint.lower()
        path = str(rule).lower()

        if "room" in endpoint or "room" in path:
            routes.append(rule)

    return routes


def test_rooms_routes_exist():
    routes = find_room_routes()

    assert routes, "No room routes were found."


def test_rooms_get_routes(client):
    routes = find_room_routes()

    for rule in routes:
        if "GET" in rule.methods:
            response = client.get(str(rule))

            assert response.status_code in (
                200,
                302,
                401,
                403
            )