# Build H1-kit-8: package the H1-0 own-arm read for one Orchard general job (CPU only here; nothing is submitted)

You are a Codex builder for lane h1_headsft on Trinity node trinity-3-30. Workspace `K=/scratch/jjyeung/orch_n30/h1_headsft/kit`
(write only inside K). Read `K/BUILD_REPORT.md` sections "Build 7" and "Build 7 lane follow-up" and `K/h1eval/h10/RUN_H10.md`
first; keep everything that passes. Work autonomously; record ambiguous choices (conservative option) in a new section
"Build 8" of `K/BUILD_REPORT.md` and continue.

## Rules for the build (binding)
- Trinity rules: never run recursive grep/find/du/ls -R or any search over `/home` or `/data*`; read named files there
  only, in bounded parts. No Git. No ssh/scp/rsync/network (no Orchard access from you). No GPU. No deletion or
  modification outside K; inputs are read-only; never kill processes. Nothing is submitted or uploaded.
- Disk: this node is BELOW its 200 GiB floor. Temporaries and pytest basetemps under ONE directory `K/tmp/b8/`; never
  copy the tree, a kit, b04's code or model files; add under 20 MB (the template copy already in K/tmp/b8/readk_tmpl
  does not count). Report the size you added.
- Python `/scratch/jjyeung/envs/p1cpu/bin/python -B` with `CUDA_VISIBLE_DEVICES= PYTHONPATH=K/tree:K`, <= 32 GB RAM,
  16 threads; pytest flags as in Build 7 with `--basetemp=K/tmp/b8/<name>` and `LANE_TEST_OUTPUT=K/tmp/b8`.
- Orchard naming (binding): the Slurm job name is `a15_cot_ap` + 11-16 random hex, no further underscore. No job name,
  comment, workdir, path, argument, environment variable or log name visible to Slurm may contain "split" in any case or
  any benchmark, dataset, model or method word (revsi, vsibench, scannet, arkit, distill, qgen, sam, qwen, h1, h10, head,
  routing, faithful, ...): use opaque random tokens and keep a token map in `K/orchard_h10/TOKENS.json` (Trinity only).
  In-job contents of shipped source and item files are exempt (ORCH ruling).
- The model converts units and formats numbers itself; nothing rewrites answers.

## Why and what
The orchestrator moved H1-0 (the step-544 own-arm read of dev-S1 routed items, baseline + registered perturbations,
`K/items/devs1_routed.json`, read plan in RUN_H10.md) to ONE Orchard `general` job (1 node, 4 GPUs at most, ~5 H100-hours
budget, a `--time` the operator sets) once GPUs return. Type order (ORCH): camera_displacement, camera_rotation,
camera_movement_direction, object_abs_distance, then room; baseline and that type's modes together (`--types`), so every
type that lands has usage (M3). Shard across the job's GPUs (one process per GPU, `--shard i/n` within each type) and stop
cleanly at the time limit with every completed record fsynced; a resubmission resumes.

## Template (read, bounded)
`K/tmp/b8/readk_tmpl/` is cont_ops's D0 read kit (an Orchard read job that ran 43 minutes on general and returned its
results): `launcher/{orchard_launcher.py,orchard_job.py,orchard_stage.py,export_stage.py,return_io.py,stdout_transfer.py,
trace_runtime.py,ORCHARD_ASSETS.json,MODELS.json,TRANSPORT.json}`, `reader/` and a real built job
`build/a4cadd8934b/{BATCH.sh,CONFIG.json,SUBMISSION.json,SUBMIT.cmd}`. Follow its patterns for staging, bwrap, opaque
naming, vnice/terminator handling, result return and ledgers. Reuse its code by import or by pinned copy inside the
package; do not re-invent transport.

## Deliver `K/orchard_h10/`
1. `build.py` that produces a package directory (code tar of K's `tree/`, `h1eval/`, `items/devs1_routed.json`, `auth/`,
   plus b04's reviewed reader code from `/scratch/jjyeung/orch_n30/b04_e2ehook/{e2e_reader,heads}` pinned by sha256,
   BATCH.sh, CONFIG.json, SUBMIT.cmd with an opaque token) and a `STAGING.md` that lists every input the job needs on
   Orchard with its expected sha256 and whether the template's ORCHARD_ASSETS.json shows it already there: the step-544
   export (artifact 1d6eeb28..., heads 8bb5e151..., full_weights 211ae87b...), the dev-S1 frames that Orchard job 170056 read
   (b04's FRAMES.json / DENSE_MANIFEST pins: `/scratch/jjyeung/orch_n30/b04_e2ehook/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json`,
   `.../evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json`), G3T, SAM 3 source/checkpoint/receipt,
   the selector head run_iso (6d97c524...), python env with torch+torchvision+transformers 5.12+scipy. Anything not
   provably on Orchard goes to `OPEN_INPUTS.md` with its size and the governed transfer it needs.
2. In-job runner: per GPU one `h1eval.h10.launch` process per type in the ORCH order, own arm only, registered modes,
   `--shard i/n`, under the template's vnice/terminator rules; output journals, projection.json and a final tar for the
   template's return path; a time guard that stops before `--time` with a margin.
3. CPU rehearsal here with stand-ins (tiny loader as Build 7's probes), under a production-style root outside
   /dev/shm and pytest basetemp, proving: naming opacity (scan every Slurm-visible string against the word list above),
   per-type ordering, sharding, resume, time-guard stop, result tar layout. Tests in `K/tests/test_build8.py`.
4. Rerun the full kit suite (Build 7: 110 passed incl. tests/test_build7_types.py); all must pass. Write "Build 8":
   files, commands, results, size, the exact operator steps (stage, CPU check on the login node, submit, fetch), and a
   GUESS of decode seconds on H100 (b04 measured 25-120 s/item on A6000 with SAM 3 in the call).
