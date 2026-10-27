THE DEPLOY - one command, one token
====================================

This folder is the complete deploy kit. Everything is in place except ONE secret.

STEP 1. Get a Cloudflare token (he does not remember the old one - the old root token
        is lost, it lived only on the ASUS which is unreachable):
        dash.cloudflare.com  ->  My Profile  ->  API Tokens  ->  Create Token
        Template: "Edit Cloudflare Workers"
        Account Resources: the knobology account (9342a170f13921bc5ef8b0ffde3b8602)
        Create  ->  copy the value (it is shown ONCE).

STEP 2. Save it as a plain text file named exactly:  cf-root-token.txt
        in THIS folder, next to deploy-stream.py. Nothing else in the file.

STEP 3. Run:   python deploy-stream.py

That is the whole thing. The script verifies the worker bytes first (80,128 B /
md5 437103ea30bf948cd7b082a856a62d17) and ABORTS on any mismatch, so it cannot
ship the wrong build. Then it PUTs to the knobology account and waits 25s.

WHAT IT FIXES (all measured live on 2026-10-27, not recalled):
  /chat         200  13,434 B  </style> count 0   -> BLANK PAGE   (fixed by this PUT)
  /console      200  19,731 B  </style> count 0   -> BLANK PAGE   (fixed by this PUT)
  /api/brain    404   "Not found"                  -> brain route missing (fixed by this PUT)
  /app          404   (added by this PUT)
  /ownership    404   (added by this PUT)
  /api/learn    404   (added by this PUT)
  /api/health   200   {"ok":true,"who":"lyra","brain":"workers-ai"}

The live worker is an intermediate Oct 15-morning revision: voice + camera + restyle,
but with an unclosed <style> block on both pages and no brain route at all - even
though the live /chat page calls /api/brain three times. Three faults, one PUT.

AFTER THE PUT - verify these:
  GET  https://lyrahome.app/chat        -> 200 AND contains </style>
  GET  https://lyrahome.app/console     -> 200 AND contains </style>
  POST https://lyrahome.app/api/brain   {"message":"hi"}  (Bearer family key) -> JSON, not 404
  GET  https://lyrahome.app/app         -> 200
  GET  https://lyrahome.app/ownership   -> 200
  POST https://lyrahome.app/api/learn   {"title":"t","text":"hello"} (Bearer) -> ok:true
  POST https://lyrahome.app/api/learn/retrieve {"query":"hello"} (Bearer) -> hits
  GET  https://lyrahome.app/api/learn   (Bearer) -> digestSynced:true
  POST https://lyrahome.app/api/brain/stream {"message":"hi"} (Bearer) -> SSE

VERIFICATION STATUS OF THIS BUILD (re-run 2026-10-27 against the EXACT bytes in this folder):
  sim-learn.mjs  36 passed, 0 failed   (absorb / embed / retrieve / delete / digest sync)
  sim-stream.mjs  7 passed, 0 failed + extended 3 passed, 0 failed  (SSE / /app / threads)
  node --check: clean
  Also cross-checked: the short harness passes against the digest artifact and the full
  digest harness passes against the staged bytes, so the two files are behaviourally identical.

FAMILY BRAIN KEY (bearer): saved beside this file as lyra-key.txt (the script reads it
automatically). If it is missing, copy the key from HANDOVER.md one level up.


WHAT THE SCRIPT DOES ON ITS OWN
  1. checks the worker bytes (80,128 B / md5 437103ea...) and ABORTS on any mismatch
  2. PUTs to the knobology account
  3. waits 25s for the edge
  4. runs 8 live checks: /chat </style>, /console </style>, /app, /ownership,
     /api/learn list, /api/brain answer, /api/learn absorb, /api/learn/retrieve
  5. prints PASS/FAIL per check and exits non-zero if anything failed

So: run it, read the eight lines, done. If all eight say PASS the site is fixed.

NEXT-DAY STEPS THAT ARE NOT YOURS
  - the Broadcom removal on the ASUS is queued on my side and needs one host-capable turn
  - evidence files 28 and 30 are written and waiting to be filed on your desktop
  - the ACEMAGIC still needs the desktop app installed and signed in ON the box
