# Review verdict: K1 fixes k1_samfix (boundaries.py 5fbe3ae6, DEPENDENCIES c0c81f33) and k1_arkit_timing (manifest 91a2dbf9)

Reviewer: lane review_k1b on trinity-1-18. I was read-only on the builder's files. My scripts and logs are in /scratch/jjyeung/orch_n30/review_k1b/work/ (test_inference_moves.py copy, reg_old.log, reg_new.log, real_sam_cpu.py, real_old4.log, real_new4.log, real_new4.json, timing_check.py, cm.py, cm.log, modprobe.py, kit_old/, kit_new/, kit_mut/).

## Verdict: GO for the tower_sam relaunch
Relaunch exactly as planned: apply_samfix.sh on kc, verify_sources on the kc pins, manifest 91a2dbf9, and the fresh root run_tower_sam_2.
Timing: fit for the own phase. The own phase on Orchard is still blocked by its GPU settings, not by timing (point 4).

## 1. Crash fix
- Mechanism. I confirmed it from the traceback and the code.
  - Sam3Tower.encode is @torch.inference_mode, and it calls _load. On capture 1 this builds SAM, so every parameter and buffer is an inference tensor.
  - boundaries.GPU.tower runs `.to('cpu')` (old line 53), and GPU.sam runs `.to(device)` (old line 86). Both run outside inference mode. Module._apply then sets param.data to a normal tensor, and the Parameter keeps its disabled version counter.
  - The next inference-mode slice, vitdet.py:247 `abs_pos[:, :1]`, therefore raises.
- Patch. With both moves inside inference_mode, the new data is an inference tensor again. Every later capture therefore starts in the same state as capture 1.
  - The fix holds for every capture, not only the second. Each capture does the same tower-then-sam pair. The _load re-entry (`eval().requires_grad_(False)`) and _detect both run in inference mode, as they did on capture 1.
  - Room-only captures skip sam(). Their tower() call moves an already-CPU model, which is a no-op.
- Real weights on CPU. I used sam3.pt 9999e234, the kit's real GPU.tower and GPU.sam, real _load and real encode on staged frames. The device moves were forced into real copies with Tensor.to(copy=True), and three captures ran: A, B, A.
  - Old boundaries b9edddf9 failed on capture 2 with the production error at vitdet.py:247 (real_old4.log).
  - New boundaries 5fbe3ae6 passed all 3 captures. Parameters were still inference tensors before each encode, and capture 3's features are bit-equal to capture 1's (real_new4.json).
  - On CPU I ran encode only. SAM's grounding decoder hard-codes CUDA tensors, so detect was not exercised after a move.
- Builder regression, rerun from my copy: old kit gives 7 tests with 3 errors (the slice error); patched kit gives 7 of 7 OK.
- Other models. I found no create-in-one-mode, move-or-mutate-in-another pattern.
  - G3T (tower_read.py 164-194): FrozenG3TTower is built, loaded and moved inside inference_mode. boundaries.tower builds a new instance for each capture, and nothing moves it afterwards.
  - Own (read_runtime.load_model line 92; boundaries.own): the own model loads in normal mode, and both of its moves run in normal mode. geometry_input and gf1 cache their tensors under inference_mode(False).
  - convert runs no model.
  - I did not trace the full own-model forward.

## 2. Pins
- samfix DEPENDENCIES.json has the same 108 keys as the mirror's. The 93 kit keys are remapped to kc and the 15 external keys are unchanged. Every hash equals the mirror's except native_kit/boundaries.py (b9edddf9 -> 5fbe3ae6). The executed kit files are all named, including run_k1.sh, verify_sources, gate, watchdog, k1_pipeline, k1_cli, k1_phases, bindings, boundaries, pipeline, sam3_tower and sam_backend.
- verify_sources:
  - On the current kc it passes (108).
  - samfix pins hashed against kc today mismatch only on boundaries.py, as expected before the apply step.
  - In a scratch copy with the patch and remapped pins it passes (108). It fails with rc 1 when I alter one byte of k1_phases.py, boundaries.py, sam3_tower.py or k1_cli.py, and passes again once I restore the byte.
- NON-BLOCKING gap: the 108 pins still leave 67 executed /scratch modules unpinned. These are 55 sam3src files (beyond the 6 that the SAM receipt checks), 7 native out2 modules (common, routed, frozen_kit, r1, reader_policy, runtime_tree, geometry_refusals) and 4 tree files (c1r_ref, g3t_online, tower_errors, __init__); see modprobe.py. The first launch ran with the same gap, so this fix did not introduce it. Fix it in the next kit.

## 3. Timing
- Diff c3bbc378 -> 91a2dbf9:
  - In captures, the only changes are fps, timestamps and total_num_frames, in exactly the 162 ARKit captures.
  - Outside captures, top-level k1_finalize also changes (schema, input, and the timing provenance block).
  - That block is metadata. B.digest(c) and the phase receipts do not read it, and check_manifest does not consult it, so it has no effect.
- 10 of the 87 covered captures (seed 23): I built Frames.resolve state myself with the sealed frame_rates.json (36ae882f) as the authority. All three fields equal the manifest on 10 of 10, and the reader also accepts the manifest values as a source row.
- 10 of the 75 derived captures: a least-squares fit over the 64 WA per-frame source timestamps gives 9.9985-10.0004 fps, which rounds to 10. My fps, index/fps timestamps and max(anchor)+1 equal the manifest on 10 of 10. The reader also agrees given a one-scene authority at 10.0. The largest residual from a straight line is 0.031 s.
- total_num_frames = max(anchor)+1 is what s1_routing.Frames.resolve (lines 116-120) returns for d3 when the plan has no raw_n. It is the only d3 path, because d1 and d2 refuse a missing raw_n. In all 162 captures max(dense) equals max(anchor), so no dense index exceeds the count.
  - Not verified: that the training-time frame_plan has no raw_n for d3. I could not locate that plan.
- Gaps: no ARKit capture's 10 Hz timeline has a gap. Across all 162 captures, no WA or plan interval between consecutive dense samples deviates from index spacing at 10 Hz by more than 0.15 s; the largest deviation is -0.067 s (41125837, plan, 804->821). All 162 have fps 10.0.

## 4. check_manifest on 91a2dbf9 (unchanged kc k1_pipeline.py; cm.log)
- tower_sam: PASS. It covers all dense frames and the four GPU pins.
- own: REFUSED with FileNotFoundError on 'REQUIRED_LOCAL_STEP_544_CONFIG'. Timing passes; the refusal comes later, at gpu.config. gpu.data_receipt is also a placeholder (sha256 "REQUIRED").
  - For the own run, Orchard must bind both. It must keep the captures byte-equal and keep gpu.artifact equal, because convert compares B.digest(c) and the artifact pin.

## Incident (mine)
At 21:59:49Z and 22:00:25Z, two of my CPU test processes briefly opened a CUDA context on physical GPU 0, not the reserved card 4, for about 30 s each. The cause was that the tmux server's environment lacked CUDA_VISIBLE_DEVICES='', and SAM's build hard-codes device="cuda". Both crashed within seconds. Every later run set the variable inside the tmux command and asserted that CUDA was unavailable.

## Not checked
- I did not exercise detect after a device move on real weights (CPU cannot run it), and I ran nothing on a real CUDA device.
- I did not trace the own-model forward end to end, and I did not check Part B's Orchard bindings.
- Not verified: the absence of raw_n for d3 in the training frame_plan.
- I did not repeat the native test_kit.py suite. I did repeat the builder's regression.
