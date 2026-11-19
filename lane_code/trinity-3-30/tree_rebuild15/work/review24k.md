# Independent review (read-only, once) of KIT builds 24g, 24h, 24i and 24k of lane tree_rebuild: vehicle N's launch kit, changed files only, versus build 24f

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict. This review gates N's launch on 4 H100 for 24 h; prioritise problems that would let a wrong launch admit, a correct launch refuse, a running launch lose its exports, or a protected or answer-only row train. The tree changes of 24j (and the pending 24l2) are reviewed separately by another model family: review only how the kits consume them.

## Context
Base: build 24f (`/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/tree_rebuild_b24f_449bc1fc.tar`, tree 57a1f14d, kit n 89ec4951, kit q 3d144296), reviewed (`/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261119T185629Z_tree_rebuild_rev24f/final_message.md`; its MUST A, MUST B and SHOULD C were to be fixed in 24h). Prompts `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24{g,h,i,k}.md`; reports `w24/out/BUILD24K_REPORT.md` and the BUILD24{G,H,I}_REPORT.md inside the packages `w24/out/tree_rebuild_b24{g,h,i,k}_*.tar` (read with tarfile in memory). Current kit dirs: `w24/out/kit_n_go` (GO variant, 05f0ffa1); kits n 814db98a and q 6215397d are inside the 24k package.
- 24g: the copier reads sessions from x_22c714e1/n_s/sess.json (dir 0700, file 0600) outside the kit dir.
- 24h: review 24f fixes A/B/C; h.py pins a host receipt; arm_go.py, identity.py, REVIEW_SCHEMA.md.
- 24i: option B: after h.py writes v.json the job publishes v.json, identity, row samples (random.Random(20261119), 40 per stream), whole-store answer-only and trace-form counts and rooms.json to x_22c714e1/o/<job>/live/ (under 2 MB), writes WAITING_REVIEW and waits <=120 min for x_22c714e1/n_r/review.json (0700/0600), refusing on timeout, identity or sha mismatch, wrong mode or symlink; PREP_FIELDS + prep_diff.py.
- 24k: kits rebuilt on tree 189df6ac (24j host receipt); h.py consumes exactly RESULT.json.host_receipt -> q/host.json; recorded_host only in mode p; read-only planning (b/pl.py) plus an authenticated copier passed as the tree's staging hook; source_code.json; bootstrap pool refresh; mode `a.py r` (b/rg.py) and out/jr.sh for the CPU routing-selection job; R1_ROUTING_SELECTION_PIN_MISSING placeholder and out/arm_routing.py; answer-only immediate refusal only for VQA and routing (pose/pointing published, not refused; ORCH 2000Z/2001Z); per-stream BENCH v2 (benchmark_scene_exclusions 3119aa4a) and dev-S1 (dev_scene_exclusions a1869ae2) room counts over the whole admitted store, refusing R1_PROTECTED_ROOM_ROWS if above zero.
- The lane submits the routing job with this wrapper on Orchard (x_22c714e1/jrw.sh), which runs the kit's resolver and then `bash jr.sh <resolved> <kit n>`:
```
#!/bin/bash
#SBATCH -p preempt
#SBATCH --job-name=a15_cot_ap24a9e61c
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --output=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24a9e61c_%j.log
#SBATCH --error=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24a9e61c_%j.err
set -euo pipefail
umask 077
X=/project/community/jjyeung/okh7/x_22c714e1
echo "$(date -u +%FT%TZ) resolve start"
python3 -I -s -B $X/n/b/resolve.py --pool /project/community/jjyeung/okh7 --listing $X/l.json --output $X/j/r_${SLURM_JOB_ID}.json
echo "$(date -u +%FT%TZ) resolve done"
bash $X/jr.sh $X/j/r_${SLURM_JOB_ID}.json $X/n
echo "$(date -u +%FT%TZ) routing job done"
```

## Check
1. Compare 24f with 24k (and the intermediate packages) member by member in memory; list every changed kit and generator file; anything beyond the items above is a finding.
2. The 24i wait and publication: refusal codes and tests as listed; nothing published exceeds its cap or carries frames, frame indices, timestamps, credentials or session URLs; the answer-only and room counts are over the whole admitted store with the trainer's own readers; the immediate refusals fire before WAITING_REVIEW.
3. Mode r: it stages exactly as mode q does, builds the selection under the same fixed namespace root as mode q's check_host_selection (so the digest can match), and its P-regeneration comparison would detect a different selection; jr.sh/jrw.sh request no GPU and use only opaque names; nothing in mode r can admit or train.
4. The staging hook and planning: every staged byte is authenticated before any read; the hook cannot write outside the job root; h.py keeps every 24h/24i refusal and accepts only the native host receipt for the same config identity.
5. Copier and stop: the 24f review's MUST A/B and SHOULD C are fixed; TERM/USR1 forwarding to the trainer, final copy, done markers only after sha256 verification.
6. kit_n_go differs from kit n only in k/a.json GO=true and the reseal; decoded scans PASS; each kit dir equals its SHA256SUMS plus BUILD.json and SHA256SUMS.txt; the guard and resolver identity checks are unchanged; the upload diffs (out/UPLOADS_24{G,H,I,K}.json/.list) are pinned and complete.
7. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data* (read only the named files there). Any process runs under nice -n 10, at most 8 threads, under 20 GB RAM. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 30 lines.
