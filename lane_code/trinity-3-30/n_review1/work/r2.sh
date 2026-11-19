W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; O=$W/w24/out; K=$O/kit_n_go
for f in BUILD24D_REPORT.md BUILD24E_REPORT.md BUILD24F_REPORT.md BUILD24G_REPORT.md N_CARD_KIT_ROWS.md DELIVERY_24G.json TREE_SEAL.json; do echo "##### $f"; cat $O/$f; done
for f in BUILD.json job.sh k/a.json k/h.json k/r.json k/y.json k/8.json k/g.json b/h.py b/u.py b/t.py b/a.py b/x.py b/v.py b/e.sh b/d.py b/o.py; do echo "##### kit_n_go/$f"; cat $K/$f; echo; done
echo "##### entry.py"; ls $W/w24/work/tree_r1 | head; sed -n 1,140p $W/w24/work/tree_r1/launch_r1/entry.py
which bwrap; bwrap --version
