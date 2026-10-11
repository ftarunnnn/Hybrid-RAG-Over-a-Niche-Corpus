"""
Integration tests for FastAPI endpoints: /api/health, /api/retrieve, /api/query.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome" in data["message"]


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "qdrant_collection" in data


def test_retrieve_endpoint():
    payload = {
        "query": "OSPF DR BDR election",
        "mode": "hybrid",
        "enable_rerank": True,
        "top_k": 3
    }
    response = client.post("/api/retrieve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "bm25_top" in data
    assert "vector_top" in data
    assert "fused_rrf_top" in data
    assert "reranked_top" in data


def test_query_endpoint():
    payload = {
        "query": "What is an A record in DNS?",
        "mode": "hybrid",
        "enable_rerank": True,
        "top_k": 3
    }
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["selected_passages"]) >= 1
    assert data["latency_ms"] > 0
