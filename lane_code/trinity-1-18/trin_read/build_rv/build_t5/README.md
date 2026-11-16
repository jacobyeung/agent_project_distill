# Trinity dev-S1 direct reader

`trinity_read.py` stages local inputs and runs the accepted direct reader on one card. It accepts `main`, `away`, `forward`, and `camera`. Production reads D0 milestone exports from lineage `8865619b`, run `359fcc3c`, using the complete e193c2a3c item set. The proof invokes the unchanged `proof/phase_b.py` directly; it does not invoke the chain's official-item phase A. No command downloads files or uses SSH, Git, or Slurm.

The operator must approve heavy I/O under the Trinity rules before running real staging, frame ingestion, or a read. GPU commands below are operator commands; this build session does not execute them. Coordinate the chosen card before launch. Run from a compute node, never `trinity`.

## Paths and inputs

```bash
cd /scratch/jjyeung/orch_n30/trin_read/build_t5
TRIN_ROOT=/scratch/jjyeung/orch_n30/trin_read/root
TRIN_DL=/scratch/jjyeung/orch_n30/trin_read/dl
TRIN_PY=/usr/bin/python3
```

The CLI supports Trinity's system Python 3.6.8 and `../kit_src/.venv/bin/python`. Runtime work uses the staged Python interpreters. Tests use the kit venv. All output stays under `build_t5/` or `root/`; production packets must stay under `--root`.

`stage` requires each complete source and its `<filename>.RECEIPT.json`: `runtime_0.tar`, `runtime_1.tar`, `runtime_2.tar`, `camera.tar`, `bwrap`, and `base.tar`. A receipt admits the transfer; runtime part hashes, camera/bwrap pins, and the base manifest authenticate its contents. `.part` files are never consumed. The existing step-544 export stays at `root/fsw/ap/8865619b/runs/469ddece/m544`.

## Stage

```bash
"$TRIN_PY" -B trinity_read.py stage --root "$TRIN_ROOT" --dl "$TRIN_DL"
```

The command stages each available piece once and records it in `root/STAGING.json`. Run it again as completed archives arrive. `complete: false` lists missing inputs; it does not mean a partial extraction succeeded. A piece marked `partial`, or an unrecorded existing destination, causes refusal. Preserve the evidence and resolve it manually; the runner never cleans, overwrites a partial extraction, or automatically retries.

The bootstrap is decoded as data from accepted job 169991's `BATCH.sh`. Its `CONFIG.json`, launcher pins, `REVIEW.json`, payload SHA256, and every payload member hash are checked. The embedded bootstrap and reader payload retain their exact bytes. Runtime extraction uses the kit's `extract_stream`, `links=True`, and unchanged `RUNTIME_ABSOLUTE_LINKS`. The base requires the exact manifest inventory. Export verification hashes the existing full-weight shards; it never moves or fetches them. Staging preserves the kit's 200 GiB free-space floor and stages no videos.

## Frames

```bash
"$TRIN_PY" -B trinity_read.py frames --root "$TRIN_ROOT" --tar "$TRIN_DL/frames20.tar"
# Additional completed dev-S1 frame archives may be supplied together:
"$TRIN_PY" -B trinity_read.py frames --root "$TRIN_ROOT" --tar "$TRIN_DL/frames_more.tar" --tar "$TRIN_DL/frames_last.tar"
```

Every member must be a PNG named `<sha[:2]>/<sha>.png` whose bytes match its SHA256. The store contains `k6tk/MEMBERS.tsv.gz` and `k6tk/parts/<tag>/<tag>_000.tar`. New gzip index members append rows; existing rows and shards remain unchanged. Duplicate frames are checked and skipped. Shards publish only after full validation. An interrupted index append may leave a corrupt gzip stream; later commands refuse it. Do not ingest frames concurrently with a read. No recovery command removes data.

`stage-export`, `proof`, `read`, `need`, `probe`, and `selfcheck` accept `--bwrap PATH` (default `/usr/bin/bwrap`). The host executable must support bubblewrap 0.4.0 flags. The pinned Orchard binary at `root/bwrap` remains authenticated evidence and never executes; selecting it, a link to it, or a byte-identical copy is refused.

