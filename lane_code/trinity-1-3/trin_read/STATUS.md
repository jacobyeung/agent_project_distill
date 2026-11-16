# trin_read STATUS (trinity-1-3) - for a successor
Updated: 2026-11-16T11:03Z by trin_read3 (session 3, started 09:41Z). Read "trin_read3 state" first, then "Successor: resume here".

## Done
- Plan RESULT 0203Z; QUESTION 0204Z (no free card on 1-3; asks for trinity-0-13 cards 1-6; default: no 0-13 action before answer).
- Export m544 extracted over IB from trinity-1-18 (02:05:49-02:06:56Z): root/fsw/ap/8865619b/runs/469ddece/m544; stream sha 3ed73aea... = accepted; artifact.json 1d6eeb28... OK.
- camera.tar 9eb53a96 OK, bwrap e3189038 OK in dl/ (unregistered small files).
- kit copy: kit_src/ (= evalx27 kit, package.tar f42aa1a4).

## In flight: governor streams (priority 50, tier 3, tmux trs_*; logs dl/*.log; launcher work/launch_pull.py)
- trin_read_rt1 -> dl/runtime_1.tar (8,466,728,960 B, sha 56c7705a) vLLM 0.32.0 env
- trin_read_rt0 -> dl/runtime_0.tar (1,621,422,080 B, sha 07006213)
- trin_read_rt2 -> dl/runtime_2.tar (409,282,560 B, sha 4b11b4df)
- trin_read_fr20 -> dl/frames20.tar (576 PNGs of the 20 proof items, NEED20.txt; via kit proof/pull.py on Orchard login)
- trin_read_base -> dl/base.tar (19,329,320,960 B; per-file check vs base_manifest ae9247f7)
- On completion each launcher renames its record .done.<epoch> and writes <out>.RECEIPT.json. Failure: no retry; BLOCKER.

- trin_read_frrest -> dl/frames_rest.tar (4,288 frames = evalx27 need_frames 4,864 minus NEED20; all dev-S1 direct main/away/forward, to be confirmed by `need --all`).
- ORCH 0205Z: 0-13 allowed with conditions (>=195 GB free there, sandbox /dev/shm bound to a /scratch folder, one card of 1-6 after two empty readings + process list, card number in a RESULT line before the run, yield on *_ORCH_* yield, 1-3 keeps first copy).

- 03:03Z per ORCH 0253Z: rt1/rt0/rt2/fr20 withdrawn (records .withdrawn.1794798...; .part and logs renamed .withdrawn.<epoch>) and re-registered at priority 35 (PRIO=35 in streams.sh / run_fr.sh). base and frrest stay at 50. Queue: mind part_02 15.8 GB until ~04:00Z, then main's bank chains.
- No base safetensors / vLLM 0.32.0 env found on 1-3 or 1-18 (/scratch/jjyeung/hf/hub, /scratch/jjyeung/models absent).

- rt1 DONE 04:15:55Z (sha 56c7705a OK), staged 04:17Z (stage2.json). Env: vLLM 0.32.0, torch 2.13.0+cu130, transformers 5.19.0, triton 3.7.1.
- Queue 04:20Z: mind rev_complete part_01 (11.1 GB, prio 1) runs before rt0/rt2/fr20 (35), then base/frrest (50).
- glibc: llguidance _lib needs 2.30 (host 2.28) -> stub overlay (work/llg_stub) bound in bwrap; CPU probe OK 04:26Z. QUESTIONs 0423Z + 0426Z (revised default: stub). Ubuntu-base download withdrawn (trin_read_ubase.withdrawn.*; 0-byte .part renamed).

