# nv_orch1 STATUS: ENDED 2026-11-20T06:05Z (the user stopped paid labelling; ORCH ORDER 0552Z). Do not start a successor.
- Orchard sends: stopped 05:58Z; no nv_orch1 job on Orchard; ALLOC RELEASE 06:01Z; watcher tmux nvo_watch stopped; key check clean (final RESULT item 2).
- Spend from Orchard: $40.94 list / $30.23 proxy, 265 calls (D/NV_SPEND_LEDGER.jsonl, lane nv_orch1, 9 lines).
- Banked: B/events/nvkey/banked_nv_orch1/ (SHA256SUMS) and B/events/nvkey/analysis_only_nv_orch1/ (dev census). Final RESULT: B/events/nvkey/*_RESULT_nv_orch1_final_*.
- Orchard root /project/community/jjyeung/4f5e45fe5d74c holds kit/, queue/, hold/, out/, meter/, idx/k6.tsv.gz (frame header index), excl/DENY*.sha256 (hashes only). out file sha256 equal the banked copies. Token meanings: L/work/ORCHARD_LEDGER.jsonl (L = /scratch/jjyeung/orch_n30/nv_orch1 on trinity-3-30).
- Removal candidates (no deletion done): REMOVAL_CANDIDATES.md.
