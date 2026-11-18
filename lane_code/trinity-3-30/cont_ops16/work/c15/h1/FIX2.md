The packet submits exactly `a15_cot_ap5ee9da63`; `a15_cot_ap` is the account-mandated opaque prefix.
The job token remains `5ee9da63` in `TOKENS_H1.json` and both IDs records; both IDs records and `payload/go.template.json` carry the full name.
`tools/make_orchard.py` generates the corrected `payload/s.sh`, payload sums, upload archive, `UPLOAD.json` and embedded `orch_h1.sh`.
`REPORT.md` gives the current name in its table and step 8; `DIFF.md` includes the submitter and test patches.
`test_visible_names.py` allows the prefix only in the submitter’s `sbatch -J` argument before a hex suffix; all other forbidden-word checks remain active.
PASS: test_derivation, test_gate_binding, test_staging, and run_fallback fallback_fix2 (the four original checks).
PASS: test_stop_bridge, test_fix1, and test_visible_names, including positive and negative prefix checks.
PASS: tests/review/rv_mut.py, rv_g_a2.py, rv_gate.py, and rv_g_fx.py.
The CPU fallback completes 200 steps, exports m100/m200, reports H1_STOP with stopped_for_resume=false, and verifies the slot.
PASS: all review Python files parse and tests/RERUN_CHAIN.sh passes bash -n.
The chain runner is byte-identical; chain_r1 does not exist. The four-rank cases remain operator-only and were not executed.
PASS: two upload builds match byte for byte; payload sums, archive members and the embedded transport agree.
Configuration identity, admission contract, trainer, derived fixture manifest and batch wrapper remain unchanged.
`evidence/fix2/tests.json` and its logs record all 11 executed checks; `evidence/hash_changes_fix2.json` records changed hashes.
`SHA256SUMS.txt` seals the current packet and evidence. Work stayed local and CPU-only, with no SSH, network, Orchard, GPU, Git or deletion.
