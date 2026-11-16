# Build V1e: run the dev-S1 proof first after staging (one-shot Codex build, small)

Same rules as V1 (`/scratch/jjyeung/orch_n30/native_r4/builds/01_vsti/BRIEF.md`, lines 3-8), except: write only inside `/scratch/jjyeung/orch_n30/native_r4/builds/05_vsti_e/` (at most 2 GB). Copy V1d (`/scratch/jjyeung/orch_n30/native_r4/builds/04_vsti_d/`: `code/`, `tests/`, `out/rehearsal/`, `work/py`, the helper scripts you need such as `work/package_d.py`, `work/finalize_d.py`) first; V1d stays unchanged. Read V1d's `BRIEF.md`, `out/DECISIONS.md`, `out/RUN_ORCHARD.md`, `out/SIZING.md`, `events/*_RESULT_final.md`.

## Change only this, with tests
The orchestrator's GO requires that the job's first phase after staging is the ten-item dev-S1 proof against job 170056, whose outcome is returned whatever it is. In V1d `code/o.py` (around lines 165-169) the order is prepare (G3T on 311 scenes) -> proof -> read, so a prepare crash ends the job before the proof runs.
1. Make the order: staging -> proof (only when not resuming, as now) -> prepare -> read. A proof failure or exception stays a receipt (PROOF.json status failed) and the job continues to prepare and read; a prepare or read failure still stops the job and the return (including PROOF.json) is still published by the `finally` block.
2. Verify that the proof phase uses nothing that prepare creates (namespaces, files, GPU state). If it does, fix it minimally and say what in `out/DECISIONS.md`.
3. Budget: the proof must not consume the read's deadline unboundedly. If the proof has no own time cap, give it one equal to its sized time plus margin from `out/SIZING.md` (state the number); on timeout it is a failed-proof receipt and the job continues.
4. Tests: a test that the phase list is [proof, prepare, read] for a fresh job and [prepare, read] for a resume; a test that a proof exception and a proof timeout each leave a failed receipt and the read phases still run; a test that a prepare failure after the proof keeps PROOF.json in the return. Rerun the whole kit suite and the inherited tests, and the CPU sample rehearsal.
5. Update `out/SIZING.md` and `out/RUN_ORCHARD.md` for the new order (no other content change).

## Deliver
`out/c.tar`, `out/FAMILY.json` rebuilt; `out/d.tar` byte-identical to 9a1de8608ea0e75e2f2436259b81f0e991b2007002a59de11d85062e8384d08f (if unavoidable change, say why); `out/DIFF_vs_V1d.patch` and `out/DIFF_vs_V1c.patch` (code only, plus a tests diff); the operator namespace rehearsal command (`out/rehearsal/RUNBOOK.md`); final RESULT (at most 20 lines) in `events/` with the new hashes, the test counts, the proof's time cap, and what you did not check.
