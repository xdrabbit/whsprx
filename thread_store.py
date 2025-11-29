import json
import os
import threading
import uuid
from datetime import datetime


class ThreadStore:
    """Simple file-backed thread storage for chat + image messages.

    Stores a JSON file in a specified path under the repo. Thread data structure:
    {
      threads: { id: {id, name, created_at, modified_at, messages: [ {id,role,type,text,extra,created_at} ] } }
    }
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.lock = threading.Lock()
        # ensure directory exists
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            self._write({"threads": {}})

    def _read(self):
        with self.lock:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)

    def _write(self, data):
        with self.lock:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def list_threads(self):
        data = self._read()
        return list(data.get("threads", {}).values())

    def create_thread(self, name: str | None = None):
        tid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        t = {
            "id": tid,
            "name": name or f"Thread {now}",
            "created_at": now,
            "modified_at": now,
            "messages": []
        }
        data = self._read()
        data.setdefault("threads", {})[tid] = t
        self._write(data)
        return t

    def get_thread(self, thread_id: str):
        data = self._read()
        return data.get("threads", {}).get(thread_id)

    def delete_thread(self, thread_id: str):
        data = self._read()
        if thread_id in data.get("threads", {}):
            del data["threads"][thread_id]
            self._write(data)
            return True
        return False

    def add_message(self, thread_id: str, role: str, text: str | None = None, type_: str = "text", extra: dict | None = None):
        thread = self.get_thread(thread_id)
        if not thread:
            raise KeyError("thread not found")
        now = datetime.utcnow().isoformat()
        msg = {
            "id": str(uuid.uuid4()),
            "role": role,
            "type": type_,
            "text": text or "",
            "extra": extra or {},
            "created_at": now
        }
        data = self._read()
        data.setdefault("threads", {})[thread_id]["messages"].append(msg)
        data["threads"][thread_id]["modified_at"] = now
        self._write(data)
        return msg

    def export_markdown(self, thread_id: str):
        thread = self.get_thread(thread_id)
        if not thread:
            raise KeyError("thread not found")

        lines = [f"# {thread.get('name')}\n", f"Created: {thread.get('created_at')}\n"]
        for m in thread.get("messages", []):
            role = m.get("role")
            t = m.get("text", "")
            if m.get("type") == "image":
                # embed image (if base64 present in extra)
                img_b64 = m.get("extra", {}).get("image_base64")
                if img_b64:
                    # default to png
                    lines.append(f"### {role} (image)\n\n![image]({img_b64})\n\n")
                else:
                    lines.append(f"### {role} (image placeholder)\n\n{t}\n\n")
            else:
                lines.append(f"### {role}\n\n{t}\n\n")

        return "\n".join(lines)
