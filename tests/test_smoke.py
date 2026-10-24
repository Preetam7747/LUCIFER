"""Smoke tests for the core SmartHostel journeys.

Run with: python -m unittest discover -s tests -v
Requires dependencies from requirements.txt.
"""
import os
import tempfile
import unittest
from pathlib import Path

_TEST_DIR = tempfile.TemporaryDirectory(prefix="smarthostel-tests-")
os.environ.setdefault("SMARTHOSTEL_DB_PATH", str(Path(_TEST_DIR.name) / "test.db"))
os.environ.setdefault("SMARTHOSTEL_SECRET", "test-only-secret-change-me")

from app import app  # noqa: E402  (environment must be set before importing app)


class SmartHostelSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True)

    def setUp(self):
        self.client = app.test_client()

    def token(self, page="/login"):
        response = self.client.get(page)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as session:
            return session["_csrf_token"]

    def login(self, username, password):
        token = self.token("/login")
        response = self.client.post(
            "/login",
            data={"username": username, "password": password, "_csrf_token": token},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard", response.data)
        return response

    def test_public_landing_and_auth_pages_render(self):
        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        self.assertIn(b"Hostel life", home.data)
        self.assertIn(b"THOUGHTFULLY CONNECTED", home.data)
        self.assertEqual(self.client.get("/login").status_code, 200)
        self.assertEqual(self.client.get("/register").status_code, 200)

    def test_admin_workspace_pages_render(self):
        self.login("admin", "1")
        for route in (
            "/dashboard", "/rooms", "/mess", "/mess-records", "/complaints",
            "/outpass", "/water-management", "/electricity-management",
            "/utilities/water", "/utilities/electricity", "/reports/utility.csv?type=water",
        ):
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200, route)

    def test_warden_has_staff_pages_but_not_admin_payment_register(self):
        self.login("warden", "Warden123!")
        for route in ("/dashboard", "/rooms", "/mess", "/complaints", "/outpass", "/water-management", "/electricity-management"):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 200, route)
        denied = self.client.get("/mess-records", follow_redirects=False)
        self.assertEqual(denied.status_code, 302)
        self.assertTrue(denied.headers["Location"].endswith("/dashboard"))

    def test_registration_and_student_workspace(self):
        token = self.token("/register")
        response = self.client.post(
            "/register",
            data={
                "name": "Demo Student", "username": "smoke_student", "email": "smoke_student@example.test",
                "student_id": "SMOKE-001", "password": "StrongDemoPass123", "role": "student",
                "_csrf_token": token,
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Registration successful", response.data)
        self.login("smoke_student", "StrongDemoPass123")
        for route in ("/dashboard", "/mess", "/complaints", "/outpass", "/water-management", "/electricity-management"):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 200, route)
        utilities_page = self.client.get("/electricity-management")
        self.assertIn(b"No room assigned yet", utilities_page.data)
        self.assertIn(b"No other room's meter data is shown", utilities_page.data)

    def test_post_without_csrf_token_is_rejected(self):
        response = self.client.post("/login", data={"username": "admin", "password": "1"})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
