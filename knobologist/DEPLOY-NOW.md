# DEPLOY NOW - lyra-home (streaming + learn pipeline + digest sync)

One PUT. Needs: a Cloudflare API token with Workers Scripts edit permission.

STEP 0 (only if you have no token): dash.cloudflare.com -> My Profile -> API Tokens ->
Create Token -> template "Edit Cloudflare Workers" -> Account Resources: the knobology
account -> Create Token -> copy the value (shown once).

1. Put the token in a file named cf-root-token.txt next to this script
   (or set the CF_TOKEN environment variable).
2. Run:  python deploy-stream.py
   The script self-checks the worker hash first (80128 bytes / md5 437103ea) and aborts
   if it does not match. Then it PUTs to account 9342a170f13921bc5ef8b0ffde3b8602,
   script lyra-home.
3. Wait 25 seconds. Then verify. This PUT fixes THREE live faults, measured Oct 24 21:00:
   (a) /chat blank    - unclosed <style>, live body 13,434 B with </style> count 0
   (b) /console blank - SAME unclosed <style>; the command deck is dead too, not just /chat
   (c) /api/brain 404 "Not found" - the live build has no brain route at all, though the live
       /chat page calls it three times. The live worker is an intermediate revision (voice +
       camera + restyle from Oct 15 morning) missing the brain route.

   - GET  https://lyrahome.app/chat        -> 200 AND must contain </style>   (fixes a)
   - GET  https://lyrahome.app/console     -> 200 AND must contain </style>   (fixes b)
   - POST https://lyrahome.app/api/brain   {"message":"hi"} (Bearer family key) -> JSON reply, NOT 404  (fixes c)
   - GET  https://lyrahome.app/app         -> 200
   - GET  https://lyrahome.app/ownership   -> 200
   - POST https://lyrahome.app/api/learn   {"title":"test","text":"hello"}  (Bearer family key) -> ok:true
   - POST https://lyrahome.app/api/learn/retrieve {"query":"hello"}         (Bearer family key) -> hits
   - GET  https://lyrahome.app/api/learn      (Bearer family key) -> digestSynced:true
   - POST https://lyrahome.app/api/brain/stream {"message":"hi"}            (Bearer family key) -> SSE

   Pre-deploy baseline re-measured Oct 24 21:00: /chat 200/13,434 B/</style> x0, /console
   200/19,731 B/</style> x0, /app 404, /ownership 404, /api/learn 404, /api/brain 404,
   /api/health 200. The workers.dev /chat serves the identical 13,434 B body - one worker,
   both hostnames, no routing split.

Family brain key (bearer): see lyra-key.txt in this folder.
