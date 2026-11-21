W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
K=$W/w24z8b/out/kit_qdp; G=$W/w24z11b/a_zffhb1q8/armed/kits/n_go
cd $K
for f in job.sh BUILD.json b/x.py b/q.sh b/q1.sh b/a.py b/l.py b/ep.sh b/v.py b/resolve.py b/f.sh b/d.py b/s.py b/w.py b/m.py b/g.py b/o.py; do echo "=====K/$f"; cat -n $f; done
echo =====K/k/a.json; head -c 1700 k/a.json; echo
echo =====grepK; grep -n "exit\|SystemExit\|raise\|sys.exit\|returncode\|check=True\|check_call" b/*.py b/*.sh | cut -c1-220
cd $G
for f in job.sh BUILD.json b/x.py b/q.sh b/q1.sh b/a.py b/e.sh b/pc.sh b/o.py; do echo "=====G/$f"; cat -n $f; done
echo =====diffs; for f in a.py rv.py h.py pl.py z.py q.sh q1.sh x.py ep.sh; do cmp $K/b/$f $G/b/$f && echo "same $f"; done
