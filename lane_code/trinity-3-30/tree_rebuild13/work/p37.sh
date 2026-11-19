Q=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/work/build21/kits/q; cd $Q
wc -c b/x.py b/l.py b/q.sh b/q1.sh b/f.sh; echo ==== l.py; cat b/l.py | cut -c1-200 | head -40
echo ==== x.py; grep -n "g.py\|subprocess\|bwrap\|q.sh\|q1.sh\|f.sh\|exit\|raise\|stderr" b/x.py | cut -c1-220 | head -40
