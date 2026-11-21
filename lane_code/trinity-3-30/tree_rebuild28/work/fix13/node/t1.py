"""Scratch test of the census fix on the bound preparation (read-only inputs; outputs in scratch only).
usage: t1.py <src run dir> <dst dir> <mode>  mode: fixed = preflight + cs.publish (diagnose: all four
verdicts) + cs._verify armed; control = preflight + base classify on the first pose rows."""
import importlib, json, os, sys, time
from pathlib import Path
hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74')
tbm = importlib.import_module(hx('7472616365') + 'back'); TBA = '__' + hx('7472616365') + 'back__'
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
KIT = Path(os.environ['Q_KIT'])
SRC = Path(sys.argv[1]).resolve(); DST = Path(sys.argv[2]); MODE = sys.argv[3]
sys.path.insert(0, str(OLD / 's')); sys.path.insert(0, str(KIT / 'b'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned, write, file_pin = prov.load, prov.pinned, prov.write, prov.file_pin
pers = mod(PK + '.r1_persisted')
def ev(kind, **kw):
    print('EV ' + json.dumps(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), kind=kind, **kw), default=str), flush=True)
def err(step, error, started):
    ev('ERROR', step=step, seconds=round(time.time() - started, 1), error=(type(error).__name__ + ':' + str(error))[:2000],
       tb=''.join(tbm.format_exception(type(error), error, getattr(error, TBA)))[-3000:])
request = load(NS / 'r.json'); paths = request.pop('_paths')
config = file_pin(SRC / 'p/q/hb/config.json')
DST.mkdir(mode=0o700); (DST / 'p').mkdir(mode=0o700); (DST / 'p/q').mkdir(mode=0o700)
for name in ('s', 'i', 'plan.json'):
    os.symlink(OLD / name, DST / 'p' / name)
for name in ('u', 'ss.json'):
    os.symlink(OQ / name, DST / 'p/q' / name)
for name in ('r.json', 'n.json', 'rooms.json'):
    (DST / name).write_bytes((NS / name).read_bytes())
write(DST / 'p/q/host.json', dict(provisional=True, stager='hook', staging_plan_sha256=request['staging']['sha256']))
import cs, sv, pf
ev('LAYOUT', dst=str(DST), config=config, mode=MODE, cs=file_pin(Path(cs.__file__)), sv=file_pin(Path(sv.__file__)), pf=file_pin(Path(pf.__file__)))
with pers.scope(paths):
    cfg = load(pinned(config))
    started = time.time()
    try:
        ev('DONE', step='pf.census preflight', counts=pf.census(cfg), seconds=round(time.time() - started, 1))
    except BaseException as error:
        err('pf.census preflight', error, started)
    if MODE == 'routing':
        started = time.time(); classify = sv.classifier(cfg)
        Rows = mod(PK + '.carrier_c1_run').Rows
        reader = Rows(load(pinned(cfg['preparation'])), None)
        try:
            record, keys = cs.evaluate(cfg, 'routing', cs.final_sources(DST, cfg)['routing'], lambda: (reader.row('routing', i)[0] for i in range(reader.count('routing'))), classify)
            ev('DONE', step='cs.evaluate routing only', counts=record['counts'], refusals=record['refusals'][:3], result=record['result'], bytes=len(json.dumps(record)), seconds=round(time.time() - started, 1))
        except BaseException as error:
            err('cs.evaluate routing', error, started)
        finally:
            reader.close()
        raise SystemExit(0)
    if MODE == 'control':
        started = time.time(); classify = sv.classifier(cfg)
        Rows = mod(PK + '.carrier_c1_run').Rows
        reader = Rows(load(pinned(cfg['preparation'])), None)
        try:
            record, keys = cs.evaluate(cfg, 'pose', [], lambda: (reader.row('pose', i)[0] for i in range(2000)), classify)
            ev('DONE', step='cs.evaluate base, first 2000 admitted pose rows (source count not compared)', counts=record['counts'], refusals=record['refusals'][:3], seconds=round(time.time() - started, 1))
        except BaseException as error:
            err('cs.evaluate base', error, started)
        finally:
            reader.close()
        raise SystemExit(0)
    original = cs.discovery
    cs.discovery = lambda kit: True
    started = time.time()
    try:
        pin = cs.publish(KIT, DST, cfg, os.environ['SLURM_JOB_ID'])
        ev('DONE', step='cs.publish (diagnose: every stream evaluated)', pin=pin, seconds=round(time.time() - started, 1))
    except BaseException as error:
        err('cs.publish', error, started)
    out = load(DST / 'c5.json') if (DST / 'c5.json').is_file() else {}
    for stream, r in (out.get('streams') or {}).items():
        ev('STREAM', stream=stream, status=r.get('status'), counts=r.get('counts'), refusals=r.get('refusals', [])[:3], result=r.get('result'))
    cs.discovery = original
    started = time.time()
    try:
        ev('DONE', step='cs._verify armed (discovery off)', pin=cs.verify(KIT, DST, cfg), seconds=round(time.time() - started, 1))
    except BaseException as error:
        err('cs.verify', error, started)
