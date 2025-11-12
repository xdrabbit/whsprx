import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

client = TestClient(app)

@patch('main.websockets.connect')
@patch('main.requests.get')
@patch('main.requests.post')
def test_generate_image_endpoint(mock_post, mock_get, mock_ws_connect):
    """
    Tests the /api/generate-image endpoint.
    It mocks calls to the ComfyUI server (REST and WebSocket) and verifies
    our endpoint logic.
    """
    # --- Arrange ---

    # 1. Mock the initial POST to /prompt
    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = {"prompt_id": "12345"}
    mock_post.return_value = mock_post_response

    # 2. Mock the WebSocket communication
    # This simulates the final message from ComfyUI when the image is ready
    final_ws_message = json.dumps({
        "type": "executed",
        "data": {
            "prompt_id": "12345",
            "output": {
                "images": [{
                    "filename": "ComfyUI_00001_.png",
                    "subfolder": "",
                    "type": "output"
                }]
            }
        }
    })
    
    # Create an AsyncMock for the WebSocket connection object
    mock_ws = AsyncMock()
    mock_ws.recv.return_value = final_ws_message # Configure what `await websocket.recv()` returns

    # The context manager for `websockets.connect` must also be an AsyncMock
    mock_ws_cm = AsyncMock()
    mock_ws_cm.__aenter__.return_value = mock_ws # This is what `async with` gets
    mock_ws_connect.return_value = mock_ws_cm

    # 3. Mock the final GET request to /view (to fetch the image)
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.headers = {'Content-Type': 'image/png'}
    # Simulate some fake image data
    mock_get_response.iter_content.return_value = [b'fake-image-data']
    mock_get.return_value = mock_get_response

    # --- Act ---
    prompt_text = "A serene landscape"
    model_name = "v1-5-pruned-emaonly.ckpt"
    response = client.post(
        "/api/generate-image",
        data={"prompt": prompt_text, "model": model_name}
    )

    # --- Assert ---
    assert response.status_code == 200
    assert response.content == b'fake-image-data'
    assert response.headers['content-type'] == 'image/png'

    # Assert that 'requests.post' was called correctly
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "http://192.168.0.45:8188/prompt"
    sent_data = json.loads(kwargs['data'])
    assert sent_data['prompt']['6']['inputs']['text'] == prompt_text
    assert sent_data['prompt']['4']['inputs']['ckpt_name'] == model_name

    # Assert that the websocket was connected to
    mock_ws_connect.assert_called_once()

    # Assert that the final image was fetched
    mock_get.assert_called_once_with(
        "http://192.168.0.45:8188/view?filename=ComfyUI_00001_.png&subfolder=&type=output",
        stream=True
    )

