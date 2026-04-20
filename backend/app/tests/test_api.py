import io


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_ai_status(client):
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "available" in data
    assert isinstance(data["available"], bool)


def test_upload_single_file(client):
    content = b"def hello():\n    pass\n"
    files = [("files", ("test.py", io.BytesIO(content), "text/plain"))]
    response = client.post("/api/upload/", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["file_count"] == 1


def test_upload_multiple_files(client):
    files = [
        ("files", ("a.py", io.BytesIO(b"pass"), "text/plain")),
        ("files", ("b.js", io.BytesIO(b"var x = 1;"), "text/plain")),
    ]
    response = client.post("/api/upload/", files=files)
    assert response.status_code == 200
    assert response.json()["file_count"] == 2


def test_upload_unsupported_type(client):
    files = [("files", ("test.exe", io.BytesIO(b"data"), "application/octet-stream"))]
    response = client.post("/api/upload/", files=files)
    assert response.status_code == 400


def test_upload_too_many_files(client):
    files = [
        ("files", (f"f{i}.py", io.BytesIO(b"pass"), "text/plain"))
        for i in range(501)
    ]
    response = client.post("/api/upload/", files=files)
    assert response.status_code == 400


def test_upload_oversized_file(client):
    big_content = b"x" * (6 * 1024 * 1024)
    files = [("files", ("big.py", io.BytesIO(big_content), "text/plain"))]
    response = client.post("/api/upload/", files=files)
    assert response.status_code == 400


def test_get_full_graph_not_found(client):
    response = client.get("/api/graph/full/9999")
    assert response.status_code == 404


def test_get_nodes_not_found(client):
    response = client.get("/api/graph/nodes/9999")
    assert response.status_code == 404


def test_get_edges_not_found(client):
    response = client.get("/api/graph/edges/9999")
    assert response.status_code == 404


def test_ai_chat_project_not_found(client):
    response = client.post("/api/ai/chat", json={
        "project_id": 9999, "message": "test"
    })
    assert response.status_code in (404, 500)


def test_ai_architecture_project_not_found(client):
    response = client.post("/api/ai/architecture", json={"project_id": 9999})
    assert response.status_code in (404, 500)


# US-205/US-207: cycles and dashboard endpoint tests


def test_get_cycles_not_found(client):
    response = client.get("/api/graph/cycles/9999")
    assert response.status_code == 404


def test_get_dashboard_not_found(client):
    response = client.get("/api/projects/9999/dashboard")
    assert response.status_code == 404


# US-009: path and stats endpoint tests


def test_get_path_not_found(client):
    response = client.get("/api/graph/path/9999?from=1&to=2")
    assert response.status_code == 404


def test_get_stats_not_found(client):
    response = client.get("/api/graph/stats/9999")
    assert response.status_code == 404
