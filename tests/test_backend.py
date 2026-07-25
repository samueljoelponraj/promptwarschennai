"""
Unit tests for FastAPI HTTP routes and helper functions.
"""

from fastapi.testclient import TestClient
from backend.app import app, scan_for_crisis


def test_index_route():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "MindCare" in response.text


def test_health_route():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "MindCare AI"}


def test_caregiver_route():
    client = TestClient(app)
    response = client.get("/caregiver")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Caregiver Portal" in response.text


def test_scan_for_crisis_keywords():
    # Test valid crisis keyword detection
    assert scan_for_crisis("I want to end my life right now") == "end my life"
    assert scan_for_crisis("suicide is my only option") == "suicide"
    assert scan_for_crisis("feeling overwhelmed and want to die") == "want to die"

    # Test non-crisis text inputs
    assert scan_for_crisis("I am feeling a little bit sad today") is None
    assert scan_for_crisis("Can we talk about my sleep routine?") is None
    assert scan_for_crisis("") is None
