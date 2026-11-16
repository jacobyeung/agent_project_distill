# Build: Orchard read job for D0 milestones (steps 100 and 200) with F1/F2 verdict script

You build code only. Work only inside /scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/ (write here; everything else is read-only). No ssh, no GPU, no network, no Git, no deletion, no Slurm command, no recursive search of /home or /data* (read named files only). Python: /scratch/jjyeung/envs/p1cpu/bin/python, or the evalx27 kit venv named in its PROOF_JOB.md.

## Goal
A one-H100 Orchard `general` job that reads one D0 milestone export with the reviewed direct reader that produced the accepted step-544 packet e193c2a3c (Orchard job 169526, reader b8ebab38). It reads the e193 item set for the direct types plus the 150 facing twins (away 150, toward/forward 150, reported apart) and returns per-item results. A Trinity-side script then computes F1 and F2 against step 544 and the stop-rule verdict. The m100 read must be submit-ready by 12:30Z today and the m200 read by 16:30Z.

## Sources (read-only)
1. /scratch/jjyeung/orch_n30/evalx27/work/kit/ is the reviewed Orchard launcher pattern for one-H100 general reads. Its PROOF_JOB.md, REPORT.md, DIFF.md and launcher/ (orchard_launcher.py, orchard_job.py, orchard_stage.py, return_io.py, MODELS.json, ORCHARD_ASSETS.json) cover prepare/submit-command, the H100 check, the return pool with write test and lock, and the GCS returns.
2. /scratch/jjyeung/orch_n30/trin_read/build_t5/ is the D0 milestone reader built for Trinity. It holds milestone.py and e193_items.json (the accepted IDs: main 1,525, away 150, forward 150, camera 450, with cells, task hashes and source hashes). It also holds stage-export (GCS tar plus .done admission: sha before extraction, safe-layout checks, `m<step>/` tree), read --all-families, MILESTONE_SUMMARY and the lineage allowlist (runs 469ddece and 359fcc3c in lineage 8865619b). REPORT_T5.md, REPORT_T5B.md and DIFF.md explain them. /scratch/jjyeung/orch_n30/trin_read/kit_src/ is the copy of the Orchard kit (package.tar f42aa1a4) that build/ and build_t5/ derive from.
3. The rules the verdict must implement word for word:
   - /data2/jjyeung/agent_project_data/distill_design/TRACE_RULING_20261115.md, section 2.7 (F1, F2, and the guards against answer priors). Read lines 357-372.
   - /data2/jjyeung/agent_project_data/distill_design/D0_STOP_RULE_20261116.md, items 1-3.

## Export inputs (Orchard side)
- Objects: `gs://cmu-gpucloud-jjyeung/q8/8865619b/359fcc3c_m<step>.tar.part00-of-04` through `part03-of-04`. The tar is the four parts concatenated in order.
- Receipt: `/project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m<step>.done` (object, total bytes, sha256 of the whole tar); the part receipts are in `o/gcs.log`.
- The job streams the parts with the Orchard gcloud configuration (`gcloud storage cat`, about 121 MB/s measured), checks the whole-tar sha256 against .done before extraction, and then applies build_t5's stage-export admission and the unchanged export checker in full mode.

## Deliverables
1. A kit tree under readk/kit/ for a D0 milestone read on Orchard, with the smallest change against the reader that ran 169526 (kit f42aa1a4 / evalx27). It needs:
   - a `--step` argument (100 or 200) and families main, away and forward;
   - camera only behind a flag, off by default, because F1 and F2 do not use it;
   - the same layout, anchors, budgets (B2048 primary) and answer policy as e193.
   DIFF.md classifies every changed line against the reader that ran as PATH/ENV or BEYOND; BEYOND lines need one review.
2. Naming rules:
   - The job name is `a15_cot_ap` plus opaque hex. No project, benchmark, dataset, model or method word may appear in any Orchard path, name, argument or log line: never "split", revsi, vsi, distill, D0 or qgen.
   - Write the token's meaning into readk/LEDGER.jsonl only.
3. Returns go to an Orchard project pool (the x27ret pattern; propose a new opaque pool name) and to GCS under `gs://cmu-gpucloud-jjyeung/q8/<opaque>/`. They hold per-item records (id, family, task type, level, room/scene key, prediction, score at B2048) plus the summary.
4. readk/f1f2.py on Trinity, with tests in readk/tests/. Inputs: the D0 per-item returns and the step-544 per-item results of e193c2a3c for the same IDs.
   - Find where the accepted e193 per-item reports exist on trinity-1-3. build_t5's accepted-comparison tests read some; look in trin_read/kit_src/parity and the paths named in build_t5 reports. State whether the away and forward twins have step-544 per-item results there. If they do not, the job must also read the step-544 export (run 469ddece m544) on the same card in the same job, and the brief's deliverable 1 includes that arm.
   - F1: for route planning, counting, direction easy/medium/hard, relative distance and object size, compute the paired difference B minus A in accuracy with a 10,000-draw bootstrap over rooms (resample rooms with replacement; reuse the route table's room bootstrap if the reader code has one, and cite it). F1 fails if any type's 95% interval lies wholly below zero.
   - F2: on the 150 twin pairs, away accuracy per level (easy, medium, hard) with its interval; it fails if the interval does not clear 54, 40 and 36 respectively. Also report the share of pairs answered alike (fail above 20%; step 544 had 49%) and toward accuracy B minus A, paired (fail if the interval is wholly below zero).
   - Also print F1's guards: totals against the constant 7 (46.30%) and single counts against the constant 2 (61.87).
   - The stop-rule verdict for step 200:
     - STOP if F1 fails.
     - If F2 fails with F1 passing: CONTINUE_TO_400 only if away accuracy at step 200 is above its step-100 value on at least two of three levels and above step 544's on all three; otherwise STOP.
     - CONTINUE otherwise.
   - At step 100 the script reports the same quantities and no verdict. Tests use synthetic fixtures that hit every branch.
5. readk/REPORT.md, at most 60 lines:
   - what was built;
   - the exact prepare/submit commands, not run;
   - the expected wall time for one read on one H100, from measured receipts of 169526 or the evalx27 jobs (cite the file), plus the transfer and staging time;
   - disk on Orchard /tmp;
   - what remains unverified.
