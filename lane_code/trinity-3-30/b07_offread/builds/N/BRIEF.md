# Build N: the native official read worker (reader as a parameter) for VSI-Bench 5,130 and ReVSI 999 (one-shot Codex build)

You run once on trinity-3-30; nobody answers questions while you run. Write only inside
`/scratch/jjyeung/orch_n30/b07_offread/builds/N/` (at most 4 GB; check `df -h /scratch` before
writing more than 1 GB). Everything else is read-only. No ssh, no network, no Git, no GPU, no Slurm or
Orchard command, no deletion outside your folder, no recursive search of /home or /data* (read named
files only). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -B` (numpy 2.2.6, torch 2.11 CPU,
transformers 5.12, av 15, pytest). Never open a benchmark answer or score to choose anything; the
scorer reads ground truth only when it scores. Prose in Markdown files: plain, complete sentences.

## Why
Step 544 of our 9B spatial student has official numbers for its direct types only (VSI-Bench six
tasks 68.77; ReVSI five categories 64.94). Absolute distance and room size were never read, because
the student answers them through calls (`<ground ...>`, `<gap ...>`, `<ground mode="room">`) that a
reader must serve. This worker reads ALL items of a benchmark with calls served, so the first
eight-task VSI-Bench and seven-category ReVSI numbers of this lineage can exist. Two readers will
serve calls and the worker takes the reader as a parameter:
- **harness**: the registered harness backend of kit C8r (Python runtime: SAM 3 proposals, fitted
  selector, G3T lifting x the checkpoint's own scale, depth cut, box rule, room rule, gravity guard),
  with every value taken from the P8 freeze file (`official_reads/ROUTED_PATH_FROZEN_<date>.md`, not yet
  written). Its numbers are labelled "harness-served, not an end-to-end result".
- **e2e**: the end-to-end reader of lane b04 (`/scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/`,
  one entry `generate(frames, question)`, towers inside the call, artifact manifest, audit hook). It is
  still being built; the worker gets a socket and fixture tests now.
Read `/data2/jjyeung/agent_project_data/distill_design/ARCHITECTURE_CURRENT.md` (the model and its
call grammar) first.

## Binding rulings (USER and orchestrator, 2026-11-16; these win over the rest of this brief)
- ReVSI first. Build, test and rehearse the `revsi999t32` path to completion before `vsibench5130`; if
  you run short of time, ReVSI is finished and VSI-Bench is listed as not done in NATIVE_KIT_READY.md.
- Frame count is a parameter. Add `--frames {32,64}` and `--frame-layout {duplicate,spread}` and bind
  them through `offkit.frames.bind_frames(count, layout, export=..., export_layout=..., override_reason=...)`
  (new module, tests in `kit/tests/test_frames.py`). Store its dict as `read_config.frames` in the binding
  (orchkit-read-v1 `frames` form) and pass count and layout to the evaluator's `sample_video(max_frames_num=)`
  and `frame_list(..., layout, frames=)`. Step 544 trains on 32 duplicated anchors, so 64 on step 544 is
  refused unless an override reason is given; a D0 `.done` export supplies its layout. The G3T dense read
  stays as pre-registered. SIZING.md states the cost of 64 (spread) against 32 (duplicate): visual tokens,
  tower seconds, decode seconds and H100-hours per benchmark.
- Answers are the model's. No reader, wrapper, server or post-processor converts units or reformats an
  answer; the official scorer's strict parse of the model's final answer is the only step between the
  model and the score. If C8r or V1c code converts or rewrites an answer, disable that path in this kit,
  list file and line in DIFF, and add a test that a model answer reaches the scorer byte-equal. Tower
  outputs a call returns (metres, boxes) are call responses and stay as C8r serves them.
- One reader core. Lane b04 (`/scratch/jjyeung/orch_n30/b04_e2ehook/e2e_reader/`) owns the end-to-end
  reader core and the shared harness `tools/orchkit/reader/` will own read drivers. Do not fork a scorer
  or a rule: scoring, aggregation, labels and binding are imported from `offkit` (which b04 also
  imports). Keep the worker's own code to staging, phase orchestration and journals, put it behind one
  `Reader` interface (`direct`, `harness`, `e2e` implement it; `e2e` delegates to b04's `generate`), and
  write in NATIVE_KIT_READY.md how each module would map onto `tools/orchkit/reader/read.py` and an
  orchkit-read-v1 config (`briefs/eff/INTERFACES.md` under
  `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/`; read it once).
- Build R (`/scratch/jjyeung/orch_n30/b07_offread/builds/R/`, direct-only re-bind, finished) is the
  direct mode; reuse its staging, Orchard naming, governed fetch and rehearsal patterns rather than
  writing new ones, and do not modify its files.

## Sources (read-only)
1. Binding and report layer (import, do not copy or change): `/scratch/jjyeung/orch_n30/b07_offread/kit/offkit/`
   - `bind.bind(benchmark, export, reader, ...)` returns BINDING (groups, items, arms, export, reader,
     freeze_values for harness); `report.ReadMode/aggregate/label_report/render/write`;
     `adapt_native.unify(row)` maps a C8r-schema journal row to the unified record. Tests in `kit/tests/`.
2. Kit C8r (the harness backend of native job 170056): `/scratch/jjyeung/orch_n30/b07_offread/in/c8r/`
   (code; `native/out2/nomdg.py` serves ground/gap/room calls from a geometry manifest and a mask cache;
   `perception.py`, `routed.py`, `reader_policy.py`, `gravity_guard.py`, `geometry.py`, `mask_kit/`).
   Kit docs: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/native_r2/c8r_kit/`
   (C8_READY.md, PIN_TABLE_C8R.md, GUARD_CALL_SITES.md, DECISIONS_C8R.md).
