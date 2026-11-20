NOT PROVED end-to-end; kit n_go e54fc1b9973cc7d3ce2020d36c6aa1829eddba267bede2d13df035e0fdba595a.
Bounded fixture populations PROVED: five complete 2,000-row subsets preserve row/target bytes; the native limit stays unchanged (rehearsal_k5b/BOUNDED_POPULATION.json; VALIDATION.json).
Fixture closure PROVED: one selected-planner closure call, 63 authenticated pins, none missing (rehearsal_k5b/FIXTURE_CLOSURE.json; RESOLVED_INPUT_INVENTORY.json).
Native fixture routing PROVED; production P reconstruction NOT PROVED (rehearsal_k5b/routing_retained/plan.json; CHECK.json).
dbb2 PROVED on the fixture digest; header mismatch search NOT PROVED (rehearsal_k5b/DBB_STEP.json; dbb/db_bytes.json).
Scene-rebuild pins NOT PROVED (rehearsal_k5b/CHECK.json; canary.log).
Native host receipt NOT PROVED (rehearsal_k5b/CHECK.json; STAGES.json).
Handover with localised pins NOT PROVED (rehearsal_k5b/CHECK.json; STAGES.json).
Clock inheritance NOT PROVED (rehearsal_k5b/CHECK.json; STAGES.json).
Fresh optimizer / counter zero NOT PROVED (rehearsal_k5b/CHECK.json; STAGES.json).
Finite losses on four ranks NOT PROVED (rehearsal_k5b/CHECK.json; STAGES.json).
Step-1 checkpoint through milestone NOT PROVED (rehearsal_k5b/CHECK.json; STAGES.json).
Timed checkpoint NOT PROVED (rehearsal_k5b/CHECK.json; STAGES.json).
Milestone export / local receipt / kit copier NOT PROVED (rehearsal_k5b/CHECK.json; STAGES.json).
TK_JOB_START budget self-stop NOT PROVED; resume_pin latest / one further step NOT PROVED (rehearsal_k5b/CHECK.json; STAGES.json).
Census receipt bound in h.py NOT PROVED; review wait / published v.json / fixture review NOT PROVED (rehearsal_k5b/CHECK.json; STAGES.json).
Stop: ValueError: R1_TWIN_AUGMENTATION_REQUIRED (rehearsal_k5b/REFUSAL_DETAIL.json; canary.log); no retry.
Integrity PROVED: source kit, helper code, extracted tree and original stores; peak RSS 577835008 B, new allocation 357687296 B (rehearsal_k5b/VALIDATION.json).
Rerun: bash /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24k/go_rehearsal_k5b.sh KIT_PATH /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24k/rehearsal_k5a_fixed; the root must be fresh. CHECK.json records the scope of every proof.
