# Fix round 3 (h1read kit): allow one more export — the step-544 checkpoint (run 469ddece, stop generation mstop, optimizer step 544) — for an R0-dev-only read

Work only inside `/scratch/jjyeung/orch_n30/cont_ops/work/h1read/` (this kit; read REPORT.md, FIX2.md, DIFF.md first). No network, ssh, Slurm, GPU, Git or deletion; no searches outside this folder. Do not touch `kit/build/*` production preparations (they are live receipts); tests may create fixtures only under `evidence/test_*`.

## Why
The orchestrator needs a step-544 read on family `a7` (R0-dev, 2,169 items) with exactly the same reader build, items, prompts, frame layout (32 anchors, `duplicate`), B2048/B4096 policy and scorer as the D0 and H1-1 R0-dev reads this kit already ran (D0 m200 job 170757, D0 m100 job 170786, H1-1 m100 job 170808). It is the baseline for the next leg's stop rule. No such read exists.

## The export (facts from Orchard)
- Run `469ddece`, namespace `8865619b`, deployment `/project/community/jjyeung/okh7/x_07ca49df`.
- Receipt `/project/community/jjyeung/okh7/x_07ca49df/o/gcs_469ddece_m544.done` = `q8/8865619b/469ddece_mstop.tar 21583032320 3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7` (same plain-text format as the others).
- Claim `/project/community/jjyeung/okh7/x_07ca49df/o/gcs_469ddece_mstop.claim` (5 bytes; expected `m544\n`).
- Four parts `q8/8865619b/469ddece_mstop.tar.part00-of-04` .. `part03-of-04` in bucket `cmu-gpucloud-jjyeung`.
- The archive's artifact is the step-544 init artifact (artifact.json sha256 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef, heads 8bb5e151..., full_weights 211ae87b...), i.e. the same init D0 and H1-1 trained from.

## Change (smallest possible)
1. `kit/launcher/binding.py`: register run `469ddece` -> `x_07ca49df` for exactly one identity: generation `mstop`, step 544 (claim must read `m544\n`). Every existing identity, refusal and message stays as is; other steps/generations for 469ddece refuse.
2. Whatever else the prepare/admission path needs so that `prepare --run 469ddece --namespace 8865619b --step 544 --generation mstop --families a7` produces a valid production preparation; keep the export checker, the four-part whole-tar check and all admission checks. If the reader/export checker rejects this artifact for a reason that cannot be fixed without weakening a check, stop and report.
3. Tests: the new identity prepares (fixture under evidence/test_*) and binds the exact receipt/claim/object; wrong step, wrong generation, wrong claim and other 469ddece steps refuse; all existing tests still pass (rerun the full suites listed in REPORT.md). Update SHA256SUMS.txt/FINAL_PINS as the kit convention requires, and write `FIX3.md` (changed lines, test results, the exact operator prepare/submit commands for this read).
