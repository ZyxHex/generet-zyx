#!/usr/bin/env python3
# ============================================================
# ZYXX API GENERATOR v3.0 - NO API KEY
# ============================================================

from flask import Flask, request, jsonify
import requests, random, string, time, os, json, codecs, base64, re, threading
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import urllib3
urllib3.disable_warnings()

app = Flask(__name__)

# ============================================================
# KONFIG
# ============================================================
HEX_KEY = bytes.fromhex("32656534343831396539623435393838343531343130363762323831363231383734643064356437616639643866376530306331653534373135623764316533")
REGION_LANG = {
    "ID":"id", "VN":"vi", "TH":"th", "MY":"ms", "SG":"en", "HK":"zh",
    "ME":"ar", "BD":"bn", "PK":"ur", "TW":"zh", "CIS":"ru", "SAC":"es", "BR":"pt", "IND":"id"
}
REGIONS = ["ME", "IND", "ID", "VN", "TH", "BD", "PK", "EU", "RU", "MA", "SAC", "BR", "CIS"]

# ============================================================
# IP POOL
# ============================================================
IP_POOL = []
IP_INDEX = 0
IP_LOCK = threading.Lock()

def init_ip():
    global IP_POOL
    prefix = [1,2,3,5,6,7,8,9,11,14,22,25,31,36,37,46,52,62,77,80,88,95,103,114,128,144,150,180,202,210]
    for _ in range(50000):
        base = random.choice(prefix)
        IP_POOL.append(f"{base}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}")
    random.shuffle(IP_POOL)

init_ip()

def get_ip():
    global IP_INDEX
    with IP_LOCK:
        ip = IP_POOL[IP_INDEX % len(IP_POOL)]
        IP_INDEX += 1
        return ip

def get_headers():
    ua = random.choice([
        "GarenaMSDK/4.0.39(SM-A325M;Android 13;en;HK;)",
        "GarenaMSDK/4.0.38(Redmi Note 10;Android 12;en;ID;)",
        "GarenaMSDK/4.0.40(Poco X3;Android 11;en;SG;)",
        "GarenaMSDK/4.0.41(SM-G991B;Android 13;en;GB;)",
    ])
    ip = get_ip()
    return {
        "User-Agent": ua,
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Accept-Encoding": "gzip",
        "X-Forwarded-For": ip,
        "X-Real-IP": ip,
        "X-Client-IP": get_ip(),
        "X-Remote-IP": get_ip(),
    }

def get_headers_form():
    h = get_headers()
    h["Content-Type"] = "application/x-www-form-urlencoded"
    return h

# ============================================================
# PROTOBUF & CRYPTO
# ============================================================
def encode_varint(n):
    if n < 0: return b''
    res = []
    while True:
        b = n & 0x7F
        n >>= 7
        if n: b |= 0x80
        res.append(b)
        if not n: break
    return bytes(res)

def proto_field(num, val):
    if isinstance(val, dict):
        nested = b''.join(proto_field(k,v) for k,v in val.items())
        return encode_varint((num<<3)|2) + encode_varint(len(nested)) + nested
    elif isinstance(val, int):
        return encode_varint((num<<3)|0) + encode_varint(val)
    elif isinstance(val, (str, bytes)):
        d = val.encode() if isinstance(val, str) else val
        return encode_varint((num<<3)|2) + encode_varint(len(d)) + d
    return b''

def build_proto(fields):
    return b''.join(proto_field(k,v) for k,v in fields.items())

AES_KEY = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
AES_IV = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])

def aes_encrypt(hex_data):
    return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(bytes.fromhex(hex_data), AES.block_size))

def encrypt_api(plain_hex):
    return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(bytes.fromhex(plain_hex), AES.block_size)).hex()

# ============================================================
# MAJOR LOGIN
# ============================================================
def major_login(uid, pwd, token, open_id, region):
    try:
        lang = REGION_LANG.get(region, "en")
        payload = b''.join([
            b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02',
            lang.encode(),
            b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118692\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5'
        ])
        data = payload.replace(b'afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390', token.encode())
        data = data.replace(b'1d8ec0240ede109973f3321b9354b44d', open_id.encode())
        d = encrypt_api(data.hex())
        headers = {
            "Accept-Encoding": "gzip", "Authorization": "Bearer",
            "Content-Type": "application/x-www-form-urlencoded",
            "ReleaseVersion": "OB54", "User-Agent": random.choice(["GarenaMSDK/4.0.39","GarenaMSDK/4.0.38"]),
            "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1",
            "X-Forwarded-For": get_ip(), "X-Real-IP": get_ip(),
            "X-Client-IP": get_ip(), "X-Remote-IP": get_ip(),
        }
        s = requests.Session()
        s.verify = False
        s.timeout = 10
        resp = s.post("https://loginbp.ggblueshark.com/MajorLogin", headers=headers, data=bytes.fromhex(d), timeout=10)
        if resp.status_code == 200 and len(resp.text) > 10:
            j = resp.text.find("eyJ")
            if j != -1:
                jwt = resp.text[j:]
                d2 = jwt.find(".", jwt.find(".")+1)
                if d2 != -1:
                    jwt = jwt[:d2+44]
                    parts = jwt.split('.')
                    if len(parts) >= 2:
                        p = parts[1]
                        p += '=' * (4 - len(p)%4) if len(p)%4 else ''
                        dec = json.loads(base64.urlsafe_b64decode(p))
                        aid = dec.get('account_id') or dec.get('external_id')
                        if aid:
                            return {"account_id": str(aid), "jwt_token": jwt}
        return {"account_id": "N/A", "jwt_token": ""}
    except:
        return {"account_id": "N/A", "jwt_token": ""}

