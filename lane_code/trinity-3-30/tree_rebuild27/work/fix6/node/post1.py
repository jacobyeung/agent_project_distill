"""Early census publish for a scratch walk: as soon as the bound config of a continuation run exists,
lay out a scratch node folder and run the kit entry's census publish on it, while the forward
goes on elsewhere. Defect finding only; every output stays in scratch."""
import importlib, json, os, sys, time
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74')
tbm = importlib.import_module(hx('7472616365') + 'back'); TBA = '__' + hx('7472616365') + 'back__'
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
KIT = Path(os.environ['Q_KIT']).resolve()
SRC = Path(sys.argv[1]).resolve(); DST = Path(sys.argv[2]).resolve(); TAG = sys.argv[3] if len(sys.argv) > 3 else ''
sys.path.insert(0, str(KIT / 'b')); sys.path.insert(0, str(OLD / 's')); sys.path.insert(0, str(KIT / 'b'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned, write, file_pin = prov.load, prov.pinned, prov.write, prov.file_pin
pers = mod(PK + '.r1_persisted')


def ev(kind, **kw):
    print('EV ' + json.dumps(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), kind=kind, **kw), default=str), flush=True)


request = load(NS / 'r.json'); paths = request.pop('_paths')
config = file_pin(SRC / 'p/q' / ('h' + TAG) / 'config.json')
DST.mkdir(mode=0o700); (DST / 'p').mkdir(mode=0o700); (DST / 'p/q').mkdir(mode=0o700)
for name in ('s', 'i', 'plan.json'):
    os.symlink(OLD / name, DST / 'p' / name)
for name in ('u', 'ss.json'):
    os.symlink(OQ / name, DST / 'p/q' / name)
for name in ('r.json', 'n.json', 'rooms.json'):
    (DST / name).write_bytes((NS / name).read_bytes())
# the census publish reads one field of the host record: the plan the job copied its inputs by
write(DST / 'p/q/host.json', dict(provisional=True, stager='hook', staging_plan_sha256=request['staging']['sha256']))
ev('LAYOUT', dst=str(DST), config=config)
started = time.time()
try:
    with pers.scope(paths):
        from cs import publish
        pin = publish(KIT, DST, load(pinned(config)), os.environ['SLURM_JOB_ID'])
    ev('DONE', step='cs.publish', pin=pin, seconds=round(time.time() - started, 1))
except BaseException as error:
    ev('ERROR', step='cs.publish', seconds=round(time.time() - started, 1), error=(type(error).__name__ + ':' + str(error))[:3000],
       tb=''.join(tbm.format_exception(type(error), error, getattr(error, TBA)))[-14000:])
    raise SystemExit(1)
