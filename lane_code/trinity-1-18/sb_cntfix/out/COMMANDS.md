# CPU reproduction commands

Run from `/scratch/jjyeung/orch_n30/sb_cntfix`. `bash cpu.sh` runs Python with nice 10, eight CPU threads, scratch caches, and hidden GPUs. These commands use no network, SSH, Git, process termination, or external writes. One-look commands are deliberately not replayable in the same namespace.

| Evidence | Command |
|---|---|
| Local K1 copies, pinned official function, pilot search, authorization copy | `bash cpu.sh prepare_local.py` (initial staging; destinations must not exist) |
| Backend/source pins and golden boundary cases | `bash cpu.sh finish_pins.py` (initial staging; not an idempotent migration) |
| K1 training pairs, selected rule, constant, confidence interval, decision | `bash cpu.sh kit/files/freeze_training.py > out/training.log 2>&1` |
| 1,605 direct scores, boundary cases, recomputed dev reference bars | `bash cpu.sh kit/files/score_count_pricing.py --selftest --items kit/files/COUNT_ITEMS_535.jsonl > out/selftest.log 2>&1` |
| 98 captures, 464 prompts, 3,136 verified frames | `bash cpu.sh kit/files/build_count_manifest.py --items kit/files/COUNT_ITEMS_535.jsonl --set R0-dev --frames-root /scratch/jjyeung/orch_n30/b10_reserve/frames/scannetpp --frame-manifests /scratch/jjyeung/orch_n30/b10_reserve/out/frame_manifests --out out/MANIFEST_R0DEV.json > out/manifest.log 2>&1` |
| Complete CPU stub | `bash cpu.sh kit/files/run_count_teacher.py --manifest out/MANIFEST_R0DEV.json --manifest-sha256 231a23e9c75af383e26f69e4133b56e1a1fbf334b1ec673beefed408148674cd --out out/stub_final --stub > out/stub_run_final.log 2>&1` |
| 385-item coverage, category errors, cross-output replay rejection | `bash cpu.sh run_stub_score.py > out/stub_score.log 2>&1` (uses synthetic namespace `final`) |
| Reviewer score, label/oracle, source receipt, timing, and missing-pilot audit | `bash cpu.sh audit_cpu.py > out/cpu_audit.log 2>&1` |
| Reviewer invalid-DONE audit: 98 invalid markers, zero payloads | `bash cpu.sh audit_controls.py > out/control_audit.log 2>&1` |
| Manifest, payload, one-look race, rounding-boundary controls | `bash cpu.sh test_controls.py > out/control_tests.log 2>&1` |
| Absolute deadline, cumulative budget, abnormal/clean resume controls | `bash cpu.sh test_runtime.py > out/runtime_tests.log 2>&1` |
| Fixture archive search and exact missing paths | `bash cpu.sh inspect_missing.py` |

The reviewer scripts are preserved verbatim under `review/`. The local CPU audit adds the local import path, pins the supplied official source instead of reporting it absent, and includes current code/config hashes. Its numerical calculations are unchanged. The control audit is unchanged.

The K1 mirror contains labels and teacher results but lacks the five geometry/learned pilot artifacts. Missing fixture frames are listed individually in `MISSING_INPUTS.json`. The full pilot table's status is `MISSING`, not a reconstructed estimate.

The training gate rejects this proposal, so no real registration, GPU run, or real R0-dev score command is authorized. The synthetic namespace remains consumed after its score. Re-running CPU checks requires fresh synthetic test/output directories; it never clears a real ledger.

Additional evidence commands:

- `bash cpu.sh test_deadline.py > out/deadline_test.log 2>&1` checks the deadline inside an active CPU call.
- `bash cpu.sh recompute_k1_references.py > out/k1_references.log 2>&1` recomputes selected and NMS diagnostic per-bin references without changing the freeze.
- `bash cpu.sh build_delivery.py` verifies the upstream function pin and writes `FIX_REPORT.md` and `GPU_NEED.json`.
- `bash cpu.sh package_delivery.py` creates the file inventory, tar archive, and SHA256 sidecar.
