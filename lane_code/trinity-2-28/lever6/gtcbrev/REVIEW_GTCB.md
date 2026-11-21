VERDICT: GO
I reviewed the GTC-B kit (lever6/gtcb) as a fresh reviewer, read-only, on trinity-2-28 on 2026-11-21. I computed no value of b and looked at none, and no b track exists yet.

## Criteria
1. PASS. Arm b matches the registration.
   - The seed is the GT instance (gt.inst == instance) on the anchor where its 240x320 area is largest; np.argmax sends ties to the lowest anchor (seeds.py:40-43, 90-98). There is one unit per (capture, instance), as in t.
   - b carries forward and backward (track.py:35, 227). It uses the same Sam3Carry tracker, FRAMES_GTC anchors, served resize and carry rule (track.py:114-134) as arm s, which two earlier reviews passed.
   - b goes through the same fit_lift, round_gap and official_mra path as a, e, t and s, paired on the same 117 items (relift_t.py:167-187). The one unseeded operand gets zeros (relift_t.py:128-129).
   - test_real_b_seeds independently checks every operand's slot, tie rule and mask against GT. Counts: 169 units, 233/234 operands seeded, median 4,827 px, 11 seeds under 200 px.
2. PASS. The verdict applies the t bars to b-a on all 117 items, with no guard (relift_t.py:69-75, 225).
   - All registered fields are computed (relift_t.py:216-227): b-a under relift's room bootstrap; the share of e-a from the same draws; b-t (descriptive); the per-dataset split; b's per-frame precision and recall per dataset and overall; and the seed facts (median, under 200 px, by dataset) from SEEDS_GTCB.
   - The run refuses to write unless the t/s fields (rows, statistics, P/R, reading, reproduction) equal RELIFT_GTC.json. The comparison prints no values (relift_t.py:244-253, 268).
3. PASS. Nothing in the kit selects after results.
   - The b seed depends on the GT raster alone, and the bars are fixed in code.
   - relift_t refuses a b track that is incomplete, not on all 32 anchors, or written under other seeds or another contract (relift_t.py:112-124).
   - SEEDS_GTCB (16:46) predates any b track. seeds.py asserts that the rebuilt t and s seeds equal SEEDS_GTC byte for byte (seeds.py:162-167).
4. PASS. The launcher follows the rules.
   - It refuses the head node and 1-13, 0-23, 0-8, 3-23 and 0-18 (launch_gpu.sh:24). It also refuses after a KILLED marker (:25, track.py:168-169) and when the kit bytes differ from SHA256SUMS_GTCB (:26).
   - It takes two nvidia-smi readings 300 s apart, and both must show <= 100 MiB used (:28-38). It records both readings in the LAUNCH event (:39).
   - It runs under timeout 3600 (:49), at normal priority on 0-13 and under vnice elsewhere (:52-53). After a kill it writes KILLED and does not rerun (:58).
   - The copy list (REPORT_GTCB.md:19) is complete: track.py reads only the kit, SEEDS_GTCB, the seed npz files (absolute paths, identical on 0-13), gtc/out/FRAMES_GTC.json, the frame PNGs and the K1 kit. The GTC pass already read those last three on 0-13 at the same paths (gtc/out/track/EVENTS.jsonl, host trinity-0-13). FRAMES_GTC's sha is identical in SHA256SUMS_GTC and SHA256SUMS_GTCB.
5. PASS. The tests cover the cases asked for, and I reran them.
   - I reran test_units.py from the kit (it writes nothing): 19/19 PASS. The suite covers the largest-anchor and tie rules, both-direction carry through a fake tracker, and the b bar edges (>=, >, <=, < via nextafter, and None).
   - I reran test_relift_t.py from a copy that wrote only under gtcbrev/tmp: PASS in 693 s. b=GT gives e and P/R 1, t/s equal RELIFT_GTC, b=served gives a, b=t gives t, the b section has every field, and an incomplete b directory is refused.
   - I reran test_launch_dry.sh from the same copy: PASS.
   - sha256sum -c SHA256SUMS_GTCB passes: all 59 entries are OK.
   - track.py --forecast gives 200.8 s.

## Blocking defects
None.

## Non-blocking notes
- N1. REPORT_GTCB.md:27 says SHA256SUMS_GTCB covers 58 files and excludes the report. It has 59 entries, and kit/REPORT_GTCB.md is among them. Any edit to the report before the launch therefore makes launch_gpu.sh refuse, which is safe but surprising. Fix the line, or re-seal after the edit.
- N2. b's precision and recall include the seed frame, which is exact by construction, and count an operand once per item. This is the same convention as t. State it beside the P/R numbers in the RESULT.
- N3. The seed facts count units (169), not operands, as the t facts in GTC did. items_all_seeds_200 = 98 is a seed fact, not a registered subset, and nothing reads it.
- N4. The b test (relift_t.py:115) checks only seeds_sha256 in the track contract, as in GTC (earlier note N3). The risk is low because the seed masks are sha-checked in track.py:230.
- N5. The report names no method for bringing gtcb/out/track (about 1 MB) back to 2-28 (REPORT_GTCB.md:21). Use one tar over .ib, or a single small file under 20 MB, per LANE_RULES.
