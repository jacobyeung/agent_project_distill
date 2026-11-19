FULL native routing inventory: NOT READY. All five source pins verify; recovery/units contain K1 hits; camera input and full host dependencies remain incomplete.
All paths and full SHA256 values, code checks, scene lists, frame requests, drafts and timings are in `FULL_INVENTORY.json` and `../work/`. `T` below is `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1`.
Five authorities: R0 `bdb5d402`, dev-S1 `969cdb56`, BENCH v2 `3119aa4a`, withheld-80 `634820b4`, K1 `4d4736cf`; every draft records their full pins. Checker PASS means complete resolution, not zero hits.
Counts come from `work/inventory.py` (JSONL count, native digest(raw), distinct scene/ordinal set) and `work/run_audits.py` (real sb_auditfix2 checker). Run both with `nice -n 10`, OMP/MKL/OPENBLAS_NUM_THREADS=8, CUDA_VISIBLE_DEVICES empty, and `/scratch/jjyeung/envs/p1cpu/bin/python -B`.

| recovery: source and binding | Independent coverage / exclusions | Frames / envelope |
|---|---|---|
| `/scratch/jjyeung/n30_mirror/rows_r1/out/recovery_v3/rows.jsonl`; SHA `58389a67f9a5b51abbc06e5953937b35541ef5effc4e70e6a35092d14f288473`; 994 rows and digest bindings; 9,854,828 bytes; CPU inventory 0.73s + checker 0.33s | 440 scenes; archived original map independently covers all rows; zero R0/dev/BENCH/withheld; K1=21; existing removal matches 21 | 31,808 frame references / 14,080 unique scene/ordinals; physical count, PNG paths, bytes and N stage=MISSING. Extent `c072905b`: 994 entries; envelope `work/envelopes/recovery.json`; upstream accounting and map/plan=MISSING. |

| absolute_distance: source and binding | Independent coverage / exclusions | Frames / envelope |
|---|---|---|
| `/scratch/jjyeung/n30_mirror/rows_r2/out/vehN_pool_abs_distance_full/repaired/rows.jsonl`; SHA `aedd3b54b913fd416b8daa53f022c86d1b3d98259f3c5e1a479e8bde528449d9`; 8,315 rows and digest bindings; 55,968,241 bytes; CPU inventory 9.50s + checker 0.90s | 1,690 scenes; archived original map independently covers all rows; zero R0/dev/BENCH/withheld; K1=0; existing removal matches 0 | 266,080 frame references / 54,080 unique scene/ordinals; physical count, PNG paths, bytes and N stage=MISSING. Extent `c072905b`: 8,315 entries; envelope `work/envelopes/absolute_distance.json`; upstream accounting and map/plan=MISSING. |

| units: source and binding | Independent coverage / exclusions | Frames / envelope |
|---|---|---|
| `/scratch/jjyeung/n30_mirror/rows_r1/out/vehN_units/repaired/rows_slice.jsonl`; SHA `aa1432cde2aa3612e0d0e287c94aaa0aeb37dc175485a3ad044bca71f3e5ce9c`; 8,577 rows and digest bindings; 108,000,408 bytes; CPU inventory 4.16s + checker 1.58s | 1,770 scenes; archived original map independently covers all rows; zero R0/dev/BENCH/withheld; K1=262; existing removal matches 262 | 274,464 frame references / 56,640 unique scene/ordinals; physical count, PNG paths, bytes and N stage=MISSING. Extent `c072905b`: 8,577 entries; envelope `work/envelopes/units.json`; upstream accounting and map/plan=MISSING. |

| coverage_distance: source and binding | Independent coverage / exclusions | Frames / envelope |
|---|---|---|
| `/scratch/jjyeung/n30_mirror/dist_diag/coverage_v2h/COVERAGE_DISTANCE_V2H.jsonl`; SHA `15387646fd4ac47b43c107129db3109545a981c1bd45a3910ac038d8c5432022`; 1,500 rows and digest bindings; 10,838,154 bytes; CPU inventory 2.40s + checker 0.32s | 761 scenes; archived original map independently covers all rows; zero R0/dev/BENCH/withheld; K1=0; existing removal matches 0 | 48,000 frame references / 24,352 unique scene/ordinals; physical count, PNG paths, bytes and N stage=MISSING. Extent `c072905b`: 1,500 entries; envelope `work/envelopes/coverage_distance.json`; upstream accounting and map/plan=MISSING. |

| coverage_units: source and binding | Independent coverage / exclusions | Frames / envelope |
|---|---|---|
| `/scratch/jjyeung/n30_mirror/dist_diag/coverage_v2h/COVERAGE_UNITS_V2H.jsonl`; SHA `8ec1efd2c1851fb856caa3631653390d76796f8c31cd8366d54df52916c7de82`; 4,500 rows and digest bindings; 57,255,154 bytes; CPU inventory 2.75s + checker 0.98s | 1,323 scenes; archived original map independently covers all rows; zero R0/dev/BENCH/withheld; K1=0; existing removal matches 0 | 144,000 frame references / 42,336 unique scene/ordinals; physical count, PNG paths, bytes and N stage=MISSING. Extent `c072905b`: 4,500 entries; envelope `work/envelopes/coverage_units.json`; upstream accounting and map/plan=MISSING. |

| Camera wording | Independent coverage / exclusions | Frames / envelope |
|---|---|---|
| `/scratch/jjyeung/orch_n30/sb_rowA2` is absent; row path, pin and count=MISSING | Scene evidence, checker and extent row binding=MISSING | Frames/bytes/stage=MISSING; `work/envelopes/camera_wording.json`; integration family requires tree owner because source_names has only five entries. |

