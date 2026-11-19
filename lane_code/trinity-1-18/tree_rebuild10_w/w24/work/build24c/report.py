from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24c'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
p=J.load(D/'DELIVERY.json');u=J.load(L/'out/UPLOADS_24C.json');c=J.load(D/'TEST_COUNTS.json');k=p['kits'];cov=J.load(D/'COVERAGE.json')
text=f'''COMPLETE: kit-only bytecode fix validated. GO=false; no production submission.
Package: `{p['package']}`; {p['bytes']:,} bytes; SHA-256 `{p['sha256']}` (`out/DELIVERY_24C.json`).
Package seal: `{p['package_seal']}`; all {p['members']} members stream-verified (`work/build24c/PACKAGE_MANIFEST.json`).
This is an overlay on unchanged `tree_rebuild_b24b_7d7a8858.tar`; it includes complete q/n kits and the unchanged source tree. Unchanged test prerequisites remain in the base package.
Tree: `{p['tree_sha256']}`; byte-identical to build24b (`RUNTIME_TESTS.json`, `BASELINE_UNCHANGED.json`).
Kit q: `{k['q']['kit_seal']}`. Kit n: `{k['n']['kit_seal']}` (`work/build24c/KIT.json`).

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
Tests: {c['tests']} passed, including all 17 guard tests for each kit, kit/naming/resolver suites, runtime tests and both helper-sequence cases (`TEST_COUNTS.json`).
Hardener statement coverage: {cov['covered']}/{cov['total']}; no missing executable statements (`COVERAGE.json`). Guard text remains byte-identical at `e397ea70`.
Decoded scans: q PASS; n PASS (`SCAN_q.json`, `SCAN_n.json`).
Own-config look-ahead: q and n both reach `R1_PROOF_FRAME_HOST_REQUIRED`, the expected CPU/frame-host boundary (`LOOKAHEAD_q.json`, `LOOKAHEAD_n.json`).
Configs, resolver identity functions, admission, legality, removals, opener rows, step-544 lineage and the DEFERRED boundary are unchanged (`RUNTIME_TESTS.json`).

Upload delta: {u['total_files']} files, {u['total_bytes']:,} bytes against the union of UPLOADS_MINIMAL plus UPLOADS_24B. Applying it reconstructs the exact final upload set (`out/UPLOADS_24C.json`).
Stream root: `{u['stream_root']}`. Tar member list: `out/UPLOADS_24C.list`; every name, byte count, SHA-256 and local path is in the JSON manifest.
Existing unlisted bytecode still refuses. Apply the delta to clean sealed directories; preserve preexisting stray files outside the kit before verification (`out/OPERATOR_24C.md`).
All existing packages remain unchanged. Workspace growth at packaging: {p['workspace_growth_bytes']:,} bytes, below 300 MB; superseded material is retained in attic (`DELIVERY_24C.json`).
No production GPU/model execution, upload or submission is claimed. CPU work ran at nice 10 or lower priority, with at most eight threads and a 20-GiB address-space ceiling.
Evidence paths without a prefix are under `work/build24c/`. GO remains false.
'''
assert len(text.splitlines())<40
(L/'out/BUILD24C_REPORT.md').write_text(text)
print(text)