# ============================================================
# GENERATE
# ============================================================
def generate_full(region, name_prefix, password_prefix):
    try:
        pwd = f"{password_prefix}_{random.randint(10000, 99999)}"
        s = requests.Session()
        s.verify = False
        s.timeout = 10
        
        r = s.post("https://100067.connect.garena.com/api/v2/oauth/guest:register",
                   headers=get_headers(),
                   json={"app_id":100067,"client_type":2,"password":pwd,"source":2},
                   timeout=10)
        if r.status_code != 200:
            return None, f"REG {r.status_code}"
        d = r.json()
        if "data" not in d or "uid" not in d["data"]:
            return None, "REG invalid"
        uid = d["data"]["uid"]
        
        r2 = s.post("https://100067.connect.garena.com/oauth/guest/token/grant",
                    headers=get_headers_form(),
                    data={"uid":uid,"password":pwd,"response_type":"token","client_type":"2","client_secret":HEX_KEY,"client_id":"100067"},
                    timeout=10)
        if r2.status_code != 200:
            return None, f"TOKEN {r2.status_code}"
        td = r2.json()
        open_id = td.get('open_id','')
        access_token = td.get('access_token','')
        if not open_id or not access_token:
            return None, "TOKEN missing"
        
        name = f"{name_prefix}{random.randint(1000,9999)}"
        ks = [0x30]*32
        enc = ''.join(chr(ord(open_id[i]) ^ ks[i % len(ks)]) for i in range(len(open_id)))
        field = codecs.decode(''.join(c if 32 <= ord(c) <= 126 else f'\\u{ord(c):04x}' for c in enc), 'unicode_escape').encode('latin1')
        lang = REGION_LANG.get(region, "en")
        pb = build_proto({1:name,2:access_token,3:open_id,5:102000007,6:4,7:1,13:1,14:field,15:lang,16:1,17:1})
        ep = aes_encrypt(pb.hex())
        hm = get_headers_form()
        hm.update({"Authorization":"Bearer","ReleaseVersion":"OB54","X-GA":"v1 1","X-Unity-Version":"2018.4.11f1"})
        s.post("https://loginbp.ggblueshark.com/MajorRegister", headers=hm, data=ep, timeout=10)
        
        login = major_login(uid, pwd, access_token, open_id, region)
        account_id = login.get("account_id", "N/A")
        
        return {
            "uid": uid,
            "account_id": account_id,
            "name": name,
            "password": pwd,
            "region": region,
            "success": True
        }, None
        
    except Exception as e:
        return None, str(e)[:50]

# ============================================================
# ROUTES (TANPA API KEY)
# ============================================================
@app.route('/gen', methods=['GET'])
def gen():
    name = request.args.get('name', 'ZYXX')
    count = int(request.args.get('count', 1))
    region = request.args.get('region', 'ID')
    password_prefix = request.args.get('password_prefix', 'ZYXX')
    
    if count > 10:
        return jsonify({"error": "Max 10 per request (Vercel limit)"}), 400
    
    accounts = []
    for _ in range(count):
        acc, err = generate_full(region, name, password_prefix)
        if acc:
            accounts.append(acc)
        else:
            accounts.append({"error": err, "success": False})
        time.sleep(0.1)
    
    return jsonify({
        "status": "success",
        "total": len(accounts),
        "region": region,
        "accounts": accounts
    })

@app.route('/')
def home():
    return jsonify({
        "message": "FreeFire Account Generator API",
        "available_regions": REGIONS,
        "endpoint": "/gen",
        "params": {
            "name": "Prefix nama",
            "count": "Jumlah akun (max 10)",
            "region": "Region ID/VN/TH/etc",
            "password_prefix": "Prefix password"
        },
        "max_count": 10,
        "patterns_endpoint": "/patterns"
    })

@app.route('/patterns')
def patterns():
    return jsonify({
        "R4": r"(\d)\1{3,}",
        "S5": r"(12345|23456|34567|45678|56789)",
        "P6": r"^(\d)(\d)(\d)\3\2\1$",
        "QD": r"(1111|2222|3333|4444|5555|6666|7777|8888|9999|0000)",
        "GHOST": "ID below 1,000,000"
    })

# ============================================================
# RUN
# ============================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