The namespace binds this store read-only at `/project/community/jjyeung/cp4tk_fr/k6tk`, so the unchanged `proof/pull.py` and `phase_b.py` consume it directly. The namespace disables networking and gives CPU planning no GPU device nodes. Temporary files, caches, the home directory, and `/dev/shm` map into `root/` by default.

## llguidance overlay and CPU import probe

Trinity uses glibc 2.28. The staged vLLM 0.32.0 imports `llguidance` through structured-output dataclass annotations, but its native `_lib.abi3.so` requires GLIBC_2.30. `proof`, `read`, `need`, and `probe` default to `--llguidance-stub`; `--no-llguidance-stub` disables the overlay.

The runner verifies all three SHA256 pins in `trinity_read.py`, rejects extra files or symlinks, and read-only binds `build_t5/llg_stub/llguidance/` over `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e/lib/python3.12/site-packages/llguidance` after the root binds. The destination must already exist. The v2 stub logs each module import and every attempted call before raising. It supplies `llguidance`, `LLMatcher`, `LLTokenizer`, and `LLInterpreter`; imports of `llguidance.hf` and `llguidance.torch` also log and raise. `work/llg_stub/` remains the v1 record. The stub supplies import-time names and raises on actual guidance use; structured-output requests remain unavailable. The overlay changes package loading while leaving staged bytes unchanged.

`COMMAND.json`, `EXIT.json`, `PROOF.json`, and packet `SPEC.json` carry `llguidance_stub` with `enabled`, source `path`, namespace `target`, the three file `sha256` pins, and `verified`. Run CONFIG and CPU NEED evidence carry the same object, including the satisfied names and stub version. Disabled overlays record the expected pins with `verified: false`. Packet SPEC is written before execution, so failed runs retain this evidence.

```bash
"$TRIN_PY" -B trinity_read.py probe --root "$TRIN_ROOT"
# Select the same private shm and host bwrap as a proof run:
"$TRIN_PY" -B trinity_read.py probe --root "$TRIN_ROOT" --shm "$TRIN_ROOT/shm" --bwrap /usr/bin/bwrap
```

`probe` requires a completed `runtime_0` receipt and its staged uv Python, plus the staged vLLM environment. It does not require the model/frame stage to be complete or wait for incoming archives. It runs the vLLM interpreter with `-I -B`, matching the isolated wrapper, inside the proof namespace with CPU-only devices, the same root binds, environment variables, stub, and private shm. It imports vLLM, torch, transformers, LLM, qwen3_5, engine core, and gpu_model_runner without loading a model or exposing GPU devices.

The command prints Python/vLLM/torch/transformers versions, glibc, and whether `cryptography` appears in the imported modules. Each invocation writes `root/runs/probe_<utc>/PROBE.json`, including refusals and failures. The report records the command, bwrap identity, overlay pins, environment, stdout/stderr, return code, and import result when execution reaches them. `cryptography_imported: null` means the import script did not report; it does not mean cryptography was absent. A failed probe exits nonzero and never retries.

The probe invokes the staged `GuidanceBackend.compile_grammar(REGEX, "a")` on CPU with a minimal backend object. It bypasses tokenizer construction and model loading; vLLM 0.32.0 reaches `llguidance.grammar_from` while serializing that request. Acceptance requires the stub's `RuntimeError` and a logged call. `PROBE.json.structured_output` records the reached stage, exception, exact reason, and call names. An unavailable interpreter or incompatible CPU API records why the check could not run; it never claims a successful failure test. `--no-llguidance-stub` records the check without requiring a stub exception.

Every proof/read/probe writes `SANDBOX.json`. It records the selected bwrap path/hash/version, the exact namespace argv, every bind's source/target and ro/rw mode, symlinks and special mounts, stub path/hashes, host `ldd --version` first line, namespace glibc, host NVIDIA driver query, `/usr/lib64/libcuda.so.1` and `libnvidia-ml.so.1` resolved paths/sizes, and the libraries resolved by `ctypes.CDLL` inside the namespace. The CPU probe supplies package versions and its provenance. Unavailable fields remain null or carry errors; `namespace_executed` distinguishes attempted execution from preflight refusal. CPU driver resolution does not establish that a GPU model can run.

