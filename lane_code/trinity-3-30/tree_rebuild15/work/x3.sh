J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l; date -u +%TZ; free -g | sed -n 2p; tmux ls | grep tr15
cat > $J/prompts/build24n.md <<'EOPX'
# Codex build 24n of lane tree_rebuild: TREE fix, the handover's donor binding check compares the preparation by its bytes, not by its path (production blocker P_EXPORT_RUN_BINDING_MISMATCH), on top of build 24l

You run once, on trinity-2-28; nobody answers questions. Writable workspace `J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l` only. Build 24l (a tree fix in launch_r1/entry.py and production_proof.py) has just finished there: its tree is `J/work/tree_r1`, its outputs `J/out/` (read `J/out/BUILD24L_REPORT.md`). First copy `J/work/tree_r1` to `J/work/tree_r1_24l` (untouched base for this build; never edit it), then work in `J/work/tree_r1`. Evidence of the blocker from trinity-1-18 is in `J/in24kr/` (REHEARSAL_K_FIX_REPORT.md, REHEARSAL_K_BINDING_FIELDS.md, REHEARSAL_K_BINDING_EVIDENCE.json, check_rehearsal_binding.py) and the 24k launch kit in `J/in24kr/kit_n_go` (base64-json configs in k/: decode with `json.loads(base64.b64decode(json.load(open(f))['payload']))`). Binding prompts: `J/prompts/build24j.md`, `J/prompts/build24l.md` (rules and ruling conditions hold). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 50 minutes.

## Blocker
In the native q path (launch_r1/production_proof._run on N's kit), student_pilot/r1_handover.py:348-352 compares whole pins (path and sha256) of the preparation recorded in the authenticated donor binding (P's step-400 export-only receipt b467c32b, binding f6b63624) with cfg r1_training.p_run.preparation. The kit localises that pin's path into the job root (/tmp/q_22c714e1/p/q/u/a5bbef1b...), as it must: 24j's confinement (entry.py:27-40, temporary_paths, called from begin_host/stage_host) refuses any read path outside the job root (R1_HOST_PATH_OUTSIDE_JOB_TMP). Only source.preparation.path and binding.preparation.path differ; sha256 a5bbef1b, config identity 9459724f and schema c1-preparation-v1 match. So the production launch refuses P_EXPORT_RUN_BINDING_MISMATCH.

## Fix (tree)
1. In r1_handover's donor binding check, compare the preparation pin by sha256 (keep the existing schema and config-identity comparisons exactly), not by path: a staged copy of the same bytes at another path passes; a different sha256 refuses with the same code. Change nothing else in that function.
2. Find every other comparison on the native q path and the u.py/train path (production_proof._run, r1_persisted.verify/admission, r1_handover.bind_handover/bind_target, r1_components.artifact_binding, carrier_c1_run prepared/train, r1_population.bind_prepared, p_opener_witness) that compares a pin recorded inside authenticated bytes with a pin the kit localises, by whole dict or by path. For each: say whether N's localised config would refuse there (use the decoded kit configs and the evidence JSON; reproduce with a fixture where you can). Fix only those that refuse solely because of the path, the same way (sha256 plus the existing non-path fields), each with a failing-before test. List all you inspected in the report with file:line and verdict.
3. Tests: same sha other path passes; other sha refuses by name; schema or identity mismatch still refuses; a fixture q run with a localised p_run reaches past the handover; all 24j and 24l tests pass; run the launch_r1, r1_population, r1_handover, r1_persisted, r1_loader and entry tests and report pre-existing failures with their cause.

## Conditions
Admission semantics otherwise unchanged: admit(), identity(), row legality, exclusions, routing policy, sampling, scoring, removals, opener rows, the step-544 lineage and the DEFERRED component evidence (ruling 0344Z: no export may claim evidence it does not have) are byte-identical. List every tree file's sha256 before and after; only the files you name differ.

## Outputs
`J/out/HOST24N.patch` (diff against tree_r1_24l), `J/out/TREE24N_SEAL.json` (seal by `student_pilot.source_seal.inventory` + `p3_provenance.digest`, file count), `J/out/UNCHANGED24N.json`, `J/out/PIN_COMPARISONS_24N.md` (item 2 table), `J/out/BUILD24N_REPORT.md` under 30 lines, and `J/out/tree_rebuild_b24n_<seal8>.tar` of work/tree_r1 plus those outputs and 24l's.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only under J. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM.
EOPX
cat > $J/prompts/build24l2.md <<'EOPX'
# Codex build 24l2 of lane tree_rebuild: finish TREE build 24l (its first run died at "model at capacity") and do TREE build 24n in the same tree, one patch

You run once, on trinity-2-28; nobody answers questions. Writable workspace `J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l` only. Two prompts bind you and you do both: `J/prompts/build24l.md` (read it whole) and `J/prompts/build24n.md` (read it whole), with the changes below. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 80 minutes.

## State
- The first 24l run (label tree_rebuild24l) died after partial work: `J/work/tree_r1` differs from `J/work/tree_r1_base` (seal 189df6ac, untouched) in launch_r1/entry.py, launch_r1/production_proof.py and a new tests/test_host24l.py; `J/out/` holds BEFORE24L.json, focused24l.json/.log. Read them; keep what is correct and complete, redo what is not. Do not trust any of it without rerunning its tests.
- build24n.md's base copy `tree_r1_24l` is NOT made: there is one base, `J/work/tree_r1_base` (189df6ac), and one patch for both builds.

## Added by the orchestrator (ORCH GO 2128Z, binding for the 24n part)
1. Comparing by hash is safe only where the bytes at the localised path are known to have that hash. For each comparison you change, show (file:line) where the staged file's sha256 is verified before the handover reads it, and add a test in which the localised path holds different bytes under the same stated sha256: it must refuse.
2. Change only path-only mismatches, each with its own test (same hash at another path passes; another hash refuses; everything else unchanged). List in the report EVERY whole-pin comparison on the q and u.py path, changed or not.

## Outputs (replace both prompts' output lists)
`J/out/HOST24LN.patch` (diff against tree_r1_base), `J/out/TREE24LN_SEAL.json` (seal by `student_pilot.source_seal.inventory` + `p3_provenance.digest`, file count), `J/out/UNCHANGED24LN.json` (every file's sha256 before and after), `J/out/ROUTING_DIGEST_STABILITY.json` (24l item 5), `J/out/PIN_COMPARISONS_24N.md` (24n item 2 table), `J/out/KIT_WIRING_24LN.md` (kit edits needed beyond 24k's wiring; expected none except the new tree tar and seals), `J/out/BUILD24LN_REPORT.md` under 40 lines (24l part, 24n part, tests, pre-existing failures), and `J/out/tree_rebuild_b24ln_<seal8>.tar` of work/tree_r1 plus those outputs.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only under J. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. Admission semantics otherwise unchanged (both prompts' conditions).
EOPX
sha256sum $J/prompts/build24n.md $J/prompts/build24l2.md | cut -c1-16
tmux new -d -s tr15_b24l2 "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh implement $J $J/prompts/build24l2.md --model gpt-6-astra --effort high --label tree_rebuild24l2 --skip-git-check > $J/build24l2_dispatch.log 2>&1"
sleep 15; tmux ls | grep tr15; tail -3 $J/build24l2_dispatch.log
