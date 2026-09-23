"""
CaseGuard - Web Application Entrypoint for Vercel
Serves the Hacker House Goa interactive dashboard and dataset.
"""
import os
import mimetypes

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend"))


def get_requested_path(environ):
    """Accurately extract client requested path across Vercel rewrite headers."""
    for key in ["HTTP_X_FORWARDED_URI", "REQUEST_URI", "PATH_INFO"]:
        val = environ.get(key)
        if val and val != "/index.py":
            if "?" in val:
                val = val.split("?")[0]
            if val.startswith("/index.py"):
                val = val[len("/index.py"):]
            if val:
                return val
    return "/"


def app(environ, start_response):
    """WSGI standard application entrypoint for Vercel Serverless Python."""
    raw_path = get_requested_path(environ)
    if not raw_path or raw_path == "/":
        clean_path = "index.html"
    else:
        clean_path = os.path.normpath(raw_path.lstrip("/"))

    target_file = os.path.join(FRONTEND_DIR, clean_path)

    # If requested file exists, serve it
    if os.path.exists(target_file) and os.path.isfile(target_file):
        content_type, _ = mimetypes.guess_type(target_file)
        if clean_path.endswith(".css"):
            content_type = "text/css; charset=utf-8"
        elif clean_path.endswith(".js"):
            content_type = "application/javascript; charset=utf-8"
        elif clean_path.endswith(".json"):
            content_type = "application/json; charset=utf-8"
        elif clean_path.endswith(".html"):
            content_type = "text/html; charset=utf-8"

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

    # Fallback to index.html for single-page routing
    fallback_index = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(fallback_index):
        with open(fallback_index, "rb") as f:
            body = f.read()
        status = "200 OK"
        headers = [
            ("Content-Type", "text/html; charset=utf-8"),
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
