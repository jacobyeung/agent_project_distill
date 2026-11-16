# Re-pin after offkit fix 5b and frames R2 (one-shot Codex build over builds R and N)

You run once on trinity-3-30; nobody answers questions while you run. Write only inside
`/scratch/jjyeung/orch_n30/b07_offread/builds/R/` and `/scratch/jjyeung/orch_n30/b07_offread/builds/N/`.
No ssh, network, Git, GPU, Slurm or Orchard command; no deletion (keep previous archives under new
names); no recursive search of /home or /data*; Python `/scratch/jjyeung/envs/p1cpu/bin/python -B`; never
open a benchmark answer or score. Read `builds/R/out/REBIND_READY.md`, `builds/R/RUN.md`,
`builds/N/out/NATIVE_KIT_READY.md`, `builds/N/RUN.md` first.

## What changed
offkit (`/scratch/jjyeung/orch_n30/b07_offread/kit/offkit`, read-only for you; 59 tests pass in `kit/tests`)
changed after re-review review_offkit2
(`/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_offkit/REVIEW_VERDICT_OFFKIT2.md`):
- `adapt_native.py`: new `check_not_scripted(row)`, called by `unify` and so by `from_journal`, refuses a
  C8r scripted record when the script fields sit inside `row['decode']` (dict or string form) or the arm is
  any case/space variant of `scripted`.
- `frames.py`: a whitespace-only override reason no longer admits a mismatched layout.
`bind.py`, `report.py`, `spec.py`, `adapt_direct.py` and `__init__.py` are unchanged.

## Do
1. Build R: regenerate `out/OFFKIT_PINS.json` from the current offkit bytes, rerun the whole suite and the
   four CPU rehearsals, reproduce 68.77 [66.5, 71.0] and 64.94 [61.3, 68.4] exactly, rebuild
   `package_vsi.tar` and `package_revsi.tar` and every manifest with the existing finish tooling, and update
   `out/REBIND_READY.md` (new hashes, test counts). Keep the previous archives under `out/prev_repin2_<UTC>/`.
2. Build N: refresh its build R snapshot and `out/OFFKIT_EXTERNAL_PINS.json` through the deliberate refresh
   command its RUN.md documents (record the diff), adapt any call site the change affects (any scorer path
   that builds unified records from C8r rows must go through `offkit.adapt_native.unify`), rerun the whole
   suite and all four CPU worker fixtures, rebuild `code.tar`, `SHIP_SHA256SUMS`, pins.
3. Build N identity proof, reduced (orchestrator ruling): the five job-170056 distance mask files
   (`/scratch/jjyeung/mask_recall_run/results/dense_aliases/candidates/*.npz`) are lost with an unreachable
   node. Record the proof as reduced in `out/NATIVE_KIT_READY.md`, `OPEN_INPUTS.md` and the proof receipt:
   camera items keep token, call, response and answer equality with independently recomputed responses;
   distance items keep token, call and answer equality and served-query/response digest equality, and lose
   independent re-serving of the distance responses from the original masks. Say in one sentence which
   failure that leaves undetected (a changed mask backend that reproduces the same digests cannot occur, but
   a backend change on items outside the five is caught only by the canary). Make the proof code accept the
   reduced mode only when the mask pins are declared lost in a pinned record, never silently.

Final message under 10 lines: new hashes, test counts.