3. Kit V1c (VSTI native read built on C8r; runs the frozen G3T tower and the checkpoint's scale and
   gravity preparation INSIDE the job on the read's own frames; Orchard packet fixes; proof, canary,
   deadline budget): `/scratch/jjyeung/orch_n30/b07_offread/in/v1c/` (code extracted at `code/`, docs in
   `out/`: RUN_ORCHARD.md, DECISIONS.md, LEGALITY.md, SIZING.md, DIFF_vs_C8R.patch).
4. In-job SAM 3 proposals: the K1 kit's tower phase (SAM 3 + G3T per capture, writes `tower.npz` and
   `candidates.json`): `/scratch/jjyeung/orch_n30/k1_ops6/bundle/sj/orch_cd/k1_build/work/kit_k1a/`
   and `.../sam3_tower/`, `.../grd_selector/`; sample outputs at
   `/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2/<capture>/`. C8r's mask-cache format:
   `in/c8r/sj/orch_cd/evalx/work/milestone/orchard_native/MASK_CACHE_C8_BOUND.json` and `nomdg.py`.
5. Official direct kits (items, media manifests, frame plan, official scorer):
   VSI f42aa1a4 `/scratch/jjyeung/orch_n30/b07_offread/in/x27/kit/` (package.tar; cohort/meta_5130.jsonl,
   cohort/MEDIA_MANIFEST.json, cohort/frame_plan.py) and ReVSI ea1a1b2d
   `/scratch/jjyeung/orch_n30/b07_offread/in/kit_revsi/` (inputs/i1.json = the 999 items,
   inputs/REVSI_PUSH_FILES.json, media/NEED_261.json, reader/evaluator/evalpath/official.py scorer).
   Frame path for the model: PyAV rgb24, 32 floor-uniform anchors `k*(N-1)//31` at stream fps, each
   duplicated (the accepted direct reads). G3T reads the same video densely (64 frames) as in the
   pre-registration (`/data2/jjyeung/agent_project_data/distill_design/REFREEZE_PREREGISTRATION_20261115.md`,
   "Fixed without re-selection").
