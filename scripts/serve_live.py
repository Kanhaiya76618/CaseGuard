"""
CaseGuard - Live Investigation HTTP Server
Serves the dynamic investigation API and hosts the Hacker House Goa frontend.
Accepts live user inputs via POST /api/investigate and queries the actual graph database.
"""
import http.server
import socketserver
import json
import urllib.parse
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
sys.path.insert(0, BASE_DIR)

from agent.live_pipeline import live_investigate_trigger, init_local_graph_db

# Initialize database index on server boot
init_local_graph_db()


class LiveInvestigationHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_POST(self):
        if self.path == "/api/investigate":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            
            try:
                payload = json.loads(post_data)
                customer_id = payload.get("customer_id", "C12382").strip()
                transaction_id = payload.get("transaction_id", "3514030").strip()
                amount = float(payload.get("amount", 120.0))
                risk_score = float(payload.get("risk_score", 0.65))
                trigger_type = payload.get("trigger_type", "risk_score")
                trigger_text = payload.get("trigger_text", "")
                card_id = payload.get("card_id", f"{customer_id}-K1")

                # Run dynamic live investigation
                result = live_investigate_trigger(
                    customer_id=customer_id,
                    transaction_id=transaction_id,
                    amount=amount,
                    trigger_type=trigger_type,
                    trigger_text=trigger_text,
                    risk_score=risk_score,
                    card_id=card_id
                )

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run_server(port=8000):
    with socketserver.TCPServer(("", port), LiveInvestigationHandler) as httpd:
        print(f"[✓] CaseGuard Live Server running at http://localhost:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
