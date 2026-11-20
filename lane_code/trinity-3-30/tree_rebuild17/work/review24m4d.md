# Delta review (read-only, once) of KIT build 24m4d of lane tree_rebuild: the fixes for your review of 24m4c

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict. This gates N's launch on 4 H100 for 24 h.

## Context (all under /scratch/jjyeung/orch_n30/tree_rebuild10_w)
- Your review of 24m4c: `/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261120T012257Z_tree_rebuild_rev24mC/final_message.md` (MUST rv.py strict VQA rooms; MUST arm_routing.py does not stage the DB; SHOULD 0664 perms). Your prompt then: `prompts/review24mC.md`.
- Base package `w24c/out/tree_rebuild_b24m4c_b7be125e.tar`; new package `w24c/out/tree_rebuild_b24m4d_*.tar` (read with tarfile in memory), report `w24c/out/BUILD24M4D_REPORT.md`, `w24c/out/DELIVERY_24M4D.json`, `w24c/out/ARM_ROUTING_USAGE.md`, prompt `prompts/build24m4d.md`. Kit dirs `w24c/out/kit_n_go`, `w24c/out/kit_qd`, `w24c/work/build24/kits/{q,n}` (seals in the report's line 1); arm tool `w24c/out/arm_routing.py`.

## Check
1. Member diff 24m4c -> 24m4d: only rv.py (all four kits), arm_routing.py, modes, seals and dependent manifests change; anything else is a finding.
2. MUST 1 fixed: rv.py resolves each stream's rooms with the authority the kit census and the tree's own room audit use (VQA tiered/direction_twins Binding when the config enables twins); your replay row (line 1 of `w24/work/build22/upload/u/7b3d696d580386f9e8af3240fa142e2ad50eebb277a8718c97e2db497dcc925e`) passes as clean; protected and unresolvable rows still refuse; no new fail-open path.
3. MUST 2 fixed: arm_routing.py binds the reviewed selection and the DB (sha256 and size from db_bytes.json) as authenticated staged pins in fresh q, n, n_go copies; the q-path planner closure resolves the DB pin to a staged member; the upload delta excludes the DB bytes; it cannot bind an unreviewed or mismatched selection or a DB whose sha differs from the selection's.
4. SHOULD fixed: non-executable modes back to 0644; executables unchanged.
5. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data* (read only the named files there). nice -n 10, at most 8 threads, under 20 GB RAM. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 20 lines.
