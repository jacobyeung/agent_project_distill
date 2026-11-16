# Build R: direct-only re-bind of the official direct kits to a selected D0 export (one-shot Codex build)

You run once on trinity-3-30; nobody answers questions while you run. Write only inside
`/scratch/jjyeung/orch_n30/b07_offread/builds/R/` (at most 2 GB). Everything else is read-only.
No ssh, no network, no Git, no GPU, no Slurm or Orchard command, no deletion outside your folder,
no recursive search of /home or /data* (read named files only). Python:
`/scratch/jjyeung/envs/p1cpu/bin/python -B` (numpy 2.2.6, torch 2.11 CPU, transformers 5.12, av, pytest).
Never open a benchmark answer or score to choose anything; tests use fixtures and the accepted
returns only where named below. Prose in Markdown files: plain, complete sentences, no fragments.

## Goal
One Orchard `general` 1-H100 job per (benchmark, export) that reads the DIRECT groups of the official
items with the accepted direct reader, for the one D0 export that the next-leg init rule selects
(`/data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_INIT_RULE_20261116.md`, item 7), so that
export is read once on exactly the items, frames, budgets and answer policy of step 544's accepted
direct reads:
- VSI-Bench: six tasks, 4,008 items, 288 scenes (kit f42aa1a4, accepted job 170008, 68.77).
- ReVSI official999 tier 32: five categories, 679 items, 261 scenes (kit ea1a1b2d, accepted job 170037, 64.94).
Absolute distance and room size are not read by this reader (they are routed types of this lineage).

## Sources (read-only)
1. VSI kit f42aa1a4: `/scratch/jjyeung/orch_n30/b07_offread/in/x27/kit/` (package.tar = the sealed
   package, sha256 in KIT_SHA256; DIFF.md, PROOF_JOB.md, REPORT.md, cohort/, parity/). Extract
   package.tar into your folder to work on a copy.
2. ReVSI kit ea1a1b2d: package `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/evalx27/kit_revsi_ea1a1b2d/package.tar`
   (already extracted read-only at `/scratch/jjyeung/orch_n30/b07_offread/in/kit_revsi/`); its DIFF.md
   (vs f42aa1a4) and F1_EVIDENCE.md are in `/scratch/jjyeung/orch_n30/b07_offread/in/x27/kit_revsi/`.
   Its media on Orchard: `/project/community/jjyeung/okh7/313db5a47f11ff0c/` (261 files).
3. The reviewed D0 direct read kit `readk` (cont_ops; review `.../orch_n30/events/review_d0r/CONFIRMED_read_kit.md`):
   `/scratch/jjyeung/orch_n30/b07_offread/in/readk/` (kit/launcher/export_stage.py stages a D0 export from
   its plain-text `.done` record `<object> <bytes> <sha256>`: four GCS parts, whole-tar sha256 before
   extraction, build_t5 admission, the unchanged export checker in full mode; REPORT.md, DIFF.md).
   readk = f42aa1a4 with that stager and the dev-S1 item set; you need its stager, not its items.
4. The kit's binding and report layer (written by the lane; import it, do not copy or change it):
   `/scratch/jjyeung/orch_n30/b07_offread/kit/offkit/` (bind.py: `bind(benchmark, export, reader, ...)`,
   `ledger_append`; adapt_direct.py: `from_return(a0_dir, 2048)`; report.py: `ReadMode`, `aggregate`,
   `label_report`, `render`, `write`). Its tests: `kit/tests/`.
5. Accepted returns for tests: `/scratch/jjyeung/orch_n30/b07_offread/in/ret_vsi/` and `.../in/ret_revsi/`
   (extracted result.tar.gz of jobs 170008 and 170037).

