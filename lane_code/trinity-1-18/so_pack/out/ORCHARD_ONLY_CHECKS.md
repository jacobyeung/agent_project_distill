# Checks that require Orchard

`pack.py check` produces a local packaging receipt. It never creates `a/c/CPU.json`, fabricates `SLURM_JOB_ID`, or grants the GPU entrypoint a substitute for the native CPU proof.

| Remaining check | Why it needs Orchard | Where its failure appears |
|---|---|---|
| Exact registered package location, private directory mode, actual pool archive presence/sizes, fill/duplicate markers | Only the Orchard filesystem establishes these facts at `/project/community/jjyeung/okh7/a15_cot_ap<hex>`. Local mirrors establish bytes, not remote presence. | Login helper traceback; generated phase EXIT message; production transport's local `*_remote.log`. |
| Allocated numeric job ID and node-local disk/storage proof | Needs an actual Slurm allocation and the selected node's `/tmp` capacity and permissions. | CPU job `a/4.err` and `a/4.log`; no success receipt on failure. |
| Native staging of template groups, bwrap binary, dependency/env archives and namespace mounts | Needs pool paths, installed template assets, filesystem/mount permissions and the job namespace. | Native CPU helper logs above, plus staged `STAGING.json` only when written successfully. |
| Real job Python and torch/torchvision/transformers/scipy versions against pinned environment receipt | The Trinity CPU environment cannot attest the Orchard job venv or CUDA libraries. | CPU prepare log `a/c/0.log` when created; otherwise `a/4.err`. |
| Exact export restore and prepared READY/settings/binding/manifest/RESTORE hashes | Requires the pinned full export, dependency archives, source assets and actual namespace. CPU stubs do not establish restore. | CPU prepare log and native exception; no `CPU.json` on failure. |
| B5/D full-reader rehearsal with staged RGB hashes/PNG decode and real mapping/reader/scorer control flow | The supplied mirror lacks the actual staged RGBs, restore and job venv. The native rehearsal itself uses model stubs, which must remain explicit in its receipt. | `a/c/1.log`, `FULL_READER.json` only after success, and the bound native CPU receipt. |
| Real return-pool permissions, symlink policy and capacity; general queue availability; duplicate submission guard | These facts can change after local checking and belong to the live Orchard pool and scheduler. | Native submit script stderr; generated phase EXIT message. The wrapper does not retry a failed attempt. |
| Assigned GPU count/UUIDs, CUDA libraries, H100 memory/kernels, real decode and node-specific bootstrap | These facts require the GPU allocation. The CPU proof checks package/runtime control flow before submission. | Existing batch EXIT trap writes node context, original exit code and last 60 log lines to `$P/a/x${SLURM_JOB_ID}` even before the return-pool write. Later failures also enter native return metadata/logs. |

The generated submit script starts the native CPU job, polls its terminal state at 60-second intervals, and requires `COMPLETED` plus the native receipt before invoking the sealed GPU submit script. A terminal CPU failure prints its stderr tail and stops. The GPU submit script retains plan/payload/input/operator/guard/dispatch/memory/full-reader, queue, pool and duplicate-submit gates. It does not retry a failed submission.

Local checks verify the exact batch trap/tail with redirected fixture I/O. They inject an early exception and check the retained nonzero exit and traceback; they also signal a running child. A separate probe exercises the genuine read runner's stop handler, worker arguments and summary with a tiny CPU decoder. Neither probe establishes trainer-rank checkpoint/export behavior.

## Missing local inputs are not Orchard-only exemptions

Export scanning, base/env archive preservation, tar header/file resolution, policy authorization, package/bundle/payload pins, item validation, isolated imports, layout metadata, operator planning/rehearsal, memory bounds, process guard/write proof and dispatch predicates can run on Trinity with authenticated input mirrors. Missing mirrors cause a local failure. This dispatch does not have the large export/dependency archives or the original SHA-pinned r10 source deliveries. The 3 GB workspace cap also prevents staging a complete production export here.

The supplied package names, payload comments and native operational scripts violate the requested strict forbidden-word policy. The wrapper rejects them before transport, including when `--yes` is supplied. There is no policy bypass. Generated remote commands received syntax checks only; no remote placement, fill, CPU job or GPU submission ran during this task.
