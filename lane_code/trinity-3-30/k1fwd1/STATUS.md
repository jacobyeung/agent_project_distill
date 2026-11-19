# k1fwd1 STATUS (Devin Opus high, trinity-3-30; started 19:59Z 11-19; hard end 00:59Z 11-20)
Brief: B/briefs/k1fwd1.md. Events B/events/k1fwd. Session /scratch/jjyeung/orch_n30/k1fwd1 (work/, b7/ = copy of 170235 build7 scripts+CONFIG, kit/ = kit_k1a py, h1/ = cont_ops read kit py).
## Decisions
- ORCH ANSWER 2016Z: D1. Changes allowed: step guard (boundaries.py:46), selected trainer tree, pins that follow the export. Grid code byte-identical. One Astra read-only review of the diff. Step-544 parity check on 5 captures with the changed package first (bit-identical or <=1e-4 rel, else stop and post). Grids needed by ~04:00Z.
## Facts
- Trainer tree is env-selected: LEGS1_TREE (kit bindings.py:6 and native out2 common.py TREE); default tree_s1_admissionfix_168872 (trainer t_b01ce449). R1 m400 needs tree b83a8a35 (t_b83a8a35d420815b.tar sha e5be8157; config identity 9459724f).
- k1_pipeline.check_manifest requires the exact 300-capture set -> runs keep 300 captures; scorer selects 242.
- R1 metadata closure on Orchard: okh7/h_6ed2c7aa/m400/s.tar (194 MB, files/<logical path>, MANIFEST.json; trainer tar, c.json seal, prep inputs, m400 artifact, init m544 artifact).
- m400 export parts: okh7/a15_cot_apda6f7936c1779/a/e/0-3 (pins in that package a/1.json: cbbe6aa0, fa217f69, 2f7f0022, 99c787cc; whole dcd49569). m544 parts: okh7/e6fc152498/e/0-3 (5cd24e72.., whole 3ed73aea).
- Advanced cards (cont_ops21 2011Z): all busy; next free ~21:15Z (own-arm takes it), then ~21:38Z for me. Avoid 173241 173243 173258 173259 173333.
## Plan
- Two jobs from one package builder: P544 (parity, short budget) then P400 (300 captures, --time 03:00:00 as 170235).
## Progress (20:37Z)
- Package okh7/a15_cot_ap90eaf12c47ba5 built (build.py 12bc0738; BUILD.json). Links done by preempt 173335 (LINKS.json; m400 parts inode group 1417811857 now 4 links; m544 parts from e6fc152498/e; s.tar).
- P544 token 944b6b6a8f8d8c7f batch 3f848683 (allocation 5400, --time 01:30:00); P400 token f67f0b1118da0677 batch 3a9e6fa7 (10800, --time 03:00:00). Same batch runs as CPU check when no card (stops before GPU; evidence in pool <token>/<job>/cpu/).
- CPU checks: 173339 (P544), 173340 (P400, after). Review: tmux k1fwd_rev (codex_local review, review/ dir; verdict review/REVIEW.md).
- Submit GPU (advanced, community-1): sbatch --account=mt01 --partition=advanced --qos=adv_4gpu_qos --nodelist=orchard-community-1 --gres=gpu:1 --cpus-per-task=16 --mem=200G --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_ap<token> <token>.sh
- Parity: compare P544 return own.npz vs trinity-1-18 /scratch/jjyeung/k1/own_170235/native/probe/<dir>/own.npz (<=1e-4 rel else stop).
## 21:22Z
- Review GO (codex receipt 20261119T203139Z_k1fwd_rev; copy review/REVIEW.md). CPU checks 173339/173340 PASS.
- P544 173343 COMPLETED 21:11Z: 64 captures bit-identical to 170235 (PARITY_544.json in package dir; return a4676ff78ac1941b6 bd10367b).
- P400 173346 RUNNING since ~21:11Z on community-1; model loaded, captures committing (21:20Z). Expected end ~22:36Z. Final return will be okh7/a15_cot_ap90eaf12c47ba5/f67f0b1118da0677/173346/a<token>/result.tar.gz.
- Return plan: kb/pull_launch.py ORCHARD_FILE BYTES /scratch/jjyeung/orch_n30/sb_own400/in/own_400/own_400_<job>.result.tar.gz 3 (runs on 3-30, streams Orchard -> ratelimit -> ssh trinity-1-18.ib; nothing stored on 3-30; registered tier 3 priority 3, io-weight 1). Then on 1-18: verify sha, rename .partial, extract in own_400/ (layout = native/probe/<dir>/own.npz + PHASE_COMPLETE.json, COMPLETE.json, logs, metadata).
- Yield: on launch GO scancel 173346 and rerun on general.
