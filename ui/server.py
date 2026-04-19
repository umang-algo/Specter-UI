"""
ui/server.py — SSE server for the live dashboard.
"""
import json
import time
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

_state_file: Path = None
PORT = 8765

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            self._serve_dashboard()
        elif self.path == "/state":
            self._serve_state()
        elif self.path == "/events":
            self._serve_sse()
        elif self.path.startswith("/workspace/"):
            self._serve_workspace_file()
        elif self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404)

    def _serve_workspace_file(self):
        # Serve files from the workspace directory (for images/snapshots)
        workspace_root = Path(__file__).parent.parent / "workspace"
        requested_path = self.path.replace("/workspace/", "")
        file_path = (workspace_root / requested_path).resolve()
        
        # Security: Ensure file is within workspace
        if not str(file_path).startswith(str(workspace_root.resolve())) or not file_path.exists():
            self.send_error(404)
            return
            
        content = file_path.read_bytes()
        self.send_response(200)
        
        # Detect content type
        ext = file_path.suffix.lower()
        content_type = "application/octet-stream"
        if ext in [".png", ".jpg", ".jpeg"]: content_type = f"image/{ext[1:]}"
        elif ext == ".html": content_type = "text/html"
        elif ext == ".json": content_type = "application/json"
        
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_dashboard(self):
        html_file = Path(__file__).parent / "dashboard.html"
        content = html_file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_state(self):
        try:
            data = _state_file.read_bytes() if _state_file and _state_file.exists() else b"{}"
        except Exception:
            data = b"{}"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def _serve_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        last_state = None
        while True:
            try:
                current = _state_file.read_text() if _state_file and _state_file.exists() else "{}"
                if current != last_state:
                    compact_json = json.dumps(json.loads(current))
                    self.wfile.write(f"data: {compact_json}\n\n".encode())
                    self.wfile.flush()
                    last_state = current
                time.sleep(1)
            except Exception:
                break

def start(state_file: Path):
    global _state_file
    _state_file = state_file
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), DashboardHandler)
        server.serve_forever()
    except Exception as e:
        print(f"Server crash: {e}")
