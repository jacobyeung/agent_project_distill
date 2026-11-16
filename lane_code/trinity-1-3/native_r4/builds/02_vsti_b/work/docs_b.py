from pathlib import Path
import sys,shutil,json
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *
a=B.parent/'01_vsti'
# Preserve the fallback runner and refresh only its local build references.
p=B/'out/ASSETS.json';p.write_text(p.read_text().replace('builds/01_vsti','builds/02_vsti_b'))
shutil.copytree(a/'work/pins',B/'work/pins',dirs_exist_ok=True)
shutil.copyfile(a/'out/SPEC.json',B/'out/SPEC.json')
text=(a/'out/RUN_TRINITY.md').read_text().replace('builds/01_vsti','builds/02_vsti_b').replace('/r01_','/r01b_')
text='Trinity is the fallback. Orchard instructions are in `out/RUN_ORCHARD.md`.\n\n'+text
text+='''
Full-frame preparation uses the existing `adapt` command above. It requires all 311 scenes in the item list, tolerates the unused extra scene, verifies each selection and PNG SHA, and writes bound inputs. The two-scene test is `tests/test_read.py:test_adapter_truth_separation`; the actual sample contains nine items. Partial frame staging cannot produce a production bound list.

The non-synthetic report now requires the proof pin carried by the item completion. Run the separate historical proof first, copy its PROOF.json unchanged into the read root as `run/P0.json`, and add `--proof-result /r/P0.json` to each `run` or `job` command. This binds its outcome to the read request; the merge carries it into the report. The proof compares the original prepared arrays as well as token streams. Its keys are `out/PROOF_KEYS.json`.

Run the release-video check after both inputs land:

```bash
./work/py code/pixels.py --videos /scratch/jjyeung/orch_n30/native_r4/in/vsti/release5 --frames /scratch/jjyeung/orch_n30/native_r4/in/vsti/frames --media /scratch/jjyeung/orch_n30/native_r4/in/vsti/media.json --pins /scratch/jjyeung/orch_n30/native_r4/work/orchard_small/videos.json --out out/RELEASE_CHECK.json
```

The script requires av 17.1, checks release-video and PNG SHA pins, counts decoded frames, records fps, and measures each selected frame's maximum/mean absolute difference and PSNR. Infinite PSNR is encoded as a null value with `psnr_infinite: true`. Current release status is `out/RELEASE_CHECK.json`; the synthetic MP4 test is `out/RELEASE_CHECK_SYNTHETIC.json`. Pass `--release-check` with that result to the report command.

Run the namespace rehearsal outside the Codex sandbox:

```bash
./work/py out/rehearsal/run_rehearsal.py --fixture-tower
```

This uses private shared memory and the production token/error-response loop. The exact command and namespace result are written to `out/rehearsal/NAMESPACE.json`. V1's operator rehearsal passed; this build does not infer V1b namespace success from it. V1b's in-sandbox library and CLI results are `work/rehearsal_b/RESULT.json` and `work/cli_b/RESULT.json`.
'''
(B/'out/RUN_TRINITY.md').write_text(text)
(B/'out/rehearsal/RUNBOOK.md').write_text('Run outside the sandbox on the assigned compute node:\n\n```bash\ncd '+str(B)+'\n./work/py out/rehearsal/run_rehearsal.py --fixture-tower\n```\n\nThe fixture flag applies to both the namespace command and its CPU fallback. A namespace failure is recorded separately from a passing library rehearsal.\n')
(B/'out/RUN_ORCHARD.md').write_text('''Orchard is primary. This build prepares the packet; it does not upload or submit it. The current family is `out/FAMILY.json`, code is `out/c.tar`, and the historical reference plus read metadata is `out/d.tar`. `out/PACKAGE.json` records their SHA256 values. The family embeds the original 170056 configuration, so the job stages C8r's runtime, base, export, numpy, FLA, trainer and dev-S1 assets through its existing staging code and generation pins.

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
''')
(B/'out/SIZING.md').write_text('''The planning rates below are the operator-supplied measurements from job 170056. No `/data2` source was read. These are projections, not measurements of this build.

| Phase | Projection in seconds | Basis |
|---|---:|---|
| Staging and one load | about 1,800 | 170056, excluding geometry |
| Pose tower | 1,181.8 | 311 scenes × 3.8 s at 32 frames; about 10 GB peak |
| Own scale/gravity | 311 × g | g is unmeasured; PHASES.json records this phase |
| Proof geometry | p × g | p is the number of distinct selected captures; original conditioning questions |
| Proof decode and repeat | 159.8–879.8 | Twice (3 × 6.0 + 3 × 7.3 + 4 × [10,100]); rotation is unmeasured, so this range is an assumption |
| Read canary | 86.6–626.6 | 2 × 6.0 + 2 × 7.3 + 6 × [10,100] |
| Remaining camera items | 638.4 | 48 × 6.0 + 48 × 7.3 |
| Remaining other items | 3,440–34,400 | 344 × [10,100], unmeasured |
| Extra checkpoint restorations | L | Unmeasured; separate preparation, proof and read processes |
| Return reserve | 300 | Explicit scheduling allowance, not a measured transfer duration |

The measured-rate subtotal excluding scale/gravity, proof, additional restoration and return is 7,146.8–38,646.8 seconds. The upper estimate exceeds C8r's 21,600-second GPU cap. A complete first job is therefore not promised. The absolute deadline is also enforced across the GPU subprocesses. Staging consumes real time before the deadline but is outside the inherited GPU-phase counter.

`out/CANARY_KEYS.json` contains four camera and six other keys. Preserving those exact keys leaves 96 camera and 344 other items. The requested 90/350 remainder is inconsistent with that fixed canary; the kit preserves the keys.

The worker observes the duration of each complete item pair, including the scripted arm when present. It predicts the next item as 1.25 × the maximum duration observed for its type, with a floor of 6.0 seconds for displacement or 7.3 for direction. An unseen other type starts at 100 seconds. The canary receipt projects all remaining items with the same rule. It starts an item only if current time + prediction is at most deadline − 300 seconds. This rule is conservative relative to observations; it cannot guarantee an unseen slow item finishes before the deadline. The subprocess timeout enforces the bound and the journal preserves the last committed item pair.
''')
