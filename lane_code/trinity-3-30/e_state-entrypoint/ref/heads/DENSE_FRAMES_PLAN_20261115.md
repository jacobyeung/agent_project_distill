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
