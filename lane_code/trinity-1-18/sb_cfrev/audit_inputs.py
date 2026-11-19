from pathlib import Path
import collections, hashlib, importlib.util, io, json, tarfile

ROOT = Path(__file__).resolve().parent
OUT3 = Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3')
KBOX = Path('/scratch/jjyeung/orch_n30/sb_kbox4')
K1 = Path('/scratch/jjyeung/k1/run_convert_2')
pins = {}
def read(p):
    p = Path(p)
    b = p.read_bytes()
    pins[str(p)] = hashlib.sha256(b).hexdigest()
    return b
def load(p):
    return json.loads(read(p))
read(__file__)
module = ROOT/'work/orig/src/b/heads/selector/sl118/selector_inputs.py'
read(module)
spec = importlib.util.spec_from_file_location('audit_selector_inputs', module)
SI = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SI)
ip, lo, hi = (SI.FIELDS.index(k) for k in ('sam_presence_members', 'presence_min', 'presence_max'))
reads = {
    'A4/read0': (200, OUT3/'A4/ret/metadata/reads/0/metadata/journals'),
    'B5/read0': (200, OUT3/'B5/ret/metadata/reads/0/metadata/journals'),
    'b1/read0': (544, OUT3/'bases/b1/work/ret/metadata/reads/0/metadata/journals'),
    'b1/read1': (544, OUT3/'bases/b1/work/ret/metadata/reads/1/metadata/journals'),
    'b2/read0': (544, OUT3/'bases/b2/work/ret/metadata/reads/0/metadata/journals'),
}
journals = {}
for label, (step, folder) in reads.items():
    c = collections.Counter()
    fields = set()
    paths = sorted(folder.glob('*/*/items.jsonl'))
    for p in paths:
        for line in read(p).splitlines():
            item = json.loads(line)
            c['items'] += 1
            for call in ((item.get('output') or {}).get('calls') or {}).get('records') or []:
                c['family_'+str(call.get('family'))] += 1
                s = call.get('stage1') or {}
                if call.get('family') != 'ground' or 'sam3' not in s:
                    continue
                c['pools'] += 1
                fields.update(s['sam3'])
                c['frames_nonempty'] += sum(x > 0 for x in s['sam3']['kept_per_frame'])
                c['frames_multi'] += sum(x > 1 for x in s['sam3']['kept_per_frame'])
                for cand in s['candidates']:
                    x = cand['inputs']
                    c['candidates'] += 1
                    c['outside_range'] += not x[lo]-1e-6 <= x[ip] <= x[hi]+1e-6
                    if len(cand['frames']) == 1:
                        c['single_member'] += 1
                        c['single_mismatch'] += max(abs(x[ip]-x[lo]), abs(x[ip]-x[hi])) > 1e-6
    journals[label] = dict(step=step, root=str(folder), files=[str(p) for p in paths],
                           status='OK' if paths else 'MISSING', counts=dict(c), sam_fields=sorted(fields),
                           mixed_frames='NOT_DIRECTLY_OBSERVED', mixed_frames_from_code=0)
    print(label, len(paths), dict(c), flush=True)

rowset = Path('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt')
ids = set(read(rowset).decode().splitlines())
manifest = load(KBOX/'pinned_train.json')
totals = collections.Counter()
sample = []
for cap in manifest['captures']:
    rows = [r for r in cap['rows'] if r['id'] in ids]
    if not rows:
        continue
    names = {n for row in rows for n in row['operands']}
    key = hashlib.sha256(json.dumps(cap['canonical'], sort_keys=True, allow_nan=False).encode()).hexdigest()[:16]
    path = K1/key/'candidates.json'
    cache = load(path)
    totals['captures'] += 1
    percache = collections.Counter()
    for fr in cache['frames'].values():
        for rec in fr['phrases'].values():
            percache['records'] += 1
            percache['record_missing_presence'] += 'presence' not in rec
            for inst in rec['instances']:
                percache['instances'] += 1
                percache['instance_has_presence'] += 'presence' in inst
    totals.update(percache)
    if len(sample) < 3:
        sample.append(dict(path=str(path), counts=dict(percache)))
    for name in names:
        totals['names'] += 1
        mixed_names = set()
        for f in cache['frames'].values():
            rec = f['phrases'].get(name)
            if rec is None:
                continue
            entries = sorted(rec['instances'], key=lambda i: -float(i['score']))
            own = [(float(i['score']), float(i.get('source_presence', rec['presence'])), i.get('source_prompt', name)) for i in entries]
            raw = [i for i in own if i[2] == name]
            totals['raw_record_mismatch_frames'] += any(i[1] != float(rec['presence']) for i in raw)
            p = raw[0][1] if raw else float(rec['presence'])
            pools = {'raw': [i for i in raw if i[0]*p >= .05][:30],
                     'merged': [i for i in own if i[0]*i[1] >= .05][:30]}
            pools['merged_lift'] = [i for i in pools['merged'] if i[0] >= .3]
            for label, values in pools.items():
                totals[label+'_frames'] += bool(values)
                totals[label+'_multi'] += len(values) >= 2
                mixed = bool(values) and any(abs(i[1]-values[0][1]) > 1e-6 for i in values[1:])
                totals[label+'_mixed'] += mixed
                totals[label+'_wrong_instances'] += sum(abs(i[1]-values[0][1]) > 1e-6 for i in values[1:]) if values else 0
                if mixed:
                    mixed_names.add(label)
        for label in mixed_names:
            totals[label+'_mixed_names'] += 1

packages = {}
files = ('b/e2e_reader/stage1.py', 'tree/student_pilot/routed_features.py', 'tree/student_pilot/routed_candidates.py')
for name, folder in {'A4':OUT3/'A4', 'B5':OUT3/'B5', 'b1':OUT3/'bases/b1', 'b2':OUT3/'bases/b2'}.items():
    p = folder/'package/0.tgz'
    if p.is_file():
        with tarfile.open(fileobj=io.BytesIO(read(p))) as tar:
            cfg = json.load(tar.extractfile('9.json'))
            hashes = {f:hashlib.sha256(tar.extractfile(f).read()).hexdigest() for f in files}
    else:
        cfg = load(folder/'src/9.json')
        hashes = {f:hashlib.sha256(read(folder/'src'/f)).hexdigest() for f in files}
    packages[name] = dict(code_sha256=hashes, settings={k:v for k,v in cfg.items() if any(w in k for w in ('memo','alias','tile','stage1'))})
step400 = Path('/scratch/jjyeung/step400/ret')
out = dict(input_sha256=pins, journals=journals, k1=dict(totals), stored_sample=sample, packages=packages,
           step400=dict(path=str(step400), status='PRESENT' if step400.exists() else 'MISSING'))
(ROOT/'evidence/input_audit.json').write_text(json.dumps(out, indent=2)+'\n')
print('K1', dict(totals), flush=True)
(ROOT/'STATUS.md').write_text('The journal audit covers A4/read0, B5/read0, b1/read0, b1/read1, and b2/read0. The evidence distinguishes code-inferred zero mixing from measured feature-vector consistency. K1 cache counts, stored-cache key checks, package code hashes, and the missing step-400 path are recorded with input hashes in evidence/input_audit.json. Patch-only K1 parity remains in progress.\n')
