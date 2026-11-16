# D0 launch procedure: data-only reseal of kit 07ca49df (cont_ops, trinity-1-3, 2026-11-15)

Lane-local evidence is on trinity-1-3 under `/scratch/jjyeung/orch_n30/cont_ops/work/d0/`. Tools are mirrored in `events/cont_ops/d0_tools/`. Nothing was submitted or written on Orchard.

## 1. Answers to the four kit points

**P1. The tree's builder does not rebuild a four-stream kit. The kit's own records do, and they need no code edit.**
- `launch_s1/build.py` always injects `mdg`, its streams and its mix from `configs/stageb_cp1rv_mdg_w4.json`. Its `bindings.config` can override keys but cannot delete one. I fed it the production values (harness `harness/run_build.sh` and `bindings_repro.py`, the unchanged builder in a bwrap namespace with a stand-in of the 24 original pin paths). It refuses at `carrier_c1_sweep.recipe_for`: `Final mode needs a mix over pose/vqa/pointing/routing` (`harness/repro4.log`).
- Kit 07ca49df's own review records how the kit was made: the certified five-stream configuration was edited by removing MDG, setting a new run identity and regenerating pins (`k/review.json`, attestation).
- So I wrote `tools/derive_kit.py` (stdlib only). It copies b/, job.sh, job8.sh, 7.json and the trainer tar unchanged, then writes a new config (file name = sha256(config)[:8]), 1.json, 0.json, launch.json (with the source_seal computed as `b/g.py` checks it) and SHA256SUMS.txt. The serialization is the builder's.
  - **T1:** with no overrides, it reproduces 07ca49df's `b02e4385.json`, `launch.json`, `0.json`, `1.json` and `7.json` byte for byte, plus SHA256SUMS except the two big tars I did not fetch.
  - **T2:** with D0 stand-in pins (new run and kit keys, new VQA and routing receipts, the m544 init, an m544 tars entry, TEST review and staging records bound to the new identity and admission contract), the kit's own `b/g.py check(... 'p')` returns PASS, and `b/a.py --build-only` passes the inventory gate. With the old review, g.py refuses ("Independent admission is not bound to the launch configuration"). Full `a.py` refuses until an ANON_OK content scan is CLEAN.
- New inputs are pinned as data: `config.streams.{vqa,routing}` take `{path, sha256}` receipts, and `0.json` `tars` entries take `{parts on project, files: {logical path: sha}}`. Any new identity needs new `review.json` and `staging.json` records and a new ANON_OK scan. Those are process steps, not code.

**P2. Yes for loading. One trainer behaviour cannot be changed by config.**
- `init_artifact = {artifact: {path, sha 1d6eeb28…}, lm: full, heads: [pose, depth]}` is the same form the leg used for CP1 m200.
- On CPU (`harness/q2_init_check.py`, trainer source b01ce449), `validate_init` and `validate(cfg)` both PASS. `init_from_artifact` passes the schema (`carrier-c1-artifact-v1`), `pose_backing` (lm_final_norm), placement, frame_layout (duplicate) and position-policy checks, and stops only at the first weight read, because weights are not staged locally.
- The m544 export's trained groups are depth (94 tensors) and pose (81), both covered by heads [pose, depth]. The LM loads in full.
- **The caveat:** after the LM load, final mode always calls `routing.init_routing_embeddings` (`carrier_c1_run.py:781-783`). That resets the routing-opener input and output rows to the mean of their constituents, discarding their 544 trained steps. LEG-S1 itself started this way from m200: routing loss was 1.18 at step 1 and 0.08 by step 18.
- Keeping the rows needs the one-hunk guard from the reviewed warm-start patch 3d2e5fa8 (`elif not receipt.get('warm_start')`), which means a source change, a new seal and a review.
- `student_pilot/warmstart.py` is the SFT-LoRA adapter path; D0 does not use it.
- **Default:** accept the reset (pure config) and state it in the run identity.

**P3. Yes, the k6 store the kit stages is complete for its own map.**
- All 151 staging source paths in `k/0.json` exist on Orchard at their pinned sizes (379.6 GB). This was a stat only; the kit re-hashes at staging.
- k6tk is 12 archives under `cp4tk_fr/k6tk/parts/{a0..a2,v0..v2}n3`: 78,318,837,760 B and 290,880 members. That equals the 290,880 unique frames of `MAP.jsonl.gz` (= kit `k/frame_map.jsonl.gz`, sha 17aa3e9e) over 4,697 scenes. The 1.33 GB evalx27 saw is the top-level metadata only.
- Re-rendered sealed rows keep their pins and are covered.
- New rows (facing pairs, totals) are covered only if every frame they cite is in that map. Rows lane: check each new row's frame sha256 or (d, s, i) against `k/frame_map.jsonl.gz` before delivery; a missing frame needs a store extension and a new pin.

