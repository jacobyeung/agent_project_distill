Cause: the kit omits `u/eb3429c5`; production stages it from the package pinned by `k/0.json` at `staged_inputs.packages[0]`.
Changes: `tools/selection_stage.py:58,159` authenticates pinned metadata, tar bytes/SHA256 and every member; it extracts only inventory files into fresh 0700 directories and rejects links/escapes.
Mounts: `tools/package_selection.py:120` binds kit `k/` and staged package destinations separately, read-only under AS and AL; the staging alias is also read-only.

| Input occurrences | Source |
|---|---|
| 13 source gzips | Orchard `/home/jjyeung/okit/i/eb3429c5/eb3429c5.tar`, pinned by kit `k/0.json`; all 40 unique inventory files are checked. |
| 25 remaining pins | `/project/community/jjyeung/okh7/x_07ca49df/k/`; every file is checked against its input pin. |

[Every input and source](evidence/fix7_selection/INPUTS.md): no additional staged-file/archive/directory, top-level tar or extra-file dependency matches the selection inputs.
Tests: all four `test_fix7_*.py` scripts PASS; package fixtures cover 15 staging refusals and existing outputs. Local bwrap verifies both read-only roots; its fixture omits sandbox-blocked network setup, while q.sh retains `--unshare-net`. Orchard execution and production equality remain unverified.
Build: deterministic, 118592 bytes; `build/q.sh` SHA256 `6240ca48a5591dc853c222cf3e9848a624b56ea8cf0afe804b269512ee801341`. Output: `BUN/q_c492e8d1/o/`; existing output is refused and run 1 remains untouched.
