W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
K=$W/w24z8b/out/kit_qdp; G=$W/w24z11b/a_zffhb1q8/armed/kits/n_go
T=$K/k/t_e047002134f979bd.tar
echo =====PP; tar xOf $T launch_r1/production_proof.py | cat -n | cut -c1-260
echo =====ZCOPY; sed -n '435,516p' $K/b/z.py | cat -n | sed 's/^/Z+434 /' | cut -c1-250
echo =====H; cat -n $K/b/h.py | cut -c1-250
echo =====EP; cat -n $K/b/ep.py | cut -c1-250
echo =====RVTOP; sed -n '1,80p' $K/b/rv.py | cat -n | cut -c1-250
