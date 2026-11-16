The script implements the binding review and scoring ruling. All fixture and pilot outputs are PLUMBING. They do not establish model performance; a real full-read report still needs the orchestrator's independent confirmation.

Run from this build directory with the supplied interpreter:

```bash
export PYTHONPATH=/scratch/jjyeung/orch_n30/native_r2/work/np226:/scratch/jjyeung/orch_n30/native_r2/work/pyextra
/scratch/jjyeung/orch_n30/native_r2/env312/bin/python3.12 -I -s -B out/native_vs_direct.py \
  --bundle /path/to/real/native/R1.json \
  --admission /path/to/real/native/paired/IN_JOB_ADMISSION.json \
  --output /scratch/jjyeung/orch_n30/native_r2/builds/05_analysis_fix/out/real
```

The delivered script uses only the standard library and runs serially. Its default draws and seed are defined in [native_vs_direct.py](native_vs_direct.py) and recorded in each output JSON. The isolated interpreter ignores PYTHONPATH; only the independent test tool explicitly imports the supplied numpy package. Every output must stay inside this build.

The default compact direct source remains primary. The default raw files under `in/direct_raw/` supply forced-close and producer-error evidence. The script refuses disagreements on any shared field for any selected key. Both raw hashes appear in each report. Override the raw paths with `--direct-raw MAIN.jsonl CAMERA.jsonl` when supplying matching alternative inputs.

Use `--direct-artifact /path/to/direct/metadata/EXPORT_ARTIFACT.json` when the direct export artifact is available. The script hashes its bytes and compares the digest with every native row's export digest. Without direct artifact evidence, the report marks this check PARTIAL and records the bounded paths searched. It does not authenticate checkpoint weight bytes or compare frames.

The script writes `ROOM_MAP.json`, `NATIVE_VS_DIRECT.json`, and `NATIVE_VS_DIRECT.md`. The report begins with the serving caveat, capped-rule disagreements, and the review's caveats. Its primary comparisons are per type and per type within capture group. Pooled comparisons have a descriptive heading. Each routed comparison prints the caveat list beside it.

Primary scoring retains parsed budget-forced closes and requires zero scores for missing final answers. All items remain in the primary denominator. `capped_zeroed` zeroes both states in every arm. The other sensitivities restrict the same keys across all arms: passed geometry, no producer errors, and metre-only questions. The scripted comparison appears beside the native comparison. Counts distinguish native budget fires, direct answer caps, direct forced closes, and both answer states.

For the fixture, add `--plumbing`. For selected keys, add `--subset /path/to/KEYS.json`; subset reports are always PLUMBING. The subset requires matching admission and unit aggregates. The local pilot adapter supplies and checks these aggregates:

```bash
/scratch/jjyeung/orch_n30/native_r2/env312/bin/python3.12 -I -s -B out/prepare_pilot.py
```

The adapter reads the local pilot archive after checking its supplied hash prefix, writes only selected records under `work/pilot/`, preserves decode flags, and runs the paired analysis. `work/pilot/PILOT_CHECK.json` records the check. This does not replace Orchard job admission.

Run the tests:

```bash
/scratch/jjyeung/orch_n30/native_r2/env312/bin/python3.12 -I -s -B out/tests/run_tests.py --all
```

The suite includes the adapted adversarial cases, exact exhaustive unequal-room interval endpoints, full fixture CLI, and real pilot subset CLI. Missing pilot evidence fails the test. Results and logs are under `out/tests/`; fixture runtime is recorded in `out/fixture/RUNTIME.json`.

The adapted review mutation tool is `out/tests/mutate.py`; it creates a separate copy for each mutant under `work/mutations/`, runs the entire suite, and records `out/tests/MUTATION_RESULTS.json`. Existing mutation directories are retained; use a fresh destination inside this build for any additional campaign.

[DECISIONS.md](DECISIONS.md) records implemented choices. [VALIDATION.json](VALIDATION.json) records evidence paths and checks that were not performed. [FIX_DIFF.patch](FIX_DIFF.patch) compares the delivered script with [native_vs_direct.orig.py](native_vs_direct.orig.py).
