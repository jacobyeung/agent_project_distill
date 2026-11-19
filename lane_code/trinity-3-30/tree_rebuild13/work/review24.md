# Independent review (read-only, once) of builds 24 and 24b of lane tree_rebuild: vehicle N's MINIMAL launch kit, changed files only

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict. This review gates N's launch on 4 H100: prioritise problems that would let a wrong launch admit, or a correct launch refuse.

## Context
- RULINGs: MINIMAL (N trains on P's own routing stream; every new routing slice is deferred under `r1_training.routing_slices: "deferred_first_boundary"`). RULING 1533Z: N's init is P's step-400 export (artifact 5083243c), admitted by the export-only receipt; nothing after step 400 is used.
- Reviewed inputs: build 22 (`/scratch/jjyeung/orch_n30/tree_rebuild10_w/w22/out/tree_rebuild_b22_d41a6dc8.tar`, tree 1c2f106b; VQA removals, twins, NOT_PRESENT, camera slice), build 23d (`w23/out/tree_rebuild_b23d_1e85df14.tar`, tree 5b349b18, kit q 928c37d5; MINIMAL + central slice-binding refusal + GPU guard, reviews GO).
- Under review: build 24 (`w24/out/tree_rebuild_b24_90637cdf.tar`, prompt `prompts/build24.md`, report `w24/out/BUILD24_REPORT.md`) merges 22 + 23/23b and adds step-600 handover acceptance; build 24b (`w24/out/tree_rebuild_b24b_*.tar`, prompt `prompts/build24b.md`, report `w24/out/BUILD24B_REPORT.md`) makes launch kit n initialise from the step-400 export, applies 23d's guard and reruns the fixture.

## Check
1. Tree: compare 24b's tree with 22's and 23d's in memory (tarfile; write nothing). Every change must come from 23b's MINIMAL patch, the step-600/receipt branch, or 24b's init acceptance; list anything else. Under the declaration the camera slice and every other slice refuse by name when bound; FULL is unchanged without it.
2. Init: launch kit n at 400 admits only P's real step-400 export-only receipt (the files in `/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/m400real`: artifact, run, trainer commit, export parts tar dcd49569, model metadata). If the tree changed to accept an export-only receipt as a training init, that change is explicit and pinned, applies only to step 400 init weights, keeps every other receipt check, and has real failing-before tests. Nothing in kit n selects step 600 or any job-172660 file after step 400.
3. Kits n and q: decoded name scan PASS; each kit dir equals its SHA256SUMS plus BUILD.json and SHA256SUMS.txt; the guard equals 23d's g.py (e397ea70...); the resolver identity checks are unchanged except the milestone/receipt branches; 4 ranks, advanced partition, opaque names. Upload lists `w24/out/UPLOADS_MINIMAL.json`/`.list` and `UPLOADS_24B.json` cover every pin the kits need, and the deferred camera rows are absent.
4. Fixture: launch kit n at 400 reaches ADMIT on all 4 ranks with finite full-forward first-batch losses; deferred cells are zero; removals (109 list) and twins (7,971) are active; refusal twins pass.
5. Card rows `w24/out/N_CARD_KIT_ROWS.md` are accurate: init, seals, the declaration, what the first 200 steps change and do not change against P, and the H3 note that the tower scale can drift.
6. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process runs under nice -n 10, at most 8 threads, under 20 GB RAM. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 35 lines.
