# Build N3: native worker, next pass (one-shot Codex build, continues builds N and N2 in place)

You run once on trinity-3-30; nobody answers questions while you run. Same rules as `BRIEF.md` and
`BRIEF_N2.md` in this folder (read both, including "Binding rulings"): write only inside
`/scratch/jjyeung/orch_n30/b07_offread/builds/N/` (at most 4 GB; check `df -h /scratch` before writing
more than 1 GB); no ssh, network, Git, GPU, Slurm or Orchard command; no deletion; no recursive search of
/home or /data*; Python `/scratch/jjyeung/envs/p1cpu/bin/python -B`; never open a benchmark answer or
score to choose anything. Read `out/NATIVE_KIT_READY.md`, `out/OPEN_INPUTS.md`, `RUN.md`, `DIFF.md` first.
Tests: `"$PY" -B -m pytest -p no:cacheprovider kit/tests --basetemp=work/<fresh> -q`.

## Rulings since N2 (they win)
1. Dense G3T on ReVSI (orchestrator, standing user ruling): reconstruct dense, then subsample; never fit
   geometry on 32 frames. `clip32` may exist only as a labelled diagnostic and is refused for production
   in any mode that can produce a claimed number. The registered mapping exists:
   `/data2/jjyeung/agent_project_data/external_benchmarks/revsi/hf_metadata/sampled_video_frame_idx.json`
   (read once; per video `{"64-frame": [...], "32-frame": [...], "16-frame": [...]}` source-video indices).
   For all 302 videos of `out/NEED_302.json` the 32-frame indices are a subset of the 64-frame indices. The
   official 64-frame clips (`.../revsi/64_frame/<name>.mp4`) hold those 64 frames. So `original` =
   G3T on the 64-frame clip, geometry subsampled at positions `i64.index(i)` for each `i` in the 32-frame list,
   which are the model's 32 anchors (the 32-frame clip). Build the mapping file (per video: both index
   lists, positions, sha256 of both clips) and its tests; make it the default; pin its sha in the binding.
   A local copy of both clip sets will land at `/scratch/jjyeung/orch_n30/b07_offread/work/stage_rv/A.tar`
   (deterministic tar; members `a/<name>.mp4` = 32-frame clips, `b/<name>.mp4` = 64-frame clips, 302 each).
   If it exists when you get there, extract it under `work/` and run the pixel correspondence check on all
   302 videos (mean absolute RGB difference of each 32-clip frame against its mapped 64-clip frame, and
   against the neighbouring 64-clip frame; record per video; a lane check on three videos gave 1.7-9.4
   matched vs 41-60 neighbour); if it does not exist yet, ship the check as a command in RUN.md and test it
   on synthetic clips. Do not read the clips from /data2.
2. Orchard media for ReVSI: the 41 additional 32-frame clips and the 302 64-frame clips are being uploaded
   by the lane as one tar to Orchard `/project/community/jjyeung/okh7/d46dd56e669a050f/7b5d2192.tar`
   (members as above). Stage both media sets from it (plus the accepted 261-clip pool
   `okh7/313db5a47f11ff0c/`), verifying each file's sha256 against a manifest you write from the local
   A.tar when present (otherwise mark the hashes as pending and refuse production). Update OPEN_INPUTS.
3. offkit API changed (review fixes; `/scratch/jjyeung/orch_n30/b07_offread/kit/offkit`, 49 tests pass):
   `bind(..., ledger=..., frames=(count, layout), frames_override_reason=None)` (production needs a ledger;
   the binding carries `frames`); `report.label_report(report, *, binding, arm, role, arm_label=None)` takes
   the verified BINDING; `adapt_native.from_journal` refuses the C8r `scripted` arm and any row with a script
   answer; `frames.bind_frames` has no caller `export_layout`; init selection needs the init-rule fields.
   Adapt every caller; do not copy or change offkit.
4. Pin b04. The e2e portable test fails now (`test_portable_worker_sources[e2e]`: canary response replay
   differs) because lane b04 keeps editing `/scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/`. Snapshot the
   b04 files the kit uses into `builds/N/vendor/b04_<sha12>/` with a pin manifest, run everything against the
   snapshot, and add a command that refreshes it deliberately and reports the diff. Same for any other live
   lane tree the kit reads.
5. Then VSI-Bench 5,130: cohort, the 288-video manifest from the direct kit
   (`/scratch/jjyeung/orch_n30/b07_offread/in/x27/kit/`), name inventory from question text, fixtures for both
   readers, admission. VSI-Bench videos are full videos, so dense G3T reads 64 frames from the same video.
6. Production-CONFIG rehearsal for ReVSI (both readers) with only transport changed, if it can run on CPU
   with stand-ins; else say exactly what blocks it.

## Deliver
Update `out/NATIVE_KIT_READY.md` (READY or NOT READY per benchmark x reader in its first sentence), new
`code.tar` with hashes, `SHIP_SHA256SUMS`, `DIFF.md`, `RUN.md`, `OPEN_INPUTS.md`. Nothing submitted or
uploaded. Final message under 10 lines.
