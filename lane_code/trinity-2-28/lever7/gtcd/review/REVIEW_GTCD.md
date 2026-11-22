# REVIEW_GTCD: fresh review of the GTC-D kit (arm d), launch and reading gates (trinity-2-28, 2026-11-22 UTC)
Verdict: **GO.** No defect blocks the launch or the reading. The advisories below are pre-flight checks, not fixes.
I checked these myself: `sha256sum -c SHA256SUMS_GTCD` OK (61 files). Every PNG in dense/ (14,910) matches its manifest sha256. All 47 files in out/seeds_b are byte-identical (cmp) to lever6/gtcb/out. test_units passed 24/24, test_dense passed, test_launch_dry passed 12/12, and `track.py --forecast` ran. I skipped test_relift_t (780 s, over 10 min) and relied on its log, logs/test_relift_t.out, which reports 7 PASS. I computed no d value.

1. Arm d as registered: **PASS**
- Seeds: track.py:135-151 checks the copies against the pinned seeds_sha256, the lever6 originals and SHA256SUMS_GTCB. The rehearsal START event reports 47/47 bit-identical. track.py:48 sets SEED_ARM d=b, and :340-342 rechecks each seed mask's sha.
- Placement and direction: each seed goes to its anchor's dense position (track.py:343). The tracker runs forward, then backward, over all n dense frames (track.py:46, :161-181), and track.py:178-180 asserts full coverage.
- Read-out: masks are kept only at the 32 anchor positions (track.py:337, :176). gtcb's carry_masks is unchanged at track.py:184-204: the seed anchor keeps the seed mask, and score > 0 carries.
- What else differs from b: embedding runs in chunks of 32 (track.py:212-236), but K1's embed is per frame (mc_tracker.py:143-155), so the features are the same. The image is cached on the host, which matters nowhere: in the pinned SAM 3, the image reaches only _encode_new_memory, and the SimpleMaskEncoder branch ignores it (sam3_tracker_base.py:832-836). track.py:308 refuses any other encoder.
2. Dense frames: **PASS**
- I rechecked DENSE_D.json against FRAMES_GTC: 28/28 captures OK, 896/896 anchors equal their slot and served sha256, and the indices equal gtc_common.dense_indices at strides 5 and 24 (gtc_common.py:57-62). No capture has missing indices, and every decoded count equals raw_n.
- Source: the decode is the mp4's own sequential decode at the amended strides (dense.py:99-117). A mismatched capture is marked SHA_MISMATCH or SOURCE_MISSING and is never substituted (dense.py:141-148). track.py:329-332 re-asserts anchor equality against FRAMES_GTC.
- ARKit is refused without a reproducing source (dense.py:184-185), as the amendment requires.
3. Relift: **PASS**
- d goes through the same fit_lift, round_gap and official_mra loop as a, e, t, s and b, on the same items, inside dump 174135 (relift_t.py:223-242; DEPTH is gtc_common.py:31).
- a through b must equal RELIFT_GTCB.json, checked without printing (relift_t.py:354-366, :398). The test log confirms this on the real dump.
- Population: the label reads "ScanNet+ScanNet++ ... (84 items); ARKit is absent" (relift_t.py:109-120). Excluded captures are named.
- Bootstrap: the same relift Bootstrap(refs) as b, with d-b paired on the same rows (relift_t.py:302-326).
4. Reading: **PASS**
- reading_d (relift_t.py:85-99) applies the first bar first, then "<= 4 with UB < 8, or mean d-b <= 0". It flags d_no_better_than_b when the first bar holds as well. This matches the registration and the 00:58Z clarification. test_units covers the edges.
- d-b, the share of e-a, the per-dataset split (ScanNet and ScanNet++ apart) and per-anchor P/R per dataset are all reported. relift_t.py:424 prints only "complete".
- out/ holds only seeds_b: no d track and no RELIFT_GTCD.json.
5. Launch: **PASS**
- Refusals: the launcher refuses the head node, 1-13, 0-23, 0-8, 3-23, 0-18 and any non-trinity host (launch_gpu.sh:30), a root off /scratch (:31) and kit bytes that differ from the seal (:34). track.py:266 also refuses paths off /scratch.
- GPU check: two nvidia-smi readings 300 s apart, each requiring <= 100 MiB used on a card of >= 24 GB with cc >= 8 (:38-47).
- Priority: normal on 0-13, vnice elsewhere (:68-70).
- Children: each child logs its exit code to EVENTS.jsonl and its stderr to its own file (:29). A timeout or signal writes KILLED with a no-rerun note (:75).
- Rehearsal: it ran the launcher's own inner line (work/cpu_inner_20261121T234922Z.sh) and exited 0 in 3,010 s. The CPU START event shows that track.py, gtc_common.py and DENSE_D.json match the sealed sha256. At that point only relift_t.py and the tests differed (work/SHA256SUMS_GTCD.at_rehearsal).
- Forecast: 1,852 s of tracking for 28 captures, 120 seeds and 14,910 frames, plus about 356 s of host loading, against a 5,400 s timeout. GPU peak is about 14.6 GiB (bf16 features, as in mc_tracker.py:148-149); even fp32 would stay under 49 GB.
- Host memory: about 12 GiB of image cache on the largest capture, against the 60 GiB RSS guard. The CPU rehearsal peaked at 13.4 GiB RSS on 212 frames.
6. Run death or an unreadable result: **PASS**, with advisories
- A1 (advisory): track.py reads paths that lane command 2 does not ship: lever6/gtc/out/FRAMES_GTC.json (sha 957fdd3a...), sb_cachk/kit_v2, the SAM 3 root /scratch/jjyeung/b01ec87a6f29b, the checkpoint and the env. They were present on 0-13 for GTC-B, but a missing one fails at start and, under the no-rerun rule, costs an order. In the same batch as the sha check, confirm that each exists on 0-13, that FRAMES_GTC.json has that sha, and that /scratch and free RAM leave room.
- A2 (advisory): work/rehearsal_cpu/d/scannet__scene0380_01.json.gz holds real d masks for one capture, unscored. Do not relift or inspect it before the post-run review. It is already a removal candidate.
- A3 (note): test_launch_dry does not exercise the off-/scratch refusal; that check exists only in code (launch_gpu.sh:31, track.py:266).
Required fixes: none.