## Build
- Codex trin_read_kit DONE 02:30Z: build/trinity_read.py (stage|frames|need|proof|read), namespace_worker.py, compare_tokens.py, DIFF.md (BEYOND list), README.md, REPORT.md, 33 tests pass. Receipt dir agent/scratch/codex_runs/20261116T021729Z_trin_read_kit.
- Codex trin_read_kit2 running (tmux trr_codex2): --shm bind, --yield-glob, selfcheck, portability. Brief work/CODEX_BRIEF_addendum.md.
- Codex trin_read_kit2 DONE 03:00Z: --shm, --yield-glob, selfcheck; 56 tests. OPEN: staged Orchard bwrap needs GLIBC 2.33+ (host 2.28).
- Codex trin_read_kit3 running (tmux trr_codex3): --bwrap /usr/bin/bwrap (0.4.0, tested OK by operator), selfcheck pinned-evidence classes. Brief work/CODEX_BRIEF_bwrap.md.
- Codex trin_read_kit3 DONE: --bwrap (default /usr/bin/bwrap), selfcheck classes; 76 tests.
- Codex trin_read_kit4 running (tmux trr_codex4): --llguidance-stub, `probe` subcommand. Brief work/CODEX_BRIEF_llg.md.
- Partial stage 02:41Z: bootstrap (payload cc33bc29), a0, bwrap, export verified. Rerun `stage` as tars land (README).

## Next
- stage all; frames --tar dl/frames20.tar; need --first 20 (=NEED20) and need --all; card (1-3 or 0-13); proof; RESULT proof; read --first 20 proof; RESULT launcher.
- Rejected: 1-18 envs/vllm (vLLM 0.23.0 vs accepted 0.32.0); 1-13 base (no safetensors).

## ORCH rulings to honour (events 0424Z, 0427Z)
- Stub accepted (0427Z; userland option withdrawn). Conditions: stub bound only inside bwrap; receipt records stub sha + every import it satisfies; stub raises on any call and a test shows a structured-output request fails loudly; proof records stub call counter = 0 after the 20 items; gate = 20-item proof PLUS a run-to-run repeat on the same card; one reader reviews launcher+stub+proof together, ordered on the proof RESULT (no review before).
- SANDBOX receipt in every packet: bwrap, binds, stub sha, host/namespace glibc, driver version and host driver libs.
- Codex trin_read_kit5 (tmux trr_codex5; brief work/CODEX_BRIEF_llg2.md) implements: stub v2 with call log (LLG_STUB_LOG), SANDBOX.json, guidance-failure probe, proof --repeat 2 + RUN_TO_RUN.json.

## Task 5 (plan only; copy nothing until ORCH says the GPU read is needed; lane native_r3 checks first whether the parent's per-item answers survive on 1-18)
- Goal: direct reads of the parent CP1 m200 and of f17 on the 636 dev-S1 keys of the native read (events/native_r2/20261116T0405Z_RESULT_native_read.md; keys in native_read_outputs.tar.gz, sha bba35cde..., on trinity-1-13 per that event), same frames and B2048 budget as the step-544 direct read; paired over 58 rooms.
- Parent CP1 m200 (models slot cp1m200, artifact logical path /scratch/fsw/.../ap/f2ad01ad/runs/49becb79/m200/artifact.json, sha c1a42588...; from vendor r4/MODELS.reference.json): GCS gs://cmu-gpucloud-jjyeung/q9/f2ad01ad/m200.tar.part00..10-of-11 (10 x 2,147,483,648 + 108,185,600 = 21,583,022,080 B; 2026-11-09). Whole-archive sha not yet known (find a receipt before pulling).
- f17 (slot f17, kind archive, logical /lustre/.../ap/bdad3598/k/f17.tar, sha 47308d99...): Orchard /project/community/jjyeung/cp4tk_f17/f17.tar, 20,189,655,040 B (sha not checked). Not in GCS by name.
- Fit with the runner: the 636 keys are distance/room/camera items. trinity_read.py reads only main/away/forward via legs1 direct.py, whose model_specs accepts only the cp1m200 slot and whose read restricts exports to the 469ddece lineage. Parent m200 = c1_export -> needs only a lineage-path generalization; f17 = archive kind -> different loader path; camera items need camera/direct.py (camera package a0). Map each of the 636 keys to its family first (need --ids), then scope the Codex change; that is beyond paths -> review.
- Pulls when ordered: parent 21.6 GB GCS (gcloud storage cat via ossh, governor), f17 20.2 GB Orchard (ossh cat, governor). Both < 200 GB.

