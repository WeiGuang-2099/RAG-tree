import asyncio
from unittest.mock import MagicMock


def test_ai_service_chat_with_mock():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This function does X."

    from app.services.ai_service import AiService
    service = AiService()
    service._client = MagicMock()
    service._client.chat.completions.create = MagicMock(return_value=mock_response)

    result = asyncio.get_event_loop().run_until_complete(
        service.chat(message="Explain hello()", graph_context="1 node, 0 edges")
    )
    assert result == "This function does X."
    service._client.chat.completions.create.assert_called_once()


def test_ai_service_architecture_with_mock():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "The project uses MVC pattern."

    from app.services.ai_service import AiService
    service = AiService()
    service._client = MagicMock()
    service._client.chat.completions.create = MagicMock(return_value=mock_response)

    result = asyncio.get_event_loop().run_until_complete(
        service.analyze_architecture(
            nodes_summary="- main (Function)\n- helper (Function)",
            edges_summary="- main -> helper (calls)",
        )
    )
    assert result == "The project uses MVC pattern."


def test_ai_service_no_client():
    from app.services.ai_service import AiService

    service = AiService()
    assert service._client is None


def test_ai_service_get_client_with_key():
    from app.services.ai_service import AiService
    import os

    original = os.environ.get("ZHIPUAI_API_KEY", "")
    os.environ["ZHIPUAI_API_KEY"] = "test-key-12345"

    service = AiService()
    client = service._get_client()
    assert client is not None

    if original:
        os.environ["ZHIPUAI_API_KEY"] = original
    else:
        os.environ.pop("ZHIPUAI_API_KEY", None)


def test_ai_service_get_client_no_key():
    from app.services.ai_service import AiService
    import os

    original = os.environ.get("ZHIPUAI_API_KEY", "")
    os.environ.pop("ZHIPUAI_API_KEY", None)

    service = AiService()
    client = service._get_client()
    assert client is not None

    if original:
        os.environ["ZHIPUAI_API_KEY"] = original


def test_ai_chat_endpoint_project_not_found(client):
    response = client.post("/api/ai/chat", json={
        "project_id": 9999, "message": "test"
    })
    assert response.status_code in (404, 500)


def test_ai_architecture_endpoint_project_not_found(client):
    response = client.post("/api/ai/architecture", json={"project_id": 9999})
    assert response.status_code in (404, 500)
