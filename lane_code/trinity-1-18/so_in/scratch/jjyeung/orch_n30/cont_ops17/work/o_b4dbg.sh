set -u
S=/project/community/jjyeung/okh7/813f42db/r7; D=$S/b4dbg; test ! -e $D && mkdir -m 700 $D
P=/project/community/jjyeung/okh7/a15_cot_apd50ba921ef1f4
/usr/bin/python3 - $P $D <<'PY'
import ast,io,tarfile,json,sys,hashlib,traceback
from pathlib import Path
P=Path(sys.argv[1]);D=Path(sys.argv[2])
l=[x for x in (P/'BATCH.sh').read_text().splitlines() if x.startswith('b=bytes.fromhex(')][0]
raw=bytes.fromhex(ast.literal_eval(ast.parse(l).body[0].value.args[0]))
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
    for m in t.getmembers(): (D/m.name).write_bytes(t.extractfile(m).read())
src=(D/'0.py').read_text().replace(' job.checked_run=make_dispatch(root,job.checked_run,operator_sha256)\n job.main(root)\n',' print("PROOF_OK")\n')
g=dict(__name__='dbg');exec(compile(src,str(D/'0.py'),'exec'),g)
sys.argv=['0.py',str(D)]
try: g['main']()
except Exception: traceback.print_exc()
sys.path.insert(0,str(D/'p'))
from orchard_h10 import job
try:
    pub=json.loads((D/'0.json').read_text()); cfg=job.read_config(P); job.verify_config(cfg); print('CONFIG_OK')
    inputs=job.check_inputs(json.loads((P/'a/1.json').read_text()),cfg); print('INPUTS_OK')
except Exception: traceback.print_exc()
c=json.loads((P/'a/c/CPU.json').read_text()); print('cpu full_reader passed',c.get('full_reader',{}).get('passed'), 'inputs match', c['inputs']==hashlib.sha256((P/'a/1.json').read_bytes()).hexdigest())
PY
grep -n "A_N\|A_T\|A_I\|A_C" $P/BATCH.sh | head; sed -n 1,20p $P/SUBMIT.cmd
