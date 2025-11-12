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

