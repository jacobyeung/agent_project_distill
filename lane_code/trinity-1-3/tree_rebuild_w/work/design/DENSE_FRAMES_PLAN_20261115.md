# Dense frames for GF-1: demand, supply and plan (design record, 2026-11-15)

**Question.** Which training clips need dense (64- or 96-frame) native samples for GF-1, what dense material already exists, what is the cheapest legal way to close the gap, and should a leg without fusion launch first?

**Answer.**
- The gap is ARKitScenes, not ScanNet or ScanNet++.
- Every in-map ScanNet and ScanNet++ clip can form a nested 64- or 96-frame sample from frames the k6 store already holds. Of 994 clips, 993 need no new decode, and one clip needs 1 frame (64) or 5 frames (96).
- ARKitScenes needs 43,008 new frames at 64 (about 12.5 GB PNG) or 86,016 at 96 (about 25.0 GB). Their only matching source is Apple's raw `lowres_wide.zip`, read by HTTP range requests: about 3.0 or 6.0 GB.
- The cheapest route builds the frames on Orchard, where the leg trains and where the k6 replica lives. It sends nothing through Trinity's head node or NFS beyond a manifest of a few tens of MB.
- GF-1 also needs dense frames for the 18,547 pose rows. No local record gives their clip windows, so that cost is unknown. It is the largest open item.
- Recommendation: launch the no-fusion leg as soon as its own gates (F1–F4 and the CPU gate) clear, and build the dense material meanwhile. The GF-1 card requires a no-fusion control on the same checkpoint and mix in any case.

## 1. Demand

GF-1 encodes every video row with dense frames (`carrier_c1_data.encode_layout_row(..., gf1=...)`, `GF1.patch:310-369`), and that includes pose rows. Pose rows pass their per-row jitter to the dense frames too. A row without a valid dense sample stops every rank (`PRELAUNCH_CARD.md`). Every row in the four streams therefore needs a dense sample.

Each scene alias has exactly one 32-index student set across all streams, so one dense clip serves all of a scene's rows. My scripts measured this: `work/demand.py`, `work/streams.py`, `work/streams2.py` → `out/DEMAND_ROWS_R2.json`, `out/DEMAND_STREAMS.json`. The student indices span the whole recording, so the median span equals `total_num_frames`.

| Corpus | Rows (rows_r2 + sealed routing + pointing) | Distinct clips | In k6 map | 64-frame dense frames | 96-frame dense frames |
|---|---:|---:|---:|---:|---:|
| d1 ScanNet | 53,012 + 19,628 + 9,216 | 795 (736 + 59 routing-only) | 396 | 50,880 | 76,320 |
| d2 ScanNet++ | 116,921 + 31,723 + 11,652 | 844 | 657 | 54,016 | 81,024 |
| d3 ARKitScenes | 53,128 + 5,785 + 0 | 1,409 | 1,409 | 90,176 | 135,264 |
| **Video clips total** | 301,065 row records | **3,048** | 2,462 | **195,072** | **292,608** |
| pose (A2, d1/d2, `/data2/k7pd`) | 18,547 retained | unknown (≤18,547) | not in k6 | unknown | unknown |

- Bytes at the recorded k6 averages (253,597 B per ScanNet/ScanNet++ PNG and 290,419 B per ARKit PNG): the full in-map dense set is 43.3 GB at 64 frames and 64.9 GB at 96, student frames included.
- Off-map clips: 586 ScanNet/ScanNet++ aliases (399 d1 and 187 d2) occur only in the `units` family, 1,172 rows in all. They are absent from the k6 map, and the map lacks even their 32 student frames. A full dense set for them would be 37,504 or 56,256 frames (9.5 or 14.3 GB), decoded from the VSI-590K release mp4s.
- Routing camera rows pin `/data2/kr9c` paths. Their frames match the k6 hashes in 1,132,777 of 1,133,536 references (`work/kr9c.log`). Dense pins must keep each row's own path; the native `r1_dense` already does this. The 759 mismatched references need a per-scene check.
- Evaluation also needs a 64-frame dense sample for every benchmark item (`EVAL_DENSE_SPEC.md`). The benchmark mp4s are on Trinity `/data2` (`DATA_MAP.md:98-104`). This plan does not price them.

