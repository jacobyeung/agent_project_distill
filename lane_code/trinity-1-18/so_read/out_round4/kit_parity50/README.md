The GPU kit is unrun. The fixed sample contains 50 items: ten per type and twelve native captures. It stresses reuse and does not estimate representative throughput.

Apply reader patches 01–03 to a fresh full copy of A4/src or B5/src. Apply patch 04 separately to a copy of A4/tower_sequence.py, outside src, for the A4 operator route. Every original file stays unchanged; the additions live in src/u0, outside the reader/evaluator hash trees. The ordinary reader entrypoint is the default OFF path. Cache settings alone do not activate extensions. Explicit activation uses `src/u0/a8.py --enable-extensions`; cache switches then default to off. The ON environment records a separate extension source hash. Rebuild and authenticate payload/artifact pins, including the extension code root, before deployment.

Keep this private kit, its original manifests, reports, and alias/reverse maps on Trinity. Public submission names, staged paths, configuration, and logs must use opaque tokens. The public array example uses numeric type slots and neutral paths. The array helper derives its command from the approved submit function, screens the command and script with the production forbidden-word list, and sends scheduler logs to /dev/null. The template is inert. Keep journals on persistent storage and keep shard membership/count fixed across attempts.

Prepare approved original and extended source roots, checkpoint/export/artifact inputs, and settings under neutral staged paths. Transport each source root as one archive and extract it only on node-local disk. Keep both parity source roots pristine: no build outputs, extra files or symlinks. Build production packages in a separate source copy because the builder writes its output inside that copy. Build a private alias JSON mapping original asset paths to those staged paths. On Trinity, seal settings and any JSON configuration metadata with the helper; its wire decoder preserves their runtime field names in memory. Seal settings only after flattening the intended item-set settings and binding every required asset. The helper rejects descriptive absolute asset paths; it never copies datasets or weights.

```bash
mkdir -p work/public
bash work/cpu.sh work/src/u0/a11.py seal --source-root work/src \
  --input PRIVATE_SETTINGS.json --aliases PRIVATE_ALIASES.json --out work/public/u3
bash work/cpu.sh work/src/u0/a11.py stage-kit --source-root work/src \
  --input out/kit_parity50 --config PRIVATE_NEUTRAL_CONFIG.json --out work/public/u0
```

The private configuration follows config.example.json. `source_root` selects the extended source; `original_source_root` selects the untouched source. Both use the same approved native tree, model, artifacts, precision, hardware, and settings. `enable_caches` uses slots 0=processor, 1=vision, 2=SAM. The staged kit contains u0.py, u1.py, a9.py, and u0.json through u4.json. The u3.json inventory binds every extension file to MANIFEST. The u4.json base pin authenticates the complete non-u0 inventory of both roots against all 927 input files; the driver rejects equal original/patched roots and an extension-bearing original root before starting an arm. It authenticates the sealed sample bytes and retains the original logical sample pin. Transfer this staged directory through the approved transport under an opaque root; never publish the private kit directory or maps.

On an assigned GPU, the acceptance command is **not executed here**:

```bash
nice -n 10 "$READ_PYTHON" -I -s -B /scratch/jjyeung/ab0123456789/u0/u0.py /scratch/jjyeung/ab0123456789/u0/u2.json \
  --out /scratch/jjyeung/ab0123456789/u9 --enable-gpu --public --repeat-baseline --shards 4
```

The kit requires token-only staged metadata, opaque paths, and explicit GPU/public flags. Every pass starts a fresh process. ORIGINAL, OFF, and OFF_REPEAT use the original journal and modulo-shard defaults. ON first tests only caches. The optional ON_JOURNAL and four sequential whole-scene shards separately test durable journaling and sharding. Sequential shards establish equality, not parallel speed.

The same explicit transport wrapper protects every arm. It emits token-only JSON, hashes item/native/room identities, and hashes arbitrary worker stdout/stderr into event tokens. It never writes an ID reverse map on Orchard. Its source hash is separate from the original reader hashes. This wrapper belongs to the explicit public parity experiment; the ordinary OFF reader imports none of these extensions. CPU tests compare all OFF output files, including source hashes and timing fields, against the original under a controlled clock, with no field exclusions.

Acceptance requires exactly the expected 50 IDs, complete production output schemas, nonempty text/tokens/heads, scale even when null, every served response and forced-token count, matching call counters, and zero semantic byte differences. ORIGINAL/OFF also requires all production source-hash fields to match. Every enabled cache must declare itself, report a valid memory bound, and show positive hits; SAM requires both feature and detection hits. Empty/all-miss runs fail. The comparator excludes measured clock fields, audit paths/counters, old memo telemetry, and new cache telemetry from GPU semantic equality; audit violations fail. No answer/trace numeric tolerance is allowed. Equal scores cannot conceal changed text or tokens.

