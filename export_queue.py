import os
import threading
import uuid
import time
import shutil
import subprocess
import zipfile
from typing import Dict

from thread_store import ThreadStore


class ExportJob:
    def __init__(self, thread_id: str, format: str = 'md'):
        self.id = str(uuid.uuid4())
        self.thread_id = thread_id
        self.format = format
        self.status = 'pending'  # pending, working, done, failed
        self.result_path = None
        self.error = None
        self.created_at = time.time()


class ExportQueue:
    def __init__(self, db_path: str, thread_store: ThreadStore):
        self.db_path = db_path
        self.thread_store = thread_store
        self.jobs: Dict[str, ExportJob] = {}
        self.lock = threading.Lock()
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker.start()

    def enqueue(self, thread_id: str, format: str = 'md') -> ExportJob:
        job = ExportJob(thread_id, format)
        with self.lock:
            self.jobs[job.id] = job
        return job

    def status(self, job_id: str) -> ExportJob | None:
        with self.lock:
            return self.jobs.get(job_id)

    def _worker_loop(self):
        while True:
            # find a pending job
            pending = None
            with self.lock:
                for j in self.jobs.values():
                    if j.status == 'pending':
                        pending = j
                        j.status = 'working'
                        break

            if pending:
                try:
                    self._process_job(pending)
                    pending.status = 'done'
                except Exception as e:
                    pending.status = 'failed'
                    pending.error = str(e)
            time.sleep(0.5)

    def _process_job(self, job: ExportJob):
        # create output directories under db/exports/<thread_id>/<job_id>/
        out_base = os.path.join(self.db_path, 'exports', job.thread_id, job.id)
        os.makedirs(out_base, exist_ok=True)

        # build markdown and write images to out_base/images
        thread = self.thread_store.get_thread(job.thread_id)
        if not thread:
            raise RuntimeError('thread not found')

        images_dir = os.path.join(out_base, 'images')
        os.makedirs(images_dir, exist_ok=True)

        md_lines = [f"# {thread.get('name')}\n", f"Created: {thread.get('created_at')}\n\n"]

        for msg in thread.get('messages', []):
            role = msg.get('role')
            t = msg.get('text', '') or ''
            if msg.get('type') == 'image':
                extra = msg.get('extra', {}) or {}
                file_path = extra.get('file_path')
                img_name = None
                # prefer file_path if it exists on disk
                if file_path and os.path.exists(file_path):
                    # copy file into images_dir
                    img_name = f"image-{msg['id']}{os.path.splitext(file_path)[1]}" if os.path.splitext(file_path)[1] else f"image-{msg['id']}.png"
                    shutil.copy(file_path, os.path.join(images_dir, img_name))
                else:
                    b64 = extra.get('image_base64')
                    if b64:
                        # b64 may be a data URI or raw base64
                        if b64.startswith('data:'):
                            # format: data:<type>;base64,<data>
                            try:
                                header, b64_data = b64.split(',', 1)
                                # extract extension
                                ext = 'png'
                                if 'image/jpeg' in header:
                                    ext = 'jpg'
                                elif 'image/png' in header:
                                    ext = 'png'
                                img_name = f"image-{msg['id']}.{ext}"
                                with open(os.path.join(images_dir, img_name), 'wb') as f:
                                    import base64 as _b64

                                    f.write(_b64.b64decode(b64_data))
                            except Exception:
                                # fallback write raw base64 blob
                                img_name = f"image-{msg['id']}.png"
                                with open(os.path.join(images_dir, img_name), 'wb') as f:
                                    import base64 as _b64

                                    f.write(_b64.b64decode(b64))
                        else:
                            img_name = f"image-{msg['id']}.png"
                            with open(os.path.join(images_dir, img_name), 'wb') as f:
                                import base64 as _b64

                                f.write(_b64.b64decode(b64))
                    else:
                        # no image data; create placeholder
                        md_lines.append(f"### {role} (image placeholder)\n\n{t}\n\n")
                if img_name:
                    md_lines.append(f"### {role} (image)\n\n![{img_name}](images/{img_name})\n\n")
            else:
                md_lines.append(f"### {role}\n\n{t}\n\n")

        # write markdown
        md_path = os.path.join(out_base, 'thread.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))

        # create a zip of the output folder
        zip_path = os.path.join(self.db_path, 'exports', job.thread_id, f"{job.id}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(md_path, arcname='thread.md')
            for root, _, files in os.walk(images_dir):
                for name in files:
                    full = os.path.join(root, name)
                    arc = os.path.relpath(full, out_base)
                    z.write(full, arcname=arc)

        job.result_path = zip_path
        # If the user requested a PDF, try pandoc first, otherwise attempt WeasyPrint
        if job.format == 'pdf':
            pdf_path = os.path.join(self.db_path, 'exports', job.thread_id, f"{job.id}.pdf")
            # Try pandoc
            pandoc = shutil.which('pandoc')
            if pandoc:
                try:
                    subprocess.run([pandoc, md_path, '-o', pdf_path], check=True, cwd=out_base)
                    job.result_path = pdf_path
                    return
                except Exception as e:
                    # continue to try other options
                    pass

            # Try WeasyPrint (requires markdown -> html conversion)
            try:
                import markdown as _md
                from weasyprint import HTML

                with open(md_path, 'r', encoding='utf-8') as f:
                    md_text = f.read()

                html = _md.markdown(md_text, extensions=['extra'])
                HTML(string=html, base_url=out_base).write_pdf(pdf_path)
                job.result_path = pdf_path
                return
            except Exception:
                # no converter available, mark as failed
                raise RuntimeError('No PDF converter available (pandoc or weasyprint+markdown required)')
