PASS: all 14 targeted cases passed on unchanged final bytes.
h.py: PASS — valid fresh export preserves identity and binds host/census/preparation; E85 and invalid host pin refuse.
rd.py: PASS — publication hashes/status verified; missing selection and invalid job refuse by name.
rv.py: PASS — timeout, matching PASS, identity mismatch, malformed JSON, non-PASS and mode 0644 tested.
pc.py: PASS — valid synthetic sessions reach denied transport; failure marker, no .done, bounded final pass and work exit 7 verified.
pc.sh: tk_live_finish executes final pc.py then ep.py; shell and Python traces record child commands and exit outcomes.
Review uses the sealed 7200-second bound with a fake clock; only pre-wait rv.evidence is stubbed; identity/census/receipt/preparation checks remain real.
rd.py r1.json contains returncode and byte counts; RESULT.json separately records verified published SHA256 values.
All endpoints are synthetic 127.0.0.1:1 URLs; seccomp denies sockets. One synthetic prior part leaves three pending parts and at most four total threads.
Source/copied SHA256SUMS pass before and after (c992c930); b/ matches reference 240f8c17; extracted tree matches its kit archive.
All writes stay under tt24t2; kit/tree mounts are read-only; tests inherit nice 10, four-CPU affinity, one-thread math settings and a 7 GiB address-space cap.
RESULT.json records commands, exits, executable hashes, assertions, coverage and produced files; no production sessions, GCS or training were used.
