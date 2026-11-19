# Counting kit: CPU controls pass; GPU launch rejected on training
The frozen K1-training decision is `REJECT_ON_TRAINING`; requested GPU time is zero.
No real R0-dev registration or look was consumed. No official item file was opened.

- `bash cpu.sh kit/files/freeze_training.py`: 24 rules, 202 train captures, 1,960 pairs, 196 large pairs.
- Training selects raw per-frame maximum, joint ≥0.35, and constant 6. MRA is 45.0 versus 53.877551; paired difference CI is [−15.674157, −2.425743]. The same command produces these values.
- Rules, thresholds, the decision, response, and row filter are frozen in `kit/files/FROZEN_CONFIG.json`. Training rejection disables the response and rows.
- `bash cpu.sh kit/files/score_count_pricing.py --selftest --items kit/files/COUNT_ITEMS_535.jsonl`: all 1,605 stored scores and 60 boundary cases pass. N's upstream function pin matches exactly (`MRA_PIN_VERIFICATION.json`).
- `bash cpu.sh audit_cpu.py`: zero stored-score mismatches; constant6=55.236220 and identity oracle=80.748031 on the 254-pair diagnostic overlap; GT frame maximum=48.300654 on all 306 large pairs. These diagnostics do not affect selection.
- `bash cpu.sh recompute_k1_references.py`: `K1_REFERENCE_RECOMPUTE.json` gives the corrected per-bin reference table and verifies that the training freeze did not change.
- The manifest command in `COMMANDS.md` verifies 3,136 frame hashes, 98 captures, and 464 prompts against the pinned allowlist.
- The full stub command in `COMMANDS.md` completes all 98 captures. `bash cpu.sh run_stub_score.py` verifies 385/385 items and rejects a second output path; scores remain `STUB_ONLY`.
- `STUB_SCORE_CATEGORY_ERRORS.json` reports category zero counts and item under/over errors. Multi-category items do not provide category-specific truth.
- `bash cpu.sh test_controls.py`: 34 checks pass, including atomic one-look races, unauthorized captures/paths, stale DONE fields, payload coverage, stub/real separation, and unrounded decisions.
- `bash cpu.sh test_runtime.py`: six checks pass for expired deadlines, cumulative budgets, abnormal restarts, changed bindings, and clean resumes.
- `bash cpu.sh test_deadline.py`: the in-flight CPU deadline exits with `time_cap`; no other process receives a signal.
- `bash cpu.sh audit_controls.py`: 98 invalid DONE markers produce a nonzero exit and zero teacher payloads. Both reviewer audits were rerun; their originals are retained under `review/`.

The ledger uses a fixed absolute path keyed by evaluation category, binds IDs/config/code/settings/manifest hashes before inference, and consumes the look before teacher results are opened. The real namespace is independent of output directories and synthetic namespaces.
The runner validates checksums, contract/settings hashes, full frame/category coverage, and non-stub provenance. It retains vnice launch requirements, nice 10, scratch caches, eight threads, a fixed deadline, cumulative accounting, and explicit clean resumes. It prohibits automatic relaunch after abnormal termination.
GPU availability and vnice were not checked. A native GPU call can delay Python's alarm; this kit does not claim an external GPU watchdog.

`bash cpu.sh inspect_missing.py` finds no matching fixture frames in the local K1 archive. `MISSING_INPUTS.json` lists all 64 exact paths and the five absent pilot files: `K1_PAIRS.json.gz`, `K1_LIFT.npz`, `K1_NMS.npz`, `K1_LMERGE.json`, and `K1_LEARN_EST.json`, expected under `kit/work/`. The full learned/geometry pilot table remains MISSING. Raw K1 labels and teacher outputs are packaged.
The active spec and design permit one preregistered R0-dev comparison only; dev-S1 remains diagnostic and its frame authority is MISSING. No count-form, floor, or future-head gate can select a release on dev.
Every generated evidence JSON records its input hashes. `COMMANDS.md` gives exact commands; `PACKAGE_PROVENANCE.json` hashes packaged files. The delivery is `sb_cntfix.tar` with `sb_cntfix.tar.sha256`.
No borderline prose-history sentence was retained; the explicit source/audit disclosures identify provenance.
