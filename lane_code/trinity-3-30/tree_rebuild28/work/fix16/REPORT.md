PULLED+STOPPED 21:45:02Z. Pull: 21:33:39Z, 31 files into work/fix16/pull_gate/ (LIST.md; files from before the frame audit, final). Stop: walk w1 ended at 21:44:36Z on the coordinator's order (a.py exit 143); proof 21:44:47Z and 21:45:02Z: no process of mine names a15_f16 on orchard-community-3, no process carries the walk's mark, no srun client of mine for it on the login node, four GPUs at 0 MiB with no app (rd/stop.out). Nothing of mine runs on Orchard.
STATUS 21:45Z: DONE. Cause shown (1); identity table (2); candidate accepted in shape by ORCH ANSWER 1924Z (3); quick test (4a); from-start walk under the candidate, EARLY STEPS PASSED 21:14:34Z, frame audit ran 31.5 min without refusal until the ordered stop (4b, 4c); DIFF.patch sha256 6dd5ffcc..., unchanged since 19:23Z (5); gate-read receipts pulled (6).
QUESTION 20:24Z answered by the coordinator (20:25Z): the walk's self-stop is now 21:45:00Z. Done at 20:25:59Z: the walk's timeout process is stopped (state T) and a watchdog step (node/wd.sh, pid 3710953) runs node/stop.sh at 21:45:00Z; proof of the stop goes to w1/log/stop.log and into section 4c by 21:50Z.
EARLY STEPS PASSED 21:14:34Z. In path order under the candidate, from-start walk w1: host selection 20:00:30Z (digest 522a3be3, rows.sqlite 5e35c3ce), direction_twins 20:01:23Z, training_components (before 20:03:02Z), witness 20:03:02Z, model and processor builds inside admit (stream builds done 20:51:31Z, prepared routing rows.sqlite 5e35c3ce = N_DB), prepare :540 and :621 (receipt 21:08:59Z, phase complete 21:09:07Z), frame audit started 21:13:01Z and by 21:14:34Z its inventory holds 20,772 kept-frame path entries under /tmp/jjyeung/q_22c714e1/p/q/f/37e7..., none under the first name, no refusal, no traceback.

# fix16 REPORT: 174198 refusal R1_ROUTING_SELECTION_DIFFERS

## 1. Cause (shown on the held node, 19:04Z; raw output rd/o1.out, script s/o1.sh)
The run root moved from /tmp/q_22c714e1/p to /tmp/jjyeung/q_22c714e1/p, and the tree's selection digest covers
every path string under that root. Nothing else in the receipt moved.

