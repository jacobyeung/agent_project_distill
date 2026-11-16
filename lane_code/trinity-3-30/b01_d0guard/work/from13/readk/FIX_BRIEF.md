# Fix round 1 for the D0 read kit (work only in /scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/)

The review verdict is /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_d0r/REVIEW_VERDICT_D0_READ_KIT.md: GO AFTER FIXES. Read it in full, then fix A1, A2, A3, B1 and B3 exactly as it describes. For B2, keep the TRACE_RULING 2.7 lower-bound reading as the verdict and also print the point-estimate reading as information.

The same rules hold as in BRIEF.md in this folder. No ssh, GPU, network, Git, deletion or Slurm. Never run a publish, gcloud or any network path during tests: mock it. The reviewer's local test reached a real `gcloud cp`, so add a guard that the tests cannot reach the real binary.

## A3 evidence
The real `.done` format comes from an Orchard ls/head at 09:34Z, saved in evidence/DONE_SAMPLES.txt. The file is plain text, not JSON: one line `<object without bucket> <bytes> <sha256>`, for example `q8/8865619b/469ddece_m1.tar 21583032320 cca97796...`. That sample is the step-1 export of run 469ddece in x_07ca49df/o/. D0's file will be `x_f5c353f7/o/gcs_359fcc3c_m<step>.done`, and its object `q8/8865619b/359fcc3c_m<step>.tar` is split into `.part00-of-04` to `.part03-of-04`. Find how the kit's uploader names the parts and what the bytes and sha cover (whole tar). Accept exactly this format. Bind the object to the expected run and step, and form the gs:// URI with bucket gs://cmu-gpucloud-jjyeung.

## B3
Add step 400 to the kit and to f1f2.py. Stop rule item 2: at step 400 the leg stops if F2 still fails. Give its verdict as STOP or CONTINUE, with F1 reported too.

## Finish
Re-pin and re-run all tests. Update DIFF.md, REPORT.md (at most 60 lines) and REVIEW.md (add a section "Fix round 1" listing each item with file:line). Write FIX1.md, at most 30 lines: each review item, its fix, and the tests that prove it.
