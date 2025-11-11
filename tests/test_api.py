import pytest
from fastapi.testclient import TestClient
from main import app
import os

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

