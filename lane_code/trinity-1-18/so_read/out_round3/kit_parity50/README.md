The GPU kit is unrun. The fixed sample contains 50 items: ten per type and twelve native captures. It stresses reuse and does not estimate representative throughput.

Apply all three diffs to a fresh full copy of A4/src or B5/src. Every original file stays unchanged; the additions live in src/u0, outside the reader/evaluator hash trees. The ordinary reader entrypoint is the default OFF path. Cache settings alone do not activate extensions. Explicit activation uses `src/u0/a8.py --enable-extensions`; cache switches then default to off. The ON environment records a separate extension source hash. Rebuild and authenticate payload/artifact pins, including the extension code root, before deployment.

Keep this private kit, its original manifests, reports, and alias/reverse maps on Trinity. Public submission names, staged paths, configuration, and logs must use opaque tokens. The public array example uses numeric type slots and neutral paths. The array helper derives its command from the approved submit function, screens the command and script with the production forbidden-word list, and sends scheduler logs to /dev/null. The template is inert. Keep journals on persistent storage and keep shard membership/count fixed across attempts.

Prepare approved original and extended source roots, checkpoint/export/artifact inputs, and settings under neutral staged paths. Build a private alias JSON mapping original asset paths to those staged paths. On Trinity, seal settings and any JSON configuration metadata with the helper; its wire decoder preserves their runtime field names in memory. Seal settings only after flattening the intended item-set settings and binding every required asset. The helper rejects descriptive absolute asset paths; it never copies datasets or weights.

```bash
mkdir -p work/public
bash work/cpu.sh work/src/u0/a11.py seal --source-root work/src \
  --input PRIVATE_SETTINGS.json --aliases PRIVATE_ALIASES.json --out work/public/u3
bash work/cpu.sh work/src/u0/a11.py stage-kit --source-root work/src \
  --input out/kit_parity50 --config PRIVATE_NEUTRAL_CONFIG.json --out work/public/u0
```

The private configuration follows config.example.json. `source_root` selects the extended source; `original_source_root` selects the untouched source. Both use the same approved native tree, model, artifacts, precision, hardware, and settings. `enable_caches` uses slots 0=processor, 1=vision, 2=SAM. The staged kit contains u0.py, u1.py, a9.py, and u0.json through u3.json. The u3.json inventory binds every extension file to MANIFEST; the driver rejects equal original/patched roots and an extension-bearing original root before starting an arm. It authenticates the sealed sample bytes and retains the original logical sample pin. Transfer this staged directory through the approved transport under an opaque root; never publish the private kit directory or maps.

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

Before adoption at step 600 or later, pass the original/OFF/OFF-repeat/ON/journal/sharded GPU gates, useful-hit checks, net seconds/item checks including hashing/copying, and real persistent-storage preemption/requeue. Live weight-content hashes protect replacements and raw-storage edits, but may outweigh cache savings. The SAM-ON default is 12 GiB; other cache configurations default to 4 GiB. These caps bound cache-owned live storage and transient copies, including keys/containers; it does not cap model working memory or caller-owned outputs. Unsupported values bypass caching. Preserve adequate whole-process host/GPU headroom.

No delivered CPU test or single-GPU parity pass requires a local OS socket. StageOneSocket is a Python callback. Socket-backed transport/distributed integration is outside this kit and remains unrun. No job, scheduler command, upload, or return publication ran here.

## Production build and return integration

The ordinary builder and reader remain byte-unchanged. The additive builder is an explicit alternative. Run it in a **full staged source tree** after applying all three diffs:

```bash
nice -n 10 "$READ_PYTHON" -I -s -B "$SOURCE/u0/a12.py" \
  --enable-extensions --reader-source "$SOURCE/b" \
  --template-source "$SOURCE/orchard_h10/vendor" --out "$SOURCE/u9"
```

This command builds locally; it never submits, uploads, or copies datasets. The output must be inside SOURCE, as the original builder requires. It adds u0 to payload pins and selects pinned entry, job, runner, and preparation overlays only in the enabled package. Preparation includes u0 in artifact code pins and enables all three caches with a 12 GiB cap. Workers use atomic journals and whole-scene shards. The runner validates scene membership and writes the deterministic answer/trace archive under metadata/u0, which the existing return envelope includes. SUMMARY binds its relative path and SHA256. Existing envelope clocks remain variable; the canonical answer/trace archive must match exactly. The optional secondary item set is rejected in extension mode.

The CPU package fixture builds real archives from supplied source files, checks every payload pin, proves original-versus-OFF package bytes, checks entry dispatch, and compares the integrated merge against one shard. It does not restore real weights or validate GPU/storage/remote transport.

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

## Review round 2: finding -> fix -> test

The isolated entry, approved path roots, array policy/retry, production packaging/dispatch/merge, deadline counts, bounded lock wait, bypass counters, independent roots/pins, and stronger test gates have CPU regressions in test_round2.py. The settings environment variable is removed; an in-process --settings argument preserves native-tree selection. The SAM cap regression models large reservations without allocating them. Full live weight hashing remains: a measured raw-data write preserves id, data_ptr, and version while changing content. Version-only memoization is unsafe under the required mutation contract, so hashing overhead remains unresolved and receives no speedup credit.
