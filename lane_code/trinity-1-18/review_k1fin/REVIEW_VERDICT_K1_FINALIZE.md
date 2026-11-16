# Review verdict: K1 finalize (finalize_k1.py 800d0f52, output manifest c3bbc378)

Reviewer: lane review_k1fin on trinity-1-18. Read-only on the builder's files. Scripts and outputs: /scratch/jjyeung/orch_n30/review_k1fin/ (diff_manifest.py, gates.py, GATES_OUTPUT.txt, probe.py, timing.py, phases.py, kitpins.py, ident.py).

## Verdict: GO for tower_sam
No finding blocks tower_sam. Findings 1 to 3 below should be fixed before the next kit, but none of them can let K1 run on frames other than the pinned ones. The reason is that the kit itself rehashes every dense frame against the manifest pins at each launch (run_k1.sh, then k1_pipeline cache, then check_manifest, then B.checked).

## 1. What check_manifest requires (kit k1_pipeline.py lines 19-40, bindings.py lines 27-31)
- All phases:
  - Both flags must be true.
  - unresolved_dense_sources and unresolved_gt_names must be empty.
  - The inventory pin and pilot_complete must hold, the capture set must equal the exact pilot set, and each capture's eligibility, room and k1_split must match.
  - P.validate_capture must pass, split must be train, and gt_name_ids_authority must be present.
- tower_sam:
  - B.checked must pass on all 64 dense frames of every capture. B.checked refuses /home and /data paths and requires the file's sha256 to equal the pin.
  - B.checked must also pass on tower_weights, tower_config, sam_checkpoint and sam_receipt.
  - Timing is not required.
- own:
  - fps, timestamps and total_num_frames must be non-null in every capture.
  - B.checked must pass on the 32 anchor frames, and on artifact, config and data_receipt.
- What the flags attest (finalize.py line 60, operator step 1): dense RGB is staged on the node, the production manifest is complete and hashed, sparse anchors were not substituted, and the empty unresolved lists reflect real input closure. The flags are gating only: the code does not tie them to any receipt.

## 2. Diff, staged ada4797e against finalized c3bbc378
- Changed fields:
  - The two flags (false to true).
  - k1_finalize was added.
  - fps, timestamps and total_num_frames changed in exactly 138 captures (51 ScanNet, 87 ScanNet++).
- Nothing else changed. dense_frames, anchors, gpu, inputs, pending, inventory and k1a_frame_parity are byte-equal.
- FINDING 3 (minor): finalize_k1.py line 244 adds a field, `timing_source`, to all 300 captures. This field is outside the allowed set. It changes B.digest(c), the cache key, which is harmless before the first cache exists.
- Re-running finalize() reproduces c3bbc378 byte for byte.
- All 19,200 staged frame pins match the base pins (14,304) or the PARITY_FINAL new frames (4,896), each with its canonical store path, and all 300 captures have consistent anchors. I checked this in JSON only.

## 3. Gate breaking: 35 mutated copies (GATES_OUTPUT.txt)
Every mutation of the six gates set both flags false and named the right failed gate:
- verify_mp4: bad non-empty, checked 137, summary line missing, conflicting second line, file missing.
- WD and WA: row dropped, duplicate row, error set, misses non-empty, wrong token, file missing.
- PARITY: n_failures 1, pass_ false, a failures row, a wrong new-frame sha, an extra key (digest mismatch), a row dropped, file missing.
- SUBSTITUTIONS: row dropped, wrong sha, ordinal dropped, wrong index, wrong kind, file missing.
- ACCEPT: bad non-empty, pinned_ok 14303, anchors_ok 299, file missing.
- A token map missing a selected capture also refuses. My first token test, tok_dropcanon, removed an unselected canonical; that was a test error.

FINDING 1, a gate that fails to refuse:
- The gate: the substitution gate (finalize_k1.py lines 170-186). It compares each row's [index, sha] with the manifest pin and never opens a store file. The probe recorded 0 file accesses under /scratch/jjyeung/k1_frames during finalize.
- The failing input: a substitution row whose PNG does not hash to its pin passes finalize.
- What catches it instead: accept_manifest.py, which hashes every store file, and check_manifest at launch.

FINDING 2: finalize trusts receipt contents without binding them to this manifest (lines 128-192):
- ACCEPT_MANIFEST.json and WD_OUT/WA_OUT name no manifest sha, and none of their frame shas are compared with the manifest.
- PARITY is the only receipt bound to the manifest, through the k1a_frame_parity digest.
- Fix for the next kit: hash every substituted store file in the substitution gate, and record the input manifest sha inside ACCEPT_MANIFEST.

## 4. Timing
- I ran the closed-form check over all 300 captures:
  - Each ScanNet and ScanNet++ capture has fps equal to the D12 fps and the WD fps, total_num_frames equal to D12 n and WD meta_n, timestamps equal to index/fps for all 32 anchors, and max(anchor) < n.
  - All 162 ARKitScenes captures have null fps, timestamps and total_num_frames, with timing_source null.
  - Bad captures: 0.
- I sampled ten captures (5 ScanNet, 5 ScanNet++, seed 17) and ran the reader's own Frames.resolve (tree_s1_admissionfix_168872) on state I built myself.
  - The result equals the finalized values, and the reader also accepts the finalized values as source input.
  - cv2 run on the staged mp4s gives the same fps (24 or 60) and the same frame count in 10 of 10 captures.
- Unchanged check_manifest (kc copy) on the finalized manifest:
  - own refused, "Native source-video metadata is unresolved".
  - all refused, with the same message.
  - convert passes.
  - The staged manifest is refused for tower_sam ("Plan is not staged...").
  - tower_sam passes. In my run, the frame-hash step hashed 300 sampled frames (one per capture), confirmed that all 19,200 files exist, and skipped hashing the two large weight files. The full rehash is the builder's PASS at 20:49Z, and the launch repeats it.

## 5. Kit unchanged
- Kit pins: all 108 DEPENDENCIES.json pins match under orch_cd. The kc copy files match the same pins.
- Modification times: no file in kit_k1a/work or native_kit changed after 20:30Z, and the kit's unpinned files (INPUT_CONTRACT.md, README.md) equal the kc copies.
- finalize_k1.py writes only into codex_finalize_v2 (write_new, line 351).
- NOTE (non-blocking): verify_sources.py in the kc copy verifies the absolute orch_cd paths, not its own files. A launch from kc is therefore covered only while kc equals orch_cd, which it does today (108/108).

## What I did not check
- I did not repeat the full 19,200-frame and weight rehash.
- I did not run accept_manifest.py again against the store.
- I did not read the builder's test suite line by line.
- I checked nothing about the own phase's GPU settings (config, data_receipt, artifact) or the ARKit timing source beyond the coverage count.
- I did not check whether the D12 mp4 fps is the right authority for the model's training-time timestamps.
