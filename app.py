from index import app, handler, application

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    print("Serving on port 8000...")
    httpd = make_server("0.0.0.0", 8000, app)
    httpd.serve_forever()
