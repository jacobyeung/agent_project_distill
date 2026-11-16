# E-A GPU hand-off

```bash
bash /scratch/jjyeung/orch_cd/own_probe/out/run_EA_phase.sh 7 1
```

Run this command in the existing allocated tmux session on **trinity-1-18, physical GPU 7**, after staging. Both launchers require the card index as an argument and reject any host/card outside this assignment. `cuda:0` inside Python denotes this single visible physical card. The launcher uses vnice and one process at a time. This CPU lane launches no GPU work or transfer.

Phase 1 runs **A1, A7, A2** in that order. Each arm runs smoke, training-only calibration and extraction, then T1/T4 for standardized four taps, standardized final layer and unstandardized four taps. It prints `P0_CARD.md` and the provisional T1 choice at `$EA_ROOT/card`, then certifies the completed phase before phase 2. R2/R3 remain PENDING without teacher labels.

The shared ledger is capped at 240 minutes and stops before an unfunded stage. Phase 1 reserves **165 minutes**: A1 36, A7 75, A2 54. The 104-minute two-readout estimate does not include the required calibration sweep, third readout or doubled real-frame smoke calls. These are planning estimates; the GPU smoke records actual time and peak memory. No slow job is killed to enforce the estimate.

Defaults:

| Variable | Value |
|---|---|
| `EA_ROOT` | `/scratch/jjyeung/ownenc_EA_r3` |
| `EA_RESULTS` | `$EA_ROOT/results` |
| `EA_FEATURES` | `/dev/shm/jjyeung_probe_r3/feats` |
| `EA_WEIGHTS` | `$EA_LANE/out/WEIGHTS.gpu.json` |
| `EA_LEDGER` | `$EA_ROOT/GPU_TIME.json` |

`STAGING_INVENTORY.json` lists named inputs and exact local byte totals. Stage these three runtime environments or confirm they exist on the target:

| Environment | Bytes |
|---|---:|
| `/scratch/jjyeung/envs/sam3_capretry_native_v1` | 7,778,998,643 |
| `/scratch/jjyeung/envs/p1cpu` | 1,265,633,075 |
| `/scratch/jjyeung/orch_cd/mdg_build/work/fla/site` | 4,578,775 |

These are summed file sizes, not allocated disk blocks. The environment helper is `mdg_build/work/c1mix_mdg/scripts/mdg_env.sh`.

G3T weights are at **`/dev/shm/jjyeung_mdg_next/g3t` on trinity-2-18** (review reports 5.5 GB). Stage them at **`/dev/shm/jjyeung_evalx/g3t` on trinity-1-18**; `WEIGHTS.gpu.json` names the target. A private RAM-disk namespace can hide the source. Do not infer host-wide absence from this lane's visibility.

SAM source is `/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src`; its six files must match `sam3_tower/out/SAM3_RECEIPT.json`. A7 uses 1008×1008. Its smoke records and checks **bf16 autocast inside the actual forward on the assigned GPU**; the card prints this result.

Every provider's smoke encodes eight real training frames and their horizontal mirrors. GT instance masks are mirrored with the image. Corresponding pooled features must beat the same mask at the unflipped position. The correct correspondence must also beat ±one-patch horizontal/vertical shifts and a transposed grid. A nondiscriminating result fails the gate and blocks extraction. Provider stubs and the real-frame CPU descriptor test verify the failure behavior; they do not certify the unrun GPU providers.

Phase 2 requires `PHASE1_COMPLETE.json` and runs A3, A5, A6, A4, A8 sequentially. A5/A6 cannot extract until their real-frame provider gates pass. Missing weights create explicit skips. A8 requires completed A2/A4 shards. Run only within the same allocation and remaining ledger:

```bash
bash /scratch/jjyeung/orch_cd/own_probe/out/run_EA_phase.sh 7 2
```

All three readouts use identical fit settings. The calibration file records arm, weight metadata, resolution, training rows, moments and a checksum. T2/T3 require that file through `--feature-root`; they never refit on validation/tuning. `CHANNEL_ENERGY.json` records every arm/tap's measured before/after shares. The card prints both controls next to the primary column. Until extraction runs, real-arm energy shares are PENDING.

Bulk region shards stay in the GPU node's private `/dev/shm`, with three 1,024-channel fp16 readouts and a 2 GB cache cap. Dense maps never reach disk. Use a new result/feature directory when code or inputs change, while preserving the allocation ledger. A system-killed stage blocks reruns pending user authorization. Commands contain no retry loop.

For a single arm or later teacher-label fit, use the same allocated session:

```bash
bash out/run_EA_arm.sh 7 A1 --phases smoke,extract,T1,T4
export EA_LABELS=/scratch/jjyeung/ownenc_inputs/o5_agreement.jsonl
bash out/run_EA_arm.sh 7 A1 --phases T2,T3
bash out/run_EA_arm.sh 7 A1 --readout final --phases T2,T3
bash out/run_EA_arm.sh 7 A1 --readout unstandardized --phases T2,T3
```

The full teacher-label matrix exceeds this allocation. Obtain a separately scheduled allowance before extending it. Fusion also requires scored training proposals for that arm/readout.

Evalx stages inputs once through its authorized direct InfiniBand workflow. Return only the small metrics, logs, receipts and card to `/scratch/jjyeung/orch_cd/own_probe/inbox_gpu/` on trinity-2-18. `work/collect_gpu_results.py` archives those files and excludes weights, feature tensors and head checkpoints. `DOWNLOADS.md` records missing outside inputs and their unresolved metadata.