Proof/read perform a CPU probe before GPU admission and copy its report into the run. Each generation run sets `LLG_STUB_LOG` to its own `llg_stub_calls.jsonl`, inherited by the reader and engine processes through the shared root bind. The default outside the runner is `$TMPDIR/llg_stub_calls.jsonl` (`/tmp` if unset). The probe's deliberate calls use a separate log. `LLGUIDANCE.json`, EXIT, and PROOF record import/call counts. Any generation-time stub call, corrupt log, or enabled stub with no import evidence fails the audit. Phase B packets under `b0/d0/` receive `SANDBOX.json` and `LLGUIDANCE.json`; read packets retain them at their root.

## Plan frames on the CPU

```bash
"$TRIN_PY" -B trinity_read.py need --root "$TRIN_ROOT" --family main --first 20 --out "$PWD/NEED20.txt"
cmp "$PWD/NEED20.txt" /scratch/jjyeung/orch_n30/trin_read/work/NEED20.txt
"$TRIN_PY" -B trinity_read.py need --root "$TRIN_ROOT" --family away --ids "$PWD/away.ids" --out "$PWD/NEED_AWAY.txt"
"$TRIN_PY" -B trinity_read.py need --root "$TRIN_ROOT" --all --out "$PWD/NEED_ALL.txt"
```

An ID file contains one exact `example_id` per line. Empty lines are ignored; duplicates, unknown IDs, nonpositive prefixes, and prefixes larger than the family are refused. ID-file order does not change execution order: the wrapper preserves `(benchmark, example_id)` sorting. `--all` covers every direct item in the four families.

Each CPU family run records `COMMAND.json` and `EXIT.json` under `root/needs/<id>/`, including the executed bwrap path, SHA256, and exact `--version` stdout/stderr. Each command writes the sorted SHA list, `<out>.missing`, and `<out>.json` with IDs, item/capture/frame counts, and estimated bytes. The estimate uses uncompressed RGB dimensions; it is not a measured PNG transfer size. Each family runs in a fresh process inside the namespace. Planning calls `direct.bind(dry=True)`, the kit's `select_tasks`, and the family's `origin.payload`; it does not decode video or load model weights. The real main-20 list must contain exactly 576 hashes and match `work/NEED20.txt`.

## Proof on one card

After a complete stage and frame ingestion, choose a fresh token and physical card index:

```bash
"$TRIN_PY" -B trinity_read.py proof --root "$TRIN_ROOT" --gpu 0 --token p2026111501 --repeat 2
```

The runner checks frame coverage before touching the GPU. It sets `CUDA_VISIBLE_DEVICES=0` and puts the token in the `SLURM_JOB_ID` environment field expected by the kit. It requires one selected card with at least 40 GiB, less than 100 MiB used, and no compute process. It executes the traced, unchanged phase B with the staged vLLM interpreter through `/data3/shared/scripts/vnice/vnice.sh`. The wrapper's documented command-string interface is shell-quoted explicitly.

With the default `--repeat 1`, outputs live in `root/runs/<token>/`: `CONFIG.json`, `ENV.json`, `COMMAND.json`, `CARD.json`, `HOST_SHM_BEFORE.json`, `MEMORY.jsonl`, `run.log`, `EXIT.json`, `b0/d0/`, `PROOF.json`, and `PROOF.md`. `COMMAND.json` is an object with `argv`, `bwrap`, and `llguidance_stub`; `EXIT.json` and `PROOF.json` carry the same identities. The identity includes the resolved executable path, SHA256, and exact `--version` stdout/stderr. Tokens and output directories are single-use. A 1 s sampler records card memory; the report labels its maximum as a sampled peak. Subsecond peaks may be missed.

The proof compares all 20 items against `kit_src/parity/DEV20.json` for ON16k, B2048, and B4096. It reports exact token equality, zero-based divergence, lengths, raw-generation equality, extracted answers, score equality, and unrounded arm means. Missing items cannot pass. Timing comes from worker journals and budget receipts. Reused ON rows do not count as new budget generation; concurrent per-item latency is not wall-clock throughput. Missing measurements remain null. A failed run or sampler cannot produce a passing proof.

