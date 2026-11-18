<!-- recovered by seal_plan: transcript=71f94277 line=3544 utc=2026-11-11T15:07:26.554Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; for L in leg_s1_rehearsal geo_bakeoff vla_integ; do mkdir -p $L/events $L/inbox $L/work $L/out; done
cat > leg_s1_rehearsal/BRIEF.md <<'EOF'
# leg_s1_rehearsal (Codex): rehearse the next training leg end to end on CPU with a tiny model, and find every silent fallback
Host trinity-2-18. Your folder: /scratch/jjyeung/orch_cd/leg_s1_rehearsal (write only here). Everything else is read-only: copy what you change into work/.

## Why
The user (2026-11-11): "we should preemptively develop all this code and test it! so when it's time to actually run, we don't need to debug and waste time!" The next training leg of our 9B student (Qwen3.5-9B LM + ViT, frozen G3T geometry tower, grounding decoder, routed "head-backed" programs that call the student's own heads inside generate()) stacks several new pieces. GPUs are held by another project until about 20:00Z today; when they free, the leg must start without debugging. Today each piece has unit tests, but nothing runs the whole chain in one go, and reviews keep finding the same class of defect: a path that fails or mismatches and silently falls back (a cold connector, a substituted row, an evaluator that loads an export without its new tensors, a test that patches out the risky call).

## Inputs (read-only)
- Student tree with the v3.14 programs: /scratch/jjyeung/orch_cd/integ_v314/work/tree_v314 (8.5 MB; student_pilot/ holds the trainer: carrier_c1_run.py, carrier_c1_sweep.py, carrier_c1_data.py, batches.py, g3t_online.py; head_programs.py and headcall/ hold the routed runtime; tests/; verifykit/). Record: /scratch/jjyeung/orch_cd/integ_v314/out/RECORD.md.
- Fusion connector tree (second pass still running; use it only if /scratch/jjyeung/orch_cd/gf1_fusion/events holds a RESULT newer than 14:32Z today, otherwise skip it and say so): /scratch/jjyeung/orch_cd/gf1_fusion/work/tree_gf1, review /scratch/jjyeung/orch_cd/gf1_fusion/REVIEW_VERDICT.md (read it: items 3, 4, 6 and "Missing tests" are examples of what this rehearsal must catch).
- How the leg is launched on the Orchard cluster: /scratch/jjyeung/orch_cd/orchard_cp2/STATUS.md (newest CURRENT STATE block) and the kit folder /scratch/jjyeung/orch_cd/orchard_cp2/work/c1mix_v313 (list one level).
- Evaluation side: benchmark_eval/ and orchard_eval/ inside the tree if present, and /scratch/jjyeung/orch_cd/evalx/STATUS.md (newest CURRENT STATE block) for how exports are loaded and scored.
- Python: /scratch/jjyeung/envs/p1cpu/bin/python (CPU torch). Real tokenizer files may be read from wherever the tree's tests already read them; do not load real 9B weights.

## Build
1. `work/rehearse.sh <tree>`: one command, CPU only, under 20 minutes, that runs the real code paths of the tree on a tiny random-weight model of the same architecture family (the tree's tests already build tiny models; reuse those fixtures), with nothing mocked or patched out between stages:
   a. build a small training receipt (a few dozen rows covering every row kind the leg mixes: VQA rows with head-backed v3.14 traces of each program type, pose rows, depth rows, grounding rows; use rows that already exist on local disk under /scratch/jjyeung/orch_cd — list one level at a time — or generate them with the tree's generator);
   b. prepare, then train 3 optimizer steps at world size 2 (two CPU ranks) through the launcher path the Orchard kit uses;
   c. save, resume, and check that step 3 after resume equals step 3 uninterrupted (state the tolerance);
   d. export the checkpoint the way the leg exports it;
   e. load that export through the evaluator's own loader and init spec, and assert that every trained tensor arrived (fail closed if any group is missing, zero or re-initialised);
   f. run generate() with routed programs on 10 benchmark-shaped items (each program type at least once) so that the head calls, the calculator and the answer parse all execute, then score them with the evaluator's scorer;
   g. print one table: stage, pass or fail, seconds, and the evidence file.
2. A silent-fallback audit of the same chain: every `except` that continues, every default that hides a missing key, every substitution or skip, every warm-start or init path that can fall back to cold weights, every test that patches the function under test. For each: file:line, what it hides, whether the rehearsal now trips it (add a negative case that proves it: delete a tensor group, drop a row field, ask for a program version the checkpoint lacks, point init at a wrong artifact). Rank by the GPU hours a silent occurrence would waste.
3. Fixes as patch files under out/ (never edit the source trees), each with a test, for every finding that would waste a training leg.

## Limits
- CPU only; no GPU, no ssh, no network, no git commands, no deletion commands of any kind (a hook blocks them; leave files in place and list them).
- Disk: run everything under `ulimit -f 204800` (no file above 200 MB) and keep this folder under 1 GB; the tiny model's checkpoints must be a few MB. A test last week saved 166 GB of checkpoints and filled this disk: never save a real-size model.
- /home and /data* are overloaded network storage: open named files only; no recursive search or listing there; write nothing there.
- Temporary files go under work/tmp, not /tmp.
- You cannot ask questions. Where something is ambiguous, choose the option that exercises more of the real path, and write the choice down.

## Deliver
out/REHEARSAL.md (the table, how to rerun, what each stage really executed, what was skipped and why), out/SILENT_FALLBACKS.md (ranked), out/*.patch with tests, and a final message of at most 15 lines. Also write events/<UTC stamp, date -u +%Y%m%dT%H%MZ>_RESULT_leg_s1_rehearsal.md with the same 15 lines.
EOF
cat > vla_integ/BRIEF.md <<'EOF'
# vla_integ (Codex): run the four VLA packages together in one process on CPU, end to end, with a tiny model
Host trinity-2-18. Your folder: /scratch/jjyeung/orch_cd/vla_integ (write only here). Everything else is read-only: snapshot what you need into work/snap/ (record the copy time) and never edit another lane's folder.

## Why
The user (2026-11-11): "we should preemptively develop all this code and test it! so when it's time to actually run, we don't need to debug and waste time!" Four lanes each built one piece of the VLA fine-tuning experiments against one shared schema, and each passes its own tests. They have never run together. Find what breaks when they do.

## The pieces (read each README or STATUS.md first; list one folder level at a time)
- Schema (the contract): /scratch/jjyeung/orch_cd/vla_design_review/VLA_SCHEMA.md (v2), schema_examples.py (worked examples and checks), SCHEMA_CHANGES.md. Design: /scratch/jjyeung/orch_cd/vla_design_review/ (local copy of VLA_ACTION_HEAD_DESIGN_20261111.md).
- Action heads: /scratch/jjyeung/orch_cd/vla_heads/work/vla_heads (regression head, flow-matching expert, token codecs; 137 tests).
- "Where" provider (object and waypoint geometry from the student's own heads): /scratch/jjyeung/orch_cd/vla_where/work (73 tests).
- Navigation runner (R2R-CE): /scratch/jjyeung/orch_cd/vla_nav/work/navrun (58 tests; its env is described in /scratch/jjyeung/orch_cd/vla_nav/STATUS.md). Note: its prompt encoder navrun.encode is being changed today to the default thinking template; take the snapshot after reading vla_nav/events for a RESULT newer than 15:00Z, or snapshot now and make your tests independent of which template is in force (assert train-side ids equal eval-side ids, not a literal string).
- LIBERO kit: /scratch/jjyeung/orch_cd/vla_libero (STATUS.md, out/HEADS_HOOK.md, work/). The LIBERO simulator stack lives on another cluster; on this node use recorded observations or the kit's replay fixtures.
- Dynamics probe kit (optional consumer of the provider): /scratch/jjyeung/orch_cd/dyn_probe/README.md.

## Build
`work/run_integ.sh`: one command, CPU only, under 15 minutes, re-runnable against the live folders, that for each arm in the design (LIBERO: B1 and U1 with the regression head and with the flow-matching expert; navigation: N1 and NU with token outputs) runs, with a tiny random-weight backbone of the right interface:
rows from the lane's own row builder -> schema validation -> the provider's "where" features (stub towers allowed only where real weights would be needed; say which) -> encode -> forward -> loss -> one optimizer step -> save (a few MB) -> load -> policy or policy server -> one environment step or one replayed observation -> action decoded and un-normalised -> the lane's metric code on a two-episode fixture.
Check across packages, not within: tensor shapes, dtypes and units at every hand-off against the schema; action normalisation statistics written by one package and read by another; camera and frame conventions (wrist and agent views, the mirrored-camera rule, quaternion order, metres); the provider's failure and occlusion outputs reaching the head as the schema says; config keys one package writes and another never reads; version tags (`vla_schema_v2`) refused when wrong.
For every break: file:line in both packages, which side departs from the schema, and a patch file under out/ with a test (do not edit their folders).

## Limits
- CPU only; no GPU, no ssh, no network, no git commands, no deletion commands of any kind (a hook blocks them).
- Disk: run under `ulimit -f 204800`; keep this folder under 1 GB; never save a real-size model. Temporary files under work/tmp, not /tmp.
- /home and /data* are overloaded network storage: open named files only; no recursive search or listing there; write nothing there.
- You cannot ask questions: choose the option that exercises more of the real path and write the choice down.

## Deliver
out/INTEG.md (per arm: stages run, pass or fail, what was stubbed), out/BREAKS.md (ranked by the GPU hours a break would waste), out/*.patch, events/<UTC stamp>_RESULT_vla_integ.md and a final message, each at most 15 lines.
EOF
for L in leg_s1_rehearsal vla_integ; do tmux new -d -s cx_$L "bash /scratch/jjyeung/orch_cd/orch_tools/codex_local.sh implement /scratch/jjyeung/orch_cd/$L /scratch/jjyeung/orch_cd/$L/BRIEF.md --model gpt-6-astra --effort high --skip-git-check --label $L > /scratch/jjyeung/orch_cd/$L/dispatch.out 2>&1"; done; sleep 4; tmux ls | grep cx_ | cut -c1-60; pgrep -u jjyeung -af "codex exec" | grep -c "leg_s1_rehearsal\|vla_integ"; date -u +%H:%M:%SZ