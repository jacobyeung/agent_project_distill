# Build H1-kit-3: bind the dev-S1 item sets, relocatable R0 pin, H1-0 launcher over b04's make_real (CPU only)

You are a Codex builder for lane h1_headsft on Trinity node trinity-3-30. Workspace `K=/scratch/jjyeung/orch_n30/h1_headsft/kit`
(write only inside K). It holds builds 1 and 2: read `K/BUILD_REPORT.md` and `K/BUILD_REPORT_BUILD1.md` first and keep
everything that passes. Work autonomously; where something is ambiguous, choose the conservative option, record it in
`K/BUILD_REPORT.md` and continue.

## Rules for the build (binding)
- Trinity rules: never run recursive grep/find/du/ls -R or any search over `/home` or `/data*`; read named files there
  only, in bounded parts. Bounded `find -maxdepth 6` is allowed inside the named `/scratch` paths below.
- No Git. No ssh/scp/rsync/network. No GPU (`CUDA_VISIBLE_DEVICES=""`). No deletion or modification outside K; all
  inputs are read-only (copy into K what you must change and record the source sha256).
- Disk is tight on this node (the node must keep 200 GiB free; about 7 GiB of headroom remain): put every temporary
  and pytest basetemp under ONE directory `K/tmp/b3/`, never copy the tree or model files per test, and keep this
  build's new files under 300 MB in total. Report the size you added.
- Python `/scratch/jjyeung/envs/p1cpu/bin/python -B` through `K/cpu.sh`; at most 32 GB RAM and 16 threads.
- No answer post-processing: the model converts units and formats numbers itself.

## Deliverables (priority order; tests pass before moving on)
1. Item sets (`h1eval/cli.py items build`):
   - `devs1_routed` becomes ready: camera tasks from
     `/scratch/jjyeung/orch_n30/b01_d0guard/work/from113/work/meta/sj/orch_cd/legs1_routed/out2/CAMERA_TASKS.jsonl`
     (must hash to the native pin f59090ffc8fd0f4d80a2b049e2624660c0f46dbc1d26016145f4747850a432ac); distance and
     room tasks from the sources build 2 recorded; the 636 IDs must equal the native inventory exactly (150 per camera
     type, 150 distance, 36 room). Check every camera task's frames against `rows/expected_calls.py` (the expected
     `<move|turn from=i to=j>` must parse from each question) and report the parse rate (target 100%).
   - `devs1_direct_main` ready: the 1,525 main tasks (`TASKS.jsonl`, sha a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e,
     from build 2's recorded source). Keep `devs1_direct` (with the 300 facing twins, pins 730ed536... and 4d6c3a94...)
     refusing until those payloads are supplied.
   - Rerun the R0 check on every ready set; report counts.
2. Relocatable R0 pin: copy `/scratch/jjyeung/orch_n30/h1_headsft/work/auth/R0_ROOMS.txt` and `R0_DEV_ROOMS.txt` into
   `K/auth/` (sha256 verified: R0_ROOMS bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3); configs and
   the CLI reference them relative to the kit root so a copied kit (another node, or the Orchard kit directory)
   resolves them; the pin is still checked by sha256. The test that failed in a relocated copy
   (`tests/test_rows.py::Rows::test_configs_keep_d0`, "Missing or changed pinned input") must pass from a copy of K at
   another path (prove it in `K/tmp/b3/relocated/`).
3. H1-0 launcher `K/h1eval/h10/` (the read of step 544 on trinity-1-13 cards; b04's reader core does the decoding):
   - Interface agreed with lane b04: `make_real(export_dir, artifact_manifest, items, *, perception_factory=None,
     device) -> generator(item)`, built on b04's `e2e_reader.core.E2EGenerator` and `e2e_reader.real.real_perception`
     (None = b04's tower perception). b04 has not published it yet: import it from a path given on the command line
     (`--reader-root`), and refuse with a clear message if it is absent. Do not implement model loading yourself.
   - `perception_own.py`: `perception_factory(artifact, model, device) -> Perception` implementing the interface of
     b04's `e2e_reader/generate.py::Perception` (`lazy(frames, prefill_state, timings) -> (route map, built)`), using
     build 1's own adapter (camera calls from the prefill's own pose9/gravity/depth; ground/gap lifted with own
     depth+pose, scale 1, no G3T, no guard) and build 1's perturbation modes.
   - `launch.py --items <manifest> --shard i/n --export <dir> --artifact-manifest <file> --reader-root <dir>
     --arms own,tower --modes <list> --out <dir> --device cuda:0`: runs every item of its shard for each arm and mode,
     appends one JSONL record per (item, arm, mode) with flush, and resumes by skipping completed records; writes the
     shard's environment, hashes and timings. `merge.py <out dirs...>` feeds `h1eval.cli` scoring and writes curve.json.
   - `run_card.sh <card> <i/n> <out>`: runs launch.py under `/data3/shared/scripts/vnice/vnice.sh` (check how its usage
     line reads, by reading that one file) with `CUDA_VISIBLE_DEVICES=<card>`, `nice`, logs to `<out>/log`. It must not
     start if `nvidia-smi` shows the card in use (memory used > 1 GiB) and prints why.
   - `cpu_first_batch.py --export <dir> --heads <heads.pt> --reader-root <dir> ...`: one dev-S1 item per call type
     (move, turn, ground/gap) through make_real on CPU in the own arm and one perturbation; prints call records,
     responses, finish reasons and seconds. Do not run it on real weights (they are not on this node).
   - Tests with a fake `make_real` (tiny model, build 1's fixture): sharding covers every item exactly once across
     shards; resume skips done records; the own perception serves every call type; the tower arm passes through
     untouched; run_card.sh refuses a busy card (mock nvidia-smi).
4. Update `K/BUILD_REPORT.md` (append a "Build 3" section: every test command with pass/fail counts, sizes added,
   what is unverified), `K/SHA256SUMS`, and add `K/h1eval/h10/RUN_H10.md` (at most 40 lines: staging list for 1-13
   with sizes — the step-544 export already in /dev/shm/jjyeung/exports/m544, heads.pt from the step-544 stop export,
   SAM 3, selector run_raw, frames; commands per card; expected card-hours; what the operator checks first).