Output directories u0/u1/u2/u3/u4/u5 mean ORIGINAL/OFF/OFF_REPEAT/ON/ON_JOURNAL/SHARDED. Reports u6 through ua hold pairwise comparisons; ub.json holds merge equality; uc/ud hold the canonical public single/sharded returns. All JSON strings in public output are wire tokens. The raw clocks and source receipts remain present. Restore on Trinity with the private original manifest/settings/config, never on Orchard:

```bash
bash work/cpu.sh work/src/u0/a11.py restore --source-root work/src \
  --input PRIVATE_RETURN --out work/RESTORED_NEW \
  --private-source out/kit_parity50/sample50.json --private-source PRIVATE_NEUTRAL_CONFIG.json \
  --private-source PRIVATE_SETTINGS.json
```

Restoration authenticates committed rows before rebuilding private-ID checksums and filenames. Merge restored journals with the original manifest using the explicit extension entrypoint/module. CPU fixtures require private and restored-public answer/trace archives to match byte for byte. The existing transport envelope still contains clocks; the canonical answer/trace archive is a separate deterministic artifact.

Before adoption at step 600 or later, pass the ORIGINAL/OFF/OFF_REPEAT/ON/journal/sharded GPU gates with every switch ON, useful-hit checks, and net seconds/item checks including hashing/copying. Require a real persistent-storage preemption/requeue before any sharded or preempt adoption. Weight guards hash at install and at type-journal entry/exit; calls check every parameter/buffer identity, pointer and version. Tracked mutations fail immediately; persistent untracked writes fail at the next boundary. A fatal mismatch rejects the run. WEIGHTS.json blocks resume, merge and comparison until a boundary validates the journal. Graceful deadlines validate before recovery; a hard kill during an unchecked type requires a fresh journal. This policy assumes frozen models: an untracked write restored before the next boundary cannot be detected. Inference tensors without counters are refused. Boundary hashes and copies still need GPU measurement. The SAM-ON default is 12 GiB; other cache configurations default to 4 GiB. These caps bound cache-owned live storage and transient copies, including keys/containers; it does not cap model working memory or caller-owned outputs. Unsupported values bypass caching. Preserve adequate whole-process host/GPU headroom.

No delivered CPU test or single-GPU parity pass requires a local OS socket. StageOneSocket is a Python callback. Socket-backed transport/distributed integration is outside this kit and remains unrun. No job, scheduler command, upload, or return publication ran here.

## Production build and return integration

The ordinary builder and reader remain byte-unchanged. The additive builder is an explicit alternative. Run it in a **separate full build source copy** after applying reader patches 01–03:

```bash
nice -n 10 "$READ_PYTHON" -I -s -B "$BUILD_SOURCE/u0/a12.py" \
  --enable-extensions --reader-source "$BUILD_SOURCE/b" \
  --template-source "$BUILD_SOURCE/orchard_h10/vendor" --out "$BUILD_SOURCE/u9"
```

This command builds locally; it never submits, uploads, or copies datasets. The output must be inside BUILD_SOURCE, as the original builder requires. Do not use BUILD_SOURCE as a parity-kit source root afterward. It adds u0 to payload pins and selects pinned entry, job, runner, and preparation overlays only in the enabled package. Preparation includes u0 in artifact code pins and enables all three caches with a 12 GiB cap. Workers use atomic journals and whole-scene shards. The runner validates scene membership and writes the deterministic answer/trace archive under metadata/u0, which the existing return envelope includes. SUMMARY binds its relative path and SHA256. Existing envelope clocks remain variable; the canonical answer/trace archive must match exactly. The optional secondary item set is rejected in extension mode.

The CPU package fixture builds real archives from supplied source files, checks every payload pin, proves original-versus-OFF package bytes, checks entry dispatch, and compares the integrated merge against one shard. It does not restore real weights or validate GPU/storage/remote transport.

For the A4 operator route in this package family, use A4's authenticated bootstrap (the delivered operator/0.py is byte-identical to the decoded A4 bootstrap) and the patched A4 sequence. The optional arguments below explicitly choose that route. Build the step-600 candidate as single-card caches only:

