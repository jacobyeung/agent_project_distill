# Narrow kit review (read-only, once) of vehicle N's upload kit round 24m4z12 of lane tree_rebuild

You review; you do not fix. Run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, with file:line and evidence. Your final message is the verdict.

- Build: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/` (prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24m4z12.md`; reports out/BUILD24M4Z12_REPORT.md, out/ENOSPC_24M4Z12.md; work/build24m4z12/). Control: the previous round `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z10/` and its review `/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261121T002908Z_tree_rebuild_rev24m4z10/final_message.md` (NO-GO, two findings; everything else in it was verified and stands). Real-session evidence on the 24m4z10 bytes: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/tgcs_900004/`; Orchard e3 job 173966 ran the 24m4z10 bytes (results under `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173966/` if present).
- Verify, each with evidence:
  1. Delta: against 24m4z10, kits n and n_go differ only in b/pc.py, SHA256SUMS.txt and BUILD.json (compare yourself); pc.py identical in n and n_go; k/y.json, gc.py, b/o.py, b/pc.sh unchanged; q, qd, rcj, tree 9d2bbb8a unchanged; GO false except n_go; seals verify.
  2. Finding (a) fixed: ordinary checkpoints upload after the stop checkpoint, exports, logs, archive and u log have settled, in the live loop and the final pass, newest first, resumable, cut by the reserve; the order and the stop-first rules of 24m4z10 still hold; fail-before on 24m4z10 bytes and pass-after.
  3. Finding (b) fixed: every log tail pc.py publishes live (incl. j2.log/j2.err) passes the sealed screen filter; reproduce the probe (a screened token in j2.log never reaches live/ unchanged).
  4. Carry: does any change touch session handling, the session cache, object names or the HTTP path (gc.py and its callers in pc.py)? If none, say that e3 on the 24m4z10 bytes and the 900004 real-session run carry for the upload path (RULING 2211Z item 4); if any, name it (file:line).
  5. Every suite listed in ENOSPC_24M4Z12.md ran on the new bytes and passed (read the logs); upload lists exact, files under 5 MB.
- Also list what you did not check.

Rules: Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data* (read only the named files there). nice -n 10, at most 8 threads, under 20 GB RAM. First line `GO`, `GO AFTER FIXES` or `NO-GO`; at most 14 lines.
