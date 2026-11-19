W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf23d; P="nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
{ date -u +%TZ; tmux has-session -t tr13_b23d 2>/dev/null && { echo STILL_RUNNING; exit 0; }
T=$(ls $W/w23/out/tree_rebuild_b23d_*.tar | head -1); echo $T; mkdir -p $C/pkg; cd $C; sha256sum $T; stat -c %s $T
(cd pkg && tar xf $T)
for d in $W/w23/work/tree_r1 $C/pkg/work/tree_r1; do (cd $d && $P -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"); done
Q=$C/pkg/work/build21/kits/q; (cd $Q && sha256sum SHA256SUMS.txt && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ": OK"; wc -l < SHA256SUMS.txt; find . -type f | wc -l)
cmp $Q/SHA256SUMS.txt $W/w23/work/build21/kits/q/SHA256SUMS.txt && echo KITSAME
cat $W/w23/out/BUILD23D_REPORT.md; echo; cat $Q/b/g.py
cat > $W/prompts/review23d.md <<'EOPR'
# Independent review (read-only, once) of build 23d of lane tree_rebuild (kit GPU guard diagnostic), changed files only, versus build 23c

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict.

## Context
Review 23c (newest `/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild_rev23c/final_message.md`) found two MUSTs in the kit's GPU guard `q/b/g.py`: `torch.__version__` read outside the handler (AttributeError, no E42), and CUDA_VISIBLE_DEVICES printed verbatim. Build 23d (prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build23d.md`, report `w23/out/BUILD23D_REPORT.md`, package `w23/out/tree_rebuild_b23d_*.tar`) fixes them on top of 23c (`w23/out/tree_rebuild_b23c_db042c7c.tar`, tree 5b349b18, kit q a258d7e7).

## Check
1. Compare the 23c and 23d packages member by member in memory (tarfile; write nothing). The sealed tree must be byte-identical (5b349b18); the only changed kit files are the guard, BUILD.json and SHA256SUMS.txt (plus tests/evidence outside the kit).
2. Both MUSTs fixed: rerun both reviewer cases in memory. Any exception still prints a diagnostic and refuses E42; no environment text or unscreened device name reaches the output; decision logic unchanged (CUDA, >=1 device, memory >= 75 GiB; 85,520,809,984 bytes passes).
3. Decoded scan PASS; kit dir file list equals SHA256SUMS plus BUILD.json and SHA256SUMS.txt; upload diff versus a258d7e7 pinned and small.
4. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process under nice -n 10, at most 8 threads, under 20 GB RAM. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 20 lines.
EOPR
sha256sum $W/prompts/review23d.md | cut -c1-16
tmux new -d -s tr13_rev23d "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh review $W/w23 $W/prompts/review23d.md --model gpt-6-astra --effort high --label tree_rebuild_rev23d --skip-git-check > $W/work/review23d_dispatch.log 2>&1"
sleep 10; tmux ls | grep tr13
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json
d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/out/UPLOADS_NEW_23D.json'))
d=d if isinstance(d,list) else d.get('files',d)
open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/k23d_names.txt','w').write('\n'.join(e.get('name',e.get('opaque_name')) for e in d)+'\n')
for e in d: print(e.get('name',e.get('opaque_name')),e['bytes'],e['sha256'][:16])
PY
} >&2
tar cf - -C $C/pkg/work/build21/kits -T $W/work/k23d_names.txt | base64 -w0