`proof --repeat 2` runs phase B sequentially on the same selected card in fresh `root/runs/<token>_r1/` and `<token>_r2/` directories. Each retains its comparison against accepted DEV20. `root/runs/<token>/RUN_TO_RUN.json` compares every item's token IDs, first divergence, raw generation, answer, and score across both runs. The parent `PROOF.md` summarizes both accepted comparisons and run 1 versus run 2; its `PROOF.json` passes only if all three comparisons pass. Missing rows never compare equal. A killed, yielded, or failed execution stops the sequence and writes incomplete comparison evidence; the runner never retries it. A completed run with only an accepted-token mismatch can proceed to the second comparison run. Both packets retain model copies, so the usual free-space check runs before each phase B.

To regenerate the report without using a GPU:

```bash
"$TRIN_PY" -B compare_tokens.py --reference ../kit_src/parity/DEV20.json --dest "$TRIN_ROOT/runs/p2026111501_r1/b0/d0" --attempt b0 --out "$TRIN_ROOT/runs/p2026111501_r1" --memory "$TRIN_ROOT/runs/p2026111501_r1/MEMORY.jsonl" --exit "$TRIN_ROOT/runs/p2026111501_r1/EXIT.json"
```

## Read D0 milestones on one card

The operator sequence is **governed pull → stage-export → selfcheck → read --all-families**. Production requires the orchestrator's GO, completed runtime/base staging, frame coverage, and the step-544 proof. The commands below are operator instructions; this build session runs CPU fixtures only.

1. After `.done` arrives, use the existing I/O governor to pull the GCS parts in order into one local `.tar.part`. Verify that the transfer completed, then publish the concatenated file as `.tar`. Keep the original `.done` JSON alongside it. The governor must admit the single 8 MB/s stream; this CLI does not download or concatenate files. Never relaunch a killed transfer automatically.
2. Admit and extract the completed tar with `stage-export`. Its `.done` schema requires `object` (nonempty string), `bytes` (positive integer total tar bytes), and `sha256` (64 lowercase hex characters for the whole tar). The local filename need not equal the GCS object name. The object name remains provenance; the bytes and hash authenticate the local tar.
3. Run `selfcheck` and inspect the export receipt. `selfcheck` checks the runtime/root bundle; the export receipt separately records the milestone checker result.
4. Read all four full families sequentially on the selected card, using a fresh token and output directory.

```bash
cd /scratch/jjyeung/orch_n30/trin_read/build_t5
TRIN_ROOT=/scratch/jjyeung/orch_n30/trin_read/root
TRIN_DL=/scratch/jjyeung/orch_n30/trin_read/dl
TRIN_PY=/usr/bin/python3
STEP=100

# After the governed pull has published the complete tar and its done record:
"$TRIN_PY" -B trinity_read.py stage-export --root "$TRIN_ROOT" \
  --tar "$TRIN_DL/359fcc3c_m${STEP}.tar" --done "$TRIN_DL/359fcc3c_m${STEP}.done" \
  --run 359fcc3c --step "$STEP"
"$TRIN_PY" -B trinity_read.py selfcheck --root "$TRIN_ROOT"

ARTIFACT="$TRIN_ROOT/fsw/ap/8865619b/runs/359fcc3c/m${STEP}/artifact.json"
ARTIFACT_SHA=$(sha256sum "$ARTIFACT" | cut -d ' ' -f 1)
"$TRIN_PY" -B trinity_read.py read --root "$TRIN_ROOT" \
  --artifact "$ARTIFACT" --sha256 "$ARTIFACT_SHA" --step "$STEP" \
  --all-families --gpu 0 --token d2026111701 \
  --out "$TRIN_ROOT/packets/d0_m${STEP}" \
  --yield-glob "$TRIN_ROOT/control/*.yield"
```

