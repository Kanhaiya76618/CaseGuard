"""
CaseGuard - Web Application Entrypoint for Vercel
Serves the Hacker House Goa interactive dashboard and dataset.
"""
import os
import mimetypes

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend"))


def app(environ, start_response):
    """WSGI standard application entrypoint for Vercel Serverless Python."""
    raw_path = environ.get("PATH_INFO", "/")
    if not raw_path or raw_path == "/":
        raw_path = "/index.html"

    # Normalize path and prevent directory traversal
    clean_path = os.path.normpath(raw_path.lstrip("/"))
    target_file = os.path.join(FRONTEND_DIR, clean_path)

    # If requested file exists, serve it
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

    # Fallback to index.html
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


# Expose handler aliases for Vercel runtimes
handler = app
application = app
