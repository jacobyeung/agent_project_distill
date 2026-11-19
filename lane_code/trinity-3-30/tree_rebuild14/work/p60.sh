W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p
cat > $W/prompts/build24fr3.md <<'EOPX'
# Codex build 24fr3 of lane tree_rebuild: third rehearsal stop, COMPONENT_EVIDENCE_PREPARATION_MISMATCH:export at the first milestone export (fixture or production?), after 24fr2

You run once, on trinity-1-18; nobody answers questions. Writable: under `L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f`, only files whose names start with `rehearsal`, `make_rehearsal`, `check_rehearsal`, `go_rehearsal`, `REHEARSAL` or `FIXTURE`, plus the dirs `L/rehearsal3` and a new `L/rehearsal4`. Build 24k runs in the same workspace on other files: touch nothing else, and never the kits, packages, tree or `out/`. Binding prompts: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24fr.md` and those it names (rules hold); read `L/REHEARSAL_FIX_REPORT.md` and `L/REHEARSAL_FIX2_REPORT.md` first. Time limit: 40 minutes.

## Finding
The lane ran `go_rehearsal.sh` on rehearsal3 at 20:10Z (log `L/rehearsal_run3.log`, `L/rehearsal3/train_fresh.log`). Clock inheritance, the fresh optimizer with counter 0, the step-1 checkpoint through milestone() and the timed checkpoint PASS. At the first milestone export, `carrier_c1_run.py:2126 export()` -> `student_pilot/r1_components.py:119 artifact_binding()` raises `COMPONENT_EVIDENCE_PREPARATION_MISMATCH:export`: for an r1_training config the pin `cfg['preparation']` must load a preparation whose normalised `component_evidence` equals `artifact_status(cfg)`. Then the other ranks lose their gloo peer.

## Do
1. Show exactly why the statuses differ in the rehearsal: which preparation `cfg['preparation']` names in v.json, what component_evidence it records, and what artifact_status(cfg) returns, field by field. Note that kit h.py/rv.py (24h/24i) synchronise or re-pin the preparation after attaching receipt pins; check whether that re-pinning drops or changes component_evidence.
2. Production verdict: in the launch job, cfg['preparation'] comes from a.py q's native preparation (launch_r1/production_proof, s1_admission prepare_only) followed by kit h.py/rv.py. Read that code and say whether the production preparation records component_evidence equal to artifact_status(cfg) for N (2 slots NOT_PRESENT, 7 DEFERRED per the card). If the production path can raise this at step 100, that is a launch BLOCKER: say so first, name the exact lines, and say whether the fix is kit-only (h.py/rv.py re-pinning) or a tree change.
3. If it is fixture-only, fix the fixture in `L/rehearsal4` (append `build24fr3` to FIXTURE_DIFF.json). If it is the kit's re-pinning, write the exact kit fix as `L/KIT_FIX_24FR3.md` for the merge build, without editing kits. Point go_rehearsal.sh at rehearsal4 only if the fixture is the cause. Write `REHEARSAL_FIX3_REPORT.md` (under 20 lines) with the cause, the evidence, the production verdict and the lane's command. Do not run the four-rank rehearsal.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. Do not change the tree, kits, config, admission or legality.
EOPX
sha256sum $W/prompts/build24fr3.md | cut -c1-16
tmux new -d -s tr14_b24fr3 "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh implement $W/w24 $W/prompts/build24fr3.md --model gpt-6-astra --effort high --label tree_rebuild24fr3 --skip-git-check > $W/work/build24fr3_dispatch.log 2>&1"
sleep 5; tmux ls | grep tr14
