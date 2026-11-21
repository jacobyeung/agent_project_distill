# n34 review packet: kit w34, seal 7e23bbddb052a6f3ddb1915858dc03e8951d35d87cc9a3cd276f8853414d5771 (fix17, 2026-11-21 ~21:20Z)

The kit is 929ab213 plus fix16's DIFF 6dd5ffccc6f10c21c053ce5ca98db386dec19e4dabf61c709c34c312609b4af9, the fix for 174198's refusal R1_ROUTING_SELECTION_DIFFERS. It is sealed, mirrored and not installed.

- Kit: trinity-1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w/w34/n_go. Tar W/w34/s34_n_go.tar is 5,959,680 B with sha256 163cf1974bc753ed1ebf57ae23d2035729f17ed8a8ad777814722782cdb18dc4.
- Mirror: trinity-3-30:/scratch/jjyeung/n30_mirror/tree_rebuild28/fix17/s34_n_go.tar has the same sha256 on both ends, and `sha256sum -c` of the extracted kit is all OK.
- Rule of the fix: the plan and the proof run under the namespace /tmp/q_22c714e1 (Q_NS), as in every job that passed. The second bind name /tmp/jjyeung/q_22c714e1 (Q_NJ) serves only two things: the /data2 frame map target and the roots that a.py hands to the frame audit (b/pf.py audit_roots, checked by device and inode).

## Criteria and evidence
1. **Built with the kit's tools.** I made a fresh copy of W/w33n/n_go (seal 929ab213 checked) and checked the DIFF's sha256. The patch applied with `patch -p1 -F0`, clean, with no offset or fuzz. The k/j.json capsule was rebuilt by a writer that first reproduces 929ab213's k/j.json byte for byte from its decoded payload; its hash is computed, not edited. support.cap cannot write this "base64" shell capsule. I resealed with support.reseal. launch_r1.build.verify(kit) = J.seal = 7e23bbdd, and SHA256SUMS.txt is byte-equal to fix16's expected file. Evidence: out_build.log, out_BUILD34.json, out_verify.log, script_b34.py.
2. **Changed members.** Five members changed and none were added or removed (all 0644):
   - k/j.json: b718d5d9 -> 2ca9c9bd; the decoded shell went from 65891ca5 to 9f7a02bb.
   - b/a.py: 891d105f -> c5bdb533.
   - b/pf.py: 531567f2 -> ceef90f0.
   - BUILD.json: b26fa29b -> 3cdcf534; only kit_sha256 changed.
   - SHA256SUMS.txt: 929ab213 -> 7e23bbdd.

   The following are unchanged: tree tar 5f2d77c4, k/c.json 76de3706, k/n.json 4b8b9533, k/p.json 77525f28, k/y.json 9ce25396, and k/h.json e693876e (routing_selection pin u/a49f117f). Full diff: DIFF_vs_929ab213.txt. Patch: fix16_DIFF.patch.
3. **Earlier fixes intact (trinity-1-18 tests on the final kit).**
   - py_compile passed 32/32, `bash -n` passed on every kit *.sh and on the decoded shell, and the kit has no __pycache__.
   - F1 receipts preflight: the old 9e809db4 kit refuses with R1_STREAM_RECEIPT_REFUSED:vqa(division), and w34 passes (out_tchk.log).
   - Census T1-T6 are identical to fix10 (out_TEST_T1_33.json).
   - fix13's ut2 reports ALL PASS (out_ut2.log); the classify-100 census is stubbed in the frames tests, as in n33.
   - frames(), mode A: fix12's nine cases, with audit_roots stubbed, are 9/9 (out_TEST_FRAMES_A.json).
4. **The new audit_roots, under real double binds (mode B in bwrap, out_TEST_FRAMES_B.json): 19/19 as expected.**
   - Pins in the second-name spelling pass the nine cases.
   - The control, with pins in the namespace spelling, refuses with R1_FRAME_ROOT_REFUSED:pointing.
   - audit_roots refuses by name each of these: the namespace itself, a missing folder, a root already under Q_NJ, a path with "..", a root outside the namespace, a file, a symlinked folder, and a twin with another inode.
5. **Static check (out_static.log).**
   - The steps a (line 421), d (429), h (432), rv (436) and t (441) take only $Q_NS paths. In 929ab213 all five took $Q_NJ.
   - $Q_NJ appears only in its definition (376), the map target Q_E4 (377) and the sandbox bind (410). No other kit shell names Q_NJ.
   - Among the b/*.py files, only pf.py and a.py name the second spelling.
   - production_proof imports admit inside _run (line 136) and passes the roots positionally (line 142), so the a.py wrapper reaches it.
6. **ORDER 1857Z item 4: a run from the start of the proof.** fix16's walk w1 ran on the held node with the candidate shell lines, b/a.py and b/pf.py (fix16_section4b_walk_step_list.md). Its RESULT line is in fix16_status_2115Z.md. In path order, these steps passed:
   - plan;
   - begin_host;
   - stage_host with the preflight frames() through audit_roots;
   - check_host_scene;
   - the host selection, with digest 522a3be3 and rows.sqlite 5e35c3ce. The receipt file is 38c52f00, the reviewed pin;
   - direction_twins;
   - training_components;
   - the witness;
   - admit through the wrapper, including the model and processor builds. The prepared routing rows.sqlite is 5e35c3ce = N_DB;
   - prepare :540 and :621, with the receipt written at 21:08:59Z;
   - the frame audit started at 21:13:01Z. By 21:14:34Z it had kept 20,772 frame entries under the second name, none under the first, with no refusal and no traceback.

   The steps after the audit (bind_prepared, the handover, the forward, the receipts, the room census and the gate copy) were not walked under this candidate. ANSWER 1924Z item 4 accepts that risk, because they passed in the first walk under the same root.
7. **ANSWER 1924Z item 2: identity table (fix16_section2_identity_table.md).**
   - These identities carry no second name: the routing selection, the prepared routing stream, twins, witness, the preparation receipts, the binding, the handover, the loader audit, RESULT/host.json, and the cs.py, sv.py and rv.py receipts.
   - Four records carry it: the admission request.json, the phase markers, frames.json and frame_inventory.sqlite. They are compared only when an admission or frames phase is resumed, second name against second name, and the proof starts on an empty root.
   - No record that carries the second name is compared with a value written under the first, with an external pin, or with an artifact of P.
   - fix17's own static read of s1_admission (request.json at 173-181, the resume check at 177-178, and FrameAudit roots at line 87) agrees with this table.
8. **Open points for n_review1k.** Both are unchanged by this kit:
   - fix16 notes that gate.py:199 requires live/s2.json, and no step of the kit writes it (sv.publish is never called). This holds in 929ab213 and in 489f7f0f too.
   - bind_prepared's row-refusal texts could quote a resolved frame path under the second name (r1_population.py:186-196). They are compared with nothing external.

## Files
INSTALL.md (upload list and post-install seal check); DIFF_vs_929ab213.txt; fix16_DIFF.patch; new_b_a.py, new_b_pf.py, new_k_j.json, new_k_j.json.decoded.sh; kit_SHA256SUMS.txt; out_* (test outputs of the final build); script_* (build and test scripts); fix16_section2_identity_table.md, fix16_section4b_walk_step_list.md, fix16_status_2115Z.md (copied from work/fix16/REPORT.md at 21:16Z); SHA256SUMS.txt (this folder).
