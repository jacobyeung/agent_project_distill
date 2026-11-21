jn5.sh SHA-256: `930d52df0399fc96a2f5c6a22a804658fb8d93b2de6e23031a2a7f77b1386377`. All 52 cases (26 jn4/jn5 pairs) and the separate fallback-bound check passed their stated assertions. Header/ROOT/forwarding, source hashes, screening and syntax pass; no live Orchard test.

| Check | jn4 → jn5 | Evidence under work/build24m4z13b/ |
|---|---|---|
| Setup; failing/caught-error publisher; resolve and l.py faults | Missing named refusal → fixed fallback; status preserved; one final attempt | tests.log, extra.log, test_table.csv |
| Blocked final publisher / blocked fallback | jn4 watchdog at 124.285 s → jn5 refusal at 120.237 s; blocked fallback returns at 15.240 s; status 3 | hang_4/, hang_5/, fallback_bound/ |
| GPU/seal/resolve/l.py controls; periodic ticks; child-tree TERM/USR1; final-publish signals | Controls pass; injected faults fail before and pass after; jn5 preserves status and makes one final attempt | results.json, VALIDATION.txt, static_checks.log; initial harness failure output: first_failure.log |
