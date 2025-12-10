# tests/test_engine.py
import time
import pytest
from fastapi.testclient import TestClient
from app import main as app_main

client = TestClient(app_main.app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "sample_graph_id" in data

def test_run_sync_complete():
    body = {
        "initial_state": {
            "code": """def a():
  print("hi")

def b():
  pass""",
            "threshold": 80
        },
        "wait_for_completion": True
    }
    r = client.post("/graph/run", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("finished", "running")
    if data["status"] == "finished":
        assert "state" in data and "log" in data

def test_run_async_and_poll():
    body = {
        "initial_state": {
            "code": """def x():
  print("hi")""",
            "threshold": 80
        },
        "wait_for_completion": True
    }
    r = client.post("/graph/run", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("finished", "running")
    if data["status"] == "finished":
        assert "state" in data and "log" in data
