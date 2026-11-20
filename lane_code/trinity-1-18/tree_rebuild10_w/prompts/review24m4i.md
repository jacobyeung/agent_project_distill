# Delta review (read-only, once) of KIT build 24m4i of lane tree_rebuild: direct room rows' draw rate restored to P's (ORCH RULING 0511Z)

You review; you do not fix. Run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems with file:line and evidence. Final message is the verdict.

- Ruling 0511Z: the direct room rows in N's VQA stream keep P's draw rate (P 1.70 rows/step); if N's plan draws them at zero for the whole job (case b), restore P's rate as a config delta limited to those draw entries; a per-family rows-per-step table P vs N over the first 200 steps goes on the card.
- Build: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24i/` (prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24m4i.md`; out/BUILD24M4I_REPORT.md, CASE_24M4I.md, DRAW_TABLE_24M4I.md/.json, EXACT_CONFIG_DELTA.json, CONFIG_IDENTITIES.json, UPLOADS_24M4I.json; kits out/kit_n_go, out/kit_qd, work/build24/kits/{q,n}). Previous kits `w24h/` (seals q d54120b4, n fec34c9d, n_go 60d24119, qd 62d8a7f5; reviewed GO).

Verify: (1) case (b) holds from the code (r1_mix.py, r1_population.py, r1_loader.py lines cited); (2) the decoded config diff old vs new in all four kits is limited to the room draw entries, the direction entry changed to keep 128 VQA rows/step, and dependent identities/seals; no b/ file and no tree byte changed; (3) the new room and direction values equal P's (read P's config / plan) and the table's P column is read from P, not assumed; (4) every DRAW_TABLE difference has a named cause or is marked UNATTRIBUTED; list the UNATTRIBUTED rows; (5) UPLOADS delta complete; arm_routing works on the new seals; GO false except kit_n_go; (6) what you did not check.

Rules: Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data* (read only the named files there). nice -n 10, at most 8 threads, under 20 GB RAM. First line `GO`, `GO AFTER FIXES` or `NO-GO`; at most 15 lines.
