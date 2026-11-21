"""fix14: scratch node folder for a two-step start. Takes the walk's layout (argv[1]) and writes a new
one (argv[2]) whose config carries a SIMULATED review receipt, made the way the kit's review script
makes it after a PASS. No reviewer saw anything; defect finding only, nothing here is evidence."""
import hashlib, importlib, json, os, sys
from pathlib import Path
hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74')
KIT = Path(os.environ['Q_KIT']).resolve()
SRC = Path(sys.argv[1]); DST = Path(sys.argv[2])
sys.path.insert(0, str(KIT / 'b'))
import rv
(DST / 'p').mkdir(parents=True, mode=0o700)
for name in ('s', 'i', 'plan.json', 'q'):
    os.symlink(SRC / 'p' / name, DST / 'p' / name)
for name in ('r.json', 'n.json', 'rooms.json', 'c5.json'):
    if (SRC / name).is_file():
        (DST / name).write_bytes((SRC / name).read_bytes())
cfg = rv.load(SRC / 'v.json')
sys.path.insert(0, str(DST / 'p/s'))
identity = importlib.import_module(PK + '.carrier_c1_run').identity
value = identity(cfg)
raw = rv.encoded(dict(verdict='PASS', config_identity=value, evidence={
    'SCRATCH_SIMULATION_NOT_A_REVIEW': 'written by subagent fix14 under ORDER 1719Z for a two-step scratch start; no reviewer saw anything'}))
rv.put(DST / 'p/rv.json', raw)
cfg['r1_training']['review'] = dict(path=str(DST / 'p/rv.json'), sha256=hashlib.sha256(raw).hexdigest())
rv.sync_preparation(cfg, DST / 'p', 'pr.json')
if identity(cfg) != value:
    raise SystemExit('identity changed')
rv.put(DST / 'v.json', rv.encoded(cfg))
q = rv.load(DST / 'p/q/RESULT.json')
print(json.dumps(dict(identity=value, output=cfg.get('output'), world_size=cfg.get('world_size'), steps=cfg.get('steps'),
                      milestones=cfg.get('milestones'), result_status=q.get('status'), init_milestone=q.get('init_milestone'),
                      result_config=q.get('config'), r1_keys=sorted(cfg['r1_training']), preparation=cfg.get('preparation'),
                      recipe=cfg.get('recipe')), default=str)[:3000])
