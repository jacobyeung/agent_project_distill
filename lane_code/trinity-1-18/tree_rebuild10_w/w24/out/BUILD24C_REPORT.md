COMPLETE: kit-only bytecode fix validated. GO=false; no production submission.
Package: `out/tree_rebuild_b24c_22859833.tar`; 9,038,821 bytes; SHA-256 `457fe75df9ee44b72c5caf95b4c4c06ec8081057916f27dbf54f4da12b081f4f` (`out/DELIVERY_24C.json`).
Package seal: `2285983395c80bab369e772402265818e0d3bc906117202492665653df1903e6`; all 1230 members stream-verified (`work/build24c/PACKAGE_MANIFEST.json`).
This is an overlay on unchanged `tree_rebuild_b24b_7d7a8858.tar`; it includes complete q/n kits and the unchanged source tree. Unchanged test prerequisites remain in the base package.
Tree: `e1e64652087c2cde689620e4fb6edca57123feccae78c8a0a4b70ce8f7b35c10`; byte-identical to build24b (`RUNTIME_TESTS.json`, `BASELINE_UNCHANGED.json`).
Kit q: `edb324ff474c598328542084d549e6a8540eed7127d63e2b1f886c64a0865c5f`. Kit n: `bff6d42cd55558534be50305607f063b4f7f5bf37fe3be670746aa632f992699` (`work/build24c/KIT.json`).

CPU reproduction: each writable original kit acquired `b/__pycache__/z.cpython-312.pyc`; native `verify(kit)` then raised `R1_KIT_CONTENT_DIFFERS` (`BEFORE.json`).
The decoded staging command runs m.py with `-I` and without `-B`; isolated mode ignores the exported PYTHONDONTWRITEBYTECODE variable. The reproduction retained that variable at 1 and used CPU Python 3.12 in place of this node's older /usr/bin/python3.
The isolated staging imports prove the cause even when the later log screener inherits the existing export. No Orchard logs or network were accessed.
Every emitted Python start now carries `-B`; shell wrappers, bootstrap and launcher also supply `PYTHONDONTWRITEBYTECODE=1`. The audit finds 31 shell starts in q and 34 in n (`STARTS_q.json`, `STARTS_n.json`).
Every active external generator applies the same hardener before sealing, including output from the unchanged sealed-tree generator. Regeneration reproduces both final kits byte-for-byte; the hardener is idempotent (`runtime_tests.py`).
N uses torch.distributed.run with `--no-python` and an explicit shell worker wrapper that invokes Python with `-B`; the four-worker topology and GO/admission checks remain intact.
Scheduler logs, working directories, temporary files, caches, staging files and helper logs use node-local storage. Result archives are assembled locally, then published to the existing output sibling outside both kits (`WRITE_AUDIT.json`).
The complete write inventory covers import caches, scheduler logs, capture args, step logs, decoded shell, staging locks/stamps, environments, overlays, extracted source, proof/room outputs and result archives (`WRITE_AUDIT.json`).

The decoded helper regression runs full staging without stamp reuse, then the native proof/log/room/output pipeline on writable copies of both kits. Every kit file and hash stays unchanged, and native verify passes (`SEQUENCE.json`, `sequence_final.log`).
The regression uses tiny pinned staging archives, CPU Python, a CPU guard diagnostic stand-in, the established bwrap view and empty room streams with the real pinned authority. The native proof uses each kit's own config; N's launcher returns at GO=false.
Tests: 136 passed, including all 17 guard tests for each kit, kit/naming/resolver suites, runtime tests and both helper-sequence cases (`TEST_COUNTS.json`).
Hardener statement coverage: 48/48; no missing executable statements (`COVERAGE.json`). Guard text remains byte-identical at `e397ea70`.
Decoded scans: q PASS; n PASS (`SCAN_q.json`, `SCAN_n.json`).
Own-config look-ahead: q and n both reach `R1_PROOF_FRAME_HOST_REQUIRED`, the expected CPU/frame-host boundary (`LOOKAHEAD_q.json`, `LOOKAHEAD_n.json`).
Configs, resolver identity functions, admission, legality, removals, opener rows, step-544 lineage and the DEFERRED boundary are unchanged (`RUNTIME_TESTS.json`).

Upload delta: 20 files, 132,622 bytes against the union of UPLOADS_MINIMAL plus UPLOADS_24B. Applying it reconstructs the exact final upload set (`out/UPLOADS_24C.json`).
Stream root: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24c/upload`. Tar member list: `out/UPLOADS_24C.list`; every name, byte count, SHA-256 and local path is in the JSON manifest.
Existing unlisted bytecode still refuses. Apply the delta to clean sealed directories; preserve preexisting stray files outside the kit before verification (`out/OPERATOR_24C.md`).
All existing packages remain unchanged. Workspace growth at packaging: 284,381,264 bytes, below 300 MB; superseded material is retained in attic (`DELIVERY_24C.json`).
No production GPU/model execution, upload or submission is claimed. CPU work ran at nice 10 or lower priority, with at most eight threads and a 20-GiB address-space ceiling.
Evidence paths without a prefix are under `work/build24c/`. GO remains false.
