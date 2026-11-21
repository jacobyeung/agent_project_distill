NO LEAK: row-key check PASS for pose and routing (both directions empty), and for pointing and vqa (16:12Z).
# fix9 REPORT: row-key evidence for the scene-census check (RULING 1554Z item 2)
STATUS 16:13Z: DONE for all four streams; (a) and (b) hold everywhere; no leak. Output rd/p2.out (node copy /tmp/a15_f9_174134/f9.out, f9_result.json).
- 16:05Z: no Trinity mirror of the a2v3/a3v2 pose stores, P's routing base 4e8e6c04 or the 14 pool sources exists on trinity-1-18 (sha-name and file-name search of 1-18 /scratch, rd/e2-e4.out) or on 3-30. Only the two lists are mirrored. So the row-key check runs on the held node (srun --overlap, own dir /tmp/a15_f9_174134, job dir read-only), with the kit tree tar 5f2d77c4 extracted there.
- Set definitions (s/f9.py; tree modules from kit tree tar 5f2d77c4 extracted at /tmp/a15_f9_174134/t, import paths asserted):
  - Key: pose (mix source k, sqlite column i); routing base ('base', i); pool ('pool', source, line index); pointing/vqa population position.
  - L = census-listed rows: population positions minus the kept indices the census receipt wrote (r2_scene_bindings.py:186-213 rebuild_receipt, receipts of p/q/sc/2.json), cross-checked by a recount with Exclusions.matched (s1_exclusions.py:74-99) over r2_scene_bindings.rows(population). Pool: rows of all 14 sources of the census pool selection (rebuild_pool -> s1_pool.prepare, s1_pool.py:125-221) that Pool.scenes.matches marks (s1_pool.py:41, s1_exclusions.py:101).
  - A = admitted rows. Pose: the job's own pose_mix_order.json (c1_pose_mix.prepare, c1_pose_mix.py:131-237). Routing base: the census_rows predicate of s1_routing.py:319-325 (COMPATIBLE type by s1_routing.compatibility, s1_routing.py:159-193, and scene in the division's train and not held-out). Pool: all rows of the pool sources the job's routing receipt names (the ELIGIBLE ones).
  - M = filter-matched rows. Pose: A minus the kept pairs of s1_exclusions.selection (s1_exclusions.py:191-229, via _database :147-163), exactly what apply/coverage_report count. Routing base: A rows that Exclusions.keep rejects as reason() calls it (s1_routing.py:273-279). Pool: the upstream part, rows of the routing build's pool sources that Pool.scenes matches (what the receipt's upstream[pool] report counts).

## Results (node run 16:07:02-16:11:11Z, step 174134.235, rc 0; rd/p2.out)
Tree modules s1_exclusions, r2_scene_bindings, s1_pool, s1_routing, c1_pose_mix, s1_scene_census, p3_provenance of the kit tar are byte-identical to the job's tree. Pose A is the job's own p/q/p/prepare_fc57.../prepared/pose_mix_order.json, sha256 d8d33340 (the walk's n1 and n2 copies have the same sha256; the script read the walk copy).

| stream | L | M | A | L∩A | L-M | L-A | (a) L-M == L-A | (b) (L∩A)-M | M-L |
|---|---|---|---|---|---|---|---|---|---|
| pose | 46,257 | 44,257 | 229,924 | 44,257 | 2,000 | 2,000 | equal | empty | 0 |
| pose/0 (a2v3) | 10,657 | 8,657 | 27,604 | 8,657 | 2,000 | 2,000 | equal | empty | 0 |
| pose/1 (a3v2) | 35,600 | 35,600 | 202,320 | 35,600 | 0 | 0 | equal | empty | 0 |
| routing | 20,497 | 18,026 | 127,640 | 18,026 | 2,471 | 2,471 | equal | empty | 0 |
| routing base | 4,768 | 3,985 | 35,423 | 3,985 | 783 | 783 | equal | empty | 0 |
| routing pool | 15,729 | 14,041 | 92,217 | 14,041 | 1,688 | 1,688 | equal | empty | 0 |
| pointing | 6,584 | 6,584 | 25,020 | 6,584 | 0 | 0 | equal | empty | 0 |
| vqa | 0 | 0 | 204,413 | 0 | 0 | 0 | equal | empty | 0 |

Evidence lines:
- Runtime config p/q/c.json c686a4b2, census record sc/2.json 3d4f7ece, reference sc/0.json 4137b8ee (exact_rebuilt_population true). a2v3 census: 66,934 rows, 10,657 listed (5,618 dev / 5,039 test), recount equal.
- Census keys equal the recount by keys for every recounted store (recount_equal true: a2v3, a3v2, base 4e8e6c04, pointing); census counts equal the reference p/q/sc/0.json (a3v2 13,440/22,160; base 4,768/0; pointing 3,640/2,944). Every sqlite store's i column is 0..n-1, so census positions and mix indices name the same rows.
- Pose filter counts from s1_exclusions.selection reproduce the walk: pose/0 seen 27,604, dev 3,777, test 4,880; pose/1 seen 202,320, dev 13,440, test 22,160; no upstream report. L-A for pose is the 2,000 listed a2v3 rows outside the frame-prefix selection (fix6 o14: 1,841 dev + 159 test). The 1,200 a3v2 rows the mix drops by its own test-scene rule hold no listed row (pose/1 L-A = 0).
- Routing base: legacy check (s1_routing.compatibility on the node) COMPATIBLE camera_displacement, camera_movement_direction, camera_rotation (200/200 each); object_abs_distance DROPPED pool_type_wins. The census_rows predicate admits 35,423 rows; Exclusions.keep on them gives seen 35,423, dev 3,985, test 0, equal to the job's routing receipt r16 entry. The 783 listed base rows lie outside A (object_abs_distance or outside the division's train scenes).
- Routing pool: census pool selection 74640a29 is the routing receipt's source; its ELIGIBLE sources are the 9 the routing build reads and the 9 of upstream[pool]. Per-source key recounts equal the census report and the routing upstream report for all 9 (and the census report for the 5 deferred). L-A = 1,688 = the listed rows of the 5 unread sources ROUTE_direct 1,498, SCENE_room 70, SCENE_room_sppK 0, T0_room 18, T1H1_room 102. No listed pool row sits in any selection's kept indices; the pool rule and the config rule agree on every row.
- vqa: the census lists none of its 204,413 rows; the stream's receipt reports 0 matches over 212,384 rows. pointing: the stream reads the whole census population (25,020) and its upstream report equals the census.
Conclusion: under the tree's own functions, every census-listed row inside the admitted subset is filter-matched, and every listed row the filter does not match lies outside the admitted subset. The count gap of the 1550Z refusal is exactly the listed rows outside the admitted subset (pose 2,000; routing 2,471).
- Record: /data2/jjyeung/agent_project_data/distill_design/N_SCENE_CENSUS_ROWKEY_20261121.md (INDEX line added). Orchard calls: 16:07:00Z, 16:09:18Z, 16:11:50Z, 16:14:02Z (each 2+ min apart); no stream over 20 MB moved (largest transfer: 2.9 MB kit tar from 1-18).
