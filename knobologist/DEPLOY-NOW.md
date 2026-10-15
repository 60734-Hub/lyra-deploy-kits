# KNOBOLOGIST WORKER - DEPLOY NOW (one command)

cd knobologist
python deploy-stream.py

Needs only: cf-root-token.txt beside it (or CF_API_TOKEN env var).
Script self-checks md5 87be4c68eeb5378c7b82b148a5ec7f25 (71,565 B) and aborts on mismatch.
Account 9342a170f13921bc5ef8b0ffde3b8602 (knobology). Bindings AI + LYRA_KV, keep_secrets.

After ~25s verify:
- https://lyrahome.app/chat -> body contains </style>
- https://lyrahome.app/app -> 200 (threads + streaming UI)
- https://lyrahome.app/ownership -> certificate
- POST /api/brain/stream with family key -> text/event-stream
