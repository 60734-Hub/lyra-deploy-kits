# KNOBOLOGIST WORKER - DEPLOY NOW (one command)

cd knobologist
python deploy-stream.py

Needs only: cf-root-token.txt beside it (or CF_API_TOKEN env var).
Script self-checks md5 89fa8d9f592d16341d3ec2f1e8e9e369 and aborts on mismatch.
Account 9342a170f13921bc5ef8b0ffde3b8602 (knobology). Bindings AI + LYRA_KV, keep_secrets.

After ~25s verify:
- https://lyrahome.app/chat -> body contains </style>
- https://lyrahome.app/app -> 200 (threads + streaming UI)
- https://lyrahome.app/ownership -> certificate
- POST /api/brain/stream with family key -> text/event-stream