6. Job 170056 (step 544 native routed read on dev-S1, C8r backend), return extracted read-only at
   `/scratch/jjyeung/orch_n30/b01_d0guard/work/ret544/` (native/paired/results/items.jsonl, R1.json,
   request.json, geometry/*.npz, metadata/CONFIG.json); record
   `/data2/jjyeung/agent_project_data/distill_design/NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md`.
7. The reviewed D0 export stager (for `--export done:`): `/scratch/jjyeung/orch_n30/b07_offread/in/readk/kit/launcher/export_stage.py`.
8. Rules that bind reports: amendment 3 (`/data2/jjyeung/agent_project_data/distill_design/REFREEZE_AMENDMENT_3_D1_D2_ROUTE_DECISIONS_20261116.md`,
   items 5 and 6: room calls served as primary with the label; unserved room as secondary arm),
   the pre-registration's fallback section (primary = as served, refusal or non-answer scores 0;
   secondary = reader-side fallback to the direct-reader answer), B6 answer 2
   (`B6_GROUNDING_DESIGN_20261115.md`: the selector fitted on VSTI/ReVSI rooms may not serve a ReVSI mask
   read; the K1 refit must; `offkit.bind` already refuses that binding).

## What to build (in builds/N/)
1. `offnative/` package and one launcher `native_read.py` (`prepare`, `submit-command`, `record-submission`,
   `fetch`, `report`), parameters as `offkit.bind`: `--benchmark {vsibench5130,revsi999t32}`,
   `--export {step544|done:<path>}`, `--reader {harness:<sha256>|e2e:<sha256>}` (`direct` is build R's),
   `--freeze-file`, `--e2e-manifest`, `--eat1-report`, `--init-selection`, `--ledger`,
   `--mode {proof,production,fixture}`. BINDING.json stays on Trinity (it carries benchmark words); the
   Orchard packet carries only opaque names and the binding sha256.
2. Job phases, in order, each writing a receipt; a phase failure ends the job with its receipt:
   a. stage: export by sha256 (step 544 as C8r/V1c stage it; a D0 export through readk's stager), towers
      (G3T as V1c; SAM 3 weights by sha256 as the K1 kit stages them), media by the benchmark's manifest
      (VSI 288 videos; ReVSI needs 302 videos for all 999 items: the 261 of NEED_261 plus 41 for the
      absolute-distance and room items; write NEED_302.json from REVSI_PUSH_FILES.json and say which 41
      files must still be uploaded).
   b. frames: the accepted direct frame path for the model; dense frames for G3T.
   c. towers on the benchmark's own videos (harness reader): G3T geometry plus the export's own scale
      and gravity preparation (V1c / C8r code unchanged), and SAM 3 proposals for every object name
      that a call can name on that video, written in C8r's geometry-manifest and mask-cache formats so
      `nomdg` serves calls unchanged. No file from another frame path is used. (The e2e reader runs its
      towers inside `generate`; this phase is then empty.)
   d. in-job identity proof BEFORE any official item is decoded: ten dev-S1 items of job 170056
      (5 camera, 5 absolute distance; fixed list chosen by sorted key hash, recorded) decoded with the
      step-544 export and the 170056 backend values; tokens, calls, responses and answers must equal
      170056's journal. For the e2e reader the camera items must be identical and the distance items are
      reported (b04's selector and scale heads change them by design). A mismatch ends the job with the
      receipt; nothing official is decoded.
   e. canary: ten official items (at least one per group with a call type among them), strict score
      recomputation and byte-equal response replay as V1c's canary.
   f. read: every item of the benchmark through the bound reader with calls served (one `generate`
      per item for e2e; C8r's decode loop for harness). Harness arms: primary as served; secondary
      room unserved (a second decode of the room items with calls unserved); secondary fallback
      computed reader-side (primary with every refused or non-answered routed item replaced by the
      unserved decode's answer for that item; so the unserved decode covers distance items too). The
      e2e reader has one arm.
   g. score each item with the official scorer of its benchmark (strict parse as the direct kits);
      write unified records (offkit schema) per arm, merged journals, completion.
   Work that does not fit one GPU stream: several decode worker processes on the one H100 are allowed
   (each with its own request and journal; a merge checks that their union equals the full id list with
   no duplicate). Keep C8r's deadline budget, item-start cutoff and return reserve (V1c S7).
3. Orchard: job name `a15_cot_ap` + opaque hex; no project, benchmark, dataset, model or method word
   in any Orchard path, name, argument or log line; token meanings only in
   `builds/N/work/ORCHARD_LEDGER.jsonl`. Packet under a new opaque pool directory under
   `/project/community/jjyeung/okh7/` (propose it), sbatch resources on the command line
   (`--gres=gpu:1 --cpus-per-task=16 --mem=200G`), `--output=/dev/null`, no hard links in input tars,
   staged `root/bwrap` (V1c F3). Returns: pool plus `gs://cmu-gpucloud-jjyeung/q8/<opaque>/<token>/`.
4. `report` (Trinity side): from a fetched return, run `offkit.report` per arm with `label_report`
   (reader dict from BINDING.json, arm and role names `primary`, `secondary_fallback`,
   `secondary_room_unserved`), so the first line of every report names the reader and its EAT-1 state
   and every harness number carries "harness-served, not an end-to-end result". Denominators are 5,130
   and 999; an unread type is impossible (`offkit.report.check_cohort` raises).
5. `RUN.md` (operator commands, governed transfers for every input above 20 MB, poll once a minute,
   fetch through the IO governor) and `SIZING.md`: H100-hours per benchmark and reader from measured
   rates (job 170056's per-item `seconds`, V1c's tower 3.8 s per scene, K1's SAM 3 seconds per name from
   its sample outputs or `sam3_tower/out/BATCH_MEASUREMENTS_FINAL.json`), with the number of names per
   video counted from the item lists (names only, no answers). The queue's expectation is 3 to 6
   H100-hours for VSI-Bench and 1 to 2 for ReVSI; say if the measured rates disagree.

## Tests (logs in builds/N/out/)
- Fixture runs of both reader modes on a tiny model, end to end (stage from local stand-ins, frames,
  towers with synthetic tower arrays as V1c's rehearsal did, proof against a fixture journal, canary,
  read of two items per subtype, score, merge, report). The direct mode's fixture is build R's.
- Whole-worker CPU rehearsal with the production CONFIG changed only in transport (lesson of K1 job
  170193), for each benchmark on two videos; record executed lines and list Orchard-only lines that did
  not run.
- The identity proof on CPU: replay 170056's ten chosen items through the decode loop with recorded
  logits or forced token ids (as lane b04's `tests/replay_170056.py` does) and show equality; plant one
  changed response and show the proof fails and no official item is decoded.
- Denominators: the read's id list equals the 5,130 / 999 cohort; dropping one id or one type fails.
- Arms: a fixture with a refused distance item shows primary 0, fallback = unserved answer's score.
- Binding: the launcher refuses a harness reader without the freeze file and a ReVSI harness read
  without a K1-refit selector (from offkit.bind), and an e2e reader without an EAT-1 PASS in production.
- First batch of the real export: not possible on this node; the in-job proof and canary stand in, and
  RUN.md says so.

## Deliver
`out/NATIVE_KIT_READY.md`: hashes of every shipped file and the code tar, the phase list, tests and
their results, executed-line census, DIFF against C8r and V1c (file and line, one sentence per
change), what is not executed, open inputs (P8 freeze file, the 41 ReVSI videos, SAM 3 weights path on
Orchard, b04's artifact manifest), SIZING.md and RUN.md pointers. Do not submit or upload anything.
