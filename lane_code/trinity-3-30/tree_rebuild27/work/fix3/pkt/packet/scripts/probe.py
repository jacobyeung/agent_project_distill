import sys,os,json,base64
S,KB,HERE,label=sys.argv[1:5]
sys.path.insert(0,S);sys.path.insert(1,KB);sys.path.insert(2,HERE)
from pathlib import Path
import t27probe
from student_pilot.r1_persisted import scope,proof_scope
import fw
kit=Path(KB).parent
cap=json.loads((kit/'k/c.json').read_text());cfg=json.loads(base64.b64decode(cap['payload']))
config_pin=cfg['r1_training']['p_run']['config'];prep_pin=cfg['r1_training']['p_run']['preparation']
U=Path('/tmp/q_22c714e1/p/q/u')
paths={p.name:str(p) for p in U.iterdir()}          # the kit's rule: every pin resolves to p/q/u/<sha256>
extra=json.loads(os.environ.get('T27_EXTRA_PATHS','{}'))   # fixed kit: {sha256: named path} from its own staging function
paths.update(extra)
print(json.dumps(dict(label=label,python=sys.version.split()[0],kit_seal=__import__('hashlib').sha256((kit/'SHA256SUMS.txt').read_bytes()).hexdigest()[:16],
    scope_entries=len(paths),named_relocations=len(extra),CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),
    config_pin=config_pin['sha256'][:12],preparation_pin=prep_pin['sha256'][:12],pid=os.getpid())))
import transformers,torch;print(json.dumps(dict(transformers=transformers.__version__,torch=torch.__version__)))
with proof_scope(),scope(paths):
    rows=[('witness in-process (as production_proof runs it)',lambda:t27probe.witness(config_pin)),
          ('forward resolution in-process',lambda:t27probe.forward(prep_pin)),
          ('forward resolution through b/fw.py (fresh interpreter)',lambda:fw.call('t27probe','forward',(prep_pin,))),
          ('witness through b/fw.py (control)',lambda:fw.call('t27probe','witness',(config_pin,)))]
    for name,function in rows:
        try:out=function()
        except Exception as error:out=dict(ok=False,harness_error=type(error).__name__+':'+str(error)[:300])
        print('RESULT',json.dumps(dict(case=name,**out),sort_keys=True),flush=True)
