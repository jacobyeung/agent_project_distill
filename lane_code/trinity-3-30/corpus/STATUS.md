# corpus STATUS (Devin Opus high, trinity-3-30; started 06:34Z 11-19)
Brief: B/briefs/corpus.md. Lane folder /scratch/jjyeung/orch_n30/corpus. Target /data2/jjyeung/agent_project_data/distill_trace_corpus/ (not created yet).
## Done
- Read map from cont_ops18: inbox/READ_MAP_cont_ops.md (11 direct kit reads, 4 routed + D@544 running).
- Inventories: work/local_jsonl.txt, work/local_markers.txt (trinity-3-30), work/inv118.out (trinity-1-18), work/orch_ls1-5.out (Orchard okh7).
- Ingest plan: work/INGEST_PLAN.json + work/meta/<read_id>.json (14 local reads).
## Running
- Codex Astra build of tool: tmux corpus_codex, brief tool/BRIEF_ingest.md, receipt codex_local/.../20261119T063725Z_corpus_ingest. Formats kit + routed.
- trinity-1-18 tmux corpus_list: tar tvf of old_lanes_3_30_{a,b}.tar and n30_mirror/cont_ops/*.tar -> /scratch/jjyeung/n30_mirror/corpus_work/*.list (DONE file).
## Next
- Second Codex job: adapters offread (b07_offread/in/ret_vsi 170008, ret_revsi 170037, official), native (b04_e2ehook/work/n13 170056), older kit layout without top ITEMS.jsonl, FAILED/partial kit (aed15a8b7cb).
- Training tars per run from Orchard okh7/x_*/{k,o,runs} (sizes first, QUESTION); analysis tars from codex_runs/*san_* + san_dd_* lanes.
