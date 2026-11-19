# Review of sb_evidence (component evidence survey) — verdict

**ACCEPT WITH FINDINGS.** The nine-MISSING conclusion stands: no surviving source lets any slot be written honestly. The gap files misstate the geometry-tower gap, omit several pinned missing sources, and the survey missed one population that touches the disclosed venue 381879.

Paths: W = `/scratch/jjyeung/orch_n30/tree_rebuild10_w`, M = `/scratch/jjyeung/n30_mirror`, B = `/scratch/jjyeung/orch_n30/sb_evidence`. Notes and listings: `notes/` here. N's tree: `W/w19/work/tree_r1`; its `r2_policy.py` (fd62d4bf…) and `tests/test_r2_policy.py` (36b91fa2…) are the bytes B tested.

## Findings

1. **No slot-serving source survives (Q1).** I listed the members of the 48 top-level mirror archives B never opened (b03 ×9, b04 ×6, b05, b06 ×2, b07 ×7, b09 ×5, b12 ×4, cont_ops ×5, cont_ops17, count_diag ×3, dist_diag ×2, r1_ops6, size_diag, tower_redecide) and of 12 nested archives (`notes/members/`). No member path contains 97a6a3eb, b19c1200, f2ad01ad, 49becb79, 1742c666, f02f16ad, 7c9f2d84 or step_400. The step-544 config (`W/w12/.../runs/469ddece/inputs/prepare_dd26…/config.json`) confirms that the parents are `f2ad01ad/runs/49becb79/m200/artifact.json` (c1a42588…) and `97a6a3eb/runs/b19c1200/train/step_400/heads.json` (fd60ac2f…). The near-hits are fixtures:
   - The `5e1d07a4/f/h/r16/receipt.json` copies in `M/cont_ops/h1pkt_fix5_2252Z.tar` are 188-byte tamper tests.
   - The `469ddece/m544/*` copies in `c16_mirror_2245Z.tar` are stubs of 77 to 384 bytes.
   - The `fix4_listing/.../prepared/*_scene_indices.json` files hold the 22-byte string "local listing fixture" (bcfa208d…).
   - No archive holds a G3T or SAM 3 frozen-parameter inventory or a GF1 connector record. `b03_e2etest_eat1_v1.tar:work/nextleg/static/SCAN_GF1.json` is a static code scan.
2. **B missed genuine pinned copies, though none serves a slot (Q1/Q4).** `M/cont_ops/h1pkt_fix5_2252Z.tar` member `h1/chain_r1/build/fx/k/` is a full copy of the LEG-S1 kit `k/`. Four of its members are byte-identical to pins that `B/out/PIN_RESOLUTION.json` lists as unresolved:
   - `frame_map.jsonl.gz` (17aa3e9e…), `frame_plan.json.gz` (7cc01f36…), `input_source_tokenizer.json` (5f9e4d49…) and `t_b01ce449beffe35b.tar` (845b1789…).
   - `M/old_lanes_3_30/old_lanes_3_30_a.tar` holds `…/ap/e84d901c/arm/frozen/6f27ae81/model.json` (cc724d5e…). This is the base-model manifest pinned as `/model` by `prepared/receipt.json` (0664bb17…).
   - The resolver also misses local files. `W/w12/fixtures/work/kit07ca49df_meta/m/k/` already holds `pool_exclusion_0..2.tsv` and `remove_0..5.jsonl` with the pinned hashes (951902ee…, a5d707ac…, 7a910565…, 62113ff3…, …), yet all are unresolved. The resolver evidently indexed JSON only, so "384 refs / 76 sha unresolved" is inflated.
3. **The survey missed a population that touches the disclosed venue (Q1).** `frame_map.jsonl.gz` from finding 2 lists the step-544 kit's frame universe: 290,880 frames over 4,697 scenes. Using the BENCH v2 token rule, it contains two in-scope captures: `d3/41159526` and `d3/41159521` (arkitscenes/venue381879; VSI-Bench and ReVSI). It also contains 126 STI-Bench/ReSTI and 20 MindCube captures. The policy admits venue 381879 when disclosed (`r2_policy.py:50`). This is a frame pool rather than proven training membership, and the inherited parents remain missing, so no slot becomes writable. Any future `init_m544`/`heads_*` record must still list these overlaps. B's population table omits this population.
4. **The gap decisions match the policy (Q2).** `record()` (`r2_policy.py:30-55`) checks the following:
   - **All slots:** a non-null pin; schema `r2-component-evidence-v1` with the slot's component, class and phase (`both`); non-empty `inputs`, each `bound()` inside the kit root; a verdict in {PROVEN_CLEAN, OVERLAP_FOUND, EXEMPT_FROZEN}.
   - **external_frozen:** `EXEMPT_FROZEN` and `frozen is True` (lines 42-44).
   - **lineage:** list-typed `overlaps` and `checked_banks`, `checked_banks` ⊇ {VSI-Bench, VSTI, ReVSI}, and no in-scope overlap except venue `'381879'` (lines 45-51).
   - **new_training:** `PROVEN_CLEAN` and `exclusions_complete is True` (lines 52-54).
   - **Callers:** `read_bank` calls `components(…,'training')` for any in-scope bank (lines 144-145).

   The code checks no inventory. The evidence bar is stated in the kit gap records `W/w19/work/n1fix2/inputs/EVIDENCE_<slot>.json`; for the external slots they demand "upstream release identity, weights/config identity and actual optimizer frozen inventory bound together." Slot by slot:
   - **segmenter:** `SAM3_RECEIPT.json` (979e2f77…) itself says "cache-time revision [is] not certified". N reads SAM 3 only through mask caches (`training_contract.py:66`, `s1_grounding.py:54`), and no record binds those caches to checkpoint 9999e234…. An inventory derived from code is not the actual optimizer inventory, so MISSING is right.
   - **heads_gf1_connector:** N sets `geometry_connector=none` (`n1fix2/inputs/config.json`, 8063ef04…), and A0 carries no geometry encoder (`r2_config.py:56-58`). N's own `r1_components.py:47` still says the "lost record is still owed before an official read." A PROVEN_CLEAN record resting on that config would claim "complete clean scene evidence" (`r2_policy.py:54`) without any scene evidence, so MISSING is right. The kit holds no `EVIDENCE_heads_gf1_connector.json`, so this slot's stated requirement is undocumented.
