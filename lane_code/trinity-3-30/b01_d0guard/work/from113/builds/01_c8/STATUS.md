C8 is a draft, not admitted for seal or launch. Sources, deterministic archive, family draft, diff, tests, call-site table, pin audit, and rehearsal harness are under `out/`.

The core suite passes 14 system-Python diagnostic tests (`out/tests/core.log`). The pin audit passes 9 checks and marks 37 N/E (`out/PIN_AUDIT.json`). Independent arithmetic on the 84 real geometries finds 11 sealed refusals and one reviewed refusal, `d3/41254810` (`out/GUARD_CENSUS.json`). The production NumPy guard has not executed.

Both whole-worker modes stop at preflight. The required Python environment points into shared memory that is inaccessible here, and the streamed inputs have no completion markers (`work/rehearsal_pilot/RESULT.json`, `work/rehearsal_full/RESULT.json`). The input monitor ended early because the runtime independently blocks the remaining proofs (`out/INPUT_WAIT_STOP.json`); it did not reach the maximum wait. No transfer, GPU, network, Git, or other-agent operation has run.