```bash
nice -n 10 "$READ_PYTHON" -I -s -B "$BUILD_SOURCE/u0/a12.py" \
  --enable-extensions --caches-only --reader-source "$BUILD_SOURCE/b" \
  --template-source "$BUILD_SOURCE/orchard_h10/vendor" --out "$BUILD_SOURCE/u9" \
  --operator-bootstrap "$DELIVERY/operator/0.py" \
  --operator-source "$DELIVERY/operator/tower_sequence.py"
```

Add `--processor-only` to enable just the processor cache; it also disables atomic journals and scene sharding. In direct settings, `read_processor_only="on"` overrides both model cache flags. Every new switch defaults OFF. Generic ON without either cache profile still enables all three caches, atomic journals and scene sharding; use that for the separate validation gates.

The A4 bootstrap routes action 0 to the pinned preparation entry and action 1 to 7.py. The sequence activates overlays in its own fresh process. Its default-OFF memory proof is unchanged; ON adds the effective read_cache_bytes allowance to host_budget_bytes. Rebuild the CPU proof, payload, plan, inputs and operator pins before launch. The proof must attest bundle_guard_passed, entry_sequence_passed and the new operator hash, with memory basis fixed_g3t_shapes and fits=true. The operator preserves A4's fixed 636-item descriptors; the owner must bind the target read's item counts/schedule and regenerate its proof when building step 600.

With atomic journals enabled for validation, the merge lands at metadata/reads/0/metadata/u0/answer_trace_return.tgz inside the outer return. The existing fetch/unpack layout therefore stays intact; unpack still authenticates operator_sha256. With --caches-only, results stay in the ordinary per-type journals and no canonical merge is requested. The CPU integration test runs the real bootstrap admission branch, rejects a failed CPU proof, and executes real preparation/settings construction with stubbed restore/admission/weight-manifest work, then dispatches a stub model worker across all 636 A4 items. It verifies overlays, pins, counts and nested return membership in fresh action-0/action-1 processes.

No multi-card operator variant is delivered. Sharded reads require one that binds card count, per-read identities, memory and CPU proof. Step 600 uses single-card ON with caches only; the two/four-shard forecasts are conditional estimates.

## Array generation and approval

The example policy has approved=false. It proposes two one-hour shards with at most two attempts each: a four-GPU-hour lifetime upper bound. No owner approval is assumed. An owner must approve the exact partition, shard count, time, and attempt budget before setting approved=true. Total allocated time across all permitted attempts must remain at most five GPU-hours. Four parallel shards need a separately approved plan that still fits this limit.

Generate the reviewable command and script on the private host:

```bash
bash work/cpu.sh work/src/u0/a15.py PRIVATE_ARRAY_CONFIG.json \
  --enable-array --token ab0123456789 --out work/ARRAY_PLAN_NEW \
  --python /scratch/jjyeung/ab0123456789/u1 \
  --source /scratch/jjyeung/ab0123456789/u2 \
  --staged-config /project/community/jjyeung/okh7/a15_cot_apab0123456789/u3.json
```

The helper writes 0.json (argv and config pin) and 0.sh; it does not run either. Seal the exact approved config with a11 before staging. The script pins its decoded configuration and executes the neutral a14 entry; descriptive imports remain inside the authenticated payload. Exit 75 requests a bounded requeue, while other failures remain failures. Lock contention waits at most 60 seconds with backoff and then returns 75. A restart count at the attempt limit forbids more model work. Shell tests use a fake local scheduler function; real scheduler preemption/requeue remains untested.

Approved path roots include /scratch/jjyeung and /project/community/jjyeung, including the established okh7/a15_cot_ap<token> package layout. Remaining segments must be opaque tokens. Every path also passes the production forbidden-word screen. These checks accept names; they do not prove storage permissions, persistent-lock behavior, or capacity.

## Review round 3: finding -> fix -> test

1. Per-call weight hashing: install/boundary hashes, fatal live-identity guards and processor-only adoption; mutation, boundary, resume, public-merge and model-sized CPU timing tests.
2. Operator integration: A4 bootstrap/sequence CPU execution, fresh-process overlays, nested merge and default-OFF cache memory accounting; test_operator_round3.py.
3. Base authentication: both complete inventories match BASE_PIN.json from MANIFEST before any arm; corrupt/equal-wrong/extra-file regressions and full 927-file checks.
4. Weak tests: the identical lock regression plus the real type-deadline path fail on round-1-before a4; the worker environment regression fails on the F16 baseline and passes on the delivery.
7. OFF guard: a0–a18 are all forbidden; direct import-guard regression and original/OFF byte tests.

The earlier key, parity-schema, memory, public-boundary, atomic-journal and array-policy regressions remain in the suites and are rerun. Exact outputs and limits are in REPORT.md.
