Proof/read support private --shm, root-local temp/home/caches, and before/after UID-owned host /dev/shm evidence.
--yield-glob polls every 30 seconds, sends TERM then KILL after 60 seconds only to its reader group, and records YIELD.json leftovers.
The unchanged reader retains both packet model copies; README budgets roughly 36 GiB per read plus frames, caches, and logs.
root/trinity_runner carries the three wrapper modules for a root-only copy at the same absolute path.
selfcheck verifies recorded sizes, small-file SHA256, bootstrap/bwrap pins, wrapper hashes, CONFIG literals, symlinks, and a CPU bwrap probe.
Tests: 56 passed (33 existing, 23 added); TESTS_ADDENDUM_FINAL.log includes real CPU TERM/KILL tests and mocked proof/read yields.
The existing STAGING.json, bootstrap, bwrap, and export metadata remain unchanged; see ROOT_PRESERVED.json.
Final metadata checks passed for 19 staged files and 3 wrapper files; five large shards received size checks only.
OPEN: the real CPU probe failed because staged bwrap requires unavailable GLIBC 2.33/2.34/2.38; no retry or binary replacement ran.
OPEN: 34 CONFIG findings include a pinned Orchard host name and outside paths; literal portability cannot pass without changing pinned evidence.
OPEN: runtime/base/payload stages remain incomplete, and the existing a0 receipt lacks member hashes; selfcheck refuses acceptance.
No GPU, network, SSH, Git, deletion, model-content scan, or input-tar wait ran. README and DIFF.md document the boundaries.
