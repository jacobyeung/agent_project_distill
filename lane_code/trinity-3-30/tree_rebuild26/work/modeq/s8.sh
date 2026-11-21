W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
K=$W/w24z8b/out/kit_qdp; T=$K/k/t_e047002134f979bd.tar
python3 -I -c '
import json,sys,base64;v=json.load(open(sys.argv[1]));v=json.loads(base64.b64decode(v["payload"]));print(sorted(v));print({k:v[k] for k in v if k not in ("routing_base","routing_selection","staged_pins")})' $K/k/r.json | cut -c1-800
echo =====QD; cut -c1-300 $W/w24z8b/out/QD_STEP1.md | head -40
echo =====PT; grep -n "forward\|R1_PROOF\|first_batch\|RLIMIT\|cuda" $W/w24z8b/out/PROCESSOR_TRACE_24M4K.md | cut -c1-250 | head -15
echo =====ADMIT2; tar xOf $T student_pilot/s1_admission.py | grep -n "setrlimit\|getrlimit" 
echo =====LM; tar xOf $T student_pilot/carrier_c1_run.py | grep -n "^def load_model" ; tar xOf $T student_pilot/carrier_c1_run.py | grep -n "mmap\|memmap" | head -5
