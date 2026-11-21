W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w27fix/n_go
echo "=== w26t5/out"; ls -la $W/w26t5/out; ls $W/w26t5/work/build26 | head -40
for f in $W/w26t5/out/T_JN6_USAGE.md $W/w24z16b/out/T_JN5_USAGE.md; do echo "=== $f"; cat $f 2>&1; done
for f in x.py a.py pc.sh q.sh q1.sh e.sh f.sh ep.sh mg.py pf.py s.py t.py m.py l.py v.py resolve.py w.py d.py g.py; do echo "=== $f"; cat $K/b/$f; done
echo "=== grep z.py"; grep -n 'bwrap\|j\.sh\|def \|WAITING\|review\|train\|export\|stop' $K/b/z.py | head -120
echo "=== grep pl.py"; grep -n 'bwrap\|j\.sh\|def \|WAITING\|review\|train\|export\|stop\|tb' $K/b/pl.py | head -80
