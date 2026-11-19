VERDICT: NO-GO

The kit cannot be staged or run on trinity-2-28 as delivered, and its comparator gives wrong verdicts in both directions. The launcher, card gate, OOM handling and sealed-reader invocation are sound. Findings 1-4 block. Downloads can start once finding 2 is fixed. The run waits on findings 1, 3 and 4.

Paths: `K` = `/scratch/jjyeung/orch_n30/so_reads228/out`, `A4` = `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4`, `CO` = `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30`.

Evidence run: 39/39 CPU tests pass. They ran from `work/patch_apply/read228/`, which is byte-identical to `K` for every script, the tests and STAGE_PLAN. Two comparator probes ran from the same copy and wrote only `work/tests/review_probe_*`.

## Findings

1. **HIGH: the runtime environment is unresolved, so the kit cannot run.**
   - `K/ENVIRONMENT_TODO.md:3-7,17` says the bytes of `q/env.json` are absent, the a2/a4 member lists are unknown, and "These unresolved steps prevent a claim that the deployment is ready to execute."
   - `K/STAGE_PLAN.json:44` has `"versions": null`. Every runtime group carries a "Resolve member-to-archive map" todo (`:54`…`:188`).
   - `K/stage228.py:126-127` requires the Python prefix to be under `/scratch/jjyeung/envs`. A4 instead selects `/scratch/jjyeung/b01ec87a6f29b/d/v/py` plus `d/v/site` (`ENVIRONMENT_TODO.md:7`), and Orchard ran that env from `/lustre/fsw` through bwrap.
   - The relocated env must lie inside settings `env_roots` and the e2e_reader audit roots. Otherwise `generate_real` raises PermissionError on the first item.
   - The control Python `/scratch/jjyeung/envs/p1cpu/bin/python` is the default at `K/run228.sh:7` and `K/compare228.sh:7`. It appears nowhere in STAGE_PLAN, and the control process imports `h1eval.items` → `student_pilot.h1_r0`.
   - Smallest fix:
     - After the downloads, list the a2/a3/a4 and r0-r2 members on 2-28 `/scratch`.
     - Record the archive-to-env map and the `q/env.json` versions in STAGE_PLAN `environment`.
     - Make `d/v/py` resolve to the `/scratch/jjyeung/envs` prefix, and confirm that `env_roots` and the audit roots cover it.
     - Add p1cpu to the plan, or set `READ228_CONTROL_PYTHON` to the staged reader Python.
     - Run `stage_check(prepare=True)` before the idle gate.

2. **HIGH: the IO plan cannot be executed and contradicts the one-stream-per-download rule.**
   - `K/STAGE_PLAN.json:883-884` sets `"streams": 1` with the instruction "register ONE sequential stream".
   - The plan has 22 `Orchard_IO_governor_stream` entries (43.1 GB). All 22 have `register_command` and `launch_command` set to null (e.g. `:451,:453`) and `"governor_readme_mirrored": false`.
   - The README is readable at `/data3/jjyeung/orch_n13_20261026/io_governor/README.md`. Its lines 63-71 require, per stream, `ratelimit.py` in the data path, a root started stopped (state T), and a `register.py --pid … --rl-pid … --expected-bytes … --allow-resume`. Line 4 says the governor itself serialises admission.
   - No entry names its source host or transport. The r0-r2 parts are `/home/jjyeung/okit/p/...` paths with no host. If those are Trinity `/home`, they are NFS reads and still need a stream.
   - Smallest fix: emit one stopped `ratelimit.py` pipeline and one `register.py` record per file. Each record gets its own `--lane` name, `--expected-bytes` set to the pinned size, `--tier 3` and `--allow-resume`. Register all of them at once from trinity-2-28.
   - Each pipeline originates on 2-28 (`ssh <orchard> cat <path> | ratelimit.py … > /scratch/jjyeung/a4228/archives/...`). Nothing relays through another node, the head node or a laptop. Name the host for every source. Keep the existing sha256 check after each stream.

