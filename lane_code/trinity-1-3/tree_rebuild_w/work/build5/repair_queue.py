"""Write the current test and delivery sequence without relying on chat history."""
from pathlib import Path
L=Path(__file__).resolve().parents[2]
(L/'work/build5/NEXT.md').write_text('''# Remaining build work

The active process is `legacy_base_copy.py`, tool session `63877`. The diagnostic tree and original-base phases completed. The verified extracted-base replay is running under the tightened harness. Read `proofs/legacy_base/progress.json` at most once a minute. Do not run another test process: module-end scratch compaction touches the common temporary root. No process was killed.

The original-base run loaded its harness before the current changes. Tree source changes made afterward are pending validation. `PROVISIONAL_REPAIRS.json` lists same-method base passes; `LEGACY_ADAPTATIONS.json` explains the explicit repairs. Do not weaken unsupported-bank guards. The native artifact reader now handles an absent camera connector. Metric and serializer checks remain in legacy tests.

After the base-copy replay finishes:

- Inspect `LEGACY_COMPARISON.json` and refresh `triage.py --brief`. Nested module replay and temporary-path subtest normalization are fixed in the harness. This remains diagnostic; the final package comparison is authoritative. A tree-only diagnostic source-artifact failure may disappear when the current tree runs from measured scratch.
- Run `bash work/build5/RUN.sh work/build5/proof.py repairs repairs`. It selects the current cases from `PROVISIONAL_REPAIRS.json` and writes `proofs/repairs`. The launcher copies only canonical source files to a hash-verified snapshot under `work/tmp/proof_source/tree_r1`, protects those source files from compaction, starts from a fresh empty cwd, and checks source identity afterward. No frame, checkpoint or cache files exist in that canonical source inventory.
- Run `bash work/build5/RUN.sh work/build5/proof.py r2_current all_r2`. This includes the new host-order and coverage tests. Freeze tree source while either proof runs. Repair failures and repeat only the necessary fixed proof, then ensure all R2/shared cases pass current source.
- Recompute coverage from current proof folders plus `proofs/new`, `proofs/r2`, `proofs/legacy_tree`, and `proofs/generator_tree`. Only hash-matched source and matching compiled code count. The census excludes generated artifacts. Close every CPU-reachable gap; actual full-store, frame-host, loader and GPU paths need an explicit missing-input reason.
- Run `reconcile.py` to account for every prior unresolved statement against reconstructed, hash-verified Build 4 source. No old hit is reused.

The harness now permits test writes only under `work/tmp` or the fixed proof folder, including file-open events. It refuses shared-path reads before path resolution. It executes a trusted `df` reserve check before each test while keeping ordinary test subprocesses forbidden. Scratch compaction filters small/preserved files before sorting. `proofs/harness_policy/CHECK.json` and `proofs/instrumentation/CHECK.json` pass; full integration under this harness is still pending.

A diagnostic run created legacy scratch artifacts beside the working source. Those files are read-only and excluded from source packaging; the exact paths and modes are in `proofs/artifact_locations/PROTECTION.json`. Do not alter them, erase them, or claim that run complied with the final temporary-location rule. The report template discloses this issue. The final extracted source and base sit under measured scratch.

The host fix stages packet inputs inside mandatory checklist item 2 before resolving their bytes. `tests/test_r2_build5_host_order.py` exercises real tiny archive/payload staging and refuses incorrect sealed pose bytes before full-store work. The new proof has not run yet. `out/FRAME_HOST_JOB.md` documents all mandatory steps and boundaries.

Delivery sequence after all source/tests/harness freeze:

- Run `seal.py`, `build_kits.py`, `make_delivery.py`. The two kit destinations must genuinely be empty; neither has been staged yet. No production authorization is granted.
- Run `PACKAGE_TEST.sh` with the delivery tar from an empty directory. The script runs generator, legacy, R2/shared and matching failed base cases in fresh empty group directories. It verifies bundled kits, current tree/base identities, and unchanged fixtures between groups. Do not edit source/harness during this run.
- Run `compare.py`, `coverage.py`, `reconcile.py`, and `fixes.py`. Require complete suites, zero R2/shared failures, zero tree-only regressions, and zero CPU-reachable gaps. Report pre-existing failures with both traces and actual causes.
- Refresh `out/PRELAUNCH_CARD.md` with the final seal, kits and qualification results. Run `fixture_audit.py` if examples changed; currently retained families are below the cap.
- Run `static_audit.py`, `final_audit.py`, `report.py`, `finish_docs.py`. These must use the qualified final package, not diagnostic receipts. The report and Build 5 design section are still absent.

Use only `login:false` shell commands and the prescribed `RUN.sh` interpreter/environment. Write only inside this lane. No Git, SSH, network, GPU, agents, real checkpoint/frame/store copies or filesystem erasure. Keep test processes serial. No real frame-host bytes, actual archive staging, real map joins, bank membership, pretrained vocabulary, remote transport/full-state recovery or runtime-output scan has been qualified.
''')
