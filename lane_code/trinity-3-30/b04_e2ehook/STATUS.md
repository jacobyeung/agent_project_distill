# b04_e2ehook STATUS (lane on trinity-3-30, Claude Opus). Updated 2026-11-16T12:05Z.
Brief: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/b04_e2ehook.md -> queue brief briefs/qs/04_e2e_reader_hook.md.
Lane folder L=/scratch/jjyeung/orch_n30/b04_e2ehook (trinity-3-30). Python: /scratch/jjyeung/envs/p1cpu/bin/python -B. Tree (read-only, imported): /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449.
## Done
- L/e2e_reader/: callhook.py (CallHook module, detection = port of sealed Row._call, decode_loop), geometry.py (G3T+own gravity+scale -> geometry, NO guard; guard verdicts recorded only), servers.py (camera via tree respond(); ground/gap via v3.14 Session), grounding.py (stage-1 socket: propose + selector argmax with null; lift_plain without depth cut; MinAreaBoxProvider, no tuned constant), artifact.py (manifest e2e-artifact-v1, verify, audit hook refusing data files outside manifest), generate.py (one entry, lazy in-call towers, entry counter).
- Proof 1 (token parity vs job 170056): L/tests/replay_170056.py -> L/out/proofs/REPLAY_170056_{suffix,nosuffix}.json: 927/927 calls detected with equal text and position; forced ids equal on 462/462 comparable calls (450 camera + 12 ground/gap/room with full recorded queries); 465 ground/gap/room calls not compared (R1 kept only digests of their queries).
- Proof 2 (guard): out/proofs/GUARD_VERDICTS_DEVS1.json: on the job's own 84 dev-S1 geometry exports the sealed guard refuses 11, reviewed guard 1 (d3/41254810); new loader refuses none.
- Proof 3 (tiny e2e, CPU): L/tests/test_tiny_e2e.py 5 passed (every call type; 1 prefill; cache length = prompt+ids-1; cached logits == fresh forward; loader refuses outside file and changed file; head perturbation changes only its responses). Output out/proofs/TINY_E2E.json.
## Running
- Subagent SH (scale head): brief L/briefs/scale_head.md; outputs L/heads/scale/ (3-30), /scratch/jjyeung/orch_n30/b04_e2ehook_sh/ (1-18).
- Subagent SL (selector head): brief L/briefs/selector_head.md (+ message: null logit, argmax only, prepare_inputs); outputs L/heads/selector/, /scratch/jjyeung/orch_n30/b04_e2ehook_sl/ (1-18).
## Inputs copied (IB from trinity-1-13 native_r2/work)
- L/work/n13/obj: geometry_8c58df15...tar (sha ok; extracted geo/: dev-S1 raw G3T g3s32 97 / g3s64 55), base_small.tgz (tokenizer/config, extracted base/), m544_artifact.json, export_head.tar, model_8005668f.tar.
- L/work/n13/full_c8r/result.tar.gz (job 170056 return, sha 5c150baf... ok) extracted at L/work/n13/ret (R1.json, 84 geometry npz).
- L/work/code_c8r.tar (C8r kit) at L/work/c8r; L/work/e3 = e3_mirror_1010Z.tar.
## Next
real.py (Qwen3.5 carrier path: tree _prepare_decode prefill + own gravity, FrozenG3TTower in call, SAM3 tower + selector, scale head), real artifact manifest, dev-S1 response-level pricing on CPU, EAT-1 static check (lane b03), parity-read kit (GPU needs ORCH GO), out/E2E_READER_READY.md, mirror, RESULT event.
