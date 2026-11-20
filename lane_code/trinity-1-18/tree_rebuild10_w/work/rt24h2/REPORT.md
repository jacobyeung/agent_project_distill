PASS: all 10 new cases and 14 inherited tt24t2 cases pass on seal 60d24119.
pc.sh: PASS; EXIT/TERM/USR1, worker drain, both copier groups stopped/reaped, final/small branches and exit codes.
pc.py: PASS; live files, ckstop.json, checkpoint tar, n_ck complete.json, no-session marker, 0644 rejection and --small.
ep.py: PASS; materialization.json, receipt.json and refresh.json retain exact bytes after routing raises; failure code retained.
z.py: PASS; load, archive name guard and screening execute; capsule/seal checks retained from rt24h.
o.py: PASS; separate o.tar member/payload checks and RESULT.json publication.
h.py: PASS; inherited rt24h/RESULT.json: h_valid, h_no_policy, h_bad_host; identical kit bytes.
rd.py: PASS; both routing-failure publication modes; three routing cases retained from rt24h/RESULT.json.
rv.py: PASS; inherited rt24h/RESULT.json: absent, PASS, identity, malformed, non-PASS and mode checks; identical kit bytes.
Harness fix: the outer launcher sets RLIMIT_FSIZE=64 MiB once; children assert the inherited limit.
Harness fix: TMPDIR is inside rt24h2; R-backed mounts permit deletion, other file trees remain read-only, and seccomp denies sockets.
Source/copied SHA256SUMS verified before and after; kit bytes unchanged. RESULT.json records commands, exits, hashes and assertions.
Run once; no case retries; synthetic fixtures only; nice>=10, <=4 threads, 7 GiB address-space limit; R stays below 1 GB.
Publication uses a synthetic builder/model pin through native rg.regenerate and ep/rd publishers; tt24t2 evidence is inherited, not rerun.