3. **HIGH: "call placement" includes perception internals, so a correct Ada run would be ruled DIAGNOSTIC_ONLY.**
   - `K/compare228.py:26-34` keeps every call-record field except `response`, `forced_tokens`, `seconds` and `timings`. The whole `stage1` block therefore enters the 50/50 gate: SAM3 scores, selector logits and candidate inputs.
   - In the first 50 Orchard rows, 21 items have 63 call records, and those records carry 17,747 float leaves. Bitwise equality of these across H100 and Ada kernels is not to be expected.
   - Probe: I moved `stage1.sam3.max_score` of `vsi590k_042674` by one ulp (`math.nextafter`) and left text, tokens, tool, arguments and order unchanged. The result was `call_placement` 49 and verdict DIAGNOSTIC_ONLY.
   - The ruling defines placement as which tool, order and arguments (`PROMPT_so_reads228.md:8`). The kit's own README (`K/README.md:54`) lists order, literal arguments, service status and token position, and nothing from `stage1`.
   - Smallest fix: make `calls()` return `[(i, r['family'], r['call'], r['served'], r['at_token'])]` and report `stage1` under trace. Add a test that `stage1` float drift still gives SAME_INSTRUMENT.

4. **HIGH: the provenance check is optional, so an Orchard return passes as the 2-28 run.**
   - `K/compare228.py:101-103` checks `LOCAL_RUN.json` only `if info.exists()`. The Orchard `ret/` has no such file.
   - `compare(reference, reference)` returns SAME_INSTRUMENT with `eligible=True`. `K/tests/test_kit.py:244-246` asserts this as the passing case, and my probe reproduced it. Any copy or rerun of the Orchard return is therefore certified as the Ada device check.
   - Smallest fix: on the trinity side, refuse unless all of the following hold:
     - `metadata/LOCAL_RUN.json` exists with backend `trinity-local`, host `trinity-2-28` and mode `OFF`.
     - `metadata/CARDS.json` `snapshot.name` contains `RTX 6000 Ada`.
     - Every journal's `environment.json` `host` starts with `trinity-2-28`; Orchard's is `orchard-community-4`.
     - `metadata/RETURN_ID.json` job ≠ `172744`.
   - Change `test_identical` to expect a refusal for Orchard-vs-Orchard, and add a positive fixture that carries `LOCAL_RUN.json`.

5. **MEDIUM: the return layout differs from Orchard's and drops files that the scorers read.**
   - The authenticated Orchard archive `A4/f/0.tgz` (sha `0dfd6ee6…`, 77 members) contains `metadata/reads/0/metadata/{IDENTITY.json,projection.json,a/30.json}`, `metadata/{ALLOCATION,STORAGE}.json` and `logs/{0,1}.log`.
   - `K/runner228.py:75-104` replaces `runner.run`. The sealed `runner.run` writes `reads/0/metadata/IDENTITY.json` (`A4/src/orchard_h10/runner.py:135`) and `projection.json` (`:181`), and the replacement writes neither.
   - Effect on consumers:
     - `CO/swarm_opt/work/corpusin/ingest_read.py:478` silently gets `{}`, so serving provenance is lost.
     - `CO/cont_ops18/dbuild/score_d.py:85` raises FileNotFoundError.
     - `A4/unpack_return.py` and the journal-based scorers (`report_r1.py:13,25`) are unaffected.
   - Smallest fix: call the sealed `runner.run`, which already accepts `launcher=` (`runner.py:124`), with a launcher that substitutes the observed worker command. Alternatively, write those two files with the same fields `runner.run` uses.

