# T2: the item-1 test on the fixed kit bytes. Runs the kit's own staging function (pl.named_folder) and preflight
# (pf.check) on the replica of the job's layout, then the tree's witness and forward resolutions.
import sys,os,json,base64,hashlib
S,KB,HERE=sys.argv[1:4]
sys.path.insert(0,S);sys.path.insert(1,KB);sys.path.insert(2,HERE)
if os.environ.get('T27_OVL'):sys.path.append(os.environ['T27_OVL'])   # test environment only: adds torchvision
from pathlib import Path
import pl,pf,fw,t27probe
from student_pilot.r1_persisted import scope,proof_scope
from student_pilot.p3_provenance import load,pinned
import torch,transformers,torchvision
kit=Path(KB).parent
def out(k,v):print(k,json.dumps(v,sort_keys=True,default=str),flush=True)
cfg=json.loads(base64.b64decode(json.loads((kit/'k/c.json').read_text())['payload']))
Q=Path('/tmp/q_22c714e1/p/q');U=Q/'u'
config_pin=cfg['r1_training']['p_run']['config'];prep_pin=cfg['r1_training']['p_run']['preparation']
base={p.name:str(p) for p in U.iterdir()}                      # staged pins: p/q/u/<sha256>
with scope(base):
    prep=load(pinned(prep_pin));man_pin=prep['model'];manifest=load(pinned(man_pin))
    from student_pilot.mdg_parent import model_pin
    forward_pin=model_pin(cfg)                                 # N's own pose stream chain (real receipts)
named={n:h for n,h in manifest['files'].items() if n.endswith(('.json','.txt','.jinja','.model'))}   # rule of pl.plan_payload
out('HEAD',dict(kit_seal=hashlib.sha256((kit/'SHA256SUMS.txt').read_bytes()).hexdigest()[:16],python=sys.version.split()[0],
    transformers=transformers.__version__,torch=torch.__version__,torchvision=torchvision.__version__,
    CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),witness_manifest=man_pin['sha256'][:12],
    forward_manifest_from_N_pose_stream=forward_pin['sha256'][:12],manifest_root=manifest['root'],named=sorted(named)))
def preflight(label,paths):
    with proof_scope(),scope(paths):
        try:pf.check(cfg,man_pin);out(label,dict(ok=True))
        except ValueError as error:out(label,dict(ok=False,error=str(error)[:260]))
preflight('PF_UNFIXED_MAPPING (must refuse as 174101 did)',base)
rehearsal=pl.named_folder(Path('/tmp/q_22c714e1/p/i/y'),lambda h:base[h],named,link=False)
out('PLAN_REHEARSAL_FOLDER',sorted({str(Path(p).parent) for p in rehearsal.values()}))
preflight('PF_PLAN_REHEARSAL (end of planning)',{**base,**rehearsal})
linked=pl.named_folder(Q/'y',lambda h:U/h,named)
final=dict(base);final.update(linked)                         # order of pl.stage: staged pins, then the named folder
y=Q/'y'
out('STAGED_NAMED_FOLDER',dict(folder=str(y),mode=oct(y.stat().st_mode&0o777),names=sorted(os.listdir(y)),
    hard_links_of_pool=all(os.stat(y/n).st_ino==os.stat(U/h).st_ino for n,h in named.items()),
    sha256_match=all(hashlib.sha256((y/n).read_bytes()).hexdigest()==h for n,h in named.items())))
preflight('PF_STAGED (after staging)',final)
with proof_scope(),scope(final):
    folder=pinned(dict(path=str(Path(manifest['root'])/'config.json'),sha256=manifest['files']['config.json'])).parent
    out('WITNESS_FOLDER_RESOLVED',str(folder))
    rows=[('witness in-process (as production_proof runs it)',lambda:t27probe.witness(config_pin)),
          ('forward resolution in-process',lambda:t27probe.forward(prep_pin)),
          ('forward resolution through b/fw.py (fresh interpreter)',lambda:fw.call('t27probe','forward',(prep_pin,))),
          ('witness through b/fw.py (control)',lambda:fw.call('t27probe','witness',(config_pin,)))]
    for name,function in rows:
        try:result=function()
        except Exception as error:result=dict(ok=False,harness_error=type(error).__name__+':'+str(error)[:300])
        out('RESULT',dict(case=name,**result))
