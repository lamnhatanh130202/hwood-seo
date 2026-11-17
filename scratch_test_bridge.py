from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
import urllib.request

class SimpleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = json.loads(body)
        print("Received data from client:", data)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', '*')
        self.end_headers()
        
    def log_message(self, format, *args):
        pass

server = HTTPServer(('127.0.0.1', 8765), SimpleHandler)
t = threading.Thread(target=server.serve_forever, daemon=True)
t.start()
print("Server running on port 8765")

test_payload = json.dumps({"keyword": "tấm ốp nano", "rank": 2, "url": "https://hwood.vn/tam-op-nano/"}).encode('utf-8')
req = urllib.request.Request("http://127.0.0.1:8765/api/rank", data=test_payload, method="POST")
req.add_header('Content-Type', 'application/json')
with urllib.request.urlopen(req) as resp:
    print("Test HTTP Response:", resp.read().decode('utf-8'))

server.shutdown()
