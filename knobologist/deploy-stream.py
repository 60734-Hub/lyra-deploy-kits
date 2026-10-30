# Deploy lyra-home streaming + blank-page fix.
# Needs: Cloudflare root token (Workers Scripts edit perm).
# Usage: set CF_TOKEN env or put token in cf-root-token.txt next to this file.
# Verify: after ~25s, GET https://lyrahome.app/chat must contain </style>,
#         POST /api/learn (Bearer brain_token) must absorb, /api/learn/retrieve must return hits,
#         POST https://lyrahome.app/api/brain/stream (Bearer brain_token) must stream SSE.
import base64, hashlib, json, os, re, time, urllib.request, urllib.error, uuid, subprocess
from pathlib import Path

ACC = "9342a170f13921bc5ef8b0ffde3b8602"   # knobology account (verified)
MD5 = "d54b345f8f9e733a541d8a05cdda1c6b"   # split-\n template escape fix (all three pages), oct 30
HERE = Path(__file__).parent

# The edge rejects requests that carry NO User-Agent header at all (403 error code
# 1010). Measured Oct 28: no UA -> 403 on every path; any UA -> 200. It is not a
# Python block and not an IP block, so no curl dependency is needed and the checks
# work on any machine that can run Python (incl. a clean Windows box with no curl.exe).
# Defined here, at the top, because the FIRST network call in this script is the
# post-PUT chat peek below and it needs the header too.
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

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
                             headers={"X-Auth-Email": "programmably@gmail.com", "X-Auth-Key": tok, "Content-Type": "multipart/form-data; boundary=" + boundary})
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        print("PUT status", r.status); print(r.read().decode()[:1200])
except urllib.error.HTTPError as e:
    print("PUT FAILED", e.code); print(e.read().decode()[:3000]); raise SystemExit(1)

print("waiting 25s for edge..."); time.sleep(25)
# NOTE: this early peek MUST send a User-Agent too - the edge 403s any request
# without one. An uncaught 403 here would abort the script AFTER a successful PUT,
# making a working deploy read as a failure.
try:
    _peek = urllib.request.Request("https://lyrahome.app/chat", headers=dict(UA))
    html = urllib.request.urlopen(_peek, timeout=60).read().decode("utf-8", "replace")
    print("chat </style> count:", html.count("</style>"))
except Exception as e:
    print("chat peek failed (non-fatal, full checks below):", type(e).__name__, e)


# ---- post-PUT verification ----
KEY = os.environ.get("LYRA_KEY", "")
if not KEY:
    kp = HERE / "lyra-key.txt"
    if kp.exists(): KEY = kp.read_text().strip()
if not KEY:
    # Fallback: scan any .md/.txt sitting next to this script (or one level up)
    # for a bare 64-hex key. Earlier revisions pointed at a HANDOVER.md that is
    # NOT shipped in this kit, so the fallback silently did nothing.
    for d in (HERE, HERE.parent):
        if KEY: break
        for f in sorted(d.glob("*")):
            if not KEY and f.suffix.lower() in (".md", ".txt") and f.is_file():
                try:
                    m = re.search(r"\b([0-9a-f]{64})\b", f.read_text(errors="replace"))
                except Exception:
                    m = None
                if m: KEY = m.group(1)
if not KEY:
    print("NOTE: no brain key found (lyra-key.txt missing) - brain/learn checks will run unauth.")
# NOTE: H is never used as-is; get()/post() build their own headers. It is kept
# only for readability. Any request built from it would lack the User-Agent the
# edge requires (403 code 1010).

def _request(req, timeout, tries=3):
    last = (0, "")
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                last = (r.status, r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            last = (e.code, e.read().decode("utf-8", "replace"))
        except Exception as e:
            last = (0, "%s: %s" % (type(e).__name__, e))
        if last[0] == 200:
            return last
        time.sleep(4)
    return last

def get(path, timeout=60, tries=3):
    return _request(urllib.request.Request("https://lyrahome.app" + path, headers=dict(UA)),
                    timeout, tries)

def post(path, obj, timeout=90, tries=3):
    h = dict(UA); h["Content-Type"] = "application/json"
    if KEY: h["Authorization"] = "Bearer " + KEY
    return _request(urllib.request.Request("https://lyrahome.app" + path,
                                           data=json.dumps(obj).encode(), method="POST",
                                           headers=h), timeout, tries)

checks = []
st, body = get("/chat");        checks.append(("/chat contains </style>", st == 200 and "</style>" in body, "%s count=%d" % (st, body.count("</style>"))))
st, body = get("/console");     checks.append(("/console contains </style>", st == 200 and "</style>" in body, "%s count=%d" % (st, body.count("</style>"))))
st, _    = get("/app");         checks.append(("/app 200", st == 200, str(st)))
st, _    = get("/ownership");   checks.append(("/ownership 200", st == 200, str(st)))
st, _    = get("/api/learn");   checks.append(("/api/learn 200 (list)", st == 200, str(st)))
st, body = post("/api/brain", {"message": "deploy self-check"}); checks.append(("/api/brain answers (POST, 200 + reply)", st == 200 and "reply" in body, str(st)))
st, body = post("/api/learn", {"title": "deploy-check", "text": "self check after deploy"})
checks.append(("/api/learn absorb", st == 200 and "ok" in body.lower(), str(st)))
st, body = post("/api/learn/retrieve", {"query": "self check", "k": 3})
checks.append(("/api/learn/retrieve hits", st == 200 and "self check" in body, str(st)))

print()
print("=== POST-PUT VERIFICATION ===")
bad = 0
for name, ok, detail in checks:
    print(("  PASS  " if ok else "  FAIL  ") + name + "  (" + detail + ")")
    bad += 0 if ok else 1
print("=== %d/%d passed ===" % (len(checks) - bad, len(checks)))
if not KEY:
    print("(no brain key found - set LYRA_KEY or drop lyra-key.txt next to this script to enable the API checks)")
if bad:
    raise SystemExit(1)
