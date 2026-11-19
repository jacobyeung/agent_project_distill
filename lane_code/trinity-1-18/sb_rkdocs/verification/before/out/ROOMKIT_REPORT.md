# Room kit: CPU delivery

The four requested review edits are implemented and all 44 tests pass. Both launch provenance records are VERIFIED. Kernel authorization remains **pending orchestrator**, and the gate rejects it. Real S1c and R0-dev inference remain unrun. This delivery authorizes no GPU launch.

## Resume and one-look controls

The runner requires `configs/GO_<run_id>.json` before authorization or CUDA. Stub integration tests execute S1c under run 1 followed by R0-dev under run 2, and interrupt `--stage all` during S1c before a manual closure and resume. They verify that completed captures are skipped, the interrupted capture resumes, and the first GO file remains unchanged.

Never edit a GO note, KERNEL_PROVENANCE.json or READER_RECEIPT.json after its first run; S1c receipts and SELECTION.json bind their hashes.

COST.json preserves prior records, including manual closure, authorization, accounted run IDs and evidence hashes, in history. STARTED.json embeds previous_started on recomputation. Predictions pass through pred.npz.part and os.replace. An interrupted partial file requires manual closure; a pred.npz without DONE remains blocked.

price.py checks prediction completeness using only receipts and hashes before its exclusive decision registration. An incomplete set consumes no look; conversion failure after registration consumes it. load_selection requires the S1c registration, f32 and dense predictions and DONE files, verifies their hashes, checks training-row identities, and recomputes every delta and the seeded bootstrap interval. Tests reject missing evidence and altered statistics.

## Reader receipt

`configs/READER_RECEIPT.json` verifies 98 frame lists against the routed item manifest, journal mapping and kit manifest. It replays all 134 direct-answer rows and scores from the accepted journal. Each value cites a file, field and SHA256. The checkpoint identity is the accepted reader's recorded export digest (sorted relative paths and file SHA256s); the receipt does not claim a local checkpoint-weight rehash.

Source: `/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/`, including `B/src/items/room134.json`, `B5/ret/metadata/reads/0/metadata/journals/4/0/`, and reader source under `A/src/tree` and `A/src/h1eval`/`B/src/h1eval`. Command: `bash scripts/cpu.sh scripts/reader_receipt.py > out/READER_RECEIPT.log 2>&1`.

## Frozen kernel

S1k selected the constants from a preregistered 16-candidate Cartesian grid on exactly 110 K1 training captures. The grid covers margin {0.05, 0.10} m, cell {0.05, 0.10} m, votes {1, 2} and closing {0.10, 0.20} m. It maximizes mean K1-train MRA, with refusal zero and ties resolved by grid order. Stored dense-64 DA3 predictions supply the 32 anchors through the kit conversion; no tower forward ran.

The winner is a **0.05 m cut below the first percentile, 0.10 m cells, two votes, and 0.20 m closing**. It scores **77.636364 K1-train MRA**, versus 76.909091 for the legacy tuple. Selection took 188.02 CPU-seconds and 188.96 elapsed seconds, with eight-thread limits. These training scores choose constants; they establish no held-out improvement.

The cited design records describe a rule selected on 88 official VSI-Bench ScanNet items and do not establish an independent origin for each legacy constant. S1k selects the deployed constants anew on K1 train. K1 labels still inherit the legacy rule, and the grid includes its tuple. These required disclosures remain in `relation_to_benchmark_rule`; `benchmark_selected: false` describes the new selection only. Authorization remains pending orchestrator.

`configs/KERNEL_FROZEN.json` binds the winner to `vendor/room_kernel.py`; both S1c and R0-dev pricing call it through `kernel.pipeline`. Legacy reproduction remains a separate consistency check. `out/S1K_REGISTRATION.json` and `out/S1K_RESULTS.json` preserve the grid, row scores, timing and input hashes. `evidence/s1k_execution_code/` preserves the source bytes used during selection; the provenance record maps historical source paths to these hashed snapshots.

Commands: `bash scripts/cpu.sh scripts/s1k.py > out/S1K.log 2>&1` and `bash scripts/cpu.sh scripts/kernel_provenance.py > out/KERNEL_PROVENANCE.log 2>&1`. S1k is already frozen and refuses a second selection. The short provenance report is `out/KERNEL_PROVENANCE_REPORT.md`.

## Validation

All commands run from `/scratch/jjyeung/orch_n30/sb_rkfix2`. `cpu.sh` disables CUDA, uses nice priority 10, and caps OMP/MKL/OpenBLAS at eight threads.

- `bash scripts/cpu.sh scripts/s0.py > out/S0.log 2>&1`: COMPLETE; 18556 input files, 98 room items. S0 binds its own script.
- `bash scripts/cpu.sh scripts/reproduce.py > out/S1b.log 2>&1`: PASS; 134/134 legacy areas and 24 training-table entries reproduce.
- `bash scripts/cpu.sh scripts/summarize_s1.py > out/S1_summary.log 2>&1`: PASS; six stored CPU-forward receipts checked. Legacy K1 64-frame areas are 14.69 and 39.79 m², within 5% of 14.73 and 39.35. DRYRUN also records the frozen kernel's areas.
- `bash scripts/cpu.sh tests/test_roomkit.py > out/TESTS.log 2>&1`: 44 tests PASS; zero failures/errors. Real-data tests verify the frozen kernel against selected K1 rows; CPU stubs verify GPU-runner control flow only.
- `bash scripts/cpu.sh scripts/score_room_pricing.py --direct evidence/direct_m200_room134.json --self-test > out/SCORER_SELF_TEST.log 2>&1`: synthetic scorer checks.
- `bash scripts/cpu.sh scripts/make_go_template.py > out/GO_IDENTITY.txt`: NOT_GO with current code/settings/provenance/reader hashes.
- `bash scripts/cpu.sh out/finalize_delivery.py > out/FINALIZE.log 2>&1`: verifies 19224 distinct local evidence hashes and computes GPU_NEED estimates from review/RK_CHECK.json.
- `bash scripts/cpu.sh scripts/package.py > tmp/PACKAGE.log 2>&1`: writes out/sb_rkfix2.tar and its SHA256, and verifies every archived member against out/DELIVERY_SHA256.txt.

## Launch state

MISSING: actual approval in `configs/KERNEL_PROVENANCE.json.authorized_by` and an orchestrator-authored `configs/GO_<run_id>.json`. S1c selection is an unrun output, not an input to `--stage all`. The orchestrator's launch command after approval is:

```bash
bash scripts/s1c_gpu.sh --run-id <run_id> --go-file configs/GO_<run_id>.json --provenance configs/KERNEL_PROVENANCE.json --reader-receipt configs/READER_RECEIPT.json
```

The estimate is 0.094 GPU-hours for S1c plus 0.084 for f32 R0-dev on one 48 GB card. If K1 selects u94, its R0-dev estimate is 0.453 GPU-hours. The cumulative cap is 1.5 GPU-hours, including loads and authorized retries. The eight-thread CPU S1c fallback estimate is 11.90 hours and was not run. GPU_NEED records the timing inputs and formula.

The single K1-selected arm receives the only R0-dev comparison. T10, an additional u94 pass and Part B are forbidden. The sensor-depth label audit is proposed, unbuilt. This task used zero GPU-hours, no network, SSH, Git or process termination, and wrote only in this workspace. Real CUDA execution remains untested. No R0-dev tower prediction or one-look registration was created outside synthetic test fixtures.
