Before edit, the launch/plan_r fixture failed: `bwrap: Can't find source path /tmp/q_22c714e1/z/s: No such file or directory` (required regression evidence: work/build24m4s/BEFORE.json).
The same mode-r layout now passes with root/c and no z/s: actual launch command and plan_r, payload stub calling real sc.bind; host bwrap 0.4.0, synthetic inputs.
Mode q imports $Q_NS/p/s: work/build24m4s/jd5.sh:414 passes $Q_NS/p to b/a.py; work/build24/kits/q/b/a.py:29-30 extracts and imports p/s, overriding the shell trainer path at jd5.sh:363.
All four sc.py copies bind the loaded package root, scope inputs, scratch, kit b and closure paths read-only; only the output is writable. Missing inputs refuse with R1_SCENE_BIND_SOURCE_MISSING; 28 cases pass.
The r/q, inherited z/s and /tmp-closure fixtures pass 200 native census comparisons and held-row refusal checks; the inherited fixture imports its staged z/s. All 30 suite groups pass, including kit, scan, naming, resolver, guard, arming, qd, planner and rcj; setup failures and outputs remain in FAILURES.json.
C'' de202f58, census-compare bytes, all rcj pins and mode-b command bytes are unchanged. VALIDATION.json records the checks and fixture scope; no production run or upload occurred.
UPLOADS_24M4S.json/.list replay exactly against the supplied Orchard pins: nine ordinary files, three optional n_go files. Seals: q 532afee4, n 91c4a62d, n_go f936e5cc, qd 8de0c8b3.
The package preserves input members and superseded bytes in attic; package.py verifies every archived byte, mode and link before writing the .sha256 last.