Use the same sequence for steps 200, 400, 800, 1000, and the positive stop step. `logical_artifact` admits exactly runs `469ddece` and `359fcc3c` in lineage `8865619b`, at any positive step, plus the fixed parent m200 path. Physical and logical paths are accepted. The artifact SHA passed to `read` is the hash of `artifact.json`, not the tar hash in `.done`.

`stage-export` requires a regular local `/scratch` tar and done file without symlinks. It refuses `.part` names, mismatched bytes or hashes, absolute paths, `..`, duplicate members, links, devices, FIFOs, and file/directory collisions. The archive must contain exactly one `m<step>/` tree with `artifact.json`, `heads.pt`, and `full_weights/full_weights.json`; only the full_weights subtree may contain additional files. It never strips an outer directory or guesses a different layout. The step-544 receiver script extracts directly into the run directory, and its staged tree has this layout. The D0 tar itself remains unverified until it arrives.

The command refuses an existing milestone or receipt. Before extraction, it preserves the 200 GiB disk floor using uncompressed member sizes. `root/exports/<run>_m<step>/RECEIPT.json` records tar authentication, extraction state, artifact SHA, checker mode/result, and failures. The unchanged, SHA-pinned `export_check.py` runs in the CPU namespace after extraction, with its original logical mounts. Default header-only mode records `HEADER_ONLY_NOT_VERIFIED`; `--full` also hashes every shard and records `VERIFIED`. Both compare tensor headers against the staged base. The tar hash authenticates transport; the later production reader still performs its unchanged full export checks. Interrupted extractions and checker failures retain all files and refuse a rerun. No command removes them.

`--all-families` equals `--families main,away,forward,camera`. Omitting every family selector also selects all four. Explicit `--families` runs a unique, ordered subset. A multi-family read requires the full families and rejects `--ids` or `--first`. A single `--family` accepts those options; omitting both reads that full family. Every full selection must match the pinned e193 inventory: main 1,525, away 150, forward (toward) 150, camera 450; total 2,275. The worker also checks the accepted cells, source hash, task-file hash, and task types.

Each family runs in a fresh process on the same card and retains its accepted packet under `<out>/<family>/direct/<family>/`, including requests, prompt pins, frame receipts, and all three result arms. The runner retains ON16k, B2048, B4096, duplicate layout, 32 anchors, true timing, and the unchanged answer-cap policy. Each packet also contains the unchanged report exporter’s label-specific `report/B2048.json`.

`MILESTONE_SUMMARY.json` and `.md` report per-family and per-task B2048 scores, total/scored counts, card identity, wall times, and measured journal token rates. Main uses released-answer scores on the 1,375 primary rows. Route planning has no primary rows, so its task score uses its 150 own-ground-truth rows and remains separate from the main primary aggregate. Away, toward, and camera use their own ground truth. The JSON also reports all-item own-ground-truth means. Scores are item-weighted percentages; toward and away never share an aggregate. Journal token rates divide generated tokens by summed request latency and are not card throughput.

The total wall time covers the full invocation, including family preflight and reporting. Each family records both invocation time and its `EXIT.json` execution time. A failure stops the sequence immediately and writes an incomplete milestone summary; completed evidence remains. The yield file is checked before each family and by the existing watcher during execution. No family retries automatically. Every family keeps its base/model copies, so reserve enough disk for all four packets above the 200 GiB floor.

`--model-slot cp1m200|f17` remains available for explicit main/camera reads using the pinned camera registry and duplicate e193 cells. It excludes `--artifact/--sha256/--step`. The 636-key files and CPU binding evidence remain in `REPORT_T5.md`; the D0 workflow uses all 2,275 items.

## Project cost from a completed proof

```bash
"$TRIN_PY" -B trinity_read.py cost --proof "$TRIN_ROOT/runs/p2026111501_r1"
```

`cost` prints JSON and writes `<proof>/COST.json`. It requires a successful EXIT with positive wall time, matching complete items in all three proof arms, and generation latencies or explicit budget-reuse receipts. Token equality against the accepted proof is not a cost prerequisite. A failed or yielded execution cannot supply a cost model.

