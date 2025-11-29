import pytest
import time
import os
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

    # Add an image message (base64 stub) and ensure server persist file
    fake_b64 = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVQYV2NgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII='
    resp = client.post(f'/api/chat/threads/{tid}/messages', json={'role': 'ai', 'type': 'image', 'text': 'An image', 'extra': {'image_base64': fake_b64}})
    assert resp.status_code == 200
    msg2 = resp.json()
    # server should have saved a file_path in message.extra
    fp = msg2.get('extra', {}).get('file_path')
    assert fp and isinstance(fp, str)
    import os
    assert os.path.exists(fp)

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


def test_pdf_export_job():
    resp = client.post('/api/chat/threads', json={'name': 'pdf-thread'})
    assert resp.status_code == 200
    tid = resp.json()['id']

    fake_b64 = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVQYV2NgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII='
    resp = client.post(f'/api/chat/threads/{tid}/messages', json={'role': 'ai', 'type': 'image', 'text': 'An image', 'extra': {'image_base64': fake_b64}})
    assert resp.status_code == 200

    r = client.post(f'/api/chat/threads/{tid}/export', json={})
    assert r.status_code == 200
    job_id = r.json()['job_id']

    # Wait for completion (done or failed)
    status = None
    for _ in range(40):
        st = client.get(f'/api/chat/threads/{tid}/export/{job_id}/status')
        assert st.status_code == 200
        status = st.json().get('status')
        if status in ('done', 'failed'):
            break
        time.sleep(0.1)

    assert status in ('done', 'failed')
    if status == 'done':
        d = client.get(f'/api/chat/threads/{tid}/export/{job_id}/download')
        assert d.status_code == 200


def test_delete_thread():
    resp = client.post('/api/chat/threads', json={'name': 'delete-me'})
    assert resp.status_code == 200
    tid = resp.json()['id']

    # add an image message so assets are created
    fake_b64 = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVQYV2NgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII='
    resp = client.post(f'/api/chat/threads/{tid}/messages', json={'role': 'ai', 'type': 'image', 'text': 'An image', 'extra': {'image_base64': fake_b64}})
    assert resp.status_code == 200
    fp = resp.json().get('extra', {}).get('file_path')
    assert fp and os.path.exists(fp)

    # create an export job too
    r = client.post(f'/api/chat/threads/{tid}/export')
    assert r.status_code == 200
    job_id = r.json()['job_id']
    # wait for job completion
    for _ in range(50):
        st = client.get(f'/api/chat/threads/{tid}/export/{job_id}/status')
        status = st.json().get('status')
        if status in ('done', 'failed'):
            break
        time.sleep(0.05)

    # ensure export artifact exists (if job done)
    if status == 'done':
        dl = client.get(f'/api/chat/threads/{tid}/export/{job_id}/download')
        assert dl.status_code == 200

    # delete thread should also remove assets and exports directories
    resp = client.delete(f'/api/chat/threads/{tid}')
    assert resp.status_code == 200
    assert resp.json().get('deleted') is True

    # ensure persisted asset dir removed
    assets_dir = os.path.join('db', 'thread_assets', tid)
    assert not os.path.exists(assets_dir)
    exports_dir = os.path.join('db', 'exports', tid)
    assert not os.path.exists(exports_dir)
