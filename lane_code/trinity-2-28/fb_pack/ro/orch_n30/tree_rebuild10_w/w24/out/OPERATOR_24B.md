The n kit binds P’s real step-400 export and export-only receipt. It requires no handover fill or step-600 file.
The q kit proves the same export. The n allocation requests advanced, four GPUs, four ranks and one launcher.

Apply the build24 stream first, then the files in `UPLOADS_24B.list`. The delta replaces the opaque source-archive filename already present in each kit, so it introduces no obsolete kit member. `SHA256SUMS.txt` must match the entire final kit directory.
The delta’s stream root is `work/build24b/upload`. `UPLOADS_24B.json` contains only added or changed files against both kit sets in `UPLOADS_MINIMAL.json`.

Resolve n on its host with the existing resolver interface:

```bash
python3 -I -s -B /project/community/jjyeung/okh7/x_22c714e1/n/b/resolve.py --pool /project/community/jjyeung/okh7 --output /project/community/jjyeung/okh7/x_22c714e1/rn.json
```

The optional listing argument can still name the existing listing. Without it, the resolver uses the four exact `x_22c714e1/w/0..3` paths and the existing `x_22c714e1/l.json` metadata inventory; if that inventory is absent, it uses the established `okh7/m/<sha256>` metadata paths. Every file remains checked against P’s authenticated metadata. The combined export length and hash are pinned in the kit. No runtime discovery changes a configuration pin or seal.
The small archive must contain the exact pinned MANIFEST.json and all its checked members. The raw s.tar and full metadata bytes were unavailable locally; verification of those bytes runs on the host.
DONE/e/r/RP and the small-file manifest are pinned. Only e/r admit the init; the checkpoint pointer in RP is never selected or loaded.

Pass the resolved record to n/job.sh through the normal submission workflow. The allocation stages data, runs the guard, then its own mode-q canary and room audit. With GO=false it trains no step.
The existing production approval must supply `/tmp/q_22c714e1/v.json`, the admitted prepared configuration, when GO is granted. It must retain the canary’s exact config identity and four ranks, and bind the native host/review receipts. Its preparation receipt must include the same r1_training inputs. All native review, source, preparation and allocation checks still run.
After the canary passes, the kit starts one launcher with `--nnodes=1 --nproc_per_node=4`; it supplies no resume checkpoint. No source acceptance check or admission gate is bypassed.

The guard requires at least 75 GiB, emits one sanitized diagnostic and refuses read failures with E42. No tower-scale freeze is configured.
No upload, submission, GPU execution or production approval was performed by this build.
