Finish up `prep_dynamic_4d`:
1. Confirm `pytest /scratch/jjyeung/orch_home_distill/spatial_v2/tests/test_dynamic_4d.py` passes `100%` (fix any failure cleanly).
2. Finalize the Orchard `1× H100 general` 4D teacher extraction script (`spatial_v2/orchard_extract_4d_teachers.sh`, opaque job name `a15_cot_ap4d<alnum>`, `/tmp` caches, GCS `gs://cmu-gpucloud-jjyeung/ae/` read -> GCS output) AND run a quick `trinity-0-8` GPU `5` (`vnice.sh`, `<3 GB` scratch) or local `2-28` schema/eval check if applicable.
3. Write the concise verified report to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_dynamic_4d_prep.md`.