5. **The geometry-tower gap overstates what is missing (Q4).** `gaps/geometry_tower.json` and report line 63 say the tower's release and weights/config identity are missing. N's tree pins both:
   - `student_pilot/tower_read.py:19-22` (2cd338e1…) sets REVISION c55e91a0…, WEIGHTS d460957b…, CONFIG 5aeb2acd… and SOURCE df1ea59a…. Lines 1-4 keep the tower outside the student's module tree.
   - `M/cont_ops/c16_mirror_2245Z.tar` member `r1route/out2/A/surviving_records/inputs_tower.json` (025b4688…) binds those weights and that config, plus SAM3 9999e234…, to artifact 1d6eeb28….

   Only the run-bound frozen optimizer inventory is missing. The slot stays MISSING, but the gap file should be narrowed to that one item.
6. **The gap files omit pinned missing sources (Q4).** The lineage gaps name only the 13 NFS receipts and row stores. They omit the step-544 run's own membership files under `ap/8865619b/runs/469ddece/inputs/prepare_dd26…/prepared/`, all pinned by `prepared/receipt.json` (0664bb17…):
   - `pointing_scene_indices.json` (93c4fed5…), `routing_scene_indices.json` (613a9f9e…), `vqa_scene_indices.json` (f9dc4a2d…), `pose_scene_order.json` (3cb1ccf5…) and `pose_mix_order.json` (d8d33340…).

   They also omit the readout pins named by `b02e4385.json` and N's config: `/lustre/…/e84d901c/z/eb035f92.json` (training_scenes, edaecb6c…), `544dcf9b/in/30c516bf.json` (d6d6a53a…) and `e84d901c/z/986ba20f.npz` (0471677f…). These names appear only in `PIN_RESOLUTION.json`, although the brief required each missing manifest to be named.
7. **The intersection counts are correct (Q3).** `notes/recompute_recovery.py` (9c24ae92…) recomputes three populations without `r1_rooms` or the alias table. It uses its own `rung1` token rule from BENCH v2's `token_rule`, its own canonical-to-room mapping, and the visits CSV (657020f2…).
   - My 1,212 member tokens equal BENCH v2 (3119aa4a…) `rung1_tokens`.
   - Bank sizes match `BENCHMARK_SCENES.json`: VSI-Bench 707 captures / 288 rooms, VSTI 312 / 142, ReVSI 852 captures (with 3rscan and multiscan) / 381 rooms.
   - recovery (58389a67…): 994 rows, 384 rooms, 0/0/0. absolute_distance (aedd3b54…): 8,315 rows, 1,125 rooms, 0/0/0. units (aa1432cd…): 8,577 rows, 1,171 rooms, 0/0/0.
   - Every row token equals `rung1(canonical)`.
   - The `union_not_attributed` branch (`intersections.py:35-38`) never fires, because every other corpus has a single owner.
8. **B overstates how much of the v7 store is unknown (Q3).** The 119,375 unresolved rows are all ScanNet (`d1`: 38,533 rows, 280 tokens) and ScanNet++ (`d2`: 80,842 rows, 617 tokens). The alias table (c47c5fcd…) has only ARKit (`d3`) entries.
   - Exhaustive hashing of `scene0000_00` through `scene0999_09` resolves all 280 ScanNet tokens to 156 rooms, none in scope (`notes/v7_d1_enum.json`).
   - No token among the 204,413 v7 rows equals any BENCH v2 capture token, and all 85,038 resolvable rows follow the `rung1` rule.
   - The only residual unknown is whether the 617 ScanNet++ tokens follow the same rule. This does not change `data_rows_r2`, which needs post-filter manifests and frame-host membership for every family, not just v7.
9. **The remaining claims hold, with minor wording issues (Q4).**
   - **Verified:** the archive SHA (18d4d04c…) matches; `policy_tests.log` shows "Ran 5 tests … OK"; SURVEY.json lists 325 sources; every self-check phase, slot and gateway case REFUSEs with `Missing component evidence`; both source-archive copies are recorded.
   - **Line 25:** it claims `Rooms` applies "ScanNet++ aliases", but the pinned alias table has none. ScanNet++ matches only through the scannetppv2→scannetpp room mapping (`r1_rooms.py:42-52,63-64`).
   - **Line 46:** the five program-choice records are required by `components(…,'native_evaluation')`. `read_bank` checks only the declared choices (`r2_policy.py:151-153`).

## Usable source by slot
None makes a slot writable. Partial sources a rebuilder should cite:
- **geometry_tower:** release, weights and config identity from `tower_read.py:19-22` and `inputs_tower.json` (finding 5).
- **init_m544 / heads_pose / heads_depth:** the frame universe and venue-381879 disclosure from `fx/k/frame_map.jsonl.gz` (finding 3).
