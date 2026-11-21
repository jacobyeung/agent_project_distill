"""Lays out a scratch node folder for the kit's receipt scripts while the forward of the scratch
walk is running in another process: bound config and loader audit from the walk, the host record
finished by the tree's finish_host, the forward marked as running. Defect finding only."""
import importlib, json, os, sys, time
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74')
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
KIT = Path(os.environ['Q_KIT']).resolve()
SRC = Path(sys.argv[1]).resolve(); DST = Path(sys.argv[2]).resolve(); TAG = sys.argv[3]; EARLY = Path(sys.argv[4])
sys.path.insert(0, str(KIT / 'b')); sys.path.insert(0, str(OLD / 's')); sys.path.insert(0, str(KIT / 'b'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned, write, file_pin = prov.load, prov.pinned, prov.write, prov.file_pin
pers = mod(PK + '.r1_persisted'); entry = mod('launch_r1.entry')


def ev(kind, **kw):
    print('EV ' + json.dumps(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), kind=kind, **kw), default=str), flush=True)


request = load(NS / 'r.json'); paths = request.pop('_paths')
old_result = load(OQ / 'RESULT.json')
Q2 = SRC / 'p/q'
config = file_pin(Q2 / ('h' + TAG) / 'config.json')
audit = load(Q2 / ('a' + TAG) / 'RESULT.json')
DST.mkdir(mode=0o700); (DST / 'p').mkdir(mode=0o700); ROOT = DST / 'p/q'; ROOT.mkdir(mode=0o700)
for name in ('s', 'i', 'plan.json'):
    os.symlink(OLD / name, DST / 'p' / name)
for name in ('u', 'ss.json'):
    os.symlink(OQ / name, ROOT / name)
for name in ('b', 'h', 'a'):
    os.symlink(Q2 / (name + TAG), ROOT / name)
os.symlink(Q2 / 'p', ROOT / 'p')
records = Q2 / 'f.json'
if records.is_file():
    (ROOT / 'f.json').write_bytes(records.read_bytes())
for name in ('r.json', 'n.json', 'rooms.json'):
    (DST / name).write_bytes((NS / name).read_bytes())
if (EARLY / 'c5.json').is_file():
    (DST / 'c5.json').write_bytes((EARLY / 'c5.json').read_bytes())
    ev('REUSE', step='cs.publish', what='census receipt of the diagnose-mode publish copied', of=str(EARLY))
host = dict(status='FAIL', config_identity=None, assertions={k: True for k in entry.ASSERTIONS}, missing=[],
            loader_audit={'complete': False}, carried_over_from='174134', stager='hook', staging_plan_sha256=request['staging']['sha256'])
host['assertions']['directory_modes'] = False
with pers.scope(paths), pers.proof_scope(), pers.scope({p['sha256']: p['path'] for p in old_result['staged']}):
    cfg = load(pinned(config))
    entry.finish_host(cfg, ROOT, host, audit, named_refusals=True)
write(ROOT / 'host.json', host)
done = len(json.loads(records.read_text())['records']) if records.is_file() else 0
result = dict(status='ADMIT', GO=False, steps=[*old_result['steps'], 's1_admission.prepare', 'r1_population.bind_prepared', 'persisted_handover',
                                                'r1_loader.production_audit'],
              config=config, init_milestone=400, absolute_resume_step=0, audit=audit, host_receipt=file_pin(ROOT / 'host.json'),
              forward='running in another scratch process when this layout was made; records so far: %d' % done,
              scratch_layout=True, continuation_of='174134')
write(ROOT / 'RESULT.json', result)
ev('LAYOUT', dst=str(DST), config=config, host_status=host['status'], forward_records=done, census_receipt=(DST / 'c5.json').is_file())
