VERDICT: GO
Second fresh review of the GTC kit (lever6/gtc), done read-only on trinity-2-28 on 2026-11-21. I computed no cell, score or difference and looked at none. I did not open out/track.

## Criteria
1. PASS. The arms match ruling item A.
   - t seeds the bound GT instance on its first anchor with at least 1 px (seeds.py:63-72) and carries it forward only (track.py:224).
   - s follows K1's S_A0 rule: the served mask on lift_plain's best frame (seeds.py:29-37, grounding.py:111 = mc_seeds.py:43-44). It carries forward and backward.
   - a and e go through relift.fit_lift inside dump 174135, and their rows and stats must equal a fresh relift.run (relift_t.py:176-185).
   - relift.py is unchanged: its sha bbc97331 equals the one recorded in SEEDS_GTC, and the file predates REVIEW_X. All 69 input_sha256 entries of the banked RELIFT_X.json match the current files.
   - All arms are paired on the same 117 items and 46 captures.
2. PASS. Frames and seeds (15:02-15:03) were fixed by rule before any track output existed. The subset rule depends on SEEDS_GTC alone. The bars and the guard follow the plan's conventions (plan:50, 224-229). Every interval uses relift's Bootstrap: 10,000 draws, seed 20261120, physical room, item weighting (round7_common.py:41-66).
3. PASS. relift_t.py:186-202 computes everything as registered: t-a, s-a and e-a under the room bootstrap; the share (t-a)/(e-a); per-frame P/R (frames where GT or prediction is non-empty) for ARKit, ScanNet/ScanNet++ and all; and the >= 200 px subset.
4. PASS.
   - Every arm reaches fit_lift as a (32,240,320) array (relift_t.py:160-163).
   - Anchor order is checked against FRAMES_GTC slots 1..32 (track.py:216-218).
   - The resize is 240->480 by the served resize, then [::2,::2]. The round trip is exact for all 334 seeds (test_mask_resize, SEEDS summary).
   - The carry rule (track.py:110-130) equals K1's mc_track_io.object_record:25-42: the seed anchor keeps the seed, and another anchor carries where its score is > 0.
5. PASS.
   - frames.py:30-39 reproduces the binding hash. 1,472 PNGs (396,791,330 B) are on /scratch with 0 missing, so no stream is needed.
   - launch_gpu.sh is unchanged. It takes two readings 300 s apart (:27-29), runs under vnice off 0-13 (:51-52) with timeout 3600 (:48), refuses after a KILLED marker (:24, track.py:165) and writes to /scratch only (track.py:161).
6. PASS.
   - SHA256SUMS_GTC verifies all 58 files.
   - I reran both test files as copies that write only under gtcrev2/tmp. test_units.py passes 14/14.
   - test_relift_t.py passes in 611 s: t==e, t==a, s==a, s==e, the subset count from compute() equals SEEDS_GTC's (58), the reading field matches reading(), and an incomplete track directory is refused.
   - test_launch_dry.sh was not rerun, because it writes under gtc/work. The launcher is byte-identical to the version the first review passed.
7. PASS.
   - Membership (relift_t.py:31-38, 168-169) follows the plan's rule exactly: every operand needs t status OK and area_240 >= 200, and a NOT_VISIBLE operand excludes its item. compute() cross-checks membership against SEEDS_GTC (:196-197).
   - Population counts agree with the registration: 58 of 117 items; 45 of 169 seeds under 200 px; smallest seed 1 px; 233 of 234 operands seeded.
   - The subset's n, rooms and t-a are reported per dataset and overall in every case (:193-195).
   - reading() (:51-64) applies the registration exactly:
     - The first bar is judged on all 117 items.
     - The guard changes 'not the source' to 'undecided' only when the subset shows >= 8 with lower bound > 0.
     - Results that clear neither bar read as undecided.
     - s-a is tested against the first bar when that bar holds.
   - Tests cover all four branches, the empty-subset case, and each bar edge (>=, >, <=, <) through nextafter.
   - The pre-fix to post-fix diff of SHA256SUMS_GTC changes only relift_t.py, test_units.py and test_relift_t.py. track.py, seeds.py, gtc_common.py, frames.py and launch_gpu.sh keep their hashes. relift_t.py.before_fix hashes to the pre-fix value (949759b6), and the diff only adds code.

## Blocking defects
None.

## Non-blocking notes
- N1. The registration now discloses the s seed (240 enlarged to 480) and the 32-anchor carry.
- N2 (open). launch_gpu.sh:23 accepts any trinity-* host. The ruling forbids 1-13, 0-23, 0-8, 3-23 and 0-18, so an allowlist of trinity-2-28 and trinity-0-13 is safer. The cluster-page check is manual.
- N3 (open). relift_t.py:103 checks only seeds_sha256. Also check the contract's frames_sha256 against the current FRAMES_GTC.json.
- N4 (open). The run does not assert equality with the banked RELIFT_X.json. The inputs and relift.py are unchanged, and the first review asserted equality, so the risk is low.
- N5. P/R includes the t seed frame, which is exact by construction, and counts each operand once per item. This matches the registration's wording. State it in the report, or add a variant without the seed frame.
- N6. kit/REPORT_GTC.md (not in SHA256SUMS_GTC) still says test_units has 11 tests and does not mention seed200 or the reading field. gtc/REGISTRATION.md lacks the membership sentence that the plan record now carries. The plan record is authoritative.
- Discrepancy in the brief: the Output section names REVIEW_GTC.md, but the Rules section allows only REVIEW_GTC2.md. I wrote REVIEW_GTC2.md.
- All 8 cards on trinity-2-28 read about 35 GB used at 16:12 local. The launcher would refuse here now, which is correct behaviour.
