import pytest
from fastapi.testclient import TestClient
from main import app
import os
from unittest.mock import patch, MagicMock, AsyncMock

client = TestClient(app)

def test_read_main():
    """
    Tests if the root endpoint returns the frontend HTML.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers['content-type']

def test_upload_and_query():
    """
    Tests file upload, chunking, and querying.
    """
    # 1. Create a dummy file for upload
    test_file_content = "This is a test sentence.\\n\\nThis is another test paragraph."
    test_file_path = "test_upload.txt"
    with open(test_file_path, "w") as f:
        f.write(test_file_content)

    # 2. Upload the file
    with open(test_file_path, "rb") as f:
        response = client.post("/upload", files={"file": (test_file_path, f, "text/plain")})
    
    assert response.status_code == 200
    assert "Successfully ingested" in response.json()["message"]

    # 3. Query the uploaded content
    response = client.get("/query?q=test paragraph")
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    assert "This is another test paragraph." in results[0]["document"]

    # 4. Clean up the dummy file
    os.remove(test_file_path)

def test_query_rag_success():
    """
    Tests the RAG endpoint with a successful query.
    Mocks both ChromaDB and Ollama API calls.
    """
    # 1. Mock the ChromaDB query
    mock_chroma_results = {
        'documents': [['This is the context for the query.']],
        'metadatas': [[{'source_filename': 'test.txt', 'chunk_index': 0}]]
    }
    
    # 2. Mock the Ollama API response
    mock_ollama_response = {
        "response": "This is the generated answer from the model."
    }

    with patch('main.collection.query', return_value=mock_chroma_results) as mock_query:
        with patch('requests.post') as mock_post:
            # Configure the mock for Ollama response
            mock_post.return_value.json.return_value = mock_ollama_response
            mock_post.return_value.raise_for_status = MagicMock()

            # 3. Make the request to the RAG endpoint
            response = client.post("/query/rag", data={"query": "What is the answer?", "model": "test-model"})

            # 4. Assert the results
            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "This is the generated answer from the model."
            assert "This is the context for the query." in data["context"]
            
            # Verify that ChromaDB was queried correctly
            mock_query.assert_called_once_with(query_texts=["What is the answer?"], n_results=5)
            
            # Verify that Ollama was called correctly
            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            assert called_args[0] == "http://127.0.0.1:11434/api/generate"
            sent_json = called_kwargs['json']
            assert sent_json['model'] == 'test-model'
            
            # Check that the core components are in the prompt, without being too strict about whitespace
            assert "This is the context for the query." in sent_json['prompt']
            assert "User's Question: What is the answer?" in sent_json['prompt']

def test_text_to_speech_success():
    """
    Tests the text-to-speech endpoint successfully generating audio.
    Mocks the ElevenLabs client.
    """
    with patch('main.eleven_client') as mock_eleven_client:
        # Mock the stream method to return an iterator of bytes
        mock_audio_chunk = b'\\x01\\x02\\x03'
        mock_eleven_client.text_to_speech.stream.return_value = iter([mock_audio_chunk])

        # Make the request
        response = client.post("/api/text-to-speech", data={"text": "Hello world", "voice_id": "21m00Tcm4TlvDq8ikWAM"})

        # Assert the response
        assert response.status_code == 200
        assert response.headers['content-type'] == 'audio/mpeg'
        assert response.content == mock_audio_chunk

        # Verify the mock was called
        mock_eleven_client.text_to_speech.stream.assert_called_once_with(
            text="Hello world",
            voice_id="21m00Tcm4TlvDq8ikWAM"
        )

def test_text_to_speech_no_client():
    """
    Tests the TTS endpoint when the ElevenLabs client is not configured.
    """
    with patch('main.eleven_client', None):
        response = client.post("/api/text-to-speech", data={"text": "Hello world", "voice_id": "any_voice"})
        assert response.status_code == 501
        assert response.json()['detail'] == "Text-to-speech service is not configured."

def test_generate_image_prompt_success():
    """
    Tests the AI Art Director endpoint for generating a new image prompt.
    Mocks the Ollama API call.
    """
    mock_ollama_response = {
        "response": "A new, wonderfully descriptive prompt."
    }
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = mock_ollama_response
        mock_post.return_value.raise_for_status = MagicMock()

        response = client.post(
            "/api/generate-image-prompt",
            data={
                "base_prompt": "The Queen of Hearts is angry.",
                "artistic_direction": "in the style of a dark fairy tale.",
                "model": "test-model"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["new_prompt"] == "A new, wonderfully descriptive prompt."

        # Verify the meta-prompt was constructed correctly
        mock_post.assert_called_once()
        sent_json = mock_post.call_args.kwargs['json']
        assert 'You are an expert prompt engineer' in sent_json['prompt']
        assert 'Base Text: "The Queen of Hearts is angry."' in sent_json['prompt']
        assert 'Artistic Direction: "in the style of a dark fairy tale."' in sent_json['prompt']


@patch('main.eleven_client', None)
def test_text_to_speech_no_client_alt():
    """
    Tests the TTS endpoint when the ElevenLabs client is not configured.
    """
    response = client.post("/api/text-to-speech", data={"text": "Hello world", "voice_id": "any_voice"})
    assert response.status_code == 501
    assert response.json()['detail'] == "Text-to-speech service is not configured."


# --- PixVerse Video Generation Tests ---

def test_pixverse_text_to_video_success():
    """
    Tests the PixVerse text-to-video endpoint with successful generation.
    Mocks the PixVerse API call.
    """
    mock_pixverse_response = {
        "ErrCode": 0,
        "ErrMsg": "success",
        "Resp": {
            "video_id": 123456789,
            "credits": 45
        }
    }
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_pixverse_response
        mock_post.return_value.raise_for_status = MagicMock()
        
        response = client.post(
            "/api/pixverse/generate-video",
            data={"prompt": "A cat playing piano"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == 123456789
        
        # Verify API was called correctly
        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args
        assert "video/text/generate" in called_args[0]
        sent_json = called_kwargs['json']
        assert sent_json['prompt'] == "A cat playing piano"
        assert sent_json['model'] == "v5"
        assert sent_json['aspect_ratio'] == "16:9"
        assert sent_json['duration'] == 5


def test_pixverse_text_to_video_no_api_key():
    """
    Tests the PixVerse endpoint when API key is not configured.
    """
    with patch('main.PIXVERSE_API_KEY', None):
        response = client.post(
            "/api/pixverse/generate-video",
            data={"prompt": "A cat playing piano"}
        )
        assert response.status_code == 501
        assert "PixVerse API key is not configured" in response.json()['detail']


def test_pixverse_text_to_video_api_error():
    """
    Tests the PixVerse endpoint when the API returns an error.
    """
    mock_pixverse_response = {
        "ErrCode": 400,
        "ErrMsg": "Invalid parameters",
        "Resp": {}
    }
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_pixverse_response
        mock_post.return_value.raise_for_status = MagicMock()
        
        response = client.post(
            "/api/pixverse/generate-video",
            data={"prompt": "A cat playing piano"}
        )
        
        assert response.status_code == 500
        assert "Invalid parameters" in response.json()['detail']


def test_pixverse_video_status_success():
    """
    Tests fetching video generation status from PixVerse.
    """
    mock_status_response = {
        "ErrCode": 0,
        "ErrMsg": "Success",
        "Resp": {
            "id": 123456789,
            "status": 1,  # Completed
            "url": "https://example.com/video.mp4",
            "prompt": "A cat playing piano",
            "seed": 12345,
            "credits": 45
        }
    }
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_status_response
        mock_get.return_value.raise_for_status = MagicMock()
        
        response = client.get("/api/pixverse/video-status/123456789")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 1
        assert data["url"] == "https://example.com/video.mp4"
        
        # Verify API was called correctly
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert "video/result/123456789" in called_url


def test_pixverse_credits_balance_success():
    """
    Tests fetching credit balance from PixVerse.
    """
    mock_balance_response = {
        "ErrCode": 0,
        "ErrMsg": "success",
        "Resp": {
            "account_id": 123456,
            "credit_monthly": 500000,
            "credit_package": 10000
        }
    }
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_balance_response
        mock_get.return_value.raise_for_status = MagicMock()
        
        response = client.get("/api/pixverse/credits")
        
        assert response.status_code == 200
        data = response.json()
        assert data["credit_monthly"] == 500000
        assert data["credit_package"] == 10000
        assert data["account_id"] == 123456
        
        # Verify API was called correctly
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert "account/balance" in called_url


def test_pixverse_image_to_video_success():
    """
    Tests the PixVerse image-to-video endpoint with successful generation.
    Mocks both the image upload and video generation API calls.
    """
    # Mock image upload response
    mock_upload_response = {
        "ErrCode": 0,
        "ErrMsg": "success",
        "Resp": {
            "img_id": 987654,
            "img_url": "https://example.com/uploaded.jpg"
        }
    }
    
    # Mock video generation response
    mock_video_response = {
        "ErrCode": 0,
        "ErrMsg": "success",
        "Resp": {
            "video_id": 123456789,
            "credits": 45
        }
    }
    
    with patch('requests.post') as mock_post:
        # Configure mock to return different responses for upload vs generation
        mock_post.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_upload_response, raise_for_status=MagicMock()),
            MagicMock(status_code=200, json=lambda: mock_video_response, raise_for_status=MagicMock())
        ]
        
        # Create a test image file
        test_image_content = b'\\x89PNG\\r\\n\\x1a\\n\\x00\\x00\\x00\\rIHDR'
        
        response = client.post(
            "/api/pixverse/generate-video-from-image",
            data={
                "prompt": "camera zooms in slowly",
                "duration": "5",
                "quality": "540p",
                "motion_mode": "normal",
                "seed": "0"
            },
            files={"image": ("test.png", test_image_content, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == 123456789
        
        # Verify both API calls were made
        assert mock_post.call_count == 2
        
        # Check first call (image upload)
        first_call_url = mock_post.call_args_list[0][0][0]
        assert "image/upload" in first_call_url
        
        # Check second call (video generation)
        second_call_url = mock_post.call_args_list[1][0][0]
        assert "video/img/generate" in second_call_url
        sent_json = mock_post.call_args_list[1][1]['json']
        assert sent_json['img_id'] == 987654
        assert sent_json['prompt'] == "camera zooms in slowly"
        assert sent_json['duration'] == 5
        assert sent_json['quality'] == "540p"


def test_pixverse_image_to_video_with_camera_movement():
    """
    Tests image-to-video with optional camera movement parameter.
    """
    mock_upload_response = {
        "ErrCode": 0,
        "ErrMsg": "success",
        "Resp": {"img_id": 987654, "img_url": "https://example.com/uploaded.jpg"}
    }
    
    mock_video_response = {
        "ErrCode": 0,
        "ErrMsg": "success",
        "Resp": {"video_id": 123456789, "credits": 45}
    }
    
    with patch('requests.post') as mock_post:
        mock_post.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_upload_response, raise_for_status=MagicMock()),
            MagicMock(status_code=200, json=lambda: mock_video_response, raise_for_status=MagicMock())
        ]
        
        test_image_content = b'\\x89PNG\\r\\n\\x1a\\n'
        
        response = client.post(
            "/api/pixverse/generate-video-from-image",
            data={
                "prompt": "camera zooms in slowly",
                "camera_movement": "zoom_in",
                "duration": "10",
                "quality": "720p",
                "motion_mode": "slow",
                "seed": "12345"
            },
            files={"image": ("test.png", test_image_content, "image/png")}
        )
        
        assert response.status_code == 200
        
        # Verify camera_movement was included in the payload
        sent_json = mock_post.call_args_list[1][1]['json']
        assert sent_json['camera_movement'] == "zoom_in"
        assert sent_json['duration'] == 10
        assert sent_json['quality'] == "720p"
        assert sent_json['motion_mode'] == "slow"
        assert sent_json['seed'] == 12345


def test_pixverse_image_to_video_upload_failure():
    """
    Tests image-to-video when image upload fails.
    """
    mock_upload_response = {
        "ErrCode": 400,
        "ErrMsg": "Invalid image format",
        "Resp": {}
    }
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_upload_response
        mock_post.return_value.raise_for_status = MagicMock()
        
        test_image_content = b'invalid image data'
        
        response = client.post(
            "/api/pixverse/generate-video-from-image",
            data={"prompt": "test"},
            files={"image": ("test.png", test_image_content, "image/png")}
        )
        
        assert response.status_code == 500
        assert "Invalid image format" in response.json()['detail']


# --- Regression Tests ---

def test_regression_upload_endpoint_still_works():
    """
    Regression test: Ensure file upload still works after adding PixVerse features.
    """
    test_content = "Regression test content."
    test_file_path = "regression_test.txt"
    
    with open(test_file_path, "w") as f:
        f.write(test_content)
    
    with open(test_file_path, "rb") as f:
        response = client.post("/upload", files={"file": (test_file_path, f, "text/plain")})
    
    assert response.status_code == 200
    assert "Successfully ingested" in response.json()["message"]
    
    os.remove(test_file_path)


def test_regression_rag_endpoint_still_works():
    """
    Regression test: Ensure RAG endpoint still works after adding PixVerse features.
    """
    mock_chroma_results = {
        'documents': [['Context text']],
        'metadatas': [[{'source_filename': 'test.txt', 'chunk_index': 0}]]
    }
    
    mock_ollama_response = {"response": "Answer text"}
    
    with patch('main.collection.query', return_value=mock_chroma_results):
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_ollama_response
            mock_post.return_value.raise_for_status = MagicMock()
            
            response = client.post("/query/rag", data={"query": "test", "model": "test-model"})
            
            assert response.status_code == 200
            assert "answer" in response.json()


def test_regression_comfyui_models_endpoint():
    """
    Regression test: Ensure ComfyUI models endpoint still works.
    """
    mock_checkpoints = [
        {"model_name": "model1.safetensors"},
        {"model_name": "model2.ckpt"}
    ]
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_checkpoints
        mock_get.return_value.raise_for_status = MagicMock()
        
        response = client.get("/api/comfyui/models")
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) == 2
        assert data["models"][0]["model_name"] == "model1.safetensors"