## 2. Supply

| Material | Where | Size | What it covers |
|---|---|---|---|
| k6 pinned map `p1c_build/k6/MAP.jsonl.gz` | metadata on 2-18 | 290,880 frames, 78.3 GB in 12 shards | d1: 562 scenes, median 133 frames each. d2: 684 scenes, median 136. d3: 3,451 scenes, median **32**, and only 131 with ≥64 |
| k6 store bytes | Orchard `/project/community/jjyeung/cp4tk_fr/k6tk` (recorded 2026-11-13, not checked); code-aws `data2root/k6tk`; GCS shard parts | 78.3 GB | **Absent on Trinity** (`K1_LAUNCH_PACKET.md` §1) |
| k6 extras usable as dense frames | the same stores | 31,807 frames (8.1 GB) at 64; 63,611 (16.1 GB) at 96 | 993 of 994 in-map d1/d2 clips complete from the map (`out/NEW_FRAMES.json`) |
| ScanNet/ScanNet++ VSI-590K release mp4 | Trinity `/data2` (K1 rebuilt 12 of 12 sampled pins byte-identical with `wd.py`); code-aws `s4_media/src_d1` (1,513 mp4, 27.7 GB) and `src_d2` (856 mp4, 21.4 GB); HF `nyu-visionx/VSI-590K` | ~49 GB total | All d1/d2 scenes, including the 586 off-map aliases. Orchard copy unknown |
| ARKit Apple raw `lowres_wide.zip` | internet only (Apple) | ≈70 KB per member by range read | The only source that matches the k6 d3 pins (`wa.py` rule). Parity is unproven until K1's `FRAME_PARITY.json` |
| ARKit `/data3/.../3dod/Training/*/lowres_wide` | Trinity NFS | 2,899 captures | Rebuilt PNGs **do not match** the k6 pins (3 of 3). Not a source |
| ARKit VSI-590K release mp4 | Trinity `/data3/.../VSI-590K/arkitscenes.tar.gz` (90 GB); code-aws `s4_media/src_d3` | 90 GB | A re-encode, so it cannot nest with the k6 student pins. Not a source |
| `frames64` (k3f8), 64/127-frame grids | code-aws `data2root/k3f8`; 3-30 store lost to TTL; `frames64_noFH.tar` on 3-3 | 20.7 GB | Different hashes from the k6 pins (K1 found no overlap for its 138 scenes) |
| pose frames k7pd | code-aws `ap/f02f16ad/f/k.tar` (27.8 GB, 113,856 PNG from VSI mp4s); Orchard staging assumed, because the leg trained on it | | Pose clip windows are not recorded locally |

The training cluster is Orchard. The leg ran there (job 169097, 4 ranks, 131 s/step; `CONTINUATION_FACTS_20261114.md`), and the step-544 export and k6 replica are recorded there. The kit's `/scratch/fsw` and `/lustre/fsw` paths are logical staging roots. Separately, code-aws access is recorded to end on 2026-11-19 (`DATA_MAP.md:133`, as of 2026-11-02).

## 3. Options, priced

These are estimates unless marked measured. Trinity shared links means the head node plus nebby.

