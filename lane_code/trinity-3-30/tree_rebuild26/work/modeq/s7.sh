W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
K=$W/w24z8b/out/kit_qdp; G=$W/w24z11b/a_zffhb1q8/armed/kits/n_go
T=$K/k/t_e047002134f979bd.tar
echo =====ADM; tar xOf $T student_pilot/s1_admission.py | sed -n '133,160p;285,300p;330,345p' | cut -c1-230
echo =====RJ; python3 -I -c '
import json,sys;v=json.load(open(sys.argv[1]));print(sorted(v));print({k:v[k] for k in v if k not in ("routing_base","routing_selection")})' $K/k/r.json | cut -c1-600
echo =====RES; grep -n "request\b\|'request'\|r.json\|weights" $K/b/z.py | sed -n '1,40p' | cut -c1-220
echo =====FBC; tar xOf $T student_pilot/carrier_c1_run.py | sed -n '3088,3175p' | cut -c1-200
echo =====RL; tar xOf $T student_pilot/carrier_c1_run.py | grep -n "RLIMIT\|setrlimit" | head; tar xOf $T launch_r1/production_proof.py | grep -n RLIMIT; for f in student_pilot/r1_loader.py student_pilot/r1_population.py; do tar xOf $T $f | grep -n "RLIMIT\|setrlimit" | sed "s|^|$f:|"; done
echo =====MD; grep -ln "RLIMIT\|address space\|all_rank_full_forward\|R1_PROOF_\|first_batch" $W/w24z8b/out/*.md $W/w24z11b/*/*.md 2>/dev/null | head; grep -n "RLIMIT\|address space\|all_rank_full_forward\|cuda.*out of memory" $W/w24z8b/out/*.md 2>/dev/null | cut -c1-250 | head -20
