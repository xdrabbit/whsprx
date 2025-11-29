import pytest
import time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_list_and_get_thread():
    # Create a new thread
    resp = client.post('/api/chat/threads', json={'name': 'unittest-thread'})
    assert resp.status_code == 200
    data = resp.json()
    assert 'id' in data
    tid = data['id']

    # List threads (should include the created one)
    resp = client.get('/api/chat/threads')
    assert resp.status_code == 200
    threads = resp.json().get('threads', [])
    assert any(t['id'] == tid for t in threads)

    # Get thread details
    resp = client.get(f'/api/chat/threads/{tid}')
    assert resp.status_code == 200
    t = resp.json()
    assert t['id'] == tid


def test_add_messages_and_export():
    # Create thread
    resp = client.post('/api/chat/threads', json={'name': 'msg-thread'})
    assert resp.status_code == 200
    tid = resp.json()['id']

    # Add text message
    resp = client.post(f'/api/chat/threads/{tid}/messages', json={'role': 'user', 'type': 'text', 'text': 'Hello'})
    assert resp.status_code == 200
    msg = resp.json()
    assert msg['role'] == 'user'

    # Add an image message (base64 stub)
    fake_b64 = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVQYV2NgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII='
    resp = client.post(f'/api/chat/threads/{tid}/messages', json={'role': 'ai', 'type': 'image', 'text': 'An image', 'extra': {'image_base64': fake_b64}})
    assert resp.status_code == 200

    # Trigger async export job (zip)
    resp = client.post(f'/api/chat/threads/{tid}/export')
    assert resp.status_code == 200
    job_id = resp.json().get('job_id')
    assert job_id

    # poll for status
    status = None
    for _ in range(30):
        st = client.get(f'/api/chat/threads/{tid}/export/{job_id}/status')
        assert st.status_code == 200
        status = st.json().get('status')
        if status == 'done':
            break
        if status == 'failed':
            pytest.fail('Export failed: ' + str(st.json()))
        time.sleep(0.1)

    assert status == 'done'

    # Download zip and assert contents
    d = client.get(f'/api/chat/threads/{tid}/export/{job_id}/download')
    assert d.status_code == 200
    import io, zipfile

    z = zipfile.ZipFile(io.BytesIO(d.content))
    names = z.namelist()
    assert 'thread.md' in names
    # ensure the image exists in the zip
    assert any(n.startswith('images/') for n in names)


def test_delete_thread():
    resp = client.post('/api/chat/threads', json={'name': 'delete-me'})
    assert resp.status_code == 200
    tid = resp.json()['id']

    resp = client.delete(f'/api/chat/threads/{tid}')
    assert resp.status_code == 200
    assert resp.json().get('deleted') is True
