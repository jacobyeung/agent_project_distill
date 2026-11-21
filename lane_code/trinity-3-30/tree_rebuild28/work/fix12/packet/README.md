# n33 review packet: merged kit F1 + census + frame map + room census (W4) (fix12, lane tree_rebuild28)
Kit trinity-1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w/w33n/n_go, seal 929ab2139b6dd408972e7b5bcffcf00588f70cecb006f6f9c0da44c55825dc57 (final). Built from F1 kit 489f7f0f with the kit's support.reseal; the tree's launch_r1.build.verify(kit) == seal: True. Tar W/w33n/s33n_n_go.tar b0c03db32dadc4a8abf975e252a6f3bea108a2eabfd9451304b63ae2205b1d18; mirror trinity-3-30:/scratch/jjyeung/n30_mirror/tree_rebuild28/fix12/s33n_n_go.tar, same sha256 (compared on both ends). Not installed, not submitted.

## Merge
- fix10 DIFF.patch sha256 94d941e6135336c7dfac1e3bc0cebe88dc937287837687a73e151618f0716166 and fix11 DIFF.patch sha256 32c31d3735885136fb3f9128083d7fea32905e303af972788099f00f676a3fb6 verified before use (copies here).
- Code hunks applied with `patch` to the 489f7f0f bytes, no fuzz, no conflict: b/cn.py (new) 90b3ca6c, b/sc.py 43d4cc26, b/pf.py 5760c7df (then 531567f2 with W4 below), b/pl.py ad29088a. The shared b/pl.py takes fix10's hunk at line 278 (scene publish s0=3.json, s1=a.json, s4=o.json) and fix11's at line 357 (offset 1: frames(cfg, request['frame_roots']) after pf.check in stage()); they touch different blocks, so both behaviours are kept as written. ad29088a equals fix11's own trial merge dd/pl_merge.py.
- k/j.json: decoded a70b7551 + fix11's decoded hunks = 65891ca5 (bash -n OK). support.cap cannot write a shell capsule (J.load JSON-parses the payload: JSONDecodeError: Expecting value: line 1 column 1 (char 0)), so the build uses fix11's tested capsule b718d5d9 after asserting its decoded payload equals 65891ca5 (fix11 capsule, decoded payload checked). No hash was edited by hand.
- Modes: all members 0644 as in 489f7f0f (fix10's test kit w31cen had 0664 on cn/sc/pl; the bytes are equal).
## Room census W4 (fix13, ORCH RULING 1716Z): fix13 DIFF.patch sha256 4768768fea08e39ac33516eb66d68a9f213cc4abdc076893718b3a0318236722 (copy: out_extra_fix13_room_census_DIFF.patch)
- Applied with `patch -p1` cleanly: b/cs.py a4a809d2 -> 0fba43e5, b/sv.py d19658c7 -> b4b4e20e (base 489f7f0f), b/pf.py 5760c7df (the merged pf) -> 531567f2 (adds census(cfg), the classify-100 preflight, called at the end of frames()). No k/ or config change: the protection table is the PROTECTION literal in b/sv.py, covered by the seal.
- Trinity on the merged kit: fix13's stub unit test ut2.py ALL PASS (out_extra_ut2.log: K1 pose -> exposure, namespace capture resolves, sibling of a dev-listed capture -> dev protected, unresolved token refuses, vqa/routing unchanged, receipt fields). fu33 frames tests stub pf.census (needs the real config) and pass.
- Held node (fix13 REPORT, not rerun by fix12): t4 (sv 3b6b0ea8) all four streams PASS and armed verify PASS; t6 on final sv b4b4e20e routing-only PASS (841 K1 exposure, record 1,222 B); t5 full publish on b4b4e20e due about 17:50Z: read fix13/REPORT.md for its result before GO.
### Review points for n_review1j (RULING 1716Z item 9)
1. Protection table as bytes: merged_b_sv.py, PROTECTION literal: benchmark, dev, R0, withheld, official protect every stream; K1_heldout protects vqa and pointing only; for pose and routing K1 rows go to detail.exposure ("exposure recorded, not protected"), never to protected. Check zero on every protecting list per stream (fix13 t4/t6 tables: all 0).
2. Namespace table uniqueness: sv.py tier 2 builds scannet/scene0000_00..0806_09 (8,070 tokens) and refuses R1_CENSUS_NAMESPACE_TOKEN_COLLISION on a shared token or a clash with tier 1; a row matching two scenes refuses R1_CENSUS_TOKEN_CONFLICT; no match refuses R1_CENSUS_ROOM_UNRESOLVED.
3. Room-level classification: list names in token form resolve to their capture and carry the physical-room key (d1/sceneNNNN), so every sibling capture is protected (ut2 "sibling" case).
4. Receipt wording (merged_b_cs.py): result.protection, result.resolved {authority_and_aliases, namespace, unresolved, by_function}, result.protected_by_resolution (namespace_token > 0 = BLOCKER), result.exposure.K1_heldout {status, rows, by_dataset, by_category, by_s1_source}.
5. Numbers to reconcile: fix13 t2 (lists only) had names 157,507 + unresolved 28,160; t4 (final tiers) has authority_and_aliases 157,027 + namespace 28,640 + unresolved 0 (both sum to 185,667). 480 rows moved from tier 1 to the namespace tier; fix13 should say why (likely the room-level token expansion), since ORCH item 1 counted 28,160.
6. pf.census() samples only the first 100 rows per source (pose among the mix's frame_prefix rows); a deep hit still surfaces only in cs.publish after the forward (fix13 risk 3).

## Unchanged pins (vs F1 kit 489f7f0f): {"k/c.json": true, "k/c0.json": true, "k/n.json": true, "k/p.json": true, "k/t_e047002134f979bd.tar": true, "k/y.json": true}
- tree tar k/t_e047002134f979bd.tar 5f2d77c4bc9905d877a259b666ac4a7fa6005de538730b806ceb249468699e38; k/c.json 76de3706b8eba5b8e0c6317f96a48d432f597358dfcda94bf1445589c6199bd7; k/n.json 4b8b9533eb12434186a9f42a06b44962574c3dedd51f9b8405d1f7e33d2504b9; k/p.json 77525f28cdbc24b8b1ce918460c91878708e200ebc05c7a17725a10787712694 (no frame-fix change needed: the map lives in k/j.json); k/y.json 9ce253964ef8d060ae99be248dab4d743035ef61fd49ee3a5b9642f543a434c2 (= 9e809db4's: True); BUILD config_sha256 = sha256(k/c.json): True.

## F1, n_review1j criteria (1523Z item 4)
- (i) receipt a7682dae differs from e3ee51da only in division.path and equals 8091154c's division pin byte for byte: fix8 build (f1_review/README.md, BUILD_F1.json); the receipt is unchanged here (k/c.json, k/n.json, k/p.json byte-identical to F1).
- (ii) streams.vqa and r1_training.store_parameter point to a7682dae; no other key of c/n/p.json changes: fix8 decoded diff (f1_DIFF_vs_9e809db4.txt); the merge changes none of the three files.
- (iii) tree tar unchanged 5f2d77c4: above.
- (iv) division_admits on the staged bytes True: fix8 held-node T2 (f1_review/held_node_T1_T5.out); Trinity rerun on the merged kit, out_tchk.log: vqa division sub-check passes for a7682dae.
- (v) preflight b/pf.py receipts(): body unchanged from F1 (the merged pf.py adds frames(), census() and docstring sentences only; pf_py_vs_9e809db4.diff). Rerun on the merged kit (out_tchk.log): old 9e809db4 config REFUSE R1_STREAM_RECEIPT_REFUSED:vqa(division); merged config PASS.

## Census, ORCH ANSWER 1604Z conditions (b)-(e) (RULING 1650Z A: GO on diff 94d941e6)
- (b) b/cn.py = the reviewed bytes 90b3ca6c; it recounts raw rows of the admitted population with the tree's Exclusions.expect/keep (fix10 REPORT, n_review1j 1648Z item 1b). Trinity T1 rerun on the merged kit (out_TEST_T1_33.json): T1 view equivalent True; T6 pool count = plain True.
- (c) tree unchanged, so coverage_report (s1_exclusions.py:319) runs as before with exact equality: T3 admitted census PASS {"pose": [800, 400, 800, 400]}; controls T4 whole-store REFUSE ValueError: Filter differs from independent scene census: pose; T5 planted listed row REFUSE ValueError: Filter differs from independent scene census: pose. Held node (fix10): all three call paths (:621, :657, :790) PASS with exact equality; four controls REFUSE.
- (d) whole = admitted + outside: T2 {"whole": [1200, 600], "admitted": [800, 400], "outside": [400, 200], "ok": true}; b/pl.py publishes sc/o.json as live/s4.json (merged pl.py hunk 1).
- (e) held-node run with real rows, prepare to its end: fix10 REPORT (16:26-16:37Z); n_review1j GO 1648Z on 94d941e6. The merged bytes of cn.py/sc.py equal the reviewed ones; the pl.py census hunk is unchanged.

## Frame fix tests (RULING 1650Z B: GO on diff 32c31d37)
- Static: merged decoded k/j.json = fix11's tested 65891ca5 (Q_NJ bind at /tmp/jjyeung/<ns>, five python steps on $Q_NJ, Q_E4 /data2 -> $Q_NJ/p/q/f/<sha256("$X/data2root")>); bash -n 0. fix11's job-bytes static check (o4: 0 resolve-output strings under the old q; plan request/config q-rooted) and held-node FrameAudit 301/301 per source + hash samples: fix11 REPORT; the bytes are identical here.
- Preflight unit tests on the merged kit (out_TEST_FRAMES_33.json, synthetic, tree resolve_read): all as expected = True: PASS when every source's pin lies under a root (pose/0 sample honours frame_prefix); R1_FRAME_ROOT_REFUSED for a frame outside the roots, a missing file under a root, and a symlink escaping a root; R1_FRAME_ROOT_MISSING (no roots, absent root); R1_FRAME_PREFLIGHT_DATABASE_MISSING; R1_FRAME_PIN_MISSING (no frame rows; no row with the prefix).
- Held node: fix11 t12 ran frames() of pf.py 5760c7df on the job's staged config (531567f2 keeps that body and only appends the census(cfg) call): fixed PASS, 174134 mapping REFUSE R1_FRAME_ROOT_REFUSED:pointing. fix12 did not rerun it (RULING 1650Z item 2: the walk has the node).

## Build checks (out_BUILD33.json)
- py_compile every b/*.py (32 files): all ok = True; bash -n every *.sh: {"b/e.sh": 0, "b/ep.sh": 0, "b/f.sh": 0, "b/pc.sh": 0, "b/q.sh": 0, "b/q1.sh": 0, "job.sh": 0}; no __pycache__ in the kit: True.
- Members added ['b/cn.py'], removed [].

## Files
DIFF_vs_9e809db4.txt (member list old/new sha256), f1_DIFF_vs_9e809db4.txt, merged_vs_489f7f0f.diff, pf_py_vs_9e809db4.diff, fix10_census_DIFF.patch, fix11_frame_DIFF.patch, merged_b_*.py, merged_k_j.json.decoded.sh, out_* (build, tests), script_* (b33.py build, tchk33.py, t1_33.py, fu33.py, overlay.json), INSTALL.md, SHA256SUMS.txt.
