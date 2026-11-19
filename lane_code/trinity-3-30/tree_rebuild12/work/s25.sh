W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; mkdir -p $W/work/conf21e
cat > $W/work/conf21e/cf21e.sh <<'EOS'
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf21e; P="nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
T=$(ls $W/w21/out/tree_rebuild_b21e_*.tar | head -1); mkdir -p $C/pkg; cd $C; sha256sum $T; stat -c %s $T
(cd pkg && tar xf $T)
for d in $W/w21/work/tree_r1 $C/pkg/work/tree_r1; do (cd $d && $P -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"); done
echo SEALDONE
ls $C/pkg/work | tr '\n' ' '; echo
echo CFDONE
EOS
cat > $W/prompts/review21e.md <<'EOS'
# Independent review (read-only, once) of builds 21d + 21e of lane tree_rebuild (changed files only, versus build 21c)

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict.

## Context
Vehicle N's job kit q (mode q production proof on vehicle P's step-400 export, run 6ed2c7aa) was last reviewed at build 21c (package `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/out/tree_rebuild_b21c_6f5e6cc2.tar`, kit q seal 93b4404f; prior verdicts `/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261119T085438Z_tree_rebuild_rev21/final_message.md` and the newest `*tree_rebuild_rev21c/final_message.md` in the same folder — read those two files only). Build 21d (prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build21d.md`, report `w21/out/BUILD21D_REPORT.md`) closed review 21c's two scanner gaps with a named allowlist. Build 21e (prompt `.../prompts/build21e.md`, report `w21/out/BUILD21E_REPORT.md`, package `w21/out/tree_rebuild_b21e_*.tar`) fixes two resolver defects the lane found by running kit q's resolver on P's REAL step-400 files on Orchard: JSON-Lines `.json` members in P's small-file archive, and the artifact's config identity (9459724f, C' runtime) versus the kit's pinned p_identity (774503e2, C' kit config). Real P files for checking: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/m400real/`.

## Check
1. Compare the 21c and 21e packages member by member in memory (tarfile; write nothing) and review only changed files.
2. 21d allowlist: every exception is authenticated file content never used as a name, path, argument, environment entry or log line; nothing job-visible escapes the scanner; try one variant the tests do not cover.
3. 21e fix 1: JSONL members are values only; a member read as metadata that fails to parse refuses by name; no check weakened (manifest, sizes, hashes, member set).
4. 21e fix 2: each reader gets the identity it really verifies; both identities pinned and their relation authenticated from P's e.json/r.json/config/binding pins; no path admits an artifact of another config; verify with the real files in m400real.
5. Nothing else changed in admission, legality, P's opener rows (routing_opener_init=keep), the step-544 lineage path, or the DEFERRED component-evidence boundary; GO stays false. If the sealed tree changed, list the files.
6. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data* (read only the named files there). Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 30 lines.
EOS
sha256sum $W/prompts/review21e.md
tmux new -d -s tr12_cf21e "bash $W/work/conf21e/cf21e.sh > $W/work/conf21e/cf21e.log 2>&1"
tmux new -d -s tr12_rev21e "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh review $W/w21 $W/prompts/review21e.md --model gpt-6-astra --effort high --label tree_rebuild_rev21e --skip-git-check > $W/work/review21e_dispatch.log 2>&1"
cat $W/w21/out/BUILD21E_REPORT.md
