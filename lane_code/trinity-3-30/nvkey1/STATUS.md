# nvkey1 STATUS (lane on trinity-3-30; API jobs and staging on trinity-2-28 /scratch/jjyeung/orch_n30/nvkey1)
Updated: 2026-11-20T03:08Z. Lane start 02:51Z; timeout 6 h (about 08:51Z); successor nvkey2 must start by 08:20Z.
Brief: B/briefs/nvkey1.md (B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; D = /data2/jjyeung/agent_project_data/distill_design).
Done: plan event B/events/nvkey/20261120T0303Z_RESULT_nvkey1_plan.md; note to main /data2/.../distillation_orchestrator_20260918/INBOX_TO_NONTRAINING_ORCHESTRATOR_20261120T030355Z_distill_nvkey1_small_nv_pilots_8_per_min.md; ALLOC.md REQUEST line 03:03Z (8 req/min, start 4/min about 03:25Z).
NV facts: keys = env NV_INFERENCE_API_KEY{,2,3,4} (or the export lines in ~/.bashrc); endpoint https://inference-api.nvidia.com, header dataClassification: sensitive; catalogue on 2-28 work/cat_v1_models.json (264 ids), costs work/costs_cat_model_info.json.
Shared ceiling 70 req/min from Trinity (/data3/jjyeung/orch_n13_20261026/nv_slots/ALLOC.md); main's argon_static_nv2_1119 (meter in its out/HEARTBEAT.log 'gov:' lines) sends 42-50/min.
Data on 2-28: K1 frames /scratch/jjyeung/k1_frames (18,944 PNG by sha, 64 per capture); dev-S1 frames /scratch/jjyeung/devs1_frames (3,264), anchors devs1_r2/anchors/g3s32 (97) g3s64 (55); pointing store fb_pack/point/out/rows_pointing_locate.sqlite (25,020 rows; 1,208 have frames on 2-28, 19 clips).
Spend so far: $0 (free catalogue calls only). Ledger: D/NV_SPEND_LEDGER.jsonl.
Next: build client (work/nvcall.py) on 3-30, copy to 2-28; stage C1 truth from 1-18; bake-off; C1/C2/C3 pilots.
