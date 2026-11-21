"""fix11 held-node test (read-only on the job folder and fix6's scratch): tree rules and the frame audit
on a sample of kept rows of every stream, under the fixed mapping or the 174134 mapping (control)."""
import hashlib, json, os, sys, time, sqlite3
from pathlib import Path
mode, out = sys.argv[1], Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, '/tmp/q_22c714e1/p/s'); sys.path.insert(0, '/tmp/a15_f11_174134/b')
import pf
import importlib
PK = bytes.fromhex('73747564656e745f70696c6f74').decode()
FrameAudit = importlib.import_module(PK + '.s1_admission').FrameAudit
resolve_read = importlib.import_module(PK + '.orchard_paths').resolve_read
from launch_r1.entry import temporary_paths
X = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b'
H = [hashlib.sha256(s.encode()).hexdigest() for s in (X + '/data2root', X + '/u/4d66fc2a/f')]
NS = Path('/tmp/jjyeung/q_22c714e1' if mode == 'fixed' else '/tmp/q_22c714e1'); q = NS / 'p/q'
roots = [str(q / 'f' / h) for h in H]
res = dict(mode=mode, utc=time.strftime('%H:%M:%SZ', time.gmtime()), map=os.environ.get('Q_E4'), roots=roots)
jr = None
for cand in ('/tmp/q_22c714e1/p/q/p/request.json',):
    if Path(cand).is_file():
        jr = json.loads(Path(cand).read_text()); res['job_request'] = dict(path=cand, frame_roots=jr.get('frame_roots'), frame_root_map=jr.get('frame_root_map'))
if mode == 'control' and jr:
    res['control_equals_174134'] = dict(roots=jr.get('frame_roots') == roots, map=jr.get('frame_root_map') == os.environ.get('Q_E4'))
def run(name, f):
    try:
        res[name] = dict(result='PASS', value=f())
    except Exception as e:
        res[name] = dict(result='REFUSE', error=type(e).__name__ + ': ' + str(e)[:400])
run('rule_begin_host_temporary_paths', lambda: temporary_paths(dict(frame_roots=roots), q))
target = json.loads(os.environ['Q_E4'])['/data2']
run('rule_resolve_read_map', lambda: str(resolve_read('/data2/k6tk/f2/f25faedce4622416aed654d13ed347ed2a3b1ea0928a5674a80169324c6888cc.png')))
res['map_target_is_a_root'] = any(Path(target).resolve() == Path(r).resolve() for r in roots)
cfg = json.loads((q / 'n.json').read_text())
run('preflight_pf_frames', lambda: pf.frames(cfg, roots))
# kept rows: the prepared receipt of fix6's n2 prepare phase (the tree's own prepare output)
base = Path('/tmp/a15_dbg_174134/n2/p/q/p'); pc = None
for p in sorted(base.rglob('config.json')) if base.is_dir() else []:
    if hashlib.sha256(p.read_bytes()).hexdigest().startswith('d6e38836'):
        pc = p; break
res['prepared_config'] = str(pc)
if pc:
    pcfg = json.loads(pc.read_text()); receipt = json.loads(Path(pcfg['preparation']['path']).read_text())
    K = int(os.environ.get('NSAMPLE', '400'))
    audit = FrameAudit(out / 'fa', roots, sample_size=8) if (out / 'fa').mkdir(exist_ok=True) is None else None
    per = {}
    def sample(label, database, indices):
        idx = sorted(indices); step = max(1, len(idx) // K); pick = idx[::step][:K] + idx[-1:]
        db = Path(database['path'])
        with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as c:
            rows = [json.loads(t) for (i, t) in c.execute('SELECT i,row FROM rows WHERE i IN (%s)' % ','.join(map(str, sorted(set(pick)))))]
        ok, bad, first = 0, 0, None
        from collections import Counter
        prefixes = Counter('/'.join(f['path'].split('/')[:3]) for row in rows for f in (row.get(bytes.fromhex('73747564656e745f696e707574').decode(), {}).get('frames') or []))
        for row in rows:
            try:
                audit.keep(row, label); ok += 1
            except ValueError as e:
                bad += 1; first = first or str(e)[:300]
        per[label] = dict(kept_rows=len(idx), sampled=len(rows), passed=ok, refused=bad, first_refusal=first, pin_prefixes=dict(prefixes))
    for name, value in receipt['streams'].items():
        if value.get('kind') == 'mix':
            order = json.loads(Path(value['order']['path']).read_text())
            for n, part in enumerate(value['sources']):
                if part['kind'] == 'rows':
                    sample(f'{name}/{n}', part['database'], [i for s, i in order if s == n])
                else:
                    per[f'{name}/{n}'] = dict(skipped=part['kind'])
        elif value.get('kind') == 'mdg':
            per[name] = dict(skipped='mdg')
        else:
            ind = json.loads(Path(value['indices']['path']).read_text()) if value.get('indices') else list(range(value['count']))
            sample(name, value['database'], ind)
    res['frame_audit_sample'] = per
    if all(v.get('refused', 0) == 0 for v in per.values()):
        run('frame_audit_finish_hash_sample', lambda: {k: dict(rows=v['rows'], unique=v['unique_frames'], hashed=len(v['hash_sample'])) for k, v in audit.finish()['sources'].items()})
    audit.close()
(out / 'result.json').write_text(json.dumps(res, indent=1, default=str))
print('RESULT ' + json.dumps(res, default=str)[:6000])
