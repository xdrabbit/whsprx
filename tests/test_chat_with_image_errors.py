import base64
from fastapi.testclient import TestClient
import pytest
from main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)


def test_chat_with_image_missing_image():
    """
    When neither image_url nor image_base64 is provided, the endpoint should return 400.
    """
    response = client.post('/api/chat-with-image', json={"message": "Hi", "model": "llava:latest"})
    assert response.status_code == 400
    assert "No image provided" in response.json()["detail"]


def test_chat_with_image_invalid_url_fetch():
    """
    If the image URL fetch fails or returns non-200, the endpoint should return 400.
    """
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 404
        mock_get.return_value.raise_for_status.side_effect = Exception("Not Found")

        response = client.post('/api/chat-with-image', json={
            'image_url': 'https://example.com/missing.png',
            'message': 'Describe it',
            'model': 'llava:latest'
        })

        assert response.status_code == 400
        assert "Failed to fetch image" in response.json()["detail"] or "Failed to fetch image URL" in response.json()["detail"]


def test_chat_with_image_ollama_returns_error():
    """
    If Ollama returns a non-200 status, the endpoint should propagate a 500 error.
    """
    fake_image_bytes = b'\x89PNG\r\n\x1a\n'

    with patch('requests.get') as mock_get:
        with patch('requests.post') as mock_post:
            # requests.get for image fetch
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = fake_image_bytes
            mock_get.return_value.raise_for_status = MagicMock()

            # Ollama responds with non-200
            mock_post.return_value.status_code = 500
            mock_post.return_value.text = 'Ollama internal error'
            mock_post.return_value.raise_for_status.side_effect = Exception('Server error')

            response = client.post('/api/chat-with-image', json={
                'image_url': 'https://example.com/fake.png',
                'message': 'Analyse',
                'model': 'llava:latest'
            })

            assert response.status_code == 500
            assert 'Ollama error' in response.json()['detail'] or 'Could not connect to Ollama' in response.json()['detail']
