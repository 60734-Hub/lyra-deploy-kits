#!/usr/bin/env python3
"""PUT the streaming worker to Cloudflare. Run ON THE ASUS with the root token.
Usage: python put-worker.py
Reads:  C:\\Users\\capta\\lyra-home\\deploy-kits\\stream\\worker.lyra.js
Token:  C:\\Users\\capta\\lyra-home\\cf-root-token.txt
Account: knobology. Worker: lyra-home.
"""
import io, sys, json, urllib.request, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WORKER = r"C:\Users\capta\lyra-home\deploy-kits\stream\worker.lyra.js"
TOKENF = r"C:\Users\capta\lyra-home\cf-root-token.txt"
ACCOUNT = "b1925ba9fbbc872b4822feb90fa38bde"   # knobology
SCRIPT = "lyra-home"

token = open(TOKENF).read().strip()
src = open(WORKER, "rb").read()
print("worker bytes:", len(src))

meta = {
    "main_module": "worker.lyra.js",
    "compatibility_date": "2026-09-01",
    "bindings": [
        {"type": "ai", "name": "AI"},
    ],
    # LYRA_KV namespace id must be filled from the live worker if different.
}

# Build multipart/form-data by hand (stdlib only, no requests on the ASUS).
b = "----LyraBoundary" + str(os.getpid())
parts = []
parts.append(("--" + b + "\r\n").encode())
parts.append(b'Content-Disposition: form-data; name="metadata"\r\nContent-Type: application/json\r\n\r\n')
parts.append(json.dumps(meta).encode() + b"\r\n")
parts.append(("--" + b + "\r\n").encode())
parts.append(b'Content-Disposition: form-data; name="worker.lyra.js"; filename="worker.lyra.js"\r\n')
parts.append(b"Content-Type: application/javascript+module\r\n\r\n")
parts.append(src + b"\r\n")
parts.append(("--" + b + "--\r\n").encode())
body = b"".join(parts)

url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/workers/scripts/{SCRIPT}?keep_secrets=true"
req = urllib.request.Request(url, data=body, method="PUT")
req.add_header("Authorization", "Bearer " + token)
req.add_header("Content-Type", "multipart/form-data; boundary=" + b)
try:
    r = urllib.request.urlopen(req, timeout=120)
    print("HTTP", r.status)
    print(r.read().decode()[:2000])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode()[:3000])
