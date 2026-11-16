# Verification recipes

## Compact targets (`student/compact_targets`)

Run `CUDA_VISIBLE_DEVICES="" python -B -m unittest discover -s student/compact_targets/tests -v` from the repository root. Set `COMPACT_TEST_OUTPUT` to an owned directory under `/data2`; the tests retain their synthetic fixtures. The golden test reads the supplied `vsi590k_037500` recovery artifacts and `EXAMPLE_RENDER_B.txt` without modifying them. The renderer's `verify` command replays all rendered admission checks, authenticates both pilot variants, and reconciles candidates and deferrals against the frozen membership.

## GT measurement (`tools/gtmeasure`)

Install `tools/gtmeasure/requirements.txt` in an owned CPU environment, then run `CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tools/gtmeasure/tests -v` from the repository root. `GTMEASURE_TEST_OUTPUT` selects a retained fixture directory below `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/`. The generator and mixer require a clean commit and create new output directories below that same pilot root. `python -B -m tools.gtmeasure.verify --directory <output> --recompute` authenticates row and coverage artifacts and replays the geometry. The mixer interprets `--ratio` as the measurement fraction of training rows and samples without replacement; it preserves published scene sides and hashes only new scene groups.
