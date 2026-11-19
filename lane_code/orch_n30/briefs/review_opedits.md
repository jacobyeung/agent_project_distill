# Review: two operator-edited driver scripts used to launch Orchard job 172660 (read-only)

You are an independent reviewer. Read only the files named below. Write nothing except your final message.

## Cluster rules (binding)
- No recursive search (`grep -r`, `find`, `du`, `ls -R`) anywhere on `/home` or `/data*`. Open the named files directly.
- No Git commands. No ssh. No network. No deletion.
- Keep the final message under 40 lines.

## Context
A training continuation (Orchard job 172660) was launched by a chain of driver scripts. Two drivers in the reviewed chain failed or were too heavy, and the operator replaced them by hand without a second look:

1. `dv1.sh` failed in its own driver because `r.py` asserted `remove_files[-1] == n.json`, while the new remove list has `z.json` last. The operator wrote `dv1b.sh`, which asserts `n.json` at index -2 and `z.json` (sha prefix `caba6a56`) at index -1, checks `z.json`'s file sha and its staged row, and moves the failed output `d0` to `d0.f1`.
2. `pre1.sh` streams a 113 GB slot to verify it. The operator wrote `pre1_light.sh`, which checks only the slot's recorded fields (`76bed248` / `c11b603f` / `a09ca55b`, size, sidecar) and leaves the full stream check to the in-job bridge.

`n.json` is a 601-row REMOVE list (rows outside the scene division). `z.json` is a second REMOVE list (counting rows in a looping list form). Both must be applied: a missed list trains on rows that were ruled out.

## Files (all in `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/r1_ops/ops_mirror/drv_cp/`)
- `dv1.sh` and `dv1b.sh` (compare)
- `pre1.sh` and `pre1_light.sh` (compare)
- `DRIVER_SHA256SUMS.txt`, `README.md`, `go_submit_canary_delta_32337655.sh` (for what the chain requires of these two steps)
- outputs one directory up: `../dv1.out`, `../dv1b.out`, `../dvp1.out`

## Questions
1. Does `dv1b.sh` drop, weaken or bypass any check `dv1.sh` made, other than the position of `n.json`? List each difference and say whether it can admit rows that `dv1.sh` would have refused.
2. Does `dv1b.sh` prove that both `n.json` and `z.json` are applied to the staged store (not merely present in a list)? Quote the lines.
3. Does `pre1_light.sh` skip any check that nothing later repeats? For each skipped check, name where the in-job bridge repeats it, or say "not visible in these files".
4. Does `go_submit_canary_delta_32337655.sh` depend on an output of `dv1.sh` or `pre1.sh` by name or sha that the replacements do not produce? If so, how did the submit pass?
5. Could either edit make job 172660 train on a wrong store, a wrong slot, or rows that were ruled out? Answer YES, NO, or CANNOT TELL, with the reason.

## Verdict
First line: `OK` (no check lost that matters), `CONCERN` (a check is lost; say what to verify on the running job) or `STOP` (the job is likely training on wrong inputs). Then the numbered answers with file:line evidence.
