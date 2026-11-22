# REVIEW_POST: GTC-D ScanNet+ScanNet++ unit, post-run integrity review (trinity-2-28, 2026-11-22 UTC)
Verdict: **GO.** The run is the reviewed kit, the tracks are complete, and the relift ran sealed on them; nothing makes the result unreadable.
Disclosure: one of my count queries also printed RELIFT_GTCD.json's d statistics. I wrote no value here, used none, and no check below depends on one.
1. Kit and launch: **PASS**
- `sha256sum -c SHA256SUMS_GTCD` OK (61 files). The track contracts carry the sealed hashes: track.py 633cf661, gtc_common.py 0228c8dc, DENSE_D.json d5ccc6c8, SEEDS_GTCB.json 69313410, and FRAMES_GTC.json 957fdd3a (I rehashed that file here).
- The first launch (00:49Z) refused itself because no card was free in both readings (GPU 4 read 2,339 MiB) and ran nothing. The second (01:16Z) took two readings 300 s apart, with GPU 4 at 2 MiB in both, and launched on trinity-0-13 without vnice, so it ran at normal priority.
- The inner line is the reviewed one: it matches the rehearsal line (work/cpu_inner_20261121T234922Z.sh) except for the device and the capture list.
- Every child exited 0 (sha256sum, nvidia_smi_1, nvidia_smi_2, pass), and PASS_DONE reports exit 0. pass.err (766 B) holds only pkg_resources and timm deprecation warnings and one SAM 3 INFO line. END and INDEX.json report done d=28 and units d=28, with no skips, no stop and no KILLED marker; the run took 2,555 s with a 15.9 GiB peak.
2. Tracks: **PASS** (each check run over all files)
- out/track/d holds 28 files, one per capture, with no duplicates. Their capture set equals DENSE_D's 28 and SEEDS_GTCB's non-ARKit 28.
- The 120 units equal SEEDS_GTCB's units capture by capture: unit ids, seed_slot and seed_sha256_240 all match, and no unit is duplicated.
- Each file's dense_frames equals DENSE_D (count, and the digest of the frame sha256 list), and every unit tracked all dense frames forward and backward.
- Each file has 32 anchors, slots 1..32, with sha256 equal to DENSE_D's anchors. anchor_positions equal the manifest, and each seed_position equals its slot's dense position.
- Every mask array has shape 32 x GRID, with 32 scores and 32 carry flags. The mask at each seed's slot reproduces that seed's sha256, and all scores are finite.
- Every file carries the same contract, and its digest equals the relift's track_contract_digest_d (c2f3350f).
3. Relift: **PASS**
- relift_d.log reads "complete RELIFT_RC=0", and status is complete. input_sha256 lists 11 inputs, and all 11, relift_t.py (fa3f6db0, the sealed hash) included, still match their files.
- a, e, t, s and b equal RELIFT_GTCB.json (sha 4802dab9): aetsb_equal_relift_gtcb.equal is true across its 6 fields. t and s equal RELIFT_GTC.json (true), and the reproduction check gives a_e_rows_equal and relift_stats_equal true on 117 items and 46 captures.
- Arm d covers 84 items, 28 captures and 25 rooms, with n=84 overall, 24 for ScanNet and 60 for ScanNet++. The 84 equal the non-ARKit rows of the 117. population.excluded is {}, so no item or capture was dropped.
- The population label reads "ScanNet+ScanNet++ items of the 117 (84 items); ARKit is absent...", as the 23:42Z amendment requires. definitions.d_reading matches the registration and the 00:45Z clarification.
4. Readability: no blocker.
- A1: RELIFT_GTCD.json keeps no per-item d rows; d appears only in its aggregate sections. A per-item audit of d therefore needs a CPU rerun of relift_t.py.
- A2: ARKit (kit_ark) is a separate unit, which I did not review here.
