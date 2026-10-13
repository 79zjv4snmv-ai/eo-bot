import os
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

def run_bot():
    subprocess.run(["python", "-u", "app_new.py"])

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"Health check server running on port {port}")
    server.serve_forever()
