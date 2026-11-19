W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; mkdir -p $W/work/conf21g
cat > $W/work/conf21g/cf21g.sh <<'EOS'
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf21g; P="nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
T=$(ls $W/w21/out/tree_rebuild_b21g_*.tar | head -1); mkdir -p $C/pkg; cd $C; sha256sum $T; stat -c %s $T
(cd pkg && tar xf $T)
for d in $W/w21/work/tree_r1 $C/pkg/work/tree_r1; do (cd $d && $P -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"); done
echo SEALDONE
ls $C/pkg/work | tr '\n' ' '; echo
echo CFDONE
EOS
cat > $W/prompts/review21g.md <<'EOS'
# Independent review (read-only, once) of build 21g of lane tree_rebuild (with build 21f's scanner), changed files only, versus build 21e

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict.

## Context
Vehicle N's production proof (mode q on P's step-400 export) ran on Orchard with build 21e's kit q (seal 5d300f19; package `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/out/tree_rebuild_b21e_ac8fa8e3.tar`, reviewed: resolver fixes verified). Staging passed; the job died at `bwrap: Can't mkdir /tmp/q_22c714e1: Read-only file system` (P's tk_bwrap ro-binds host top-level entries; N's namespace mount point did not exist on the host). Build 21f (report `w21/out/BUILD21F_REPORT.md`) made the environment scanner strict; build 21g (prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build21g.md`, report `w21/out/BUILD21G_REPORT.md`, package `w21/out/tree_rebuild_b21g_*.tar`) finishes 21f, fixes the bwrap mount points in the kit, and runs a look-ahead of the in-view stages on trinity-1-18. P's view code: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/pwrap/b/c.sh` (tk_bwrap lines 339-366).

## Check
1. Compare the 21e and 21g packages member by member in memory (tarfile; write nothing); review only changed files. The sealed tree must be byte-identical (seal b262e7a7).
2. Mount points: every bwrap destination in mode q either exists on the host, is created by the kit on node-local storage before the view (never in the pool, never outside the job's control), or lies inside a writable bind; the fix cannot write into P's kit, P's run, or any shared pool path; the failing-before/passing-after test is real.
3. Scanner: the `**os.environ` inheritance acceptance is exact (no added non-literal key passes); the tuple variant and 21f's mutations refuse; the decoded scan of the real kit passes.
4. Look-ahead: is the furthest stage claimed actually reached, and are its stand-ins only at the GPU/weights/production-store boundary?
5. Nothing changed in admission, legality, P's opener rows (routing_opener_init=keep), the step-544 lineage, the resolver's identity checks, or the DEFERRED boundary; GO stays false.
6. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 30 lines.
EOS
sha256sum $W/prompts/review21g.md | cut -c1-16
tmux new -d -s tr12_rev21g "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh review $W/w21 $W/prompts/review21g.md --model gpt-6-astra --effort high --label tree_rebuild_rev21g --skip-git-check > $W/work/review21g_dispatch.log 2>&1"
bash $W/work/conf21g/cf21g.sh > $W/work/conf21g/cf21g.log 2>&1; cat $W/work/conf21g/cf21g.log
cat $W/w21/out/BUILD21G_REPORT.md | cut -c1-400
