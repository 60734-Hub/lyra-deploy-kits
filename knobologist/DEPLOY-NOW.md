# DEPLOY NOW - lyra-home (streaming + learn pipeline)

One PUT. Needs: a Cloudflare root token with Workers Scripts edit permission.

1. Put the token in a file named cf-root-token.txt next to this script
   (or set the CF_TOKEN environment variable).
2. Run:  python deploy-stream.py
   The script self-checks the worker hash first (78333 bytes / md5 43c7a72b) and aborts
   if it does not match. Then it PUTs to account 9342a170f13921bc5ef8b0ffde3b8602,
   script lyra-home.
3. Wait 25 seconds. Then verify:
   - GET  https://lyrahome.app/chat        -> must contain </style>  (page no longer blank)
   - GET  https://lyrahome.app/app         -> 200
   - GET  https://lyrahome.app/ownership   -> 200
   - POST https://lyrahome.app/api/learn   {"title":"test","text":"hello"}  (Bearer family key) -> ok:true
   - POST https://lyrahome.app/api/learn/retrieve {"query":"hello"}         (Bearer family key) -> hits
   - POST https://lyrahome.app/api/brain/stream {"message":"hi"}            (Bearer family key) -> SSE

Family brain key (bearer): see HANDOVER.md.