## Successor: resume here (state 05:25Z)
- Streams still waiting (tmux trs_rt0, trs_rt2, trs_fr20 at prio 35; trs_base, trs_frrest at 50). Ahead of them 05:21Z: k1_ops4 2.6 GB (running), mind rev_complete part_02 (prio 1). Each launcher verifies size/sha, writes <out>.RECEIPT.json, renames its governor record .done.<epoch>; on failure it stops (no retry): write a BLOCKER. Logs dl/*.log.
- Codex runs all finished (kit, kit2-kit5); latest build REPORT_LLG2.md (134 tests). Build mirror: work/mirror_build_v1.tar sha 4ec18624... also at trinity-1-13:/scratch/jjyeung/n30_mirror/trin_read/mirror_build_v1.tar (sha equal). Re-mirror after any build change.
- Steps, all from /scratch/jjyeung/orch_n30/trin_read/build with /usr/bin/python3 -B trinity_read.py (README.md has exact commands):
  1. `stage --root ../root --dl ../dl` after each tar lands (runtime_1 already staged).
  2. `frames --root ../root --tar ../dl/frames20.tar` (later also frames_rest.tar).
  3. `probe --root ../root` (CPU): expect imports OK, guidance backend raises the stub RuntimeError and logs one call, cryptography not loaded.
  4. `need --root ../root --family main --first 20 --out ...` must equal work/NEED20.txt (576); `need --all` should be covered by work/NEED_X27.txt (4,864 = NEED20 + NEED_REST).
  5. Card: trinity-1-3 cards all held by yimingg2 (42-45 GB each, 3+ days) at every check 01:58-05:20Z. Else trinity-0-13 cards 1-6 under ORCH 0205Z conditions (>=195 GB free there; copy root over IB to /scratch/jjyeung/n30_trin_read/root at the same absolute path? NOTE: the runner expects the root path; selfcheck after copy; --shm under /scratch/jjyeung/n30_trin_read; card number in a RESULT line before the run; yield on *_ORCH_* yield file via --yield-glob). Each read copies base+export into the packet (~36 GiB).
  6. `proof --root ../root --gpu N --token pXXXX --repeat 2` under vnice; then RESULT proof (token equality share, first divergence, scores per arm, run-to-run, tok/s, s/item, peak memory, stub call count 0, SANDBOX.json). ORCH then orders one review of launcher+stub+proof.
  7. `read --first 20` short proof for the launcher; RESULT launcher with DIFF.md BEYOND list (card check, Slurm token, item filter, frame store, piecewise stage, host bwrap 0.4.0, llguidance stub, sampler, comparisons).
- Then Task 5 planning (above).

## trin_read3 state (11:03Z) - read this first
- Base LANDED 10:47Z (dl/base.tar sha 20a2ab6c..., record trin_read_base0.done.1794826039), staged 10:48Z; STAGING.json complete. RESULT 1059Z base_staged.
- need main --first 20 == NEED20 (576; build/NEED20_t3.txt); need --all 4,544 frames (build/NEED_ALL_t3.txt) inside NEED_X27.
- pyc drift: 5,061 __pycache__ files in root/m/ap/19252904/e rewritten 04:20-04:25Z; restored from dl/runtime_1.tar (work/pycfix/restore.py, RESTORE.json, drifted.tar evidence); 1-18 got the same restored files (IB, 10:58Z). Selfcheck on both nodes: 0 piece errors; one host-side portability false positive (p1cpu link via /scratch/jjyeung, bound to root/sj in the sandbox). Rerun selfcheck after every GPU run to catch drift.
- Root+build_t6 on 1-18 (send4.log 10:51Z). Relay trr_yield runs on 1-18 and 1-3. Proof launcher: `bash work/run_proof.sh GPU TOKEN` on the card's host (tmux trr_proof, log work/proof_TOKEN.log) after the card-line RESULT.
- build_t6 DONE (260 tests, REPORT_T6.md). --link-models only after the review (ORCH 1003Z).
- ORCH 1003Z: no cap, floor 300 GB free on 1-3 (check before >10 GB writes); NO removal by anyone of ours (list in REMOVAL_CANDIDATES.md); priority 0 only for base; use 40 for milestone pulls (my default).
- frrest stream (prio 50) position 1 at 11:02Z.
- Next: card -> RESULT card line -> proof; m100 .done (Orchard /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m100.done, ~13:00Z) -> launch_gcs.py at prio 40 -> build_t6 stage-export; 544 baseline after proof: build_t5/6 read --families main,away,forward then `items --a A544`.

## Successor: resume here (state 05:25Z)
- Streams still waiting (tmux trs_rt0, trs_rt2, trs_fr20 at prio 35; trs_base, trs_frrest at 50). Ahead of them 05:21Z: k1_ops4 2.6 GB (running), mind rev_complete part_02 (prio 1). Each launcher verifies size/sha, writes <out>.RECEIPT.json, renames its governor record .done.<epoch>; on failure it stops (no retry): write a BLOCKER. Logs dl/*.log.
- Codex runs all finished (kit, kit2-kit5); latest build REPORT_LLG2.md (134 tests). Build mirror: work/mirror_build_v1.tar sha 4ec18624... also at trinity-1-13:/scratch/jjyeung/n30_mirror/trin_read/mirror_build_v1.tar (sha equal). Re-mirror after any build change.
- Steps, all from /scratch/jjyeung/orch_n30/trin_read/build with /usr/bin/python3 -B trinity_read.py (README.md has exact commands):
  1. `stage --root ../root --dl ../dl` after each tar lands (runtime_1 already staged).
  2. `frames --root ../root --tar ../dl/frames20.tar` (later also frames_rest.tar).
  3. `probe --root ../root` (CPU): expect imports OK, guidance backend raises the stub RuntimeError and logs one call, cryptography not loaded.
  4. `need --root ../root --family main --first 20 --out ...` must equal work/NEED20.txt (576); `need --all` should be covered by work/NEED_X27.txt (4,864 = NEED20 + NEED_REST).
  5. Card: trinity-1-3 cards all held by yimingg2 (42-45 GB each, 3+ days) at every check 01:58-05:20Z. Else trinity-0-13 cards 1-6 under ORCH 0205Z conditions (>=195 GB free there; copy root over IB to /scratch/jjyeung/n30_trin_read/root at the same absolute path? NOTE: the runner expects the root path; selfcheck after copy; --shm under /scratch/jjyeung/n30_trin_read; card number in a RESULT line before the run; yield on *_ORCH_* yield file via --yield-glob). Each read copies base+export into the packet (~36 GiB).
  6. `proof --root ../root --gpu N --token pXXXX --repeat 2` under vnice; then RESULT proof (token equality share, first divergence, scores per arm, run-to-run, tok/s, s/item, peak memory, stub call count 0, SANDBOX.json). ORCH then orders one review of launcher+stub+proof.
  7. `read --first 20` short proof for the launcher; RESULT launcher with DIFF.md BEYOND list (card check, Slurm token, item filter, frame store, piecewise stage, host bwrap 0.4.0, llguidance stub, sampler, comparisons).
- Then Task 5 planning (above).

## trin_read3 state (10:04Z) - read this first
- Base: withdrawn from prio 40 (09:44Z, record .withdrawn.1794822273), re-registered prio 0 as trin_read_base; governor classed it exited (stale watch on reused name), so withdrawn again (.withdrawn.1794822571) and registered as **trin_read_base0** (prio 0, 09:52Z, tmux trs_base, log dl/base.log, out dl/base.tar). Position 1 at 10:02Z behind native_r4_upw. On landing: its launcher renames record trin_read_base0.done.<epoch>.
- Card poller restarted 09:45Z (tmux trr_cardpoll; old CARD_FOUND renamed .seen.1794822345). 09:46Z: 1-3 all 8 yimingg2; 1-18 all 8 in use (lnayak, aayushm).
- Codex trin_read_t6 running 10:00Z (tmux trr_codex8, brief work/CODEX_BRIEF_t6.md, log work/codex_t6.log, receipts agent/scratch/codex_runs/20261116T100043Z_trin_read_t6): build_t6 = build_t5 + plain-text .done (real format `<object> <bytes> <sha>`; build_t5 stage-export JSON-loads it and would refuse), `items` subcommand -> ITEMS.jsonl via cont_ops readk/kit/reader/records.py + f1f2.index/align vs A544.jsonl, --link-models (default off), launch_gcs.py governed GCS pull.
- QUESTION 1002Z disk_cap: 70 GB cap vs ~146 GB per milestone read; default: grow for proof + 544 baseline (free >= 300 GB on 1-3), remove nothing, --link-models only on ORCH yes.
- Packets for cont_ops: f1f2.py (/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/f1f2.py) takes `--a evidence/A544.jsonl --b ITEMS.jsonl`; A544 = main 1525/away 150/forward 150. D0 .done on Orchard: /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m<step>.done; objects gs://cmu-gpucloud-jjyeung/q8/8865619b/359fcc3c_m<step>.tar.partNN-of-04.

## Successor: resume here (state 09:37Z, steps unchanged)
- Landed+staged on 1-3: runtime_0 (09:23:18Z, sha 07006213 = pin), runtime_1, runtime_2 (06:16:39Z, sha 4b11b4df), bootstrap, reader_payload, a0 camera, bwrap, export m544. frames20.tar (157,040,640 B, sha 4a7cf2b4) ingested 09:34Z (576 frames). STAGING.json missing only base. CPU probe 09:27Z PASSED (root/runs/probe_20261116T092741*/PROBE.json: vLLM 0.32.0 / torch 2.13.0+cu130 / transformers 5.19.0 import inside bwrap; structured-output request raises the stub RuntimeError and logs 1 call; cryptography not imported).
- Waiting in governor: trin_read_base (prio 40, 19.3 GB, registered 08:39:55Z with launch_pull2.py; position 6 at 09:27Z), trin_read_frrest (50). `need` refuses until base is staged.
- When base lands: (1) `stage` (README), check STAGING.json complete; report base path dl/base.tar + sha in the next RESULT (ORCH 0633Z: lane native_r4 reads it from our root). (2) `need --family main --first 20` must equal work/NEED20.txt. (3) ship root to 1-18: `bash work/n118/send.sh root` (one IB tar pipe, ~80 s), then on 1-18 run `selfcheck`. (4) start relay on 1-18 (tmux trr_yield: bash work/n118/relay.sh). (5) restart card poller (tmux trr_cardpoll, work/cardpoll/poll.py; delete nothing; it writes CARD_FOUND.json; rename the old CARD_FOUND.json first, e.g. .seen.<epoch>). (6) RESULT line with host+card, then `proof --root R --gpu N --token pXXXXXXXX --repeat 2 --yield-glob '/scratch/jjyeung/orch_n30/trin_read/root/yield/*'` under vnice (runner does vnice) on 1-18 or 1-3. (7) RESULT proof incl. `cost --proof` minutes per milestone (use build_t5 trinity_read.py cost) and cards wanted; ORCH orders one review (launcher+stub+proof). (8) If the card is still held: step-544 baseline read with build_t5 `read --all-families` (2,275 items), ORCH 0800Z. Do not hold an idle card.
- Root on 1-18 = copy of 1-3 root at 09:35Z (send3.log, RECV_OK) except base. build_t5 mirrored to 1-18 (tree digest 1d6b510f equal both nodes, 09:01Z).
- Card history: 1-18 card 0 empty at 08:51 and 08:56Z (poller), not taken (inputs missing). 1-3 all yimingg2.

