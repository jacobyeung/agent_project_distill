# REVIEW_POST_ARK: GTC-D ARKit unit after the run (fresh, trinity-2-28, 2026-11-22; read-only; no d value printed or computed)
## Verdict: GO. RELIFT_GTCD_ARK.json may be read under the registered rule. The pooled 117 items decide.
1. Run = reviewed kit: PASS.
   - SHA256SUMS_GTCD_ARK (64 files, f7b7a5a4...) and SHA256SUMS_GTCD both check (rerun now), and dense_ark/DENSE_D_ARK.json matches its .sha256 (8ad7d0b1...).
   - kit_ark mtimes stop at 20:05, so nothing changed after REVIEW_ARK2. The track.py, gtc_common.py and K1 hashes in INDEX.json equal the sealed files.
   - The launch log shows two readings 300 s apart (02:42Z, 02:47Z) on which card 4 had 2 MiB used, cc 8.9 and 49140 MiB, and the launcher picked gpu=4.
     Every event reports host=trinity-0-13. The vnice line is absent, so the pass ran at normal priority (launch_gpu.sh:98-99).
   - The inner line is the absolute form REVIEW_ARK2 F1 required: track.py --device cuda --arms d --out .../out_ark/track --hard-stop 5280 --captures all --dense .../DENSE_D_ARK.json.
   - All five children exited 0 (dense_sha256, sha256sum, nvidia_smi_1/2, pass). PASS_DONE exit=0 at 03:14:29Z.
     pass.err (766 B) holds only pkg_resources, timm and INFO lines. pass log: no error or traceback. INDEX: stopped=null, skipped=[].
2. Tracks: PASS (independent check of all 18 files).
   - There are 18 files in d/, one per ARKit capture, equal to the 18 OK captures of DENSE_D_ARK.json and the 18 ARKit captures of SEEDS_GTCB.
   - The files hold 49 b units, each unit set equal to SEEDS_GTCB, no duplicates. Seed sha256 and slots match, skipped_units=[].
   - Every file's contract equals INDEX's: dense, seeds and FRAMES_GTC sha256 all equal the files on disk.
   - Per file, dense_frames equals the manifest count (12,551 total) and dense_frames_sha256 equals the digest of the manifest's frame sha256.
     Anchor slots run 1..32 with served sha256 equal to FRAMES_GTC and anchor positions equal to the manifest. Every mask is (32,240,320), both directions, and the bit lengths are consistent.
3. Relift: PASS. status=complete. The log reads "scannet_scannetpp complete, arkit complete; pooled read", RELIFT_RC=0.
   - All 12 input_sha256 entries equal the current files, among them the sealed kit_ark/relift_t.py and both dense manifests. tracks_d names out/track and out_ark/track.
     Each track_contract_digest_d equals the digest of its INDEX contract.
   - a..b equal RELIFT_GTCB.json: the file's flag is true, and my own gtcb_view comparison is equal on rows, statistics, P/R, reading, reproduction and b. ts_equal_relift_gtc is true.
   - Counts: ScanNet+ScanNet++ 84 items/28 captures, ARKit 33/18, pooled 117/46. All three are status "read" and labelled, with excluded={} in every population and unit.
   - The ScanNet population equals RELIFT_GTCD.json: equals_relift_gtcd=true, and statistics, P/R, reading, items, captures, rooms and the 84 rows' d cells are equal.
     Only population.label text and one schema key (items vs datasets) differ. Population captures and excluded are equal.
   - No item or capture was dropped: 117 row ids equal RELIFT_GTCD's, and the 33 ARKit rows cover exactly the 18 track captures.
4. Readability: nothing blocks. Note: registration estimated ARKit at 12,259 frames, and the run used 12,551. REVIEW_ARK2 verified stride 2 with every anchor included, so the estimate was only approximate.
   - I did not check whether a mirror copy of out_ark/track exists, or the copy-back hash (all 18 gz files parse and pass every check above).
