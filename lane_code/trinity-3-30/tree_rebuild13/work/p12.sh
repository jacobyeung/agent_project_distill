W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p
cat > $W/prompts/build23b.md <<'EOPX'
# Codex build 23b of lane tree_rebuild: fix review 23's MUST (MINIMAL silently ignores a bound routing slice), reseal kit q

You run once, on trinity-1-18; nobody answers questions. Writable workspace `L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23` only (continue in it; keep `out/tree_rebuild_b23_40abf77b.tar` unchanged; move superseded files to `L/attic/`). Binding prompts: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build23.md` (read first; its rules and ruling hold) and the prompts it names. Base: build 23 (`out/tree_rebuild_b23_40abf77b.tar`, tree b4edc475, kit q bb04241c, report `out/BUILD23_REPORT.md`). Time limit: package by 14:55Z 2026-11-19 (`date -u` at each step); the production proof waits on you.

## Finding (review 23, verdict GO AFTER FIXES; `/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261119T140644Z_tree_rebuild_rev23/final_message.md`, read only that file there)
MUST: `work/tree_r1/student_pilot/r1_coverage.py:16` checks `routing_inputs` under the MINIMAL declaration but ignores a nonempty `r1_training.row_slice_inputs`; `source_names()` then returns empty. A mutation binding `row_slice_inputs.recovery` to the kit's pinned recovery source still reached `R1_PROOF_FRAME_HOST_REQUIRED`: the slice is silently ignored. The orchestrator's condition is that under MINIMAL a kit that binds any routing slice refuses by name.

## Do, in order
1. Enumerate every config/request field through which a routing slice (recovery, absolute_distance, units, coverage_distance, coverage_units, camera wording, any EXTRA/coverage PINS) can be bound or would be read in FULL mode (row_slice_inputs, routing_inputs, row_sources entries that FULL would compose, source_membership entries, card cells, request fields in launch_r1/build.py and entry.py). Under the declaration, each such binding must refuse by name (e.g. `R1_MINIMAL_SLICE_BOUND:<field>:<name>`) before any reader runs, at one central check called from every MINIMAL path (production_proof, entry, s1_admission, r1_population, r1_rooms, build). State in the report which fields are refused and which are legitimately present under MINIMAL (e.g. pinned source lists the room audit needs) and why that is not a binding.
2. Failing-before (the reviewer's mutation reaches R1_PROOF_FRAME_HOST_REQUIRED on tree b4edc475) / passing-after tests and one mutation per field. FULL behaviour unchanged.
3. Rerun build 23's tests (204), decoded scan, look-ahead with the kit's own config (must still reach R1_PROOF_FRAME_HOST_REQUIRED), the MINIMAL capacity fixture at 400 (600 if cheap). Regenerate kit q; update `out/MINIMAL_TREE.patch` (against tree b262e7a7) and `out/MINIMAL_MERGE_NOTES.md`; write `out/UPLOADS_NEW_23B.json` (diff versus kit q bb04241c, names, bytes, sha256, local_path).
4. Package `out/tree_rebuild_b23b_<seal8>.tar`; `out/BUILD23B_REPORT.md` under 60 lines (fields, tests, seals, upload diff, look-ahead, fixture).

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents; never list, search or grep on /home or /data*: read only named files there; write only under L; no deletion; every CPU process under `nice -n 10` with at most 8 threads; no process above 20 GB RAM; L under 3 GB. Do not change admission, legality, removals, P's opener rows, the step-544 lineage, the resolver's identity checks or the DEFERRED boundary; names opaque in the kit; GO stays false.
EOPX
sha256sum $W/prompts/build23b.md | cut -c1-16
tmux new -d -s tr13_b23b "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh implement $W/w23 $W/prompts/build23b.md --model gpt-6-astra --effort high --label tree_rebuild23b --skip-git-check > $W/work/build23b_dispatch.log 2>&1"
sleep 20; tmux ls | grep tr1
