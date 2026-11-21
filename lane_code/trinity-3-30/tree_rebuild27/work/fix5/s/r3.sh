W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w27fix/n_go
echo "=== z.py 576-628"; sed -n 576,628p $K/b/z.py
echo "=== k"; ls -la $K/k
echo "=== u.py"; cat $K/b/u.py
echo "=== sr.py"; cat $K/b/sr.py
echo "=== grep others"; for f in cs.py rv.py sv.py pc.py ep.py gc.py h.py i.py o.py px.py rd.py sc.py rg.py rb.py; do echo "--- $f"; grep -n 'WAITING\|review\|steps\|stop\.request\|def \|\.sh\|bwrap\|q0\|first' $K/b/$f | head -40; done