| Option | Trinity shared-link bytes | CPU | GPU | Wall clock | Must build | Unproven |
|---|---|---|---|---|---|---|
| **(a) Build on Orchard** from the k6 replica plus Apple range reads | ≈0. Only the manifest and builder kit (<0.2 GB) | ~43k–86k ARKit decodes at ~20 ms each, under 1 CPU-h (guess) | 0 | ~1 day, mostly building and testing the manifest | Dense manifest builder (select k6 extras, nested, deterministic); fetch plan for 1,409 d3 captures (extend K1's `D3_FETCH_PLAN`); metadata-only pre-pass (review F5) | Orchard has HTTP egress to Apple; the replica holds all 290,880 members; d3 parity |
| (b) Build on Trinity and ship | Apple in through the head node 3.0 or 6.0 GB, plus d3 PNG out 12.5 or 25.0 GB. Total **15.5–31 GB**; the 96-frame case needs an administrator | same as (a) | 0 | +1–2 h of throttled transfer at 8 MB/s after the build | same as (a), plus shipping archives | Head-node congestion tonight. d1/d2 extras still depend on the Orchard replica, because Trinity has no k6 bytes |
| (c) Run the tower offline and cache the pooled bank | as (a) or (b) for the frames | small | dense pass once per clip: 3,048 clips at ~1–3 s each ≈ **1–3 GPU-h at 64 frames** (guess), about 2× at 96 | +0.5 day for the code change | A `cached_bank` input to `Fusion.pooled_bank`; a cache writer; a parity test against the online path | Equality holds up to rounding (bf16 projection before pooling online, versus pooled-normalised fp32 then projection). Pose rows cannot use it (see below) |
| (d) Staged: fusion on d1/d2 only, d3 later | ≈0 for d1/d2 | 0 | 0 | soonest for the frames themselves | Per-row GF-1 optionality, which the code refuses today (one bad row stops all ranks) | It confounds the A/B: ARKit is about 20% of video rows and has its own task mix. Pose rows are still needed |

**Can GF-1 consume cached tower outputs?** Yes, for every non-pose row, and exactly in algebra.
- The connector computes `area_pool(proj(norm(x)))` (`gf1.py`, `pooled_bank`). Area pooling is linear, with weights that sum to 1 for an ROI inside [0, 1024]. LayerNorm's affine part and the projection are linear and shared across tokens.
- Hence `pool(W(γ⊙n̂+β)+b) = W(γ⊙pool(n̂)+β)+b`, where n̂ is the per-token normalised feature with no learned parameters. Caching `pool(n̂)` per layer, anchor frame and merger cell keeps every trainable parameter live. The top-2 router and the `lm_012` injection also work unchanged, because both act after pooling.
- Storage: 3 layers × 32 frames × ~130 cells × 2048 channels × 2 B ≈ 51 MB per clip, or **≈156 GB for 3,048 clips**. The 130-cell grid is a guess from the spec's 10×13 check; the real merger grid sets the true size. Caching full token banks instead would take about 1.6 TB.
- Layer ablations (12–23) add about 17 MB per clip per extra layer.
- Pose rows apply a per-row augmentation to the dense frames, so their tower input differs per row, and they must run the tower online.
- The camera pass on the 32 student-unpatchified frames is also frozen and deterministic for non-augmented rows, so the same method could cache it.
- Fidelity holds because the tower still reconstructs from the dense 64 or 96 frames and then subsamples to the 32 anchors, which is the user's rule.

**Online tower cost without the cache (guess):**
- About 1×10^15 FLOPs per 64-frame dense pass, roughly 2.5 s on an H100.
- At 72 rows per rank per step, that adds about 180 s to the 131 s step, giving about 310 s per step.
- A 1,000-step leg grows from about 146 to about 345 GPU-h.
- With the cache, only the pose rows run online (16 per rank per step, about +40 s), giving about 171 s per step and about 190 GPU-h. Nobody has measured either figure (`PRELAUNCH_CARD.md`: runtime and peak are unmeasured).

**Soonest first fusion step:** (a) with the online tower. It needs only the manifest builder and the d3 fetch, with no model-code change. **Cheapest in shared-link bytes:** (a), with zero Trinity bytes. **Cheapest in GPU-h over the leg:** (a) plus (c).

## 4. Recommendation on sequencing

Launch the no-fusion leg first, on the existing 32-frame stores, once F1–F4 and the CPU gate clear. Build the dense material meanwhile with (a), add (c) for the non-pose streams, and start GF-1 Stage 1 from the same inherited checkpoint when the material passes its gates.

| Choice | GPU-h | Calendar |
|---|---|---|
| No-fusion leg now, GF-1 after | ~146 GPU-h for 1,000 steps (4 × H100, 131 s/step measured), then GF-1 at ~190 GPU-h (cached) or ~345 (online), estimates | Control finishes ~1.5 days after launch (two 24 h allocations). GF-1 can start ~1–2 days after launch, when the dense build and its GPU calibration finish |
| Wait and launch once with fusion | the same GF-1 GPU-h, and the card's comparison still needs a no-fusion arm (~146 GPU-h) | GPUs sit idle for the ~1–2-day dense build and the GF-1 gates |

The card asks for the same checkpoint, mix and membership "with and without GF-1". The no-fusion leg is therefore that comparison's control, so running it first does not waste any GPU-h.

**The fact that would flip this:** if only one leg's allocation is available before the next deadline, launch once with fusion and compare against the existing step-544 checkpoint instead. A dense build plus GF-1 GPU gates that close before the no-fusion leg's own gates would flip it the same way. Code-aws access ending on 2026-11-19 does not flip it, because training runs on Orchard.

## 5. Options rejected

- Decoding d3 from `/data3` 3DOD PNGs or the VSI ARKit mp4: their hashes and pixels differ from the k6 student pins, and nesting would fail or mix sources.
- Using `frames64`/k3f8 grids: their hashes differ from the student pins.
- Building on code-aws: the store and mp4s exist there, but access is recorded to end on 2026-11-19, training runs on Orchard, and the naming rules make an ARKit fetch plan there awkward.
- Duplicating sparse frames: the spec forbids it.
- Caching full token banks: about 1.6 TB.

## 6. What might not work, and the tests that settle it

1. **Orchard k6 replica completeness.** Count the members of `cp4tk_fr/k6tk` against `MAP.jsonl.gz` (290,880 hashes), and do the same for `kr9c`. If extras are missing, d1/d2 need 8–16 GB from the code-aws or GCS shards.
2. **d3 parity.** K1's `FRAME_PARITY.json` on its 5,504 pinned d3 frames must match byte for byte. If it fails, the extra frames still come from Apple raw, but their equality with the student frames must then be argued from pixels.
3. **Orchard egress to Apple.** Run one ranged GET of one `lowres_wide.zip` central directory from an Orchard node.
4. **Pose clips.** Stream `a2v3/rows.sqlite` where it lives. For each of the 18,547 retained rows, check whether a nested 64 or 96 exists within the scene's 127 posed ordinals and k7pd, and count the new decodes from the VSI mp4s. Until that count exists, the pose cost is unknown.
5. **Cache parity (c).** On one real row, compare the GF-1 output from the cached `pool(n̂)` against the online path in the trainer's dtype, to a stated tolerance, before any cached run.
6. **Manifest pre-pass.** Run `select_clip`, `nested_indices` and the seal on every row before any RGB read (review F5). It must report 0 refusals, or defer the 586 off-map `units` clips and the 759 kr9c-mismatch references with stated reasons.
7. **Online tower cost.** One H100 step with GF-1 on a real batch measures the 2.5 s per row guess and the memory peak.

## 7. Status

Inventory and plan only. Nothing was copied, launched or edited outside this lane. Scripts: `work/demand.py`, `join.py`, `gap.py`, `streams.py`, `streams2.py`, `kr9c.py`, `newframes.py`. Outputs: `out/DEMAND_ROWS_R2.json`, `SUPPLY_JOIN.json`, `GAP_COVERAGE.json`, `DEMAND_STREAMS.json`, `NEW_FRAMES.json`, `CLIPS_DEMAND.jsonl.gz`. The pose stream, the Orchard replica's contents and every GPU figure remain unmeasured.
