#!/usr/bin/env python3
"""PUT the streaming worker to Cloudflare. Run ON THE ASUS with the root token.
Usage: python put-worker.py
Reads:  C:\\Users\\capta\\lyra-home\\deploy-kits\\stream\\worker.lyra.js
Token:  C:\\Users\\capta\\lyra-home\\cf-root-token.txt
Account: knobology. Worker: lyra-home.

FIXED 2026-10-15 (heartbeat): the account id was b1925ba9... (wrong) and the LYRA_KV
binding was MISSING from metadata. A PUT without the full bindings array WIPES LYRA_KV
(that is how CORPUS_CACHE was erased on Oct 1). Correct values below are from
memory/concepts/lyra-home.md line 75-76, the proven redeploy recipe.
"""
import io, sys, json, urllib.request, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WORKER = r"C:\Users\capta\lyra-home\deploy-kits\stream\worker.lyra.js"
TOKENF = r"C:\Users\capta\lyra-home\cf-root-token.txt"
ACCOUNT = "9342a170f13921bc5ef8b0ffde3b8602"   # knobology (proven, lyra-home.md:76)
KV_ID = "24e2b30874a04c2584b9a831a1b66a32"    # LYRA_KV namespace (lyra-home.md:75)
SCRIPT = "lyra-home"

token = open(TOKENF).read().strip()
src = open(WORKER, "rb").read()
print("worker bytes:", len(src))

meta = {
    "main_module": "worker.lyra.js",
    "compatibility_date": "2024-12-01",
    "bindings": [
        {"type": "kv_namespace", "name": "LYRA_KV", "namespace_id": KV_ID},
        {"type": "ai", "name": "AI"},
    ],
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
