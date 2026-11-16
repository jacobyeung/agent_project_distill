# build_rv2 status

D0 integration is blocked because the reviewed source directory
`/scratch/jjyeung/orch_n30/b07_offread` is absent on `trinity-1-3`.
The required inputs are `kit/offkit/` and `builds/R/`, including
`rebind.py`, `RUN.md`, `out/REBIND_READY.md`, `out/OFFKIT_PINS.json`,
and `package_revsi.tar` at its documented location.

`build_rv2/` is the requested `cp -a` copy of `build_rv/`. Its executable
code is unchanged and still refuses D0. No new binding logic or substitute
sources have been introduced. The missing sources prevent verification of
the required pins, inspection of the reviewed API, and D0 fixture testing.

All 34 inherited ReVSI CPU fixtures passed in 133.42 seconds.
`TESTS_RV2_BASELINE_01.log` records the run with
`/scratch/jjyeung/envs/p1cpu/bin/python`, bytecode and pytest caching
disabled, and fresh basetemp `tests/rv2_baseline_01`.
This run checks the copied baseline, not D0 support.

All writes stay under `build_rv2/`. No GPU, SSH, network, Git, Slurm, or
deletion command was used. `build_rv_d0` was not inspected or used.

This report applies the no-archaeology skill. It retains no borderline
revision-history prose.
