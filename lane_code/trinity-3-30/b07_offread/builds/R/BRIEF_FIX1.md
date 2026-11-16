# Build R fix 1: apply review fixes 4 and 6 and the new offkit API (one-shot Codex build, continues build R in place)

You run once on trinity-3-30; nobody answers questions while you run. Same rules as `BRIEF.md` in this
folder (read it first): write only inside `/scratch/jjyeung/orch_n30/b07_offread/builds/R/`; no ssh,
network, Git, GPU, Slurm or Orchard command; no deletion (write new versions); no recursive search of
/home or /data*; Python `/scratch/jjyeung/envs/p1cpu/bin/python -B`; never open a benchmark answer or
score to choose anything. Read `out/REBIND_READY.md`, `RUN.md`, `DIFF.md` and `kit/rebind.py` first.

## Review verdict to satisfy
`/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_offkit/REVIEW_VERDICT_OFFKIT.md`
(read it once). Build R is GO after fixes 4 and 6. The offkit side of fixes 1-5 is done in
`/scratch/jjyeung/orch_n30/b07_offread/kit/offkit` (read-only for you; 49 tests pass in `kit/tests`). New API:
- `bind(benchmark, export, reader, *, mode, init_selection, ledger, ..., frames=(32,'duplicate'), frames_override_reason=None)`:
  production refuses without a ledger; the binding carries `frames` (from `offkit.frames.bind_frames`) and
  its sha covers them; `verify_binding(b)`, `binding_sha256(b)` exist.
- Init selection JSON now needs `selected_sha256`, `selected_step` in {200,400,600,800,1000} equal to the
  `.done` object step, `init_rule_sha256` = `bind.INIT_RULE_SHA` (d53f9c1a...), `d0_ended` {reason in
  `bind.D0_ENDED`, event}; the `.done` object must match `q8/8865619b/359fcc3c_m<step>.tar`.
- `report.label_report(report, *, binding, arm, role, arm_label=None)` takes the verified BINDING (reader
  and export come from it; reader kind, benchmark and arm must match the aggregate and the binding).

## Changes
1. Fix 4: `kit/rebind.py:86` admits m100; drop it (only the init-rule candidates); keep the reviewed
   `export_stage.parse_done` call. Tests: an m100 `.done` with an otherwise valid selection refuses.
2. Fix 6: rebind.py imports offkit from the lane path and never checks pins at run time. Pin offkit by
   content: at import (before prepare, report and every action), verify the sha256 of every offkit module
   it imports (`bind.py`, `report.py`, `spec.py`, `adapt_direct.py`, `frames.py`, `__init__.py`) against
   `out/OFFKIT_PINS.json` and refuse on any difference. Regenerate `OFFKIT_PINS.json` from the current
   offkit bytes. Test: a mutated copy of offkit on `sys.path` refuses.
3. Adapt every call to the new API (`label_report(binding=b, ...)`; `bind(..., ledger=...)` in
   `tests/rehearse.py` and any fixture; selection fixtures with the new fields).
4. Rerun the whole suite and both D0 CPU rehearsals and the step-544 fixture rehearsals; reproduce the
   accepted 68.77 [66.5, 71.0] and 64.94 [61.3, 68.4] exactly as before; rebuild `package_vsi.tar`,
   `package_revsi.tar`, `SHIP_SHA256SUMS`, `VALIDATION.json`, `FINAL_CHECK.json` with the existing finish
   tooling; update `DIFF.md`, `RUN.md` (init-selection fields) and `out/REBIND_READY.md` (new hashes, the
   two fixes with file and line, test counts). Keep the previous archives under new names (for example
   `out/prev_1217Z/`), never overwrite them.

Do not submit or upload anything. Final message: under 10 lines with the new package hashes and test counts.
