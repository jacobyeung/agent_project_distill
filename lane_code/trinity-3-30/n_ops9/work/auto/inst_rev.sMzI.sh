set -euo pipefail; umask 077; D=/project/community/jjyeung/okh7/x_22c714e1/n_r; T=$D/review.json
[[ -e $T || -L $T ]] && { echo "REFUSED: $T exists"; exit 3; }
[[ -d $D ]] || mkdir -m 700 $D; [[ -d $D && ! -L $D ]] || { echo "REFUSED: n_r not a dir"; exit 3; }; chmod 700 $D
python3 -B - <<'PY'
import base64,hashlib,os
raw=base64.b64decode("eyJjb25maWdfaWRlbnRpdHkiOiAiZjYyNTBmNzAwY2Y1NmQyZWQ1MDUzMmY5NzNmODIwNjEyM2Y3MjZiNjk3MGZkYWRhNWM0NTg1MTA5YTdiYzA5MiIsICJldmlkZW5jZSI6IHsiYWRtaXRfc2hhMjU2IjogIjBmNGQ1OGFiMWI0OGY4NjEyYTVkMDk3YWVmYTc3MzIxNzk5NmJmZjM0MWMzMmM2NDUyMDRiNjQ4MmQ1Y2QzMDgiLCAiZ2F0ZV9vdXRfc2hhMjU2IjogIjYxOGMyMzcxZGVhNjE2ZTMzZmEzZWQ1M2M5ZjgzNTYwOWUwOTAwNTFmNGQ0MTgzNzNkNWI5MTFlYWU1NDRhMzMiLCAiZ2F0ZV9weV9zaGEyNTYiOiAiMzkwZjlmMTQ1NDUxMTA3Y2UzMTc3MWEzOTIzYzQzYTE4ZDdiZjkzN2NmMjEzNDU2MTBkNjRhOTUyZDA4NmJkOCIsICJraXRfc2VhbCI6ICI3ZTIzYmJkZGIwNTJhNmYzZGRiMTkxNTg1OGRjMDNlODk1MWQzNWQ4N2NjOWEzY2QyNzZmODg1MzQxNGQ1NzcxIiwgInBvaW50cyI6IFsiaWRlbnRpdHkiLCAiZF9wb3B1bGF0aW9uIiwgIlAxX2ZpbHRlcnMiLCAiY2Vuc3VzIiwgIml0ZW0zX2NvdW50cyIsICJmaXJzdF9iYXRjaCIsICJhZG1pdF90ZXN0IiwgInNjZW5lX2NlbnN1cyJdLCAicmV2aWV3ZXIiOiAibl9yZXZpZXcxayIsICJ2X2pzb25fc2hhMjU2IjogIjA2ZmQ2MWJlOGU1NDEwYTdkZTQ5MmJlN2VhMWRhMmFlMTVkZWNmNjE4MjgwNzg0N2E2NDNiNTFiM2YxMGZjZDcifSwgInZlcmRpY3QiOiAiUEFTUyJ9Cg=="); assert hashlib.sha256(raw).hexdigest()=="476d17bdba5b5aebab848ef6537d4323260c0f53b55879b8fbc79ca0bfe1a4c6"
fd=os.open("/project/community/jjyeung/okh7/x_22c714e1/n_r/review.json",os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.write(fd,raw); os.close(fd)
PY
echo "476d17bdba5b5aebab848ef6537d4323260c0f53b55879b8fbc79ca0bfe1a4c6  $T" | sha256sum -c --quiet && echo "PASS installed $T sha256=476d17bdba5b5aebab848ef6537d4323260c0f53b55879b8fbc79ca0bfe1a4c6 mode $(stat -c %a $T) dir $(stat -c %a $D)"
ls -la $D
