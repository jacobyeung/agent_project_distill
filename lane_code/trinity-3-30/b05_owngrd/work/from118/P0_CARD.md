# E-A frozen-feature probe decision

Status: PENDING_GPU_OR_INPUTS.
Keys: None. Add G3T: False.
T1 has no eligible own selection baseline yet.
Mask keys: A7 (SAM 3 tower).
Pending rules: .

| Arm | R1 | R1+ | R2 | R3 | R4 | Input/status |
|---|---|---|---|---|---|---|
| A1 | PENDING | PENDING | PENDING | PENDING | PENDING | Local inputs present; GPU smoke pending |
| A7 | PENDING | PENDING | PENDING | PENDING | PENDING | Local inputs present; GPU smoke pending |
| A2 | PENDING | PENDING | PENDING | PENDING | PENDING | Local inputs present; GPU smoke pending |
| A3 | PENDING | PENDING | PENDING | PENDING | PENDING | Local inputs present; GPU smoke pending |
| A5 | PENDING | PENDING | PENDING | PENDING | PENDING | /scratch/jjyeung/ownenc_inputs/cradio_v4_so400m; LOCAL_PIN.json for cradio_v4_so400m |
| A6 | PENDING | PENDING | PENDING | PENDING | PENDING | /scratch/jjyeung/ownenc_inputs/dinov3_vitl16; LOCAL_PIN.json for dinov3_vitl16 |
| A4 | PENDING | PENDING | PENDING | PENDING | PENDING | /dev/shm/jjyeung_mdg_next/g3t/model.safetensors |
| A8 | PENDING | PENDING | PENDING | PENDING | PENDING | /dev/shm/jjyeung_mdg_next/g3t/model.safetensors |

| Arm | Task | Metric | Standardized four taps [95% CI] | Standardized final layer [95% CI] | Unstandardized four taps [95% CI] |
|---|---|---|---|---|---|
| A1 | T1–T4 | All measurements | Pending | Pending | Pending |
| A7 | T1–T4 | All measurements | Pending | Pending | Pending |
| A2 | T1–T4 | All measurements | Pending | Pending | Pending |
| A3 | T1–T4 | All measurements | Pending | Pending | Pending |
| A5 | T1–T4 | All measurements | Pending | Pending | Pending |
| A6 | T1–T4 | All measurements | Pending | Pending | Pending |
| A4 | T1–T4 | All measurements | Pending | Pending | Pending |
| A8 | T1–T4 | All measurements | Pending | Pending | Pending |

| Paired T1 difference | Points [95% CI] |
|---|---|

| Arm minus A7 (R1) | Points [95% CI] |
|---|---|
| A1 | PENDING |
| A7 | PENDING |
| A2 | PENDING |
| A3 | PENDING |
| A5 | PENDING |
| A6 | PENDING |
| A4 | PENDING |
| A8 | PENDING |

Paired mask-only differences: `{}`.

| Arm | Tap | Split | Native before | Native after | Head before | Head after |
|---|---|---|---|---|---|---|
| A1 | 1 | All | PENDING | PENDING | PENDING | PENDING |
| A1 | 2 | All | PENDING | PENDING | PENDING | PENDING |
| A1 | 3 | All | PENDING | PENDING | PENDING | PENDING |
| A1 | 4 | All | PENDING | PENDING | PENDING | PENDING |
| A7 | 1 | All | PENDING | PENDING | PENDING | PENDING |
| A7 | 2 | All | PENDING | PENDING | PENDING | PENDING |
| A7 | 3 | All | PENDING | PENDING | PENDING | PENDING |
| A7 | 4 | All | PENDING | PENDING | PENDING | PENDING |
| A2 | 1 | All | PENDING | PENDING | PENDING | PENDING |
| A2 | 2 | All | PENDING | PENDING | PENDING | PENDING |
| A2 | 3 | All | PENDING | PENDING | PENDING | PENDING |
| A2 | 4 | All | PENDING | PENDING | PENDING | PENDING |
| A3 | 1 | All | PENDING | PENDING | PENDING | PENDING |
| A3 | 2 | All | PENDING | PENDING | PENDING | PENDING |
| A3 | 3 | All | PENDING | PENDING | PENDING | PENDING |
| A3 | 4 | All | PENDING | PENDING | PENDING | PENDING |
| A5 | 1 | All | PENDING | PENDING | PENDING | PENDING |
| A5 | 2 | All | PENDING | PENDING | PENDING | PENDING |
| A5 | 3 | All | PENDING | PENDING | PENDING | PENDING |
| A5 | 4 | All | PENDING | PENDING | PENDING | PENDING |
| A6 | 1 | All | PENDING | PENDING | PENDING | PENDING |
| A6 | 2 | All | PENDING | PENDING | PENDING | PENDING |
| A6 | 3 | All | PENDING | PENDING | PENDING | PENDING |
| A6 | 4 | All | PENDING | PENDING | PENDING | PENDING |
| A4 | 1 | All | PENDING | PENDING | PENDING | PENDING |
| A4 | 2 | All | PENDING | PENDING | PENDING | PENDING |
| A4 | 3 | All | PENDING | PENDING | PENDING | PENDING |
| A4 | 4 | All | PENDING | PENDING | PENDING | PENDING |
| A8 | 1 | All | PENDING | PENDING | PENDING | PENDING |
| A8 | 2 | All | PENDING | PENDING | PENDING | PENDING |
| A8 | 3 | All | PENDING | PENDING | PENDING | PENDING |
| A8 | 4 | All | PENDING | PENDING | PENDING | PENDING |

Energy shares are token-weighted means of the largest channel share after per-token LN, before/after training-only standardization.
SAM 3 bf16 autocast: PENDING.

All shares use [0,1] in JSON. Intervals use 4,000 paired room-cluster draws, preserving every object, seed 17.
No clean-33 data enters this probe. Missing metrics leave their rules pending.
Per-arm metrics, intervals, sample counts and routed diagnostics are stored in P0_CARD.json.
