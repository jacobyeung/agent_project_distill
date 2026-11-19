# Independent review (read-only, once) of build 23b of lane tree_rebuild, changed files only, versus build 23

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict.

## Context
Build 23 (package `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/out/tree_rebuild_b23_40abf77b.tar`, tree b4edc475, kit q bb04241c, prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build23.md`) added vehicle N's MINIMAL mode: under the pinned declaration `r1_training.routing_slices: "deferred_first_boundary"` N trains on P's own routing stream, compose_native is skipped, and every new routing slice is deferred. Review 23 (`/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261119T140644Z_tree_rebuild_rev23/final_message.md`) found one MUST: a nonempty `row_slice_inputs` was silently ignored under MINIMAL. Build 23b (prompt `prompts/build23b.md`, report `w23/out/BUILD23B_REPORT.md`, package `w23/out/tree_rebuild_b23b_*.tar`) fixes it.

## Check
1. Compare the 23 and 23b packages member by member in memory (tarfile; write nothing); review only changed files. List the changed tree files; anything beyond the central slice-binding refusal, its call sites and its tests is a finding.
2. The MUST is fixed: rerun the reviewer's mutation (bind `row_slice_inputs.recovery` to the kit's pinned recovery source) in memory against 23b; it must refuse by name before any reader runs. Try each other field through which a slice can be bound (routing_inputs, row_sources entries FULL would compose, source_membership, card cells, request fields in launch_r1/build.py and entry.py, the camera/coverage EXTRA pins): each must refuse by name under the declaration, or the report must show why it is not a binding.
3. FULL behaviour (no declaration) and every earlier refusal are unchanged; the kit's own config still passes the routing/card/room gates (look-ahead reaches R1_PROOF_FRAME_HOST_REQUIRED); the MINIMAL fixture still ADMITs with finite first-batch losses.
4. Kit q: name scan clean; kit dir file list equals SHA256SUMS (plus BUILD.json and SHA256SUMS.txt); resolver identity checks unchanged; upload diff versus bb04241c small and pinned.
5. Nothing changed in admission, legality, removals, P's opener rows, the step-544 lineage or the DEFERRED boundary; GO stays false. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process under nice -n 10, at most 8 threads, under 20 GB RAM. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 30 lines.