For each arm, `seconds_per_item` sums measured generation latency and divides by all proof items; reused ON answers contribute zero new budget latency. The one-card projection uses `EXIT.wall_seconds / proof_items × 2275 / 60`. Per-family and per-task counts come from the pinned e193 inventory. Arm wall-time allocations use each arm’s share of summed latency and are explicitly estimates. The projection assumes the proof’s task mix, concurrency, and setup cost per item transfer to each family. It includes setup within EXIT, excludes the outer preflight and transfer/staging, and does not claim measured full-milestone throughput. Missing timing evidence causes refusal rather than a fabricated projection.

## Private shared memory and yielding

Both `proof` and `read` accept `--shm DIR`; the default is `<root>/shm`. The wrapper creates the directory and binds it over `/dev/shm` after the GPU namespace's `--dev-bind /dev /dev`. CPU planning uses the same selection with a private device namespace. `DIR` must remain within the authorized `build_t5/` or `root/` trees. Keep it under `root/` for a root-only copy; the default uses disk space rather than the host's shared-memory mount.

`TMPDIR`, `HOME`, `XDG_CACHE_HOME`, `HF_HOME`, `TRITON_CACHE_DIR`, `TORCHINDUCTOR_CACHE_DIR`, and `VLLM_CACHE_ROOT` point under `root/`; `ENV.json` records their values. The wrapper lists immediate host `/dev/shm` entries owned by the current UID before and after execution, without following symlinks or descending into directories. `HOST_SHM_BEFORE.json` records the initial listing; `EXIT.json` and `PROOF.json` contain `host_dev_shm_ours_before` and `host_dev_shm_ours`. Empty lists are expected. Entries from other jobs under the same UID may appear; these observations do not attribute or delete them.

Add these options to either launch command:

```bash
--shm "$TRIN_ROOT/shm" --yield-glob "$TRIN_ROOT/control/*.yield"
```

Quote the glob so the wrapper receives it literally. Its parent must be a fixed directory within `build_t5/` or `root/`; recursive globs and wildcard parents are refused. The watcher checks immediately after launching the reader, then every 30 seconds while it runs. A matching regular file triggers SIGTERM to the reader's own process group, a 60-second grace period, then SIGKILL to that group only. The wrapper creates the group with `start_new_session=True`; it never signals its caller's group or another job. Processes that deliberately leave that group are outside this signal boundary.

A yield makes `EXIT.json.returncode` 75 and the CLI exit nonzero. `YIELD.json` records the matched file, Unix/UTC time, group ID, and paths and byte sizes under the run directory and packet model directories. It inventories metadata after termination and reporting, before writing `YIELD.json` itself; it does not read model contents or follow symlinks. All leftovers remain for inspection. A yielded proof cannot pass, and the wrapper never retries it.

## Copying a root and checking it

The root carries the wrapper modules and their hashes in `root/trinity_runner_t5/`; staging installs and verifies the same bundle. Runtime namespaces bind that directory and use the staged package's parity reference, so a copied root does not need `kit_src/` or `evalx27/work/`. The default llguidance overlay additionally requires the three pinned files at `/scratch/jjyeung/orch_n30/trin_read/build_t5/llg_stub/llguidance/` on the destination. Disabling the overlay removes that dependency but leaves the native GLIBC_2.30 requirement. The runner still needs the system directories, a compatible driver/runtime, and `/data3/shared/scripts/vnice/vnice.sh`. Use the **same absolute root path** on the destination node and preserve permissions and symlinks when copying its tar archive under the cluster transfer rules. This session performs no transfer.

After the copy, run on the destination compute node:

```bash
/usr/bin/python3 -B "$TRIN_ROOT/trinity_runner_t5/trinity_read.py" selfcheck --root "$TRIN_ROOT"
# The build copy supports the same check:
"$TRIN_PY" -B trinity_read.py selfcheck --root "$TRIN_ROOT" --bwrap /usr/bin/bwrap
```

`selfcheck` writes JSON to stdout and exits nonzero for incomplete, unverifiable, or failed checks. It does not change the root. It checks recorded file sizes, SHA256 for files up to 1 MiB, the bootstrap payload and bwrap hashes, and wrapper hashes. It does not rehash large model shards or runtime archives. New runtime/camera/payload receipts retain member inventories; base/export checks use pinned manifests. A later authorized `stage` can enrich the existing camera receipt from its completed, authenticated small archive without extracting it again. Until that happens, its extracted files are explicitly unverifiable.

