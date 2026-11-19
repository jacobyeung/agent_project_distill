W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1
cat > $W/prompts/build24c.md <<'EOPX'
# Codex build 24c of lane tree_rebuild: kit-only fix for R1_KIT_CONTENT_DIFFERS, caused by bytecode that the kit's own helpers write into the kit dir (Orchard job 173222)

You run once, on trinity-1-18; nobody answers questions. Writable workspace `L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24` only. Continue in it, keep every existing package unchanged, and move superseded files to `L/attic/`. Binding prompts: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24b.md` and the prompts it names (rules hold). Base: build 24b (`out/tree_rebuild_b24b_7d7a8858.tar`, tree e1e64652, kit n efe2a12e, kit q 13a54582; report `out/BUILD24B_REPORT.md`). Time limit: package by 16:50Z 2026-11-19; N's launch waits on you. The sealed tree must stay byte-identical (e1e64652): this is a kit-only change. Add under 300 MB to L.

## Finding (Orchard job 173222, kit q 928c37d5 from build 23d, on an H100 80GB)
Resolver, staging, frames and init mirror passed, and the new guard passed (m=85,017,493,504). Then `b/a.py` failed at line 21, `verify(kit)` in `launch_r1/build.py:11-16`, with `ValueError: R1_KIT_CONTENT_DIFFERS`. `rooms_rc` was 1 too. Evidence: Orchard x_22c714e1/o/173222/o.tar holds q.log and rooms.log. verify() hashes every file under the kit with `rglob('*')` and compares the set with SHA256SUMS.txt. In the decoded `k/j.json` payload (lines ~387-396), `/usr/bin/python3 "$Q_KIT/b/l.py"` (the log screener, started in the same pipeline as `a.py`), `b/w.py` and `b/o.py` run without `-B`. They import `b/z.py`, so `b/__pycache__/z.cpython-*.pyc` appears inside the kit dir before or while `a.py` verifies it. Earlier Orchard jobs left exactly that pyc in q/b/.

## Do
1. Confirm the cause by reproducing it on CPU: with a writable copy of the kit, run the helpers in j.sh's order, then verify(kit). It must refuse R1_KIT_CONTENT_DIFFERS before the fix and pass after.
2. Fix it kit-only in every generator and emitted script of kits q and n (j.sh payload, job.sh, q.sh, q1.sh, f.sh, the launcher and anything else that starts Python on the host or in the view). Every Python start carries `-B`, and the environment handed to those processes sets PYTHONDONTWRITEBYTECODE=1. Also list any other way the kit dir can gain or change a file during a job (logs, temp files, caches); move every such write to node-local job storage. Add a test that runs the whole decoded j.sh helper sequence against a writable kit copy and asserts the kit's file set and hashes are unchanged afterwards.
3. Rerun the guard tests, the decoded scans (PASS), the kit/naming/resolver suites, and the look-ahead of kits q and n with their own configs (expected R1_PROOF_FRAME_HOST_REQUIRED). Reseal kits q and n. Write `out/UPLOADS_24C.json` and `out/UPLOADS_24C.list` (names, bytes, sha256, local_path), as a diff against 24b's upload set (24's UPLOADS_MINIMAL plus UPLOADS_24B), and give the stream root. Package `out/tree_rebuild_b24c_<seal8>.tar`; `out/BUILD24C_REPORT.md` under 40 lines.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*. Write only under L. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. Do not change the tree, config, resolver identities, admission, legality, removals, opener rows, the step-544 lineage or the DEFERRED boundary. GO stays false.
EOPX
cat > $W/prompts/review24.md <<'EOPX'
# Independent review (read-only, once) of builds 24 and 24b of lane tree_rebuild: vehicle N's MINIMAL launch kit, changed files only

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict. This review gates N's launch on 4 H100: prioritise problems that would let a wrong launch admit, or a correct launch refuse.

## Context
- RULINGs: MINIMAL (N trains on P's own routing stream; every new routing slice is deferred under `r1_training.routing_slices: "deferred_first_boundary"`). RULING 1533Z: N's init is P's step-400 export (artifact 5083243c), admitted by the export-only receipt; nothing after step 400 is used.
- Reviewed inputs: build 22 (`/scratch/jjyeung/orch_n30/tree_rebuild10_w/w22/out/tree_rebuild_b22_d41a6dc8.tar`, tree 1c2f106b; VQA removals, twins, NOT_PRESENT, camera slice), build 23d (`w23/out/tree_rebuild_b23d_1e85df14.tar`, tree 5b349b18, kit q 928c37d5; MINIMAL + central slice-binding refusal + GPU guard, reviews GO).
- Under review: build 24 (`w24/out/tree_rebuild_b24_90637cdf.tar`, prompt `prompts/build24.md`, report `w24/out/BUILD24_REPORT.md`) merges 22 + 23/23b and adds step-600 handover acceptance; build 24b (`w24/out/tree_rebuild_b24b_7d7a8858.tar`, tree e1e64652, kit n efe2a12e, kit q 13a54582, prompt `prompts/build24b.md`, report `w24/out/BUILD24B_REPORT.md`) makes launch kit n initialise from the step-400 export, applies 23d's guard and reruns the fixture.

## Check
1. Tree: compare 24b's tree with 22's and 23d's in memory (tarfile; write nothing). Every change must come from 23b's MINIMAL patch, the step-600/receipt branch, or 24b's init acceptance; list anything else. Under the declaration the camera slice and every other slice refuse by name when bound; FULL is unchanged without it.
2. Init: launch kit n at 400 admits only P's real step-400 export-only receipt (the files in `/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/m400real`: artifact, run, trainer commit, export parts tar dcd49569, model metadata). If the tree changed to accept an export-only receipt as a training init, that change is explicit and pinned, applies only to step 400 init weights, keeps every other receipt check, and has real failing-before tests. Nothing in kit n selects step 600 or any job-172660 file after step 400.
3. Kits n and q: decoded name scan PASS; each kit dir equals its SHA256SUMS plus BUILD.json and SHA256SUMS.txt; the guard equals 23d's g.py (e397ea70...); the resolver identity checks are unchanged except the milestone/receipt branches; 4 ranks, advanced partition, opaque names. Upload lists `w24/out/UPLOADS_MINIMAL.json`/`.list` and `UPLOADS_24B.json` cover every pin the kits need, and the deferred camera rows are absent.
4. Fixture: launch kit n at 400 reaches ADMIT on all 4 ranks with finite full-forward first-batch losses; deferred cells are zero; removals (109 list) and twins (7,971) are active; refusal twins pass.
5. Card rows `w24/out/N_CARD_KIT_ROWS.md` are accurate: init, seals, the declaration, what the first 200 steps change and do not change against P, and the H3 note that the tower scale can drift.
6. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process runs under nice -n 10, at most 8 threads, under 20 GB RAM. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 35 lines.
EOPX
sha256sum $W/prompts/build24c.md $W/prompts/review24.md | cut -c1-16
tmux new -d -s tr13_b24c "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh implement $W/w24 $W/prompts/build24c.md --model gpt-6-astra --effort high --label tree_rebuild24c --skip-git-check > $W/work/build24c_dispatch.log 2>&1"
tmux new -d -s tr13_rev24 "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh review $W/w24 $W/prompts/review24.md --model gpt-6-astra --effort high --label tree_rebuild_rev24 --skip-git-check > $W/work/review24_dispatch.log 2>&1"
sleep 15; tmux ls | grep tr13
