# Streaming-replies deploy to lyrahome.app — laptop kit (interactive turn only)

State: patched + sim-verified 4/4 in the sandbox. NOT deployed. Live /api/brain/stream returns 404.
Ferry: https://raw.githubusercontent.com/60734-Hub/lyra-deploy-kits/main/eyes/worker.lyra.js.b64 (public, 74,332 B)
Expected worker: 55,748 B, md5 6e88f602baa31caaa6dde428be7e4827

## Step 1 — pull + decode on the ASUS (PowerShell, as capta)
```powershell
$dir = "C:\Users\capta\lyra-home\deploy-kits\stream"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/60734-Hub/lyra-deploy-kits/main/eyes/worker.lyra.js.b64" -OutFile "$dir\worker.lyra.js.b64"
$b64 = [System.IO.File]::ReadAllText("$dir\worker.lyra.js.b64")
$bytes = [System.Convert]::FromBase64String($b64)
[System.IO.File]::WriteAllBytes("$dir\worker.lyra.js", $bytes)
(Get-Item "$dir\worker.lyra.js").Length
Get-FileHash "$dir\worker.lyra.js" -Algorithm MD5
```
Expect Length 55748, MD5 6E88F602BAA31CAAA6DDE428BE7E4827. STOP if it differs.

## Step 2 — SAFETY: compare live KV lyra_soul against the kit copy BEFORE any deploy script
Any deploy script that bulk-PUTs lyra_soul + lyra_memory_digest from lyra-soul.json can clobber
his console edits. Compare first; only proceed if live == kit.

## Step 3 — PUT the worker (root token at C:\Users\capta\lyra-home\cf-root-token.txt)
Full array of bindings is required on every PUT; keep_secrets=true.
Bindings on worker `lyra-home`: AI (workers-ai), LYRA_KV (kv_namespace).
Content-Type for the module part MUST be `application/javascript+module` (plain application/javascript = error 10021).
Part filename MUST match main_module exactly (worker.lyra.js).
Use metadata body_part "metadata" + script part, multipart/form-data.

## Step 4 — verify LIVE (wait ~25 s after PUT; edge serves the old version until then)
```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://lyrahome.app/api/brain/stream -H "Content-Type: application/json" -d '{"message":"hi"}'   # expect 401 (unauth token check)
curl -sN -X POST https://lyrahome.app/api/brain/stream -H "Content-Type: application/json" -H "Authorization: Bearer <family key>" -d '{"message":"say hi"}' | head -20   # expect text/event-stream, data: {"t":"..."} frames, then data: {"done":true,...}
curl -s https://lyrahome.app/api/health   # expect {"ok":true,"who":"lyra","brain":"workers-ai"}
curl -s https://lyrahome.app/chat | wc -c  # page must contain the streaming send()
```
Do NOT trust the PUT response's success line. The curl output is the evidence.

## Step 5 — close out
- Flip the ferry repo back to private: PATCH /repos/60734-Hub/lyra-deploy-kits {"private":true}
- File evidence 28: what shipped, md5 before/after, live SSE transcript, bindings intact.

## Gotchas already paid (do not relearn)
- PowerShell here-strings write CRLF into .sh -> WSL bash chokes on '\r'. Use
  [System.IO.File]::WriteAllText($p, $s, [System.Text.Encoding]::ASCII) with "`n" replaced by [char]10.
- Do not inline python in a PowerShell heredoc; write the .py to disk and run it by path.
- A 403 on the first POST right after deploy = old edge version, not an auth failure. Wait and retest.
