Trinity is the fallback. Orchard instructions are in `out/RUN_ORCHARD.md`.

The runner requires completed local assets. This build does not certify the production namespace or submit a job. `out/ASSETS.json` lists the expected sources; `out/UNEXECUTED.md` lists untested lines. Run on the assigned compute node, within the user's existing allocation and IO rules.

Use the build's interpreter wrapper for host preparation:

```bash
cd /scratch/jjyeung/orch_n30/native_r4/builds/04_vsti_d
./work/py code/entry.py adapt --items /scratch/jjyeung/orch_n30/native_r4/in/vsti/vstibench_repr_450_v3.json --media /scratch/jjyeung/orch_n30/native_r4/in/vsti/media.json --frames /scratch/jjyeung/orch_n30/native_r4/in/vsti/frames --out work/input --logical-root /i
./work/py -c 'from pathlib import Path; Path("work/input/SPEC.json").write_bytes(Path("out/SPEC.json").read_bytes())'
```

Stage the runtime, FLA and small metadata archives into a fresh local root. The expanded runtime exceeds this build's storage allowance, so this operator command uses a separate scratch root and a larger explicit staging allowance. It was not run during the build.

```bash
./work/py code/venue.py stage --assets out/ASSETS.json --root /scratch/jjyeung/orch_n30/r01c_stage --budget 48000000000
./work/py code/venue.py plan --assets /scratch/jjyeung/orch_n30/r01c_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01c_run --gpu 0
```

The plan must report no missing paths. It invokes the host bwrap and wraps GPU execution with the required vnice script. Its shared-memory folder lives under the private root, never in host shared memory. The runner preserves the checkpoint's logical paths through read-only mounts. Additional preparation dependencies must be supplied if the original authenticated loader rejects them; this build has not established that closure.

For a single complete job, run the integrated path so the sealed deadline includes restoration and geometry:

```bash
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01c_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01c_run --gpu 0 -- job --bound /i/BOUND.json --spec /i/SPEC.json --out /r/cell --limit 21600
```

For shared geometry and separate item shards, prepare geometry once and then decode:

```bash
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01c_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01c_run --gpu 0 -- geometry --bound /i/BOUND.json --spec /i/SPEC.json --out /r/g
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01c_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01c_run --gpu 0 -- run --bound /i/BOUND.json --spec /i/SPEC.json --geometry /r/g/scaled/GEOMETRY.json --out /r/j0 --shard 0/1 --limit 21600
```

A canary-only smoke run uses a fresh output:

```bash
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01c_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01c_run --gpu 0 -- run --bound /i/BOUND.json --spec /i/SPEC.json --geometry /r/g/scaled/GEOMETRY.json --out /r/canary --canary-only
```

For several assigned cards, use a fresh pair of outputs with the same bound inputs and geometry. Start the second command after the first shard writes a passed CANARY receipt. Each command has its own journal. A separate canary-only run is diagnostic; shard zero still executes the canonical canary.

```bash
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01c_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01c_run --gpu 0 -- run --bound /i/BOUND.json --spec /i/SPEC.json --geometry /r/g/scaled/GEOMETRY.json --out /r/s0 --shard 0/2
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01c_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01c_run --gpu 1 -- run --bound /i/BOUND.json --spec /i/SPEC.json --geometry /r/g/scaled/GEOMETRY.json --out /r/s1 --shard 1/2 --canary-receipt /r/s0/CANARY.json
```

Merge and report on CPU inside the same namespace so absolute pins resolve. The CPU mode uses the specified interpreter and numerical overlay.

```bash
./work/py code/venue.py run --cpu --assets /scratch/jjyeung/orch_n30/r01c_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01c_run -- merge --bound /i/BOUND.json --out /r/MERGED.json /r/s0 /r/s1
./work/py code/venue.py run --cpu --assets /scratch/jjyeung/orch_n30/r01c_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01c_run -- report --merged /r/MERGED.json --out /r/report --comparators /scratch/jjyeung/orch_n30/native_r4/in/comparators/f17.per_question_scores.jsonl /scratch/jjyeung/orch_n30/native_r4/in/comparators/p1m200.per_question_scores.jsonl
```

