# T4: where each load after the processor resolves on the job's layout. Runs the tree's own resolution calls
# (pinned / relocated / init_mirror) under the kit's path rule on the replica. Bytes that are not on this node
# (weight shards, heads, depth weights) are 1-byte placeholders, marked as such; nothing is loaded.
import sys,os,json,base64,hashlib
S,KB,HERE,DEPTH=sys.argv[1:5]
sys.path.insert(0,S);sys.path.insert(1,KB);sys.path.insert(2,HERE)
if os.environ.get('T27_OVL'):sys.path.append(os.environ['T27_OVL'])
from pathlib import Path
from student_pilot.r1_persisted import scope,proof_scope,relocated
from student_pilot.p3_provenance import load,pinned
import student_pilot.carrier_c1_run as c
kit=Path(KB).parent
def out(k,v):print(k,json.dumps(v,sort_keys=True,default=str),flush=True)
cfg=json.loads(base64.b64decode(json.loads((kit/'k/c.json').read_text())['payload']))
Q=Path('/tmp/q_22c714e1/p/q');U=Q/'u';Wd=Q/'w';Wd.mkdir(exist_ok=True)
base={p.name:str(p) for p in U.iterdir()};placeholder=set()
art_pin=cfg['init_artifact']['artifact']
with scope(base):
    artifact=load(pinned(art_pin));export=load(pinned(artifact['full_weights']))
    handover=load(pinned(cfg['r1_training']['p_run'].get('artifact',art_pin))) if False else None
names={'full_weights.json':artifact['full_weights']['sha256'],export['index']['name']:export['index']['sha256']}
names.update({item['name']:item['sha256'] for item in export['files']})
def ensure(h):
    if not (U/h).exists():(U/h).write_bytes(b'\0');placeholder.add(h)
for name,h in names.items():                    # the kit's rule: z.py:503-514 links u/<sha> to w/<name>; pl.py:171-177 maps the hash there
    ensure(h)
    if not (Wd/name).exists():os.link(U/h,Wd/name)
ensure(artifact['heads']['sha256'])
paths={p.name:str(p) for p in U.iterdir()};paths.update({h:str(Wd/name) for name,h in names.items()})
rows=[]
def row(load_name,code,path,holds=None,note=''):
    path=Path(path);rows.append(dict(load=load_name,code=code,resolves_to=str(path),exists=path.exists(),holds=holds,note=note))
with proof_scope(),scope(paths):
    receipt=load(pinned(cfg['r1_training']['p_run']['preparation']));manifest=load(pinned(receipt['model']));root=Path(manifest['root'])
    row('processor: tokenizer, image and video processor, chat template','carrier_c1_run.py:1242 processor_for(manifest[root])',root,
        [n for n in sorted(os.listdir(root)) if not n.endswith('.safetensors')])
    row('base asset authentication: sha256 of 13 manifest files','carrier_c1_run.py:807-810',root,sorted(os.listdir(root)),'4 weight shards are placeholders here')
    row('base config and 4 weight shards: from_pretrained(root)','carrier_c1_run.py:811',root,[n for n in sorted(os.listdir(root)) if 'safetensors' in n or n=='config.json'])
    row('init artifact record','carrier_c1_run.py init_from_artifact: load(pinned(spec[artifact]))',pinned(art_pin))
    out('INIT_MIRROR',dict(init_mirror=str(c.init_mirror(art_pin)),C1_INIT_LOCAL=os.environ.get('C1_INIT_LOCAL')))
    directory=pinned(artifact['full_weights']).parent
    row('LM full-weights export: manifest, index, 5 shards','carrier_c1_run.py:965-967, 1031-1043 pinned(artifact[full_weights]).parent',directory,
        sorted(os.listdir(directory)),'manifest names '+('all present' if set(names)<=set(os.listdir(directory)) else 'MISSING')+'; index and shards are placeholders here')
    row('heads state','carrier_c1_run.py:976-977 torch.load(pinned(artifact[heads]))',relocated(artifact['heads']),None,'placeholder here; a file opened by path')
    depth=json.loads(Path(DEPTH).read_text())
    row('depth init record','carrier_c1.py:709 load(pinned(depth_init))',relocated(cfg['depth_init']) if cfg['depth_init']['sha256'] in paths else 'p/q/u/'+cfg['depth_init']['sha256'],None,
        'an uploaded pin; staged to p/q/u/<sha256> by the stage hook (not on this replica)')
    for label,pin in (('depth encoder copy weights',depth['encoder_copy']['weights']),('depth head weights',depth['weights'])):
        row(label,'carrier_c1.py:714-716 load_file(pinned(pin))',relocated(pin),None,'not a staged pin: the literal path, which the job script joins and binds (kit staging map, extra)')
out('PLACEHOLDERS',sorted(h[:12] for h in placeholder))
for r in rows:out('LOAD',r)