| Envelope contract | Exact checks (paths relative to T) |
|---|---|
| Pins, family, count | Exact `{path,sha256}`, absolute/hash-verified (`p3_provenance.py:43-51`); schema/family (`r2_intake.py:34-37`); count is reported, not compared to cardinality (`:120-123`). |
| Composition | Five names and fixed V2H/wording pins (`r1_coverage.py:5-48`); staging hashes, catalog schema/hash/QID membership; rows/family/stream/extent exact equality (`r1_routing.py:162-191`). |
| Native contract | `trace_contract=next-leg-r2-v1`; validator `a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268`; per-QID digest of raw JSON, no duplicate QIDs (`r2_intake.py:36-37,76-88`). |
| Coverage | Pinned coverage exclusions equal envelope exclusions, rows_sha256 matches rows; QID status=known, names include native and canonical identities (`r2_intake.py:55-57`; `r2_exclusions.py:47-68`). All five coverage files are produced from verified archived map `488480ab`, not row canonical claims. |
| Exclusions | Exactly seven SEALED roles (`r2_exclusions.py:5-44`); merged dev `a1869ae2` and withheld checks (`r2_intake.py:45-54,93-108`); R0/K1 room authority is additionally enforced in composition (`r1_rooms.py:19-35,71-83`). Documentary five-pin fields do not add intake checks. |
| Upstream | Receipt pins must bind identical exclusions and valid seen=admitted+refused counts; prefiltered needs nonempty receipts (`r2_exclusions.py:70-85`; `r2_intake.py:67-68`). No authenticated family accounting identified. |
| Extent | Exact config pin `c072905be4405a92d7bb906112209f2d27a8c9b58d291b64373c5551c3e96495`; normalized content/repair digest, full box counts (`extent_receipt.py:5-47`). All 6,000 V2H rows pass exact rewording/inherited-entry checks; no synthetic frames or new geometry proof supplied. |
| RGB metadata | gzip map (d,s,i)→content-addressed PNG, plan raw_n and dataset, FPS authority; 32 ordered anchors and clock/hash agreement (`s1_routing.py:58-150`; `r2_contract.py:124-140`). Map/plan missing; FPS `36ae882f` exists (47,800 bytes). |
| Grammar / optional fields | Normalize, event/direct grammar, units and type checks; optional both-path policy/heads; mix_cells copied; row failures become refusals (`r2_adapters.py:7-73`; `r2_contract.py:143-207`; `r2_intake.py:95-126`). Full field/check inventory is `work/CONTRACT.json`. |
| Full host / first failures | Every draft with limit=None fails `r2_intake.py:42`: Local slices must contain at most 2000 rows per family. With 2000, five fail upstream MISSING at `r2_intake.py:58`→`p3_provenance.py:46`; camera fails scene_coverage MISSING at `:55`→`:46`. No hostname or function substitution. |
| routing_base | P step-400 receipt `ca0616db…` is c1-routing-stream-v1/train/zero overlap, database `4e8e6c04…`, division `f41d15aa…`; `ext/m400real/r.json` binds its config. Set request.routing_base AND cfg.streams.routing; mode q uses config and preparation regenerates the base (`launch_r1/entry.py:160-163`; `s1_admission.py:202-215`). |

The five slices share 56,640 distinct scene/ordinal requests. Their exact PNG paths/bytes require the missing map `17aa3e9e` and plan `7cc01f36` at the config's `/scratch/fsw/.../8865619b/k/` paths. P's listing records 14,502,816 and 1,518,048 bytes; current N staging is unproved.
The frame host must hold those PNGs under mapped `/data2/k6tk`, map/plan/FPS, all source rows/envelopes/coverage/exclusions/extent/catalog, routing/base division and native stores. P's recorded k6tk bundles total 78,318,837,760 bytes/290,880 members; these are not N subset totals. JSON lists all archive paths and P frame-audit roots.
N VQA store `210b2534` exists locally: 1,718,255,616 bytes. Pointing `c09bb5ca` is recorded as 218,099,712 bytes; routing base `4e8e6c04`, pose `b32359ce`/`0b95850a` sizes remain MISSING. JSON lists exact store paths, pins, provenance and staging status.
The kit needs exact staged family/source/catalog/extent pins in config and request, Q_E4 absolute frame-root mappings, and verified frame admission. Q_E7=1 works only after sb_fhalias/tree_rebuild adds the alias and reseals; this lane writes no alias patch. Preserve the non-Trinity/local-node/limit vetoes.

| Rank / owner | Required production and CPU estimate |
|---|---|
| 1 main + tree_rebuild | Certify final retained K1 exclusion: existing removals cover all 283 source hits (0 unmatched). Produce accounting/census; no new source pin needed for these hits. Matching: 1–5 s; integration estimate: 5–15 min. |
| 2 this lane — done | Digests, independent coverage, six drafts and dry checks: 19.53 s; five exclusion audits: 4.10 s measured. |
| 3 main | Supply camera report/rows and pinned map/plan plus current frame inventory. Camera audit estimate 1–10 s; map parse/join 1–3 min once present; availability wait MISSING. |
| 4 tree_rebuild + main | Authenticate upstream receipts, finish envelopes and config/request bindings, decide camera integration. Metadata checks 1–5 min; engineering estimate 15–30 min. |
| 5 tree_rebuild / sb_fhalias | Separate naming-only alias patch and new seal. Focused CPU checks 1–5 min; engineering estimate 15–30 min. |
| 6 main on frame host | Stage exact RGB/stores, compose, prepare and audit every retained frame plus fixed hash sample. Presence estimate 1–5 min; hash time B/(100–300 MB/s), B=MISSING; full preparation CPU time MISSING. |

Estimates assume ≤8 CPU threads and available local inputs; no transfers, RGB reads, GPU, network, launcher, tmux, Git or foreign writes occurred. No revision-history wording is retained.