The selfcheck CPU probe starts `/bin/true` using the selected bwrap with networking disabled and private devices/shared memory. Its `--dev-bind` probe binds only `/dev/null`; it exposes no GPU devices. It exercises all flags emitted by the runner, including `--bind`, `--dir`, `--chdir`, and `--die-with-parent`. The JSON records the executed bwrap identity and probe command/result. It tests host compatibility, not the complete reader or CUDA runtime.

CONFIG auditing classifies unchanged literals from the authenticated accepted bootstrap as `pinned_evidence` when they are not active paths. These include Orchard host names, accepted job/transport paths, and hashes. They remain visible and do not fail selfcheck. Active model, artifact, interpreter, package, manifest, and run paths are checked against root, `/data3/shared/scripts/vnice`, and system directories. Logical namespace aliases map into root; path traversal and symlink escapes fail. The accepted bootstrap CONFIG SHA256 anchors the evidence classification. The exact llguidance stub source path is classified as `pinned_overlay` and authenticated against its three pins when enabled. The audit checks CONFIG strings and symlink targets without scanning source text, archives, or model contents.

`SELF_CHECK_BWRAP.json` records the real partial-root check with `/usr/bin/bwrap` 0.4.0. Its CONFIG audit passes, but selfcheck remains nonzero because runtime/base/payload pieces are missing, the camera receipt lacks a member inventory, and this agent sandbox rejects the probe's `NETLINK_ROUTE` socket. The flag set passes option parsing and appears in 0.4.0's help; namespace execution remains unverified in this session. `BWRAP_FLAGS.json` records coverage. No flag replacement is needed. The operator's successful namespace test is separate evidence; no GPU result is claimed here.

## Settings, tests, and failure meanings

The reader retains `max_model_len=49152`, greedy decoding, thinking cap 16384, memory utilization 0.90, max sequences 32, batched-token cap 8192, inflight 16, seed 17, tensor parallel size 1, and disabled prefix caching. An OOM or unsupported runtime fails the run; no setting is reduced automatically. See `DIFF.md` for the complete added-code ledger and open validation risks.

The unchanged reader retains two model copies per packet: `direct/<family>/models/base` and `direct/<family>/models/cp1m200` (`b0/d0/models/` for proof). `--keep-models` and `--no-keep-models` are documentation concepts only: neither flag is implemented, and the wrapper never removes these copies.

Budget roughly **36 GiB per read for model copies**, even for a one-item read. The step-544 export's five shards total 18,819,721,016 bytes (17.527 GiB); the base archive is 18.002 GiB including tar overhead. The base's exact copied size comes from its pinned manifest when staged; copied model metadata adds a small amount. Each fresh packet needs its own copies.

Before launch, `SPACE.json` records `base manifest bytes + export shard bytes + 2 × estimated frame bytes + 2 GiB`, while preserving the 200 GiB free-space floor. Frames occupy both a tar and extracted PNGs. Caches, private shared-memory files, and concurrent disk users also consume space; the reserve neither allocates nor caps them.

```bash
# Use a fresh basetemp path for every invocation; retain existing test evidence.
PYTHONDONTWRITEBYTECODE=1 ../kit_src/.venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp="$PWD/tests/operator_run_01" tests
```

The tests use kit fakes, miniature frame archives, mocked GPU boundaries, and real CPU child process groups for TERM/KILL handling. Public dry-bind tests read the accepted runtime copy in `evalx27/work/pull/x27c/r2`, including its away/forward payloads. They do not establish that the real namespace or vLLM engine runs on Ada.

`REFUSED` means an input, pin, path, card, stage, or membership check failed. A nonzero GPU command requires inspection of `run.log`, `EXIT.json`, and any proof report. If a process is killed or a connection drops, stop and coordinate under the Trinity rules; do not relaunch automatically. `PROOF.json` with `passed: false` reports a mismatch or incomplete evidence, not acceptance. No real GPU result is claimed by the CPU tests.
