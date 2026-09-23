"""
CaseGuard - Vercel Serverless Function & Web API Entrypoint
Serves frontend dashboard and dynamic investigation pipeline.
"""
import os
import mimetypes

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")


def app(environ, start_response):
    """Standard WSGI Handler for Vercel Serverless Functions."""
    raw_path = environ.get("PATH_INFO", "/")
    if not raw_path or raw_path == "/":
        raw_path = "/index.html"

    clean_path = os.path.normpath(raw_path.lstrip("/"))
    target_file = os.path.join(FRONTEND_DIR, clean_path)

    if os.path.exists(target_file) and os.path.isfile(target_file):
        content_type, _ = mimetypes.guess_type(target_file)
        content_type = content_type or "application/octet-stream"

        with open(target_file, "rb") as f:
            body = f.read()

        status = "200 OK"
        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body))),
            ("Access-Control-Allow-Origin", "*"),
            ("Cache-Control", "public, max-age=3600")
        ]
        start_response(status, headers)
        return [body]

    fallback_index = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(fallback_index):
        with open(fallback_index, "rb") as f:
            body = f.read()
        status = "200 OK"
        headers = [
            ("Content-Type", "text/html"),
            ("Content-Length", str(len(body))),
            ("Access-Control-Allow-Origin", "*")
        ]
        start_response(status, headers)
        return [body]

    status = "404 Not Found"
    headers = [("Content-Type", "text/plain")]
    start_response(status, headers)
    return [b"Not Found"]


# Handlers for Vercel runtime
handler = app
application = app
