# Deploy lyra-home streaming + blank-page fix.
# Needs: Cloudflare root token (Workers Scripts edit perm).
# Usage: set CF_TOKEN env or put token in cf-root-token.txt next to this file.
# Verify: after ~25s, GET https://lyrahome.app/chat must contain </style>,
#         POST /api/learn (Bearer brain_token) must absorb, /api/learn/retrieve must return hits,
#         POST https://lyrahome.app/api/brain/stream (Bearer brain_token) must stream SSE.
import base64, hashlib, json, os, time, urllib.request, urllib.error, uuid
from pathlib import Path

ACC = "9342a170f13921bc5ef8b0ffde3b8602"   # knobology account (verified)
MD5 = "43c7a72bb452947b5bcb6ba56dbdba90"   # verified build (78,333 B, learn pipeline)
HERE = Path(__file__).parent

code = (HERE / "worker.lyra.js").read_bytes()
md5 = hashlib.md5(code).hexdigest()
print("bytes", len(code), "md5", md5)
if md5 != MD5:
    print("MD5 MISMATCH - ABORT"); raise SystemExit(1)

tok = os.environ.get("CF_TOKEN")
if not tok:
    p = HERE / "cf-root-token.txt"
    if not p.exists(): print("NO TOKEN"); raise SystemExit(1)
    tok = p.read_text().strip()

boundary = "----lyrastream" + uuid.uuid4().hex
meta = {"main_module": "worker.js", "compatibility_date": "2024-12-01",
        "bindings": [{"type": "ai", "name": "AI"},
                     {"type": "kv_namespace", "name": "LYRA_KV", "namespace_id": "24e2b30874a04c2584b9a831a1b66a32"}],
        "keep_secrets": True}
def part(name, fn, ct, data):
    b = boundary.encode()
    return b"--" + b + b"\r\nContent-Disposition: form-data; name=\"" + name.encode() + b"\"; filename=\"" + fn.encode() + b"\"\r\nContent-Type: " + ct.encode() + b"\r\n\r\n" + data + b"\r\n"
body = part("metadata", "metadata.json", "application/json", json.dumps(meta).encode()) \
     + part("worker.js", "worker.js", "application/javascript+module", code) \
     + b"--" + boundary.encode() + b"--\r\n"
req = urllib.request.Request("https://api.cloudflare.com/client/v4/accounts/%s/workers/scripts/lyra-home" % ACC,
                             data=body, method="PUT",
                             headers={"Authorization": "Bearer " + tok, "Content-Type": "multipart/form-data; boundary=" + boundary})
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        print("PUT status", r.status); print(r.read().decode()[:1200])
except urllib.error.HTTPError as e:
    print("PUT FAILED", e.code); print(e.read().decode()[:3000]); raise SystemExit(1)

print("waiting 25s for edge..."); time.sleep(25)
html = urllib.request.urlopen("https://lyrahome.app/chat", timeout=60).read().decode("utf-8", "replace")
print("chat </style> count:", html.count("</style>"))
