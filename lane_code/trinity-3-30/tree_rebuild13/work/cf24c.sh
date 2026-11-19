W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf24c; P="nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
date -u +%TZ; tmux has-session -t tr13_b24c 2>/dev/null && { echo STILL_RUNNING; exit 0; }
T=$(ls $W/w24/out/tree_rebuild_b24c_*.tar | head -1); echo $T; mkdir -p $C/pkg; cd $C; sha256sum $T; stat -c %s $T
(cd pkg && tar xf $T)
for d in $W/w24/work/tree_r1 $C/pkg/work/tree_r1; do (cd $d && $P -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"); done
cat $W/w24/out/BUILD24C_REPORT.md; echo; head -30 $W/w24/out/OPERATOR_24C.md
for f in review24c build24d; do echo; done
cat > $W/prompts/review24c.md <<'EOPR'
# Independent review (read-only, once) of build 24c of lane tree_rebuild (kit-only: no bytecode or other job-time writes into the kit dir), changed files only, versus build 24b

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict. This review gates N's launch.

## Context
Orchard job 173222 refused `R1_KIT_CONTENT_DIFFERS` at `launch_r1/build.py` verify(kit): the kit's own helpers (`/usr/bin/python3 b/l.py`, w.py, o.py in the decoded `k/j.json` payload) ran without `-B` and wrote `b/__pycache__` into the kit dir. Build 24c (prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24c.md`, report `w24/out/BUILD24C_REPORT.md`, package `w24/out/tree_rebuild_b24c_*.tar`) fixes this kit-only on top of 24b (`w24/out/tree_rebuild_b24b_7d7a8858.tar`, tree e1e64652, kits n efe2a12e and q 13a54582).

## Check
1. Compare the 24b and 24c packages member by member in memory (tarfile; write nothing). The tree is byte-identical (e1e64652). List the changed kit files and generator files; anything beyond the bytecode/write fix and its tests is a finding.
2. In both kits, every Python start on the host and in the view (decoded j.sh, job.sh, q.sh, q1.sh, f.sh, launcher and worker scripts) carries -B or runs with PYTHONDONTWRITEBYTECODE=1. Nothing else writes into the kit dir during a job. The new test really runs the decoded helper sequence against a writable kit copy, and it fails on 24b's kit.
3. Decoded scans PASS; each kit dir equals its SHA256SUMS plus BUILD.json and SHA256SUMS.txt; the guard is unchanged (e397ea70...); resolver identity checks are unchanged; the upload diff is pinned and complete.
4. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process runs under nice -n 10, at most 8 threads, under 20 GB RAM. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 20 lines.
EOPR
cat > $W/prompts/build24d.md <<'EOPR'
# Codex build 24d of lane tree_rebuild: kit n must not depend on post-step-400 files (review 24 MUST); full decoded job-sequence look-ahead; GO-armed rehearsal of the training path

You run once, on trinity-1-18; nobody answers questions. Writable workspace `L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24` only. Continue in it, keep every existing package unchanged, and move superseded files to `L/attic/`. Binding prompts: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24c.md` and the prompts it names (rules hold). Base: build 24c (`out/tree_rebuild_b24c_*.tar`, report `out/BUILD24C_REPORT.md`; tree e1e64652). Time limit: package by 17:35Z 2026-11-19. N's launch on 4 H100 waits on you. Kit-only: the sealed tree stays byte-identical. Add under 1 GB to L.

## Findings and orders
- Review 24 (newest `/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild_rev24/final_message.md`, read only that file) found one MUST. Kit n's pinned small-file manifest (`/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/m400real/MANIFEST.json:88`) includes P's step-414 `complete.json` and `rng000.pt`-`rng003.pt`. The resolver (`kits/n/b/z.py:133`, lines 60, 188, 207, 420) requires them, stages them and hashes them into the required inputs. RULING 1533Z says nothing produced by job 172660 after step 400 is selected for anything, so a step-400 launch must not depend on them.
- ORCH 1628Z item 3: before the launch, run the whole decoded job sequence against a writable copy of the real kit, every helper in job order, up to the first GPU call. Report the furthest stage reached and any refusal.

## Do, in order
1. Kit n (and kit q only if the same change is needed for its proof; say which) stages and requires only what the step-400 init needs: the export-only receipt files (DONE/e/r/RP as pinned), the export artifact and parts, and the model metadata. Authenticate the small archive s.tar by its pinned sha256 as one object if that is required, but extract, stage and require no post-step-400 member. RP's checkpoint pointer stays provenance only, never resolved to files. Resolver identity checks stay unchanged. Add failing-before/passing-after tests: 24c's resolver refuses without the step-414 members, and 24d's passes without them; a mutation that tries to stage any post-400 member refuses by name.
2. Full sequence look-ahead (ORCH item 3) for kits n and q. Use a writable copy of each real kit and the decoded job.sh, then j.sh with every helper in order: the bwrap view, the guard (stub only the CUDA query at the GPU boundary), the canary a.py q, the room audit d.py, o.py, and for n also t.py/u.py. Stand-ins are allowed only at the GPU, the 9B weights, the production stores and the frame host. Report each stage reached and the first refusal, and say whether it is a boundary or a defect. Fix kit defects in the kit while time allows, with tests.
3. GO-armed variant, NOT for upload until the orchestrator's launch GO: write `out/kit_n_go/` as a copy of kit n with `k/a.json` GO=true, resealed and scanned. Then rehearse the GO=true training path on CPU with the fixture: canary, v.json (say exactly which step produces `/tmp/q_22c714e1/v.json` and what it contains), t.py, u.py and one torch.distributed.run with 4 gloo CPU workers on the tiny fixture model for 2 optimizer steps. Show fresh optimizer, counter 0 to 2, finite loss on every rank, and the first export/gate step numbering. Any refusal is reported with its stage.
4. Reseal kits q and n. Write `out/UPLOADS_24D.json` and `out/UPLOADS_24D.list` (a diff against 24c's set: names, bytes, sha256, local_path) and `out/UPLOADS_24D_GO.json` (the a.json/SHA256SUMS/BUILD.json diff for the GO variant). Package `out/tree_rebuild_b24d_<seal8>.tar`; `out/BUILD24D_REPORT.md` under 60 lines with the stage table.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*. Write only under L; read anything under /scratch/jjyeung/orch_n30/tree_rebuild10_w. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. Do not change the tree, admission, legality, removals, opener rows, the step-544 lineage or the DEFERRED boundary. GO stays false everywhere except `out/kit_n_go/`, which is not uploaded.
EOPR
sha256sum $W/prompts/review24c.md $W/prompts/build24d.md | cut -c1-16
tmux new -d -s tr13_rev24c "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh review $W/w24 $W/prompts/review24c.md --model gpt-6-astra --effort high --label tree_rebuild_rev24c --skip-git-check > $W/work/review24c_dispatch.log 2>&1"
tmux new -d -s tr13_b24d "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh implement $W/w24 $W/prompts/build24d.md --model gpt-6-astra --effort high --label tree_rebuild24d --skip-git-check > $W/work/build24d_dispatch.log 2>&1"
sleep 15; tmux ls | grep tr13
