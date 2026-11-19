from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'out/NOTE_FOR_TREE_REBUILD.md';s=p.read_text().replace('868.441 s','1016.666 s');p.write_text(s)
p=ROOT/'out/kit_timing/README.md';s=p.read_text()
s=s.replace('the 0–3-second metric estimate remains insufficiently resolved', 'the estimated ≤0.1-second metrics gain remains unresolved')
s=s.replace('expected to save approximately zero seconds under low reuse', 'expected to save at most zero seconds under low reuse: misses add a read and SHA-256')
a=s.index('`PLAN` can be');b=s.index('\nBoth GPU kits',a)
s=s[:a]+'''For continuation acceptance, first run `write_plan.py --tree "$TREE" --config "$CONFIG" --receipt "$RECEIPT" --resume-pin "$RESUME_PIN" --steps 10 --out "$PLAN"`. The writer uses the same sampler arguments as native `run_steps`, starting at the pinned checkpoint step plus the configuration's row offset. Use a fresh plan file.

Run `data_only.py --steps 10 --require-coverage` for four rank projections and OFF/prefetch arms, serially, in separate processes. The exact commands are in [NOTE_FOR_TREE_REBUILD.md](../NOTE_FOR_TREE_REBUILD.md). This audit costs about 42 minutes estimated from the supplied data timer; allow 45–60 minutes including startup and hashing. `--full-plan` remains available to inspect every supplied plan but is not required for a complete epoch.

The kit requires actual nonzero augmented pose calls, records worker thread names, and checks every emitted processor grid against `[32,20,26]`. It refuses missing augmented-pose coverage. Sidecars record the continuation step/pin, checked plans, grid and augmentation coverage, group tensor bytes including targets/audits, and Linux process `peak_rss_bytes`. RSS includes the worker's deep-copied receipt/processor and all startup allocations. The default 1-GiB group guard still applies; the audit keeps optional fallback OFF. `align_settings` follows the receipt so teacher-aligned pose targets receive the real validation.

This audit compares hashes and row draws, with unchanged Python/NumPy/torch RNG. It does not load a model or prove GPU loss/gradient equality. Hash time is included in wall time and reported separately. GPU-copy and simulated-consumer variants cannot establish a training speedup. Run on the actual production processor; the local CPU environment lacks torchvision.

For a short numerical acceptance replay, use [kit_profile/replay.sh](../kit_profile/replay.sh), not the long precision experiment above. It runs OFF, OFF, ON, one update each from the same checkpoint and audited plan. `replay_compare.py` requires bitwise ON losses when OFF repeats agree, otherwise ON deviations no larger than the per-scalar OFF spread, with identical CPU inputs in either case. It also requires ON step provenance. Estimated wall time is 30–60 minutes total; each leg has a 60-minute limit and no automatic retry. This acceptance policy is separate from the long timing experiment's stricter bitwise parity gate.
'''+s[b:];p.write_text(s)
p=ROOT/'out/kit_profile/README.md';s=p.read_text()
s+='''
## Continuation acceptance replay

`replay.sh` uses `launch.py --mode replay`: one update, zero warmup and no profiler. It runs OFF, OFF, ON in that order from the same explicit `RESUME_PIN` and CPU-audited `PLAN`. Set `AUDIT_DIR` to the eight completed data audits and `OUT` to fresh scratch. Hold 03 constant with `REPLAY_METRICS=0|1`; 02 and fallback remain OFF. `RESUME_CONFIG` supplies the original checkpoint configuration when needed by the source-only bridge.

The exact invocation, CPU plan writer, metric fields and acceptance rules are in [NOTE_FOR_TREE_REBUILD.md](../NOTE_FOR_TREE_REBUILD.md). Estimate 30–60 minutes total for three cold one-step replays and startup/restore. Each leg has a 3,600-second cap, heartbeat and no retry. This replay is separate from the 895-second instrumented profile above. `kit_timing/replay_compare.py` checks the completed legs and writes `acceptance.json`; missing ON `performance.C1_CPU_PREFETCH="1"` fails the gate.
''';p.write_text(s)
p=ROOT/'out/SOURCE_NOTES.md';s=p.read_text().replace('A complete epoch plan on every rank is required before production prefetch.', 'The bounded first-10-update continuation plan is audited on every rank and both arms before production prefetch; every emitted grid and actual augmented-pose coverage must pass.')
s=s.replace('The likely direct gain is well under one second, still unmeasured.', 'The likely direct gain is approximately zero, estimated at ≤0.1 s/update: grid/carrier scalar reads still wait after backward.')
s+='''
## Round-3 audit and fallback semantics

`B = /scratch/jjyeung/orch_n30/so_step/work/b21_final/work/tree_r1`. The fallback discards prepared tensors after the storage guard trips and calls the unchanged `fetch`/`fetch_nominal` with the original main-thread `Rows`. It introduces no worker collective or CUDA call. The optional value shares the existing preparation payload, and default OFF retains the three-value switch tuple. `tests/test_so_round3.py` compares exact tensor bytes, all gradients, updated weights, optimizer state and numerical records against synchronous OFF. The lane test additionally forces only rank 1 over budget and checks admitted rows, collectives and shared failures.

Storage accounting uses `E/torch/storage.py:71–75,1036–1045`. The byte comparator checks dtype and shape before comparing uint8 views because value equality does not prove byte identity (`E/torch/_torch_docs.py:4066–4085`); its signed-zero regression remains active. Official [storage](https://docs.pytorch.org/docs/2.11/storage.html) and [equality](https://docs.pytorch.org/docs/2.11/generated/torch.equal.html) pages were checked on 2026-11-19. No new framework scheduling behavior is assumed by the fallback.

The CPU audit uses `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` for process lifetime maximum RSS, converted from Linux KiB to bytes. Separate arm processes keep their peaks independent; the result includes all threads, startup and receipt/processor copies. See Python's [resource usage documentation](https://docs.python.org/3.12/library/resource.html#resource.getrusage). This is not worker-only RSS or a total-memory bound. Real production RSS remains unmeasured here.

The real train-startup CPU regression mocks transport/device selection, then restores CPU availability for the actual optimizer update. Installed torch `E/torch/optim/optimizer.py:451–474` selects a graph-capture check from accelerator availability; advertising mock CUDA availability during a CPU AdamW update would invoke the unavailable CUDA stub. The test retains actual CPU row preparation, model math and optimizer execution.
''';p.write_text(s)
