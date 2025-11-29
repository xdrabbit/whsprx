import pytest
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
    fake_b64 = 'data:image/png;base64,AAA'
    resp = client.post(f'/api/chat/threads/{tid}/messages', json={'role': 'ai', 'type': 'image', 'text': 'An image', 'extra': {'image_base64': fake_b64}})
    assert resp.status_code == 200

    # Export markdown
    resp = client.get(f'/api/chat/threads/{tid}/export')
    assert resp.status_code == 200
    content = resp.text
    assert 'Hello' in content
    assert 'data:image/png;base64,AAA' in content


def test_delete_thread():
    resp = client.post('/api/chat/threads', json={'name': 'delete-me'})
    assert resp.status_code == 200
    tid = resp.json()['id']

    resp = client.delete(f'/api/chat/threads/{tid}')
    assert resp.status_code == 200
    assert resp.json().get('deleted') is True
