The GPU kit is unrun. The fixed sample contains 50 items: ten per type and twelve native captures. It stresses reuse and does not estimate representative throughput.

Apply both diffs to a fresh full copy of A4/src or B5/src. Every original file stays unchanged; the additions live in src/u0, outside the reader/evaluator hash trees. The ordinary reader entrypoint is the default OFF path. Cache settings alone do not activate extensions. Explicit activation uses `src/u0/a8.py --enable-extensions`; cache switches then default to off. The ON environment records a separate extension source hash. Rebuild and authenticate payload/artifact pins, including the extension code root, before deployment.

Keep this private kit, its original manifests, reports, and alias/reverse maps on Trinity. Public submission names, staged paths, configuration, and logs must use opaque tokens. The public array example uses numeric type slots and neutral paths. Its template supplies an opaque job name and explicit log destinations. Keep journals on persistent storage and keep shard membership/count fixed across attempts.

Prepare approved original and extended source roots, checkpoint/export/artifact inputs, and settings under neutral staged paths. Build a private alias JSON mapping original asset paths to those staged paths. On Trinity, seal settings and any JSON configuration metadata with the helper; its wire decoder preserves their runtime field names in memory. Seal settings only after flattening the intended item-set settings and binding every required asset. The helper rejects descriptive absolute asset paths; it never copies datasets or weights.

```bash
mkdir -p work/public
bash work/cpu.sh work/src/u0/a11.py seal --source-root work/src \
  --input PRIVATE_SETTINGS.json --aliases PRIVATE_ALIASES.json --out work/public/u3
bash work/cpu.sh work/src/u0/a11.py stage-kit --source-root work/src \
  --input out/kit_parity50 --config PRIVATE_NEUTRAL_CONFIG.json --out work/public/u0
```

The private configuration follows config.example.json. `source_root` selects the extended source; `original_source_root` selects the untouched source. Both use the same approved native tree, model, artifacts, precision, hardware, and settings. `enable_caches` uses slots 0=processor, 1=vision, 2=SAM. The staged kit has only u0.py, u1.py, a9.py, u0.json, u1.json, and u2.json. It authenticates the sealed sample bytes and retains the original logical sample pin. Transfer this staged directory through the approved transport under an opaque root; never publish the private kit directory or maps.

On an assigned GPU, the acceptance command is **not executed here**:

```bash
nice -n 10 "$READ_PYTHON" -I -s -B /scratch/u0/u0/u0.py /scratch/u0/u0/u2.json \
  --out /scratch/u0/u9 --enable-gpu --public --repeat-baseline --shards 4
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

Before adoption at step 600 or later, pass the original/OFF/OFF-repeat/ON/journal/sharded GPU gates, useful-hit checks, net seconds/item checks including hashing/copying, and real persistent-storage preemption/requeue. Live weight-content hashes protect replacements and raw-storage edits, but may outweigh cache savings. The 4 GiB default bounds cache-owned live storage and transient copies, including keys/containers; it does not cap model working memory or caller-owned outputs. Unsupported values bypass caching. Preserve adequate whole-process host/GPU headroom.

No delivered CPU test or single-GPU parity pass requires a local OS socket. StageOneSocket is a Python callback. Socket-backed transport/distributed integration is outside this kit and remains unrun. No job, scheduler command, upload, or return publication ran here.
