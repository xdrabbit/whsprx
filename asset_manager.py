import os
import uuid
import base64
from typing import Optional


def save_base64_image(base64_str: str, dest_dir: str, filename_prefix: str = 'image') -> Optional[str]:
    """Save a base64-encoded image string to dest_dir and return file path.

    Accepts either a data URI (data:image/png;base64,AAA...) or a raw base64 string.
    Returns absolute path to the saved file or None on failure.
    """
    os.makedirs(dest_dir, exist_ok=True)

    try:
        if base64_str.startswith('data:'):
            header, b64data = base64_str.split(',', 1)
            # derive extension
            ext = 'png'
            if 'image/jpeg' in header or 'image/jpg' in header:
                ext = 'jpg'
            elif 'image/png' in header:
                ext = 'png'
            elif 'image/gif' in header:
                ext = 'gif'
        else:
            b64data = base64_str
            ext = 'png'

        filename = f"{filename_prefix}-{uuid.uuid4().hex}.{ext}"
        path = os.path.join(dest_dir, filename)

        with open(path, 'wb') as f:
            f.write(base64.b64decode(b64data))

        return os.path.abspath(path)
    except Exception:
        return None
