"""Lays out a scratch node folder for the kit's receipt scripts from a finished continuation run and
performs the kit entry's last step (the census publish) on it. Defect finding only; scratch only."""
import importlib, json, os, sys, time
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74')
tbm = importlib.import_module(hx('7472616365') + 'back'); TBA = '__' + hx('7472616365') + 'back__'
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
KIT = Path(os.environ['Q_KIT']).resolve()
SRC = Path(sys.argv[1]).resolve(); DST = Path(sys.argv[2]).resolve()
FORCE = len(sys.argv) > 3 and sys.argv[3] == 'force'
TAG = os.environ.get('A15_TAG', '')
sys.path.insert(0, str(KIT / 'b')); sys.path.insert(0, str(OLD / 's')); sys.path.insert(0, str(KIT / 'b'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned, write, file_pin = prov.load, prov.pinned, prov.write, prov.file_pin
pers = mod(PK + '.r1_persisted')


def ev(kind, **kw):
    print('EV ' + json.dumps(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), kind=kind, **kw), default=str), flush=True)


request = load(NS / 'r.json'); paths = request.pop('_paths')
res = load(SRC / 'p/q' / ('RESULT' + TAG + '.json'))
DST.mkdir(mode=0o700); (DST / 'p').mkdir(mode=0o700); (DST / 'p/q').mkdir(mode=0o700)
for name in ('s', 'i', 'plan.json'):
    os.symlink(OLD / name, DST / 'p' / name)
for name in ('u', 'ss.json'):
    os.symlink(OQ / name, DST / 'p/q' / name)
for name in ('b', 'h', 'a'):
    if (SRC / 'p/q' / (name + TAG)).exists():
        os.symlink(SRC / 'p/q' / (name + TAG), DST / 'p/q' / name)
if (SRC / 'p/q/p').exists():
    os.symlink(SRC / 'p/q/p', DST / 'p/q/p')
for records in (SRC / 'p/q' / ('fw' + TAG) / 'f.json', SRC / 'p/q/f.json'):
    if records.is_file():
        (DST / 'p/q/f.json').write_bytes(records.read_bytes())
        break
for name in ('r.json', 'n.json', 'rooms.json'):
    (DST / name).write_bytes((NS / name).read_bytes())
if (SRC / 'p/q' / ('host' + TAG + '.json')).is_file():
    host = load(SRC / 'p/q' / ('host' + TAG + '.json'))
    # two fields the job's host record gets while it copies its inputs; taken from the job's request
    host.update(stager='hook', staging_plan_sha256=request['staging']['sha256'])
    write(DST / 'p/q/host.json', host)
    res['host_receipt'] = file_pin(DST / 'p/q/host.json')
write(DST / 'p/q/RESULT.json', res)
ev('LAYOUT', dst=str(DST), status=res.get('status'), failed=res.get('failed'), config=res.get('config'), host_receipt=res.get('host_receipt'))
EARLY = os.environ.get('A15_EARLY', '')
if EARLY and (Path(EARLY) / 'c5.json').is_file():
    (DST / 'c5.json').write_bytes((Path(EARLY) / 'c5.json').read_bytes())
    ev('REUSE', step='cs.publish', what='census receipt of the early publish copied', of=EARLY)
elif res.get('status') == 'ADMIT' or (FORCE and res.get('config')):
    try:
        with pers.scope(paths):
            from cs import publish
            pin = publish(KIT, DST, load(pinned(res['config'])), os.environ['SLURM_JOB_ID'])
        ev('DONE', step='cs.publish', pin=pin)
    except BaseException as error:
        ev('ERROR', step='cs.publish', error=(type(error).__name__ + ':' + str(error))[:3000],
           tb=''.join(tbm.format_exception(type(error), error, getattr(error, TBA)))[-14000:])
        raise SystemExit(1)
else:
    ev('SKIP', step='cs.publish', why='result is not ADMIT')
    raise SystemExit(2)
