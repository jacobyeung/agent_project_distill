W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
K=$W/w24z8b/out/kit_qdp; G=$W/w24z11b/a_zffhb1q8/armed/kits/n_go
cd $K
echo =====zdefs; grep -n "^def \|^    def \|^class " b/z.py
echo =====z440; sed -n '440,$p' b/z.py | cat -n | sed 's/^/Z+439 /' | cut -c1-300
echo =====f0; cat -n b/f0.py | cut -c1-300
echo =====pl; cat -n b/pl.py | cut -c1-300
echo =====tar; tar tvf k/t_e047002134f979bd.tar | head -100
echo =====rvdiff; diff $K/b/rv.py $G/b/rv.py; diff $K/b/h.py $G/b/h.py; diff $K/b/a.py $G/b/a.py
cmp $K/k/t_e047002134f979bd.tar $G/k/t_e047002134f979bd.tar && echo same tree tar; ls $G/k
