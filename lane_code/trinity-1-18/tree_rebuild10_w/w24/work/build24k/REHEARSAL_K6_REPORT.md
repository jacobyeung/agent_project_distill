NOT PROVED end-to-end; kit n_go e54fc1b9973cc7d3ce2020d36c6aa1829eddba267bede2d13df035e0fdba595a; furthest stage: canary.
Bounded populations PROVED; 1,000 complete VQA pairs and removal census PROVED (rehearsal_k6/TWIN_SUBSET.json; BOUNDED_POPULATION.json; VALIDATION.json).
Fixture closure PROVED: one native closure call, 64 pins, none missing (rehearsal_k6/FIXTURE_CLOSURE.json).
Native fixture routing PROVED; production P reconstruction NOT PROVED (rehearsal_k6/routing_retained/plan.json; CHECK.json).
dbb2 PROVED on the fixture digest; header mismatch search NOT PROVED (rehearsal_k6/DBB_STEP.json; dbb/db_bytes.json).
Scene-rebuild pins NOT PROVED (rehearsal_k6/CHECK.json; canary.log).
Native host receipt NOT PROVED (rehearsal_k6/CHECK.json; STAGES.json).
Handover with localised pins NOT PROVED (rehearsal_k6/CHECK.json; STAGES.json).
Clock inheritance NOT PROVED (rehearsal_k6/CHECK.json; STAGES.json).
Fresh optimizer / counter zero NOT PROVED (rehearsal_k6/CHECK.json; STAGES.json).
Finite losses on four ranks NOT PROVED (rehearsal_k6/CHECK.json; STAGES.json).
Step-1 checkpoint through milestone NOT PROVED (rehearsal_k6/CHECK.json; STAGES.json).
Timed checkpoint NOT PROVED (rehearsal_k6/CHECK.json; STAGES.json).
Milestone export / local receipt / kit copier NOT PROVED (rehearsal_k6/CHECK.json; STAGES.json).
TK_JOB_START budget self-stop NOT PROVED; resume_pin latest / one further step NOT PROVED (rehearsal_k6/CHECK.json; STAGES.json).
Census receipt bound in h.py NOT PROVED; review wait / published v.json / fixture review NOT PROVED (rehearsal_k6/CHECK.json; STAGES.json).
Stop: ValueError: R1_TWIN_BINDING_COUNT (rehearsal_k6/canary.log:37; REFUSAL_DETAIL.json). One attempt; no retry.
Integrity PROVED; peak RSS 560607232 B; new allocation 194482176 B (rehearsal_k6/VALIDATION.json).
Capacity impossible: 32,000 sampler rows and 7,971 mandatory twins exceed the 2,000-row scene limit. This blocks bounded rehearsal; it does not prove a production-kit defect (rehearsal_k6/CAPACITY_DECISION.md).