## What to build (in builds/R/)
1. `kit/`: ONE launcher `rebind.py` with subcommands `prepare`, `submit-command`, `record-submission`,
   `fetch`, `report`, built from the two official kits with the smallest change:
   - parameters `--benchmark {vsibench5130,revsi999t32}`, `--export {step544|done:<path>}`,
     `--init-selection <json>` (required for done:), `--ledger <path>` (default
     `/scratch/jjyeung/orch_n30/b07_offread/out/OFFICIAL_READ_LEDGER.jsonl`), `--mode {proof,production}`,
     `--token`, `--destination`. `prepare` calls `offkit.bind.bind(..., reader='direct')` and writes
     BINDING.json (with its binding_sha256) into the Trinity destination only; the ledger is appended
     only in `record-submission` (production). BINDING.json carries benchmark words, so it never goes
     to Orchard: the packet carries the binding_sha256 and the export sha256 under opaque names, and the
     job refuses at start if the staged export's sha256 differs from the bound one. Add no new
     project, benchmark, dataset, model or method word to any Orchard-visible name, argument or log line
     beyond what the accepted packages already carry (list any that the accepted packages carry).
   - `--export step544`: the payload, staging and items are byte-identical to the accepted kit of that
     benchmark except the binding file and the token (show this with a byte comparison in a test).
   - `--export done:`: replace the step-544 export staging with readk's `export_stage.py` path
     unchanged (same lineage allowlist run 359fcc3c / 8865619b, steps 100..1000, same checks). Nothing
     else changes: items, media roots, frame plan (PyAV rgb24, 32 floor-uniform anchors each
     duplicated), processor, budgets ON16k/B2048/B4096 with B2048 primary, answer policy, scorer.
   - In-job proof before decoding: the accepted kits' prompt-byte parity (parity/ACCEPTED20.json and
     the processor check) must pass; on failure the job ends with a receipt and decodes nothing.
   - Orchard naming: job name `a15_cot_ap` + opaque hex; no project, benchmark, dataset, model or
     method word in any Orchard path, name, argument or log line. Token meanings go only into
     `builds/R/work/ORCHARD_LEDGER.jsonl`. Returns: a new opaque pool under
     `/project/community/jjyeung/okh7/` (propose the name) plus `gs://cmu-gpucloud-jjyeung/q8/<opaque>/<token>/`,
     with the pool write test, lock and size limit of readk.
   - sbatch resources on the command line (`--gres=gpu:1 --cpus-per-task=16 --mem=200G`), not inside the
     batch file; no hard links in any input tar (lessons of VSTI job 170209).
   - `report`: from a fetched return, build unified items with `offkit.adapt_direct.from_return` and
     write labelled reports with `offkit.report` (reader dict `{'kind':'direct','id':'direct kit <8 hex>',
     'eat1':{'passed':None}}`, the export dict from BINDING.json, arm `primary`), for B2048 (primary) and
     ON16k/B4096 (secondary). The first line of every report is the offkit first line.
2. `DIFF.md`: every changed line against the accepted package of its benchmark, classified PATH/ENV or
   BEYOND as readk's DIFF.md does, one table per benchmark.
3. `RUN.md`: exact operator commands (prepare, governed upload if any input exceeds 20 MB, submit,
   poll at most once a minute, fetch through the IO governor, report), for both benchmarks, with a
   time and disk estimate per job from jobs 170008 (35 min) and 170037 (13 min) plus D0 export staging.

## Tests (logs in builds/R/out/)
- The step544 path reproduces the accepted numbers when `report` runs on the accepted returns:
  VSI six-task 68.77 [66.5, 71.0] and ReVSI five-category 64.94 [61.3, 68.4] (exact floats against
  report/B2048.json of each return).
- Binding: done: without init selection, with a non-matching selection, a second D0 milestone in the
  ledger, a malformed `.done` line, and a tampered BINDING.json are each refused (prepare or job start).
- Whole-worker CPU rehearsal for each benchmark with the production CONFIG changed only in transport
  (staging from local stand-ins, a tiny or fake model as the official kits' proof/fakes.py does): stage,
  prompt parity, decode of two items per group, merge, publish, fetch, report. Record which code lines
  ran (coverage) and list Orchard-only lines that did not.
- Item membership: the job decodes exactly 4,008 / 679 ids, equal to the accepted cohorts, and no
  item of absolute distance or room size.

## Deliver
`out/REBIND_READY.md` (hashes of every file you ship, the package tar sha256, test results, DIFF
summary, RUN.md pointer, time estimates, what was not executed), `out/package_vsi.tar`,
`out/package_revsi.tar`. Do not submit anything.
