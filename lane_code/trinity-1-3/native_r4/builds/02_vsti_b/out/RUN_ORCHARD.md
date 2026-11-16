Orchard is primary. This build prepares the packet; it does not upload or submit it. The current family is `out/FAMILY.json`, code is `out/c.tar`, and the historical reference plus read metadata is `out/d.tar`. `out/PACKAGE.json` records their SHA256 values. The family embeds the original 170056 configuration, so the job stages C8r's runtime, base, export, numpy, FLA, trainer and dev-S1 assets through its existing staging code and generation pins.

The additional assets are fixed:

| Name | Contents | Primary path | GCS name |
|---|---|---|---|
| a.tar | Frozen weights and configuration | /project/community/jjyeung/okh7/d9c35d0a/a.tar | q8/d9c35d0a/a.tar |
| b.tar | The prepared frames folder | /project/community/jjyeung/okh7/d9c35d0a/b.tar | q8/d9c35d0a/b.tar |
| c.tar | This code package | /project/community/jjyeung/okh7/d9c35d0a/c.tar | q8/d9c35d0a/c.tar |
| d.tar | Original reference outputs and small input metadata | /project/community/jjyeung/okh7/d9c35d0a/d.tar | q8/d9c35d0a/d.tar |

The weight and configuration member hashes are sealed in `FAMILY.json:tower_members`. `a.tar` must contain `model.safetensors` and `config.json`; `b.tar` must contain `frames/<cache-id>/selection.json` and its PNGs. The incoming upload receipt is expected at the lane's `work/streams/native_r4_upw.RECEIPT.json`. Its SHA was not available during the build. No guessed SHA or generation is accepted. `out/ADDITIONS.pending.json` shows the missing fields.

On Orchard, place the package files under an opaque local path, for example `/tmp/d9c35d0a`, and extract c.tar there to `c/`. Upload the four archives to the primary paths above and their GCS names through the operator's authorized transport. Uploading is not part of this build. Write `/tmp/d9c35d0a/g.json` as an object mapping `a`, `b`, `c`, `d` to their actual GCS generation numbers. The verifier streams each generation once, checks its complete SHA against the primary copy, and never retries a failed stream.

```bash
cd /tmp/d9c35d0a
/usr/bin/python3 -s -B c/u.py --family FAMILY.json --generations g.json --out r.json
/usr/bin/python3 -s -B c/o.py packet --family FAMILY.json --receipts r.json --out /tmp/d9c35d0a/5d648e9274d54fba92aef108 --token 5d648e9274d54fba92aef108 --deadline-utc 2026-11-16T16:15:00Z
sbatch /tmp/d9c35d0a/5d648e9274d54fba92aef108/a.sh
```

The packet requires all four verified upload records. Its job name is `a15_cot_ap` followed by the opaque token. It requests one H100 in general. All newly introduced transport paths, arguments identifying inputs, environment settings and log names are opaque. Existing C8r asset locations retain the original family names as required. The old `orchard.py` and `venue.py packet` interfaces remain inherited fallback code; `o.py` is the V1b primary packet entry.

The job runs stage, pose tower, own scale/gravity preparation, the isolated original-policy proof, and then the read. The proof selects three displacement, three movement-direction and four rotation items from 170056. It repeats decoding, compares tokens/calls/responses/answers, and recomputes proof-capture geometry from the original raw cache with the original conditioning questions. Prepared arrays are present in the reference return, so scale, camera_to_world and K are compared bitwise. A divergence is recorded and the read continues; an exception, call error or replay mismatch stops the job.

The read starts with the fixed V1 canary, then the remaining camera keys, then the other keys. The canary contains four camera items: the resulting remainder is 96 camera and 344 other items, as recorded in `out/DECISIONS.md`. `--deadline-utc` defaults to 2026-11-16T16:15:00Z. Before each item the worker reserves 300 seconds for the return and applies a 1.25 margin to its measured rate. It returns a complete journal with missing keys when the next item would cross that boundary. A partial report has no complete primary score. The full return cap remains C8r's 300,000,000 bytes.

Returns use `/project/community/jjyeung/okh7/n2r/<token>` and `gs://cmu-gpucloud-jjyeung/q8/n2r/<token>/`. The return includes the input manifests, request, prepared geometry arrays, proof, canary, committed journals, missing keys and report. It omits frame pixels and raw tower arrays. The job reconstructs and rechecks frame pixels from b.tar on resume.

For a second job, preserve the first returned archive unchanged. Write `/tmp/d9c35d0a/s.json` with its absolute Orchard-local `path` and SHA256 `sha256`, obtained from the returned EXIT receipt. Use a fresh token and the desired later deadline:

```bash
/usr/bin/python3 -s -B c/o.py packet --family FAMILY.json --receipts r.json --out /tmp/d9c35d0a/9ea1cfc0b79848029c0e53d4 --token 9ea1cfc0b79848029c0e53d4 --deadline-utc 2026-11-17T16:15:00Z --resume /tmp/d9c35d0a/s.json
sbatch /tmp/d9c35d0a/9ea1cfc0b79848029c0e53d4/a.sh
```

The second job verifies request, config, geometry and input pins; it skips completed keys and merges the two journals as disjoint shards. `RESULT.json:segments` lists their order. Its return is cumulative; do not also merge the first archive a second time. A crash before preparation or proof completes is a failed job, not a resumable read. No failed job is relaunched by this kit.

Unchecked: actual Orchard staging, namespace closure, H100 execution, deadline return timing and both remote return channels. CPU tests exercise packet admission, geometry equality, report requirements, rate decisions and disjoint resume. The final line census distinguishes those tests from unexecuted venue and GPU paths.