**P4. Yes for the code; the CPU admission run settles the data.**
- A pool selection without ROUTE_direct works with no code change if ROUTE_direct's `status` becomes non-ELIGIBLE with a `reason`. Production already carries one deferred source (SCENE_room_sppK, `room_set_not_authorized`).
- In that case `s1_pool_relocate.relocate` skips it, `s1_routing.materialize` records it under `source_deferrals` (the denominator keeps its 10,458 declared rows), and `pool_types` drops route_planning, so the legacy r16 check is unaffected.
- The new `pool_selection.json` is a new pin: it changes `config.s1_routing.selection` and the catalog, hence the identity, review and staging. `pool_s1:ROUTE_direct` should also leave `scene_coverage.source_map.routing`. It is only a reference count today (NOT_COMPARED), so leaving it in does not fail.
- **Routing shares, from 169097's materialization report:** routing goes from 57,136 to 47,732 rows, all programs, at natural share within the 64 routing rows per step:

  | Type | Rows | Share | Rows/step now | Rows/step before |
  |---|---|---|---|---|
  | camera displacement | 14,020 | 29.4% | 18.8 | 15.7 |
  | camera movement direction | 12,260 | 25.7% | 16.4 | 13.7 |
  | camera rotation | 9,143 | 19.2% | 12.3 | 10.2 |
  | object absolute distance | 11,728 | 24.6% | 15.7 | 13.1 |
  | room size | 581 | 1.2% | 0.8 | 0.65 |
  | route planning | 0 | 0% | 0 | 10.5 |

- Unverified: whether the VQA stream's admission accepts `route_planning` rows. The CPU mode-p run below settles it.

## 2. Procedure, from a delivered row set to the first GPU step

| # | Step | Command or tool | Cost |
|---|---|---|---|
| 1 | Rows lane delivers VQA and routing stores in the sealed receipt and rows.sqlite format, a new `pool_selection.json` (ROUTE_direct DEFERRED), and a frame check against `k/frame_map.jsonl.gz` | rows_rebuild | — |
| 2 | Stage rows on Orchard as tar parts under `/project/community/jjyeung/distill/okit/in/cr/` (one archive per store) | governor-registered stream; size from the rows lane | project space |
| 3 | Repack the m544 export: GCS `q8/8865619b/469ddece_mstop.tar` (members `m544/…`) to parts whose members are `ap/8865619b/runs/469ddece/m544/{heads.pt,full_weights/*}`, plus `ap/d0i<run>/m544/artifact.json`, a copy at a logical path outside `ap/8865619b`, because `hp()` maps that prefix to the per-job kit root and not to the staging union | on the Orchard login node: `gsutil cat` parts \| Python tarfile renaming \| write parts, with a sha per member checked against the artifact pins | read 21.6 GB from GCS, write 21.6 GB to project, about 10-20 min |
| 4 | Derive the kit, pass 1: `derive_kit.py kit07ca49df OUT over.json` with run_key, kit_key, persistent root (project path, not /home), streams, init_artifact, `deployment.init`, `deployment.tars` (drop m200, add m544 and the new stores) and `add_k` pool_selection.json; print identity and `d.contract` digest | `d0_tools/derive_kit.py` | seconds |
| 5 | Independent review of the derived config and admission contract (verdict PASS bound to identity and contract), and a read-only staging verification (`missing: []`) | Codex Astra review plus an Orchard read-only stat/sha step | about 1-2 h |
| 6 | Pass 2: derive with `add_k` review.json and staging.json and `admission_file`; ANON_OK content scan of the new manifest (CLEAN, hits 0); local `g.py check p` and `a.py` | as in T2 | minutes plus the scan |
| 7 | New wrapper `j/<kit>.sh` from `source_jl13.sh`, changing only `KH` (kit dir), `RUN` and `RS` (persistent root). Both on project, since `/home` writes are allowed again but must not grow. Review the 3-line diff | sed and review | 30 min |
| 8 | CPU admission and first batch on `general`, 0 GPU: `sbatch -p general -c 16 --mem=800G -t 06:00:00 -J a15_cot_ap<hex> -o /dev/null -e <kit>/o/%j.err --wrap '/bin/bash <kit>/b/r.sh p 0 && /bin/bash <kit>/b/r.sh c 0'`. Mode p is the native full-population derivation; mode c runs the first batch on every rank, on CPU when no GPU is visible | after ORCH GO, one job; `general` allows one running job per user (evalx27) | p measured about 1 h 45 min in 169097; c on CPU unmeasured |
| 9 | Advanced job: `cd /home/jjyeung/okit && env -u TK_JOB_START sbatch -J a15_cot_ap<hex> -o /dev/null -e <kit>/o/%j.err <kit wrapper>`. Mode t, cold start, with in-job admission again and the GPU first-step gate `all_rank_native_v1` | ORCH GO | 4 H100 × 24 h; 1,000 steps at about 131 s is about 36 h, so two allocations, about 146 GPU-h |
| 10 | Stop rule and reads: TRACE_RULING 2.7 F1-F4 at m100 and m200 (exports via sessions minted for the new run names); rule E's analogue (steps 1-3 vs LEG-S1 steps 1-3) does not apply to a warm start, so use the native first-step gate plus a step-1 loss sanity check against m544's 530-544 baseline, with routing exempt because of the opener reset | evalx lanes | per read |

**Prerequisites outside the kit:**
- **Upload sessions:** `sess.json` holds sessions only for run 469ddece object names. D0 exports need new sessions minted for its run key. Minting is a Trinity-side step that GCS credentials gate.
- **Authorization:** `k/4.json` allows modes p, t and u until 2026-11-26. Re-issue it if D0 launches later, and for honesty, since its `config_sha256` field names a7ad7051.
- **Project space:** 215 GB free now. D0 adds rows (size from the rows lane), 21.6 GB of m544 parts and a 113 GB end slot per allocation.
- **Advanced queue:** the 4-GPU per-user QOS is shared with the continuation and with main.
