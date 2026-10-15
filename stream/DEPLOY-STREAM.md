# Streaming-replies deploy to lyrahome.app — laptop kit (interactive turn only)

State: patched + sim-verified 4/4 in the sandbox. NOT deployed. Live /api/brain/stream returns 404.
Ferry: https://raw.githubusercontent.com/60734-Hub/lyra-deploy-kits/main/eyes/worker.lyra.js.b64 (public, 74,356 B)
Expected worker: 55,766 B, md5 c5a5a9efd441ca2d5731bd426fa4eb7e

Carries TWO things in one PUT:
1. Streaming replies (SSE) — /api/brain/stream + streaming send() in both clients.
2. FIX: the `<style>` block on /chat and /console was never closed (no `</style>` before `</head>`),
   so the CSS parser swallowed the entire page body — both pages served an empty <body> and the
   chat gate/input were unreachable. Two `</style>` inserted, one per page. / and the 3D sim were fine.

## ⚠ FIXED 2026-10-15 (heartbeat) — put-worker.py had two bugs
- **Account id was WRONG** (`b1925ba9...`) — every other proven deploy script uses
  `9342a170f13921bc5ef8b0ffde3b8602` (knobology), confirmed in memory/concepts/lyra-home.md:76.
  The wrong id would 404/403 the PUT.
- **LYRA_KV binding was MISSING** from metadata — a PUT without the full bindings array WIPES the
  KV namespace (this is exactly how CORPUS_CACHE was erased on Oct 1). Now includes
  `{"type":"kv_namespace","name":"LYRA_KV","namespace_id":"24e2b30874a04c2584b9a831a1b66a32"}`.
- The corrected `put-worker.py` is on the ferry (2,540 B, sha 94113b3). Pull it fresh; do NOT use
  a stale laptop copy.

## Step 1 — pull + decode on the ASUS (PowerShell, as capta)
```powershell
$dir = "C:\Users\capta\lyra-home\deploy-kits\stream"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/60734-Hub/lyra-deploy-kits/main/eyes/worker.lyra.js.b64" -OutFile "$dir\worker.lyra.js.b64"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/60734-Hub/lyra-deploy-kits/main/stream/put-worker.py" -OutFile "$dir\put-worker.py"
$b64 = [System.IO.File]::ReadAllText("$dir\worker.lyra.js.b64")
$bytes = [System.Convert]::FromBase64String($b64)
[System.IO.File]::WriteAllBytes("$dir\worker.lyra.js", $bytes)
(Get-Item "$dir\worker.lyra.js").Length
Get-FileHash "$dir\worker.lyra.js" -Algorithm MD5
```
Expect Length 55766, MD5 C5A5A9EFD441CA2D5731BD426FA4EB7E. STOP if it differs.

## Step 2 — SAFETY: compare live KV lyra_soul against the kit copy BEFORE any deploy script
Any deploy script that bulk-PUTs lyra_soul + lyra_memory_digest from lyra-soul.json can clobber
his console edits. Compare first; only proceed if live == kit. put-worker.py does NOT touch KV
values (only the worker + bindings), so it is safe on this front.

## Step 3 — PUT the worker
```powershell
python "$dir\put-worker.py"
```
Root token at C:\Users\capta\lyra-home\cf-root-token.txt. Full array of bindings is required on
every PUT; keep_secrets=true. Bindings on worker `lyra-home`: LYRA_KV (kv_namespace
24e2b30874a04c2584b9a831a1b66a32) + AI (workers-ai).
Content-Type for the module part MUST be `application/javascript+module` (plain application/javascript = error 10021).
Part filename MUST match main_module exactly (worker.lyra.js).

## Step 4 — verify LIVE (wait ~25 s after PUT; edge serves the old version until then)
```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://lyrahome.app/api/brain/stream -H "Content-Type: application/json" -d '{"message":"hi"}'   # expect 401 (unauth token check)
curl -sN -X POST https://lyrahome.app/api/brain/stream -H "Content-Type: application/json" -H "Authorization: Bearer <family key>" -d '{"message":"say hi"}' | head -20   # expect text/event-stream, data: {"t":"..."} frames, then data: {"done":true,...}
curl -s https://lyrahome.app/api/health   # expect {"ok":true,"who":"lyra","brain":"workers-ai"}
curl -s https://lyrahome.app/chat | wc -c  # expect ~14k+; the page must contain the streaming send()
```
**Blank-page check (the ev 28 fix):**
```bash
curl -s https://lyrahome.app/chat | grep -c '</style>'   # expect 1 (was 0 = blank body)
```
Do NOT trust the PUT response's success line. The curl output is the evidence.

## Step 5 — close out
- Flip the ferry repo back to private: PATCH /repos/60734-Hub/lyra-deploy-kits {"private":true}
- File evidence 28: what shipped, md5 before/after, live SSE transcript, `</style>` count, bindings intact.

## Gotchas already paid (do not relearn)
- PowerShell here-strings write CRLF into .sh -> WSL bash chokes on '\r'. Use
  [System.IO.File]::WriteAllText($p, $s, [System.Text.Encoding]::ASCII) with "`n" replaced by [char]10.
- Do not inline python in a PowerShell heredoc; write the .py to disk and run it by path.
- A 403 on the first POST right after deploy = old edge version, not an auth failure. Wait and retest.