## trin_read2 state (06:32Z) - read this first
- ORCH 0548Z: proof on trinity-1-18 card 4 approved (IB copy of root+build+kit_src to the same absolute path; 1-3 keeps first copy; two fresh empty readings + process list; card line in a RESULT first; proof --repeat 2 under vnice; --shm under root; yield relay work/n118/relay.sh copies *_ORCH_*yield* from events/trin_read into root/yield/ on 1-18, pass --yield-glob '/scratch/jjyeung/orch_n30/trin_read/root/yield/*'). 1-18 load ~240; keep 200 GB free; write only under our root (k1_ops5 works there). Copy script work/n118/send.sh.
- ORCH 0602Z: parent/f17 636-key reads DROPPED; copy neither. Production use = D0 milestone exports (events/cont_ops/READS_PLAN_D0.md; run 359fcc3c, first ~2026-11-17T04:30Z). Proof RESULT must state minutes per milestone read on one card.
- Governor: rt0 refused 06:10Z (launcher exec changed comm after a pause). Fix work/launch_pull2.py (no exec). BLOCKER 0623Z; ORCH 0624Z OK. rt0 re-registered 06:28:32Z (prio 35); fr20 (35), base (50), frrest (50) withdrawn (.withdrawn.1794810072) and re-registered 06:22Z with launch_pull2.py (streams2.sh). rt2 DONE 06:16:39Z sha 4b11b4df OK. Refused part: dl/runtime_0.tar.part.refused.1794809877 (unused). If refused again: stop, BLOCKER.
- Codex t5 DONE (build_t5/, 161 tests, REPORT_T5.md: model slots, rebuilt camera wrapper, KEYS636, NEED636 within NEED_X27). Codex t5b running (tmux trr_codex7, brief work/CODEX_BRIEF_t5b.md): D0 lineage allowlist, stage-export from GCS tar + .done, read --all-families with MILESTONE_SUMMARY (toward/away apart), cost model. build/ stays fixed for the proof.
- ORCH 0633Z: base shared with lane native_r4 (reads it from our root); base re-registered at prio 30 at 06:36:30Z (old record .withdrawn.1794810987). Report base path+sha in next RESULT.
- ORCH 0658Z: rt0 and fr20 re-registered at prio 29 at 07:02Z (old records .withdrawn.1794812544); base stays 30, frrest 50. Ahead 07:02Z: carbon bank streams (~21 GB, prio 0-1).
- Codex t5b DONE (216 tests, build_t5/REPORT_T5B.md): stage-export (tar + .done), lineage allowlist 469ddece/359fcc3c, read --all-families (main 1,525, away 150, forward 150, camera 450 = 2,275) with MILESTONE_SUMMARY, cost --proof DIR -> COST.json.
- 07:14Z: root(29 GB)+build+kit_src+NEED lists+relay.sh copied to trinity-1-18 same path (work/n118/send1.log, RECV_OK). Ship deltas (new root pieces) later with work/n118/send.sh <paths>.
- ORCH 0729Z: D0 job 170111 started 07:25Z; step-100 export ~13:00Z, step-200 ~16:40Z. ORCH 0800Z: no free card anywhere (1-18 taken 07:52Z; 0-13 152 GB free -> nothing there, no low-disk kit change). D0 reads go to Orchard as primary; this reader is second path. After proof, if a card is held: read the step-544 export on the dev-S1 direct set (build_t5 read --all-families) as paired baseline. Do not hold idle cards.
- Card poller: tmux trr_cardpoll (work/cardpoll/poll.py): every 10 min reads 1-3 locally + 1-18 by one ssh; empty card rechecked 5 min later; writes work/cardpoll/CARD_FOUND.json and exits. Launches nothing.
- ORCH 0821Z: base re-registered at prio 40 at 08:40Z (old .withdrawn.1794818392); rt0/fr20 stay 29.
- Next: when rt0, fr20, base land: stage, frames, probe, need check on 1-3; send root to 1-18; readings; RESULT card line; proof --repeat 2; RESULT proof (+cost per milestone); RESULT launcher (build_t5 DIFF, review).
