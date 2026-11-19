K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go; T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1
nice -n 10 python3 -B /tmp/tr14_dec.py $K/k/c.json r2_persistence,wall_seconds,resume_every,stop_before,stop_control,stall_guard,first_step_admission </dev/null | cut -c1-600
nice -n 10 python3 -B -c "import json,base64;d=json.load(open('$K/k/c.json'));c=json.loads(base64.b64decode(d['payload']));r=c['recipe'];print({k:v for k,v in r.items() if k not in ('mix',)})" </dev/null | cut -c1-1500
sed -n 2846,3002p $T/student_pilot/carrier_c1_run.py </dev/null | grep -v "^\s*#" | cut -c1-170
