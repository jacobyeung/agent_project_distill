"""fix16 quick test, read-only on the refused run's staged bytes (sandbox layout ro).
argv: <installed kit> <candidate folder> <scratch folder>
A. the candidate's audit_roots on the request's frame roots spelled under the namespace, and its refusals;
B. the preflight frames(): candidate vs installed kit on those roots;
C. the tree's own rules: entry.temporary_paths on the roots (begin_host's rule) and s1_admission.FrameAudit
   keep()/finish() on up to 200 rows with frames per stream source, with and without the candidate's naming."""
import importlib.util, json, sqlite3, sys, time
from pathlib import Path
kit, cand, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
NS, NJ = '/tmp/q_22c714e1', '/tmp/jjyeung/q_22c714e1'
sys.path.insert(0, str(kit / 'b')); sys.path.insert(0, NS + '/p/s')
from z import load
from student_pilot.r1_persisted import scope, relocated
from student_pilot.s1_admission import FrameAudit
from launch_r1.entry import temporary_paths
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
new = module('pf_candidate', cand / 'b/pf.py'); new.__file__ = str(kit / 'b/pf.py')
old = module('pf_installed', kit / 'b/pf.py')
request = load(NS + '/r.json'); cfg = load(NS + '/n.json')
roots_nj = request['frame_roots']; roots_ns = [NS + r[len(NJ):] for r in roots_nj]
print('request frame_roots of the refused run', roots_nj)
print('the same roots spelled under the namespace', roots_ns)
def attempt(label, fn, *args):
    t = time.time()
    try:
        value = fn(*args); print('%s: PASS %.1fs %s' % (label, time.time() - t, json.dumps(value)[:700]), flush=True); return value
    except Exception as error:
        print('%s: REFUSE %.1fs %s:%s' % (label, time.time() - t, type(error).__name__, str(error)[:260]), flush=True)
print('== A audit_roots')
attempt('A1 audit_roots(namespace roots)', new.audit_roots, roots_ns)
name = Path(roots_ns[0]).name
for label, bad in (('A2 the namespace itself', [NS]), ('A3 a missing folder', [NS + '/p/q/f/absent']),
                   ('A4 a root already under the second name', [NJ + '/p/q/f/' + name]), ('A5 a path with ..', [NS + '/p/q/f/../f/' + name]),
                   ('A6 a root outside the namespace', ['/scratch']), ('A7 a file', [NS + '/n.json'])):
    attempt(label, new.audit_roots, bad)
print('== C1 begin_host rule (entry.temporary_paths) with job_tmp', NS + '/p/q')
attempt('C1 namespace roots', temporary_paths, dict(frame_roots=roots_ns), Path(NS + '/p/q'))
attempt('C1 second-name roots (control)', temporary_paths, dict(frame_roots=roots_nj), Path(NS + '/p/q'))
with scope(request['_paths']):
    print('== B preflight frames()')
    attempt('B1 candidate, namespace roots', new.frames, cfg, roots_ns)
    attempt('B2 installed kit, namespace roots (control)', old.frames, cfg, roots_ns)
    attempt('B3 installed kit, second-name roots (the refused run)', old.frames, cfg, roots_nj)
    print('== C2 tree FrameAudit on rows with frames')
    def read(pin): return json.loads(Path(relocated(pin)).read_text())
    sources = []
    for stream, pin in sorted(cfg['streams'].items()):
        value = read(pin)
        if value.get('schema') == 'c1-pose-mix-v1':
            sources += [(stream + '/' + str(i), part['receipt'], part.get('frame_prefix')) for i, part in enumerate(value['sources']) if part.get('kind') == 'rows']
        else:
            sources.append((stream, pin, None))
    rows = {}
    for label, pin, prefix in sources:
        database = Path(relocated(read(pin)['database'])); kept = []
        with sqlite3.connect(database.as_uri() + '?mode=ro&immutable=1', uri=True) as connection:
            for (text,) in connection.execute('SELECT row FROM rows ORDER BY i LIMIT 20000'):
                row = json.loads(text); found = row.get('student_input', {}).get('frames')
                if (isinstance(found, list) and found and all(isinstance(f, dict) and isinstance(f.get('path'), str) for f in found)
                        and (prefix is None or all(f['path'].startswith(prefix) for f in found))):
                    kept.append(row)
                    if len(kept) == 200: break
        rows[label] = kept
    def audit(label, roots, folder):
        folder.mkdir(parents=True)
        a = FrameAudit(folder, roots, sample_size=8)
        try:
            counts = {}
            for source, kept in rows.items():
                good = 0; first = None
                for row in kept:
                    try: a.keep(row, source); good += 1
                    except ValueError as error:
                        first = first or str(error)[:200]
                counts[source] = '%d/%d' % (good, len(kept)) + ('' if first is None else ' first refusal: ' + first)
            print(label, 'keep:', json.dumps(counts), flush=True)
            try:
                report = a.finish(); print(label, 'finish: PASS roots', report['roots'], 'sources', {k: (v['rows'], v['unique_frames'], len(v['hash_sample'])) for k, v in report['sources'].items()})
            except ValueError as error: print(label, 'finish: REFUSE', str(error)[:200])
        finally: a.close()
    audit('C2a candidate naming audit_roots(namespace roots)', new.audit_roots(roots_ns), out / 'fa_candidate')
    audit('C2b namespace roots as the request names them (control)', roots_ns, out / 'fa_control')
print('done')