6. **LOW: the worker environment drops USER and HOME.**
   - `K/common228.py:70-78` keeps only PATH and LD_LIBRARY_PATH.
   - Without USER, vnice's `terminator.sh:39` creates `/tmp/terminator/${USER}-${pid}` as `/tmp/terminator/-<pid>`, which cannot be attributed to jjyeung.
   - Without HOME, any `~` fallback resolves to `/home/jjyeung` on NFS. CUDA_CACHE_PATH and MPLCONFIGDIR are not set.
   - Smallest fix: add `USER`/`LOGNAME=jjyeung`, `HOME=<out>/home`, `CUDA_CACHE_PATH=<out>/cache/nv` and `MPLCONFIGDIR=<out>/cache/mpl`.

7. **LOW: the comparator's OFF check inspects the wrong field.**
   - `K/compare228.py:107-109` looks for `read_*` keys in `environment.json` `binding`, which never holds them. The settings live in `environment.json` `settings`.
   - OFF is therefore enforced only through the optional `LOCAL_RUN.json` (finding 4).
   - Smallest fix: check `env['settings']`. `rows()` must then return the full `environment.json`, not only `binding`.

8. **LOW: the vnice script is not pinned.**
   - `K/common228.py:14` runs `/data3/shared/scripts/vnice/vnice.sh` without a hash.
   - Today `vnice.sh` and `terminator.sh` match the Orchard pins (`3ab2b542…`, `19727987…`), but the kit never checks them.
   - Smallest fix: add both sha256 values to `A4_PINS.json` and verify them in `deployment()`.

9. **LOW: a test writes outside `work/`, and the comparator output path is unconstrained.**
   - `K/tests/test_kit.py:325` writes `HERE/'test_returns'`, so a direct run of `K/tests` writes into `out/`.
   - `K/compare228.py:142` accepts any `--out` path, including `/home` or `/data*`.
   - Smallest fix: use `WORK` in the test, and pass `--out` through `local()`.

10. **INFO: the worker launch is not byte-identical to Orchard's, but it reaches the same code.**
    - `K/worker228.py:23` appends `--settings` to sys.argv, which is the package's own native-tree hook.
    - `K/worker228.py:30-33` imports `e2e_reader.parity`, `h1eval.h10.launch`, torch and transformers before `runpy` of `entry.py`. Lines 30-31 repeat the same import.
    - `K/worker228.py:45-57` wraps `parity.load_native` and returns the original result.
    - The same `p/tree` is selected, and I found no numeric effect. Record this in REPORT.

11. **INFO: what passes.**
    - **Sealed bytes:** unchanged except the two placeholders, which equal the Orchard INPUTS/EXPORT_PIN. The export is Orchard's m200 (`a15_cot_apd72cdcff1e22a/a/e/0..3`, matching `ret/metadata/INPUTS.json`), not the template's m544.
    - **Reference:** the first 50 rows equal the authenticated `f/0.tgz` rows (canonical `507b54ff…` = the `FIRST50.json` pin). The environment, EXPORT_PIN and IDENTITY files are identical.
    - **Card gate** (`K/gpu228.py:33-49`):
      - It takes two readings at least 300 s apart.
      - It requires under 100 MiB in use, no process, the RTX 6000 Ada name and 48-50 GB total memory.
      - It holds a UUID lock and fails closed.
      - CUDA_VISIBLE_DEVICES is the card's UUID.
      - The worker re-checks for exactly one Ada device.
    - **Memory telemetry and OOM:**
      - Each item records peak allocated and reserved memory, and nvidia-smi polls every 1 s.
      - The first OOM writes `OOM.json` and `STOP`, exits with rc 42 and writes FAILED/EXIT with no COMPLETE or retry (`K/observe228.py:25-37`, `K/worker228.py:66-73`, `K/runner228.py:109,115`).
    - **Comparator refusals:** missing, reordered, duplicate, torn, empty and non-prefix returns all fail.
    - **Budget:** 120.7 GB estimated peak, under 150 GB, with a 200 GiB free floor.
    - **Notes:**
      - The worker shares the control process group (`K/runner228.py:93`), so an admin terminator kill leaves no return receipt.
      - `read228.sh` runs the full 636-item read, not the 50-item check.