For interrupted reads, add `--partial` to merge. It lists missing keys and suppresses the complete primary. Interrupted journals retain their last durable completion checkpoint. A partial merge authenticates only the committed byte prefix. It ignores an unfinished append and reports its uncommitted item as missing.

Historical proof preparation and GPU repeats use a separate root and the original assets:

```bash
./work/py code/proof_stage.py --root /scratch/jjyeung/orch_n30/r01c_proof_assets --assets /scratch/jjyeung/orch_n30/r01c_stage/ASSETS.json --family /scratch/jjyeung/orch_n30/native_r4/work/c8r/FAMILY.json --code /scratch/jjyeung/orch_n30/native_r4/work/c8r/code_c8r.tar --objects /scratch/jjyeung/orch_n30/native_r4/from113/work/obj --reference work/proof_reference.json --request work/proof_request.json --returned /scratch/jjyeung/orch_n30/native_r4/from113/work/full_c8r/result.tar.gz
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01c_proof_assets/ASSETS.json --root /scratch/jjyeung/orch_n30/r01c_proof_run --gpu 0 -- proof --reference /i/REFERENCE.json --request /i/REQUEST.json --spec /i/SPEC.json --out /r/proof
```

The selected keys and their source are `out/PROOF_KEYS.json`. The proof writes both runs and PROOF.json; it checks the original adapters before decoding. Neither GPU command nor large staging command was executed in this build.

Full-frame preparation uses the existing `adapt` command above. It requires all 311 scenes in the item list, tolerates the unused extra scene, verifies each selection and PNG SHA, and writes bound inputs. The two-scene test is `tests/test_read.py:test_adapter_truth_separation`; the actual sample contains nine items. Partial frame staging cannot produce a production bound list. Full adaptation passed on all 311 scenes and 9,952 PNGs; see out/FULL_ADAPT.json.

The non-synthetic report now requires the proof pin carried by the item completion. Run the separate historical proof first, copy its PROOF.json unchanged into the read root as `run/P0.json`, and add `--proof-result /r/P0.json` to each `run` or `job` command. This binds its outcome to the read request; the merge carries it into the report. The proof compares the original prepared arrays as well as token streams. Its keys are `out/PROOF_KEYS.json`.

Run the release-video check after both inputs land:

```bash
./work/py code/pixels.py --videos /scratch/jjyeung/orch_n30/native_r4/in/vsti/release5 --frames /scratch/jjyeung/orch_n30/native_r4/in/vsti/frames --media /scratch/jjyeung/orch_n30/native_r4/in/vsti/media.json --pins /scratch/jjyeung/orch_n30/native_r4/work/orchard_small/videos.json --out out/RELEASE_CHECK.json
```

The script requires av 17.1, checks release-video and PNG SHA pins, counts decoded frames, records fps, and measures each selected frame's maximum/mean absolute difference and PSNR. Infinite PSNR is encoded as a null value with `psnr_infinite: true`. The decoder asserts that the full frame count equals selection.total_num_frames. Current release status is `out/RELEASE_CHECK.json`; the synthetic MP4 test is `out/RELEASE_CHECK_SYNTHETIC.json`. Pass `--release-check` with that result to the report command.

Run the namespace rehearsal outside the Codex sandbox:

```bash
./work/py out/rehearsal/run_rehearsal.py --fixture-tower
```

This uses private shared memory and the production token/error-response loop. The exact command and namespace result are written to `out/rehearsal/NAMESPACE.json`. This build's namespace attempt and CPU fallback are recorded in `out/rehearsal/RESULT.json`; the CLI rehearsal is `work/cli_d_final/RESULT.json`.

The full selected-frame index comparison and its missing input are documented in `out/FRAME_CHECKS.md`. The real release-video check completed; none of the selected frames is byte-identical. See `out/RELEASE_CHECK.json`.
