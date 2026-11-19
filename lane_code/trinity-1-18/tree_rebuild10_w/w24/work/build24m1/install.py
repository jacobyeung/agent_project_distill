from pathlib import Path
import base64, hashlib, json, sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24m1'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build24f'),str(L/'work/tree_r1')]
import joblib as J
from kit24f import reseal

def replace(p, raw, mode=None):
    if p.exists():
        old=L/'attic/build24m1'/p.relative_to(L);old.parent.mkdir(parents=True,exist_ok=True)
        if not old.exists():p.rename(old)
    p.write_bytes(raw)
    if mode is not None:p.chmod(mode)

for name in ('q','n','n_go'):
    k=L/('out/kit_n_go' if name=='n_go' else 'work/build24/kits/'+name)
    p=k/'b/a.py';s=p.read_text()
    start=s.index("    spec=read(kit/'k/p.json');job=")
    end=s.index("    r={'status':'ADMIT'}",start)
    s=s[:start]+s[end:]
    hook='''if sys.argv[1]=='r':
 import os
 sys.path.insert(0,str(kit/'b'))
 from z import screen,write,load
 def refused(kind,value,traceback):
  text=screen(kind.__name__+':'+str(value),read(kit/'k/g.json'),load(kit/'b/wh.json'))
  write(root/'r0.json',dict(status='REFUSE',refusal=text[:100000]))
  sys.__excepthook__(kind,value,traceback)
 sys.excepthook=refused
 job=os.environ.get('SLURM_JOB_ID','')
 if not job.isascii() or not job.isdigit():raise ValueError('R1_ROUTING_JOB_ID_REQUIRED')
'''
    s=s.replace("src=control['source'];p=kit/src['path']",hook+"src=control['source'];p=kit/src['path']")
    replace(p,s.encode())
    replace(k/'b/rd.py',(D/'rd.py').read_bytes())
    p=k/'b/rv.py'
    if p.exists():
        s=p.read_text();start=s.index('def strip_frames(');end=s.index('\n\ndef reasoning(',start)
        s=s[:start]+'''def strip_frames(value):
    if isinstance(value, dict):
        return {k: strip_frames(v) for k, v in value.items()
                if not (k in {'frame', 'frames', 'frame_index', 'frame_indices', 'frame_id',
                              'timestamp', 'timestamps'} or '_frame' in k)}
    if isinstance(value, list):
        return [strip_frames(v) for v in value]
    return value
'''+s[end:]
        replace(p,s.encode())
    p=k/'b/pl.py';s=p.read_text()
    s=s.replace("        with scope(sources):\n            p_config=", "        closure(cfg['r1_training']['p_run']['config'])\n        with scope(sources):\n            p_config=")
    # The P recipe consumes its own removals and exclusions, independently of N.
    s=s.replace("        for field in ('inputs','legacy','division','base_model'):closure(recipe[field])", "        for field in ('remove_files','dev_scene_exclusions','benchmark_scene_exclusions'):\n            closure(p_config[field])\n        for field in ('inputs','legacy','division','base_model'):closure(recipe[field])")
    replace(p,s.encode())
    p=k/'b/rg.py';s=p.read_text()
    s=s.replace("        reproduced=build(pcfg,root/'pr',", "        from i import refresh\n        p_input=write(root/'p0.json',pcfg)\n        refreshed=refresh(dict(config=p_input,staged_pins=[p_input]),root/'pi')\n        pcfg=load(pinned(refreshed['config']))\n        reproduced=build(pcfg,root/'pr',")
    replace(p,s.encode())
    p=k/'k/j.json';doc=json.loads(p.read_text());s=base64.b64decode(doc['payload']).decode()
    s=s.replace('if [[ "${Q_MODE:-q}" == r ]]; then exit "$rc"; fi', '''if [[ "${Q_MODE:-q}" == r ]]; then
    /usr/bin/python3 -B -I -s "$Q_KIT/b/rd.py" "$Q_ROOT" "${SLURM_JOB_ID:?}" "$rc"
    rp=$?
    if [[ "$rc" == 0 ]]; then rc=$rp; fi
    exit "$rc"
fi''')
    # bwrap may be a pinned pool binary rather than installed on the host PATH.
    s=s.replace('tk_bwrap\nBW+=', 'tk_bwrap\nexport PATH="$(dirname "${BW[0]}"):$PATH"\nBW+=')
    doc.update(payload=base64.b64encode(s.encode()).decode(),sha256=hashlib.sha256(s.encode()).hexdigest())
    replace(p,(json.dumps(doc)+'\n').encode())
    for p in [k/'job.sh',*k.glob('b/*.sh')]:replace(p,p.read_bytes(),0o755)
    for n in ('BUILD.json','SHA256SUMS.txt'):replace(k/n,(k/n).read_bytes())
    print(name,reseal(k))
