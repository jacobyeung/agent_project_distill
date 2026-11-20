K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24h/out/kit_n_go
echo "== a.py"; cat -n $K/b/a.py
echo "== pl need/closure"; grep -n "def need\|def closure\|R1_STAGED\|raise ValueError" $K/b/pl.py | head -30; sed -n 20,40p $K/b/pl.py
echo "== rb.py 100-200"; sed -n 100,200p $K/b/rb.py
