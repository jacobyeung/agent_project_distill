# Separate r6 read kit

**Validation status:** all suites pass: candidate 133/133, ported and reference 53/53 each, refute 4/4, r6 9/9, FIX6 7/7, FIX5 6/6, FIX4 10/10, and step-544 7/7. Real-RGB runtime fixtures pass 4 unfiltered a7, 3 direct-filter a7 and 6 r6 items. All 106 legacy main/a7 plans match h1read fix 6 byte-for-byte and by hash. `FIXV1.md` records the final seal and verification results.

This fork prepares the 900-item VSTI relative dev read as opaque family `r6`. It admits only run `469ddece`, generation `mstop`, step 544, or run `673bc60f`, milestone 200, with `r6` alone. Decision reads using main and a7 remain on the untouched sibling h1read kit.

`FIXV1.md` describes the implementation, validation, scoring, operator commands and wall-time estimate. `UPLOAD_PLAN_V1.md` specifies the only new upload: `assets/b62c14e9.jsonl`, 2,375,536 bytes. All 2,176 required frames already belong to a7's pinned archive; no new frame upload is needed.

The reader preserves the six source types at 150 items each, across 68 rooms. The documented commands omit `--types`; `--types direct` also retains all 900 items. Both use a7's direct reader, MC prompt builder, greedy decoding, 32 anchors duplicated into 64 processor frames, and ON16k → B2048/B4096 continuation policy. B2048 supplies the scores. The adapter registers the six MC task names in the isolated process; evaluator source and functions stay unchanged.

Each compact record contains its item ID, room, task type, predicted letter, gold letter, binary score and template-capture flag. The capture implementation is byte-identical to the pinned source, packaged as `c6.py`. `vsti_summary.py` reports per-type and pooled accuracy, the constant baselines, capture rates and the compact item's SHA256. Paired reports compare R1 m200 against step 544 with 10,000 whole-room bootstrap draws, seed 20261118. The gate requires a positive pooled point difference and no per-type interval wholly below zero.

The offline test runner confines fixtures and ledgers to `evidence/test_*` and rejects deletion and network operations. Fixed-token preparations are fixtures only. Runtime fixtures execute the actual worker, evaluator, budget derivation and mergers on real RGB frames with mocked engine, export/model staging and GPU parity probes. They do not establish live GPU parity or production scores.

The retained FIX3–FIX6 reports describe the reference contracts. Their historical fixture paths are read from h1read because this fork excludes its top-level test directories. Tests explicitly account for the three changed reader adapters (`worker.py`, `x7.py`, `chain.py`) and two new modules. All other 71 inherited reader files retain their pins. Legacy plan checks compare serialized plan bytes and `plan_sha256`; CONFIG integrity pins change to authenticate the fork.

The following commands run the complete validation gate. They write only inside h1vsti. The sealer produces this fork's `evidence/FINAL_PINS.json` and `SHA256SUMS.txt`. FIXV1.md and post-seal verification logs remain outside the manifest to avoid circular hashes.

```bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1vsti
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
"$PY" -B tools/test_fix3.py fixv1 > evidence/FIXV1_NEW_TESTS.log 2>&1
"$PY" -B tools/test_fix3.py fix6 > evidence/FIXV1_FIX6_TESTS.log 2>&1
"$PY" -B tools/test_fix3.py fix5 > evidence/FIXV1_FIX5_TESTS.log 2>&1
"$PY" -B tools/test_fix3.py fix4 > evidence/FIXV1_FIX4_TESTS.log 2>&1
"$PY" -B tools/test_fix3.py targeted > evidence/FIXV1_TARGETED.log 2>&1
"$PY" -B tools/test_fix3.py runtime > evidence/FIXV1_RUNTIME.log 2>&1
"$PY" -B tools/test_fix3.py runtime_direct > evidence/FIXV1_RUNTIME_DIRECT.log 2>&1
"$PY" -B tools/test_fix3.py runtime_r6 > evidence/FIXV1_RUNTIME_R6.log 2>&1
"$PY" -B tools/seal.py --pre-test > evidence/FIXV1_PRESEAL.log
"$PY" -B tools/test_fix3.py candidate > evidence/FIXV1_TESTS.log 2>&1
"$PY" -B tools/test_fix3.py ported > evidence/FIXV1_READK_PORTED.log 2>&1
"$PY" -B tools/test_fix3.py reference > evidence/FIXV1_READK_REFERENCE.log 2>&1
"$PY" -B tools/test_fix3.py refute > evidence/FIXV1_REFUTE.log 2>&1
"$PY" -B tools/seal.py > evidence/FIXV1_SEAL.log
"$PY" -B tools/test_fix3.py pins > evidence/FIXV1_FINAL_PIN_TEST.log 2>&1
sha256sum -c SHA256SUMS.txt > evidence/FIXV1_SHA256_CHECK.log
```

Use a local CPU Python with the existing test dependencies for runtime suites. Preparation, unpacking and the summarizer use the standard library. No network, SSH, Slurm, GPU, Git, deletion, production preparation or submission is part of this validation.
