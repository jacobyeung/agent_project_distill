NOT PROVED end-to-end; kit n_go 8d3021783a9d875ae96727f1929bf8e0a59b6ea82ab1222a415b4ea19b7b14af; tree C 0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de.
Harness error: make_rehearsal_k5.py omitted the bounded-population call, so the run supplied the original stores (rehearsal_k5/HARNESS_REFUSAL.json).
Fixture closure PROVED: one native closure call, 13 stream pins and 62 authenticated inputs, none missing (rehearsal_k5/FIXTURE_CLOSURE.json).
Native fixture routing PROVED; production P reconstruction NOT PROVED (rehearsal_k5/routing_retained/plan.json; STAGES.json).
dbb2 PROVED on the fixture database digest; header mismatch search NOT PROVED (rehearsal_k5/DBB_STEP.json; dbb/db_bytes.json).
Scene-rebuild pins NOT PROVED: camera count 16,000 exceeds the unchanged 2,000-row limit; canary.log:59 records the native refusal (rehearsal_k5/p2/i/sc.json).
Native host receipt NOT PROVED: admission was not reached (rehearsal_k5/CHECK.json; STAGES.json).
Handover with localised pins NOT PROVED: admission was not reached (rehearsal_k5/CHECK.json; STAGES.json).
Clock inheritance NOT PROVED: training was not reached (rehearsal_k5/CHECK.json; STAGES.json).
Fresh optimizer / counter zero NOT PROVED: training was not reached (rehearsal_k5/CHECK.json; STAGES.json).
Finite losses on four ranks NOT PROVED: training was not reached (rehearsal_k5/CHECK.json; STAGES.json).
Step-1 checkpoint through milestone NOT PROVED; timed checkpoint NOT PROVED: training was not reached (rehearsal_k5/CHECK.json; STAGES.json).
Milestone export / local receipt / kit copier NOT PROVED: training was not reached (rehearsal_k5/CHECK.json; STAGES.json).
TK_JOB_START budget self-stop NOT PROVED; resume_pin latest / one further step NOT PROVED: training was not reached (rehearsal_k5/CHECK.json; STAGES.json).
Census receipt bound in h.py NOT PROVED; review wait / published v.json / fixture review NOT PROVED: publication was not reached (rehearsal_k5/CHECK.json; STAGES.json).
Corrected fixture-reader check PROVED: five complete 2,000-row subsets preserve row/target bytes and pass native rows() on Trinity; no rehearsal stage was rerun (rehearsal_k5/harness_validation/RESULT.json).
Rerun artifact: go_rehearsal_k5a.sh KIT_PATH FRESH_ROOT takes a fresh build24k/rehearsal_k5* root; its wiring is checked, its rehearsal is NOT PROVED. go_rehearsal_k5.sh preserves the failed launcher.
Full admission remains constrained: the unchanged sampler needs 32,000 VQA rows, exceeding a complete 2,000-row fixture; this is source-derived, not a measured second refusal (rehearsal_k5/CAPACITY_CONSTRAINT.json).
One attempt, no retry; no kit defect established. Source kit, helpers, tree and original stores verify unchanged; peak RSS 741928960 B; new allocation 297410560 B (rehearsal_k5/VALIDATION.json).
