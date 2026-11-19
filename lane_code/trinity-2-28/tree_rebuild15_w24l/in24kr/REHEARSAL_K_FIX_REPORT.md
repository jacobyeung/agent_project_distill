LAUNCH BLOCKER: production N reproduces P_EXPORT_RUN_BINDING_MISMATCH at work/tree_r1/student_pilot/r1_handover.py:348–352; a tree change is required, not a kit-only fixture fix.
Cause: out/kit_n_go/b/pl.py:143–165 localizes p_run.preparation.path, but authenticated P config/binding bytes retain the original path; both whole-pin equalities at line 349 fail.
Production pins authenticate: step-400 artifact 5083243c, export-only receipt b467c32b, config b08fe50c, binding f6b63624, preparation a5bbef1b; decoded k/c.json and k/p.json agree.
The original production binding passes all seven field comparisons; native _donor refuses after the shipped localization, with runtime identity 9459724f unchanged.
The rehearsal3 donor also passes before localization and fails afterward: preparation e2cd4d01 changes from rehearsal3/donor/preparation.json to /tmp/q_22c714e1/p2/q/u/e2cd4d01…; identity 48b37d82 remains equal.
Only source.preparation.path and binding.preparation.path differ in both cases; preparation hashes, both config identities and c1-preparation-v1 schema match.
REHEARSAL_K_BINDING_FIELDS.md gives the complete comparison table; REHEARSAL_K_BINDING_EVIDENCE.json records full p_run/init_artifact/receipt pins, local files, hashes and native refusals.
Production preparation comes from the UPLOADS_MINIMAL.json local_path; other authenticated donor members come from the ext/m400real snapshot named by that inventory's routing receipt.
Preserving p_run unchanged instead fails R1_HOST_PATH_OUTSIDE_JOB_TMP at work/tree_r1/launch_r1/entry.py:27–40 (called at :116–117 and :197); the tree must reconcile authenticated provenance pins with confined relocated reads.
No fix was applied. The fixture-only condition is false, so rehearsal_k2, launcher changes and prepare-only validation were not performed; the tree, kits, out/, rehearsal_k and rehearsal5 remain untouched.
The existing rehearsal_k_run1.log proves only the FSDP reproduction and routing stage; native host and all later training paths remain NOT PROVED. No training ran here.
Lane diagnostic command: `cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24 && OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build24k/check_rehearsal_binding.py`; do not launch N pending the tree fix and kit reseal.