- What entry.py:277-288 compares (job's own p/s/launch_r1/entry.py, sha256 74665f35): digest(regenerated) ==
  load(pinned(request['routing_selection']))['regenerated_sha256'], where regenerated =
  s1_routing.build(cfg, root/'selection', point['division'], model_pin(cfg)) and digest = sha256 of the sorted compact JSON.
- Expected side: reviewed selection u/a49f117f..., regenerated_sha256 522a3be39b90d6fd8ec4dd599d89e1d5762c3a1a150e198c0c0bbb70f931ba39,
  rows 43,101, logical_output "/tmp/q_22c714e1/p/q/selection", regenerated_receipt sha256 38c52f00....
  The expected object is on Orchard: X/o/174134/a0r.json has file sha256 38c52f00... and digest 522a3be3... (the job that passed).
- Regenerated side (174198): X/o/174198/a0r.json = p/q/selection/receipt.json, file sha256 0b60cae4..., digest
  76cff58cbf50e0ebdd4a8527711017d8575b838073ae013cd09667014523c83e.
- Field diff of the two receipts (1,271 leaves each): 116 leaves differ.
  - 104 are path strings whose only change is the prefix /tmp/q_22c714e1 -> /tmp/jjyeung/q_22c714e1
    (database.path, materialization.path, removals[*].file.path, source.path, division, exclusion files ...).
  - 12 are sha256 values of files whose bytes embed those paths: database.sha256 5e35c3ce -> b2f3db7c;
    materialization.sha256 6faab9cc -> 4f5c423b; source.sha256 (the refreshed pool selection, cfg['s1_routing']['selection'])
    74640a29 -> 6050a820; 9 x source_scene_exclusions.expected.pool/<set>.reference.sha256 (relocated pool receipt) 0dd39e28 -> d6ed8c14.
  - The other 1,155 leaves are equal: count 43,101, scenes 1,881, types, policy, tokens, removal counts, scene census numbers.
    So F1, the census binding and the room census did not move this receipt; no config value or implementation hash differs.
- Rows (p/q/selection/rows.sqlite of 174198, read immutable): 43,101 rows; row_id_digest bdd91b75... == reviewed (same rows, same
  order); row_bytes_sha256 df95db8f != reviewed 802414c8, and after replacing the prefix in the row text it is 802414c8... == reviewed.
  The prefix occurs 46,652 times in the rows, in s1_source.source.path and s1_source.frame_binding.authority.{map,plan,fps_authority}.path.
- source.sha256 is also spelling only (19:24Z, rd/p2.out): the pool selection of 174198 (p/q/sc/p/p/receipt.json, 6050a820, 267 prefix occurrences)
  rewritten in memory with the prefix replaced, and its one nested pin (sc/p/0.json) rewritten likewise, has sha256 74640a29f939..., the reviewed value.
  So the new kit's plan (F1, census, room census) writes the reviewed pool selection once the root is spelled /tmp/q_22c714e1.
- Kit change responsible: the frame-map fix (fix11, DIFF 32c31d37), k/j.json decoded line 419: a.py's root argument "$Q_NS/p" -> "$Q_NJ/p".
  pl.py plans every path under q = root/'q' (plan.json of 174198: 1,223,220 strings under /tmp/jjyeung/q_22c714e1, 0 under /tmp/q_22c714e1),
  stage_host localizes the rest with str(root/value), and file_pin records resolved paths. 174134 ran the old line and passed.

## 2. Every identity that embeds a path under the candidate, and what compares it (read from the code, 19:26-19:34Z)
First name = /tmp/q_22c714e1 (the run root, as in 174134). Second name = /tmp/jjyeung/q_22c714e1. Under the candidate only two inputs carry the second name: the frame root map Q_E4 and the roots a.py hands to the tree's admit(). The table follows them into every record.
| identity (file under p/q unless said) | embeds paths | second name inside | compared later: where, with what |
|---|---|---|---|
| routing selection: selection/receipt.json, rows.sqlite, materialization.json, pool/* | 104 strings in the receipt, 46,652 in the rows | no | entry.py:283, digest vs reviewed 522a3be3 (u/a49f117f, written under the first name) |
| prepared routing stream: p/prepare_*/routing/* (s1_admission.py:208) | same row bytes | no | gate.py:179 d_population: prepared routing database or e2.databases sha256 == N_DB 5e35c3ce; N_ROWS 43,101 |
| twins: twins/* and room_audit.json | pins | no | r1_direction_twins.py:91-93 (same process); r1_rooms.py:96-123 verify_audit recomputes from this cfg, pins stripped |
| witness and target: v.json, m.json, c.json | pins | no | inside the proof only |
| admission request: p/request.json (frame_roots, frame_root_map) | yes | YES | only a resumed admission compares it (s1_admission.py:177-179; PhaseJournal binding, first_batch_progress.py:33). The proof starts on an empty root (entry.py:122), so neither fires; both sides would be this proof's own |
| preparation receipts: p/prepare_*/config.json, prepared/receipt.json, s1_receipt.json, pointing/ and vqa/ receipts | pins | no (build_stream keeps logical frame paths, carrier_c1_data.py:631-664) | carrier_c1_run.prepared 669-800, same process; config identity vs the training cfg (entry.py:100) |
| frame audit record: p/frames_*/frames.json (roots, hash_sample.resolved), frame_inventory.sqlite (path) | yes | YES | verify_frames (s1_admission.py:105-118) only when the frames phase is reused: resolve_read(logical).resolve() vs the stored path, second name on both sides |
| p/data_receipt.json (pins frames.json) | pins under the first name; its digest covers frames.json | by digest only | only against an existing file on resume (s1_admission.py:286-290). The proof reads prepared['config'] alone (production_proof.py:153); the receipt never enters cfg, RESULT or the host receipt |
| binding: b/* (population, reader_filters.json, r2_sampling, row_plan_sha256) | pins | no | r1_loader.py:49 and entry.py:96, digest(cfg['r2_sampling']) recomputed from this cfg |
| handover: h/mapping.json, receipt.json, config.json | pins, digests | no | r1_handover.py:421-424 recomputed; compare_configs vs P's config: pins by sha256 (136-146), bare strings literally (185-186), independent of the second name |
| loader audit a/*, RESULT.json, host.json | pins | no | h.py:19: host receipt path == str((argv[1]/'q/host.json').resolve()); h.py:25,42 and entry.py:100-112: identity |
| cs.py: live c0-c4, c5.json (a.py:115) | row keys, store pins; c5 pinned under the caller's root | no | h.py:32 stores pin(c5.json) in hr.json; rv.py:267-270 recomputes it under rv.py's root (R1_CENSUS_RECEIPT_PIN_DIFFERS); gate.py:205,214 |
| sv.py | classifier only (rv.py:151, cs.py:116, pf.py:103); writes no receipt in this kit | no | none |
| rv.py: live v.json, identity.txt, WAITING_REVIEW.json, e0-e3, h0.json; p/rv.json, ph.json | config pins; e*.databases path from the prepared receipt | no | gate.py:145,146,292,295 (sha of the same bytes, identity); gate.py:179 (N_DB); rv.py:294 review identity |
| d.py rooms.json; plan-time live s0, s1, s4 and sc/* | pins | no | copied to e4; gate.py:317-318 sha |
Conclusions:
- No record that carries the second name is compared with a value written under the first, with an external pin, or with an artifact of P. The four records that carry it (request, phase markers, frames.json, inventory) are compared only on resume, second name against second name.
- Two external pins cover path-dependent bytes: the reviewed selection digest and the gate's N_DB. Both were written under the first name and hold only with the run root there. That is why the 929ab213 kit would also have failed the gate after a re-reviewed selection.
- Two checks tie the steps' spelling together: h.py:19 (a.py and h.py) and rv.py:267-270 (h.py and rv.py). The candidate runs all five steps under the first name.
- The map string must be byte-identical in every sandboxed step; tk_env exports it once before all of them.
- The older modules that record the map string (startup_receipt.py, provisional_data.py, storage.py) are not imported by carrier_c1_*, r1_*, s1_* or launch_r1.
Readers: two Opus subagents read the tree side (production_proof, entry, s1_admission, orchard_paths, first_batch_progress, carrier_c1_run 465-800, carrier_c1_data 513-678, r1_handover, r1_persisted, r1_training, r1_population 159-243, r1_loader, r1_direction_twins, r1_rooms) and the kit and gate side (rv, cs, sv, cn, h, d, t, e.sh, ep, o, sc, a, gate.py, USAGE.md). I re-read h.py:19, rv.py:262-270, cs.py:165-210, sv.py:145-178, gate.py:168-222, s1_admission.py:105-300.
Not read: admit_test.py behind the gate's ADMIT.json point (it reads v.json, which is spelled as in 174134), run_gate.sh, r1_population.produce, r2_contract, the body of first_batch_check. One loose end: bind_prepared stores row-refusal texts (r1_population.py:186-196); a text that quoted a resolved frame path would carry the second name into reader_filters.json. It is compared with nothing external, and the gate requires the routing refusals empty.
Outside the namespace question, for ORCH and n_review1k: gate.py:199 requires live/s2.json. Its only writer in kit 929ab213 is sv.publish (sv.py:145-178), and no file in b/ or the inner shell calls it (a.py:115 calls cs.publish; the same holds in kit 489f7f0f). The gate's census point would report "missing s2.json". I checked this by grep only; the candidate does not change it. Update 21:33Z: n_review1k's gate.py no longer lists s2.json in that point's need() call.

## 3. Candidate (files in cand/, DIFF.patch follows)
One rule: the plan and the proof run under the namespace Q_NS, as in every job that passed; the second bind name Q_NJ serves only the frame root map and the roots handed to the frame audit.
- k/j.json (decoded j.sh): the five python steps a.py, d.py, h.py, rv.py, t.py take $Q_NS paths again (lines 421, 429, 432, 436, 441). The Q_NJ bind (line 410) and the map target Q_E4 = $Q_NJ/p/q/f/<sha256 of the store root> (line 377) stay.
- b/pf.py: new audit_roots(roots). Each request root must lie under the kit namespace (k/p.json), be a real directory, and be the same directory (st_dev, st_ino) under /tmp/jjyeung/<namespace name>; it returns the second-name spelling. Refusals: R1_FRAME_ROOT_NAME_REFUSED:<root>, R1_FRAME_ROOT_MISSING:<root>. frames() tests against audit_roots(roots).
- b/a.py: restoring_admit passes audit_roots(roots) to the tree's admit().
- Why all five steps move back: h.py line 19 demands host receipt path == str((argv[1]/'q/host.json').resolve()), so the later steps must spell the root as a.py did.
- Why a.py cannot stay under Q_NJ with only the selection check respelled: the receipt pins the pool selection the plan writes (source.sha256 74640a29 reviewed, 6050a820 in 174198), and the reviewer's gate pins the prepared routing database (N_DB 5e35c3ce, gate.py d_population). Both carry the plan's root spelling in their bytes.
- Why the roots need the second name: begin_host confines request paths to job_tmp (under Q_NS); resolve_read accepts a "/data2" target only at $R1_MOUNT/data2root or under /tmp/jjyeung; FrameAudit compares resolved paths, and a bind is not a symlink, so the two names never meet by themselves.

## 4a. Quick held-node test (19:19:52Z, run t1, read-only on the refused run's staged bytes; node/tq.py, output rd/o2.out)
Sandbox: the job's own (L16.sh from fix15's L.sh), job folder read-only at its three names, tree = the job's p/s, no device.
- audit_roots on the two request roots spelled under Q_NS: PASS, returns the two Q_NJ spellings. Six refusals by name: the namespace itself, a missing folder, a root already under Q_NJ, a path with "..", a root outside the namespace, a file.
- begin_host's rule (entry.temporary_paths, job_tmp Q_NS/p/q): Q_NS roots PASS; Q_NJ roots REFUSE R1_HOST_PATH_OUTSIDE_JOB_TMP. So the request cannot name the Q_NJ spelling itself.
- Preflight frames(): candidate with Q_NS roots PASS (one pin per source, all five under root 37e7...). Control, installed kit with Q_NS roots: REFUSE R1_FRAME_ROOT_REFUSED:pointing:...
- Tree FrameAudit (s1_admission) on 200 rows with frames per stream source: with audit_roots naming keep 200/200 for pointing, pose/0, pose/1, routing, vqa, and finish() PASS (hash sample of 8 per source verified). Control, Q_NS roots as the request names them: keep 0/200 in every source ("Retained RGB is absent or outside its frame store"), finish() REFUSE.

## 4b. Walk w1: the kit's mode q from the start of a.py, candidate, run root /tmp/q_22c714e1/p (node /tmp/a15_f16_174198/w1, started 19:19:22Z)
Layout: node/L16.sh (the job's tk_env, tk_pythonpath c, tk_bwrap; the namespace at its three names is a scratch folder with the job folder's entries bound read-only, p fresh; scratch for every read-write bind; no device visible). The installed sealed kit X/n (929ab213) is the kit folder; node/ta.py runs the candidate b/a.py and b/pf.py against it (four test-only differences listed in its header: kit folder, pf module, one printed line at the selection check, stop before the forward opens a device). Hard stop 21:12Z.
Step list (path order; filled as steps land; raw polls rd/p*.out):
| step | result | time | evidence |
|---|---|---|---|
| plan (pl.py: refresh, census, scene rebuild 577 s, frame hashes) | PASS | 19:19:23-19:42:00Z | p/plan.json 568,417,853 bytes = the refused run's 578,203,613 minus 8 bytes x 1,223,220 path strings |
| begin_host (fresh job_tmp, confinement of cfg and request) | PASS | 19:43:22Z | p/q created |
| check_host_runtime, stage_host: staging plan checks, kit hook (payload, 1.1M frame copies, y), preflight frames() with audit_roots, census preflight | PASS | 19:43:22-19:57:31Z | p/q/n.json 33,808 bytes, 0 second-name strings, 134 first-name; s1_routing.selection sha256 74640a29... (the reviewed source) |
| check_host_scene | PASS | before 19:58:03Z | the selection build started |
| HOST SELECTION (entry.py:277-288 through the kit's guarded_selection) | PASS | 19:58:03-20:00:30Z | log line {"A15_SELECTION": "PASS", "root": "/tmp/q_22c714e1/p/q", "regenerated_sha256": "522a3be39b90d6fd8ec4dd599d89e1d5762c3a1a150e198c0c0bbb70f931ba39", "assertion": true}; selection/receipt.json file sha256 38c52f008d131a8554d3d18974f4d2de1e77bdf092c747132df477db8ff08398 = the reviewed regenerated_receipt pin; rows.sqlite sha256 5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df (849,543,168 bytes) = N_DB; materialization.json sha256 6faab9cc...; source 74640a29...; count 43,101; 0 second-name strings, 104 first-name (raw rd/p14.out) |
| direction_twins (augment, census, verify_audit, check_host_scene) | PASS | 20:00:30-20:01:23Z | twins/rows.sqlite, receipt.json, augmentation.json 20:00:46Z; twins/room_audit.json 20:01:23Z (0 second-name strings, 22 first-name) |
| persisted closure (r1_persisted.verify), training_components | PASS | before 20:03:02Z | the witness that follows was written |
| witness (p_opener_witness) and bind_target | PASS | 20:03:02-20:03:33Z | v.json 485 bytes, m.json 1,116 bytes, c.json 29,680 bytes (0 second-name strings, 137 first-name) |
| admit entered through the candidate's wrapper | started | 20:03:33Z | p/request.json: frame_roots = the two /tmp/jjyeung/q_22c714e1/p/q/f/... names, frame_root_map the same target; config pin under the first name |
| admit prepare phase: parent grounding, pointing stream, vqa stream | PASS | 20:03:34-20:49:03Z | parent_grounding.json 20:03:34Z; pointing/receipt.json 20:08:33Z; vqa/receipt.json 20:49:03Z (rows.sqlite 1,670,574,080 bytes) |
| admit prepare phase: routing build (the tree's s1_routing.build again, with its processor build) | PASS | 20:49:03-20:51:31Z | p/prepare_9bfb0f3b.../routing/rows.sqlite sha256 5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df = N_DB (the gate's d_population pin); routing/receipt.json 0 second-name strings, 104 first-name |
| admit prepare phase: bind_target | PASS | 20:52:02Z | handover.json 1,116 bytes |
| admit prepare phase: carrier_c1_run.prepare, pose mix | PASS | 20:52:02-21:03:30Z | log: source 0 selected 27,604, source 1 selected 202,320, 0 rows outside the division; prepared/pose_mix_order.json |
| prepare :540 (stream receipts, division) and the row loops | PASS | 21:03:30-21:05Z | prepare went on into line 621's apply, which follows the receipts loop |
| prepare :621 (s1_exclusions.apply and its census comparison), verify, receipt | PASS | 21:05:32-21:08:59Z | apply's files pointing_scene_indices.json 21:05:32Z, pose_scene_order.json 21:06:43Z, routing_scene_indices.json 21:06:53Z, vqa_scene_indices.json 21:07:06Z; prepared/receipt.json 151,380 bytes 21:08:59Z (0 second-name strings, 213 first-name); s1_receipt.json; config.json |
| admit prepare phase complete | PASS | 21:09:07Z | p/phase_prepare.complete.json -> prepare_9bfb0f3b.../result.json |
| carrier_c1_run.prepared (re-read of the prepared receipt) | PASS | 21:09:07-21:13:01Z | the frames phase started |
| FRAME AUDIT started, first frames kept (s1_admission frame_phase, FrameAudit.keep with the roots under the second name) | running, no refusal | 21:13:01Z- | p/frames_df2e222e.../frame_inventory.sqlite 5,771,264 bytes at 21:14:34Z and growing, with its journal; the pages written so far hold 20,772 kept-frame path entries under /tmp/jjyeung/q_22c714e1/p/q/f/37e7..., 0 under /tmp/q_22c714e1; first one .../k6tk/dd/dd9d2afe017044c9....png; tb.txt absent; q.err empty (raw rd/p35.out). The first walk's audit took 81 min, so it will not finish before the stop at 21:45Z |
| frame audit, later readings | running, no refusal | 21:21:59Z, 21:31:29Z | inventory 132,358,144 then 223,289,344 bytes; 386,961 kept-frame path entries under the second name in its first 96 MB, 0 under the first; no traceback (rd/p36.out, rd/p37.out) |
| frame audit at the ordered stop | stopped by me, no refusal | 21:13:01-21:44:36Z | 31.5 min; inventory 385,077,248 bytes; tb.txt absent; q.err holds one library notice only; a.py exit 143 (TERM) |

## 4c. Stop of the walk and proof (rd/stop.out; node log w1/log/stop.log)
- 20:25:59Z: the walk's own 21:12Z limit lifted on the coordinator's answer (its timeout process stopped), watchdog set for 21:45:00Z.
- 21:44:36Z: stop ordered by the coordinator (RELEASE planned for 21:47Z). node/stop.sh sent TERM to the one marked process (the walk's python, pid 3644989); go.sh logged "a.py exit 143" and ended; the timeout process was continued and ended.
- 21:44:47Z proof: marked processes left: none; go.sh alive: no; timeout alive: no; ps lines naming a15_f16: 0; GPUs 0 MiB on all four, no compute app.
- 21:45:00Z: the watchdog ran its own stop, found nothing and ended. 21:45:02Z: no process of mine names a15_f16 on the node; none carries A15_RUN=/tmp/a15_f16_174198/w1; no srun client of mine for it on the login node.
- I wrote no RELEASE, sent no scancel and no sbatch, and wrote nothing under /tmp/q_22c714e1_174198, X/n or X/o/174198. The walk never saw a device.
- Left on the node: /tmp/a15_f16_174198 (about 330 GB by df, the walk's staged copy), listed in REMOVAL_CANDIDATES.txt. I deleted nothing.

## 5. DIFF.patch (work/fix16/DIFF.patch, sha256 6dd5ffccc6f10c21c053ce5ca98db386dec19e4dabf61c709c34c312609b4af9, written 19:23Z, against W/w33n/n_go seal 929ab213)
- Base check: the local copy fix15/kit2/n_go passes sha256sum -c on all 55 members and sha256(SHA256SUMS.txt) = 929ab213...; the node's X/n/SHA256SUMS.txt has the same sha256 (walk log).
- Changed members (old -> new): k/j.json b718d5d9 -> 2ca9c9bd (decoded inner shell 65891ca5 -> 9f7a02bb); b/a.py 891d105f -> c5bdb533; b/pf.py 531567f2 -> ceef90f0. Nothing else. b/pl.py, the tree tar, k/c.json, k/n.json, k/p.json, k/h.json, k/c0.json are unchanged.
- The decoded candidate shell differs from the pre-frame-fix shell a70b7551 (kit 9e809db4, job 174134) in three places only: the map target Q_E4, the Q_NJ definition with its guard, and the second bind.
- Candidate files: cand/b/a.py, cand/b/pf.py, cand/j.sh (decoded), cand/k/j.json (capsule; the encoder reproduces the base capsule bytes), cand/SHA256SUMS.expected.txt (expected seal 7e23bbdd..., computed without the kit tools; the builder's reseal is authoritative, and BUILD.json kit_sha256 follows it).
- Not built, not sealed, not installed.
- Follow-on outside the kit: fix15's rehearsal passes $Q_NJ to accept.py and t2.py (rh/go.sh lines 105 and 115); under the candidate the kit's t.py takes $Q_NS, so the rehearsal must use $Q_NS there.

## 6. pull_gate (ORCH ANSWER 2125Z item 5; work/fix16/pull_gate/, pulled 21:33:39Z in one Orchard call, 201,016 bytes of base64)
- 31 files, 1,037,897 bytes, archive w1_receipts.tgz; each file's sha256 equals the node's (node_sums.txt). LIST.md names every file, the gate files present and the gate files missing with the step that would write them.
- Present for the gate: live/s1.json, live/s4.json (plan time) and p/q/p/request.json (the reviewer's spell.py reads it: 3 second-name strings, as intended).
- Missing because the step did not run: live v.json, identity.txt, WAITING_REVIEW.json, e0-e3 (rv.py), h0.json (h.py), c0-c4 (cs.publish at ADMIT), b/population.json, indices.json, reader_filters.json, binding.json, receipt.json (bind_prepared, after the frame audit), f.json (forward, not run by design), frames.json (written when the audit finishes), ADMIT.json.
- Also pulled: the selection, twins, witness, prepared and stream receipts, the planned and prepared configs, the phase marker and the walk logs.
