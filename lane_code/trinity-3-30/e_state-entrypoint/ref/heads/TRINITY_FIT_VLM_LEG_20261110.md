# Which 9B training carries the method on Trinity this week (design lane trinity_fit_scope, 2026-11-10 05:30Z)

Status: DESIGN, read-only lane. Nothing was built or launched. FACT = measured, with its source; E = estimate with the arithmetic shown; HYP = hypothesis. GB = 10^9 B, GiB = 2^30 B; "38-42 GB usable" = 35.4-39.1 GiB.

## 1. The answer in five lines
1. **Run:** TB-1, stage B with the LM frozen, on trinity-0-18 at world 8 under vnice. It is design item 9 promoted from fallback to first choice. It fits the cards (E 30-36 GB per rank against 38-42 GB usable) and touches no ruling except the span LoRA, which the user decides.
2. **Trains:** the MDG decoder (39-43M) plus the span-gated LoRA (r32, 36.2M, active only on the `<ground obj="…">` call tokens). The LM, ViT, V-C, CPDM and G3T stay frozen, which is the clean-stages ruling's Stage 1 (perception head on a frozen VLM).
3. **Starts from:** a frozen CP1 m200, the init of E2E-0 and E2E-1, which lands on 1-18 ~07:00Z and moves to 0-18 over IB. The decoder starts from MDG-A's last or best export. The data is r7, the 9,128 ScanNet clips already in 0-18 `/dev/shm/mdg`, so the run copies nothing over NFS or the head node.
4. **Should move:** held-out placement. MDG-A's internal val reads in-mask 0.671 / 0.674 / 0.668 / 0.696 and null 0.659 / 0.687 / 0.708 / 0.738 at steps 600 / 900 / 1200 / 1500 (FACT, `mdg_build/work/runs_backup/mdga.status.txt`). On the s3i curve, ≥ 80% placement routes all 4 VSI object types (VSI-Bench macro +4 to +7, HYP), while ~0.72 routes abs distance only (+0 to +2). No record measures what the LoRA adds.
5. **Earliest launch:** Tue 11-10 ~09:30Z (01:30 PT), once MDG-A ends (~08:15Z projected), its held-out export finishes (~08:45Z), CP1 m200 is on 0-18 and the frozen-mode build is done (3-4 h from dispatch). If E2E-0 takes 0-18 first, the launch moves to ~14:00Z (06:00 PT). 5,000 steps take ~4-8 h. The m-final read follows the same day.
   - **Second run, conditional:** CP1-Rv full fine-tune on 0-18 with the trainer's built CPU-offload switch (`C1_FSDP_CPU_OFFLOAD=1`, E ~30 GiB per rank). It needs a GPU probe, user approval for a ~104 GB input copy and ~8-14 steps/h. It could start Wed; see §2c and §5.

## 2. Memory budget per rank, world 8, RTX A6000 48 GB shared (38-42 GB usable)
**Sizes from the base snapshot** (`mdg_build/work/t0rt/base/config.json`, safetensors index total 19,306,216,416 B):
- 9.65B parameters in BF16. The LM has 32 layers (24 Gated DeltaNet, 8 full attention), hidden 4096, MLP 12288, vocab 248,320, untied embeddings.
- E: LM ≈ 9.2B (embed 1.02B + lm_head 1.02B + 32 x ~214M). Vision ≈ 0.45B (27 blocks + merger).
- V-C is a trainable FP32 copy of the 27 vision blocks (~0.41B; its merger is frozen). It sits in `auxiliary_heads`, outside FSDP, and is replicated on every rank (`carrier_c1.py:39-58`, `full_ft.py:16`).

**Full-FT storage rule** (`full_ft.py:13-15, 159-185, 314-341`): once any base group trains, every base parameter is held as an FP32 master and FULL_SHARD-ed, frozen vision included. Trained parameters cost 16 B each (master 4 + grad 4 + Adam m 4 + v 4). Gradients reduce in FP32, and the trainer runs activation checkpointing on the LM.

**Measured anchors (FACT):**
- C1 pose rows: 57 GiB per rank at world 4 on Orchard (`orchard_kit/STATUS.md`). C1-a on AWS at world 8: 39.7 GiB allocated / ~46 GiB reserved (`heads_up/STATUS.md` 13:22Z 11-08).
- G1 (final mode: pose, pose, VQA, pointing, routing, with V-C depth) at world 8 on H100: peak 46 GiB (`p3_build/STATUS.md` lines 64 and 74). The record does not say whether that figure is allocated or reserved.
- MDG-A, frozen T0 m800, DDP, on these A6000s: 21 GB per rank loaded, peak 27.9 GB, 2.6-4.8 s/step (`mdg_build/STATUS.md`, LAUNCH 0338Z). Cards held 36 GB in total at launch and 31.7 GB at 05:22Z, so the other user's jobs take ~4-8 GB.
- Consistency check: 57 − 39.75 = 17.25 GiB, which matches the predicted sharded-state difference between world 4 and world 8 (34.7 − 17.4 = 17.3 GiB). The non-state part at C1 is therefore 39.75 − 17.4 ≈ 22.4 GiB. G1's 46 − 17.4 = 28.6 GiB matches 22.4 + V-C's ~6.2 GiB.

| Term (GiB per rank) | (a) TB-1 stage B, frozen LM, DDP | (b) LoRA or top-K LM, frozen rest | (c) full FT + CPU offload | (d) full FT as it is |
|---|---|---|---|---|
| Base weights | 19.6 (21 GB measured, BF16, replicated) | 19.6 replicated, or 2.5 if the frozen BF16 base is FSDP-sharded (no code path) | on CPU (FP32 masters offloaded) | 9.65B → 9.2B x 16 B + 0.45B x 4 B = 149 GB / 8 = **17.4** |
| Gradients + optimizer (trained) | decoder ~0.65 + LoRA 36.2M x 16 B = 0.54 + DDP buckets ~0.3 → **~1.5** | LoRA r32 on every LM linear ~87M x 16 B = 1.3; top-8 layers + lm_head 2.7B x 16 B / 8 = 5.0 | on CPU; ~1 for the per-unit FP32 shard and grad staging | in the 17.4 above |
