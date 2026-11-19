"""CPU-only v2 audit; writes only beside this script. No source scripts run their mutation code."""
import ast, collections, contextlib, gzip, hashlib, io, json, math, re, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = Path('/scratch/jjyeung/orch_n30/sb_harev/out')
PACK = Path('/scratch/jjyeung/n30_mirror/sb_headacc2/pack')
ROWSETS = PACK.parent / 'K1_ROWSETS'
INPUTS, RESULTS = {}, []
CMD = 'OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /usr/bin/python3 out/recompute.py'

# Reuse the prior audit's functions without executing its old findings or side effects.
old_bytes = (OLD / 'recompute.py').read_bytes()
module = ast.parse(old_bytes)
helpers = ast.Module(body=[n for n in module.body if isinstance(n, ast.FunctionDef)], type_ignores=[])
exec(compile(helpers, str(OLD / 'recompute.py'), 'exec'), globals())
INPUTS[str(OLD / 'recompute.py')] = dict(sha256=hashlib.sha256(old_bytes).hexdigest(), bytes=len(old_bytes))

def raw(path):
    p = Path(path)
    assert str(p.resolve()).startswith('/scratch/'), p
    b = p.read_bytes()
    INPUTS[str(p)] = dict(sha256=hashlib.sha256(b).hexdigest(), bytes=len(b))
    return b

def jgz(path):
    return [json.loads(s) for s in gzip.decompress(raw(path)).splitlines() if s.strip()]

def add(name, values, method, status='VERIFIED'):
    result(name, status, values, [], method)

for p in sorted((ROOT / 'inputs').glob('*.md')):
    read(p)
add('reviewed design identity', dict(advertised_prefix='6ed2e786', actual=INPUTS[str(ROOT / 'inputs/HEAD_ACCURACY_DESIGN_20261119.md')]['sha256'], matches_advertised=False), 'Hash the once-copied NFS snapshot; do not fetch a moving file again.', 'PIN-MISMATCH')
prior = js(OLD / 'RECOMPUTE.json')
read(OLD / 'REVIEW_VERDICT.md')
read(OLD.parent / 'inputs/E2E_READER_B04_20261116.md')

manifest = read(PACK / 'MANIFEST.sha256')
checks = []
for line in manifest.splitlines():
    expected, rel = line.split(maxsplit=1)
    p = PACK / rel
    data = raw(p)
    checks.append(dict(path=rel, bytes=len(data), sha256=INPUTS[str(p)]['sha256'], matches=hashlib.sha256(data).hexdigest() == expected))
add('pack_manifest', dict(files=len(checks), bytes=sum(r['bytes'] for r in checks), mismatches=[r for r in checks if not r['matches']]), 'Hash every manifest member locally; never open its original NFS path.')

source_pins = []
for line in read(PACK / 'R1_A4_SRC_SHA256.txt').splitlines():
    expected, rel = line.split(maxsplit=1)
    p = PACK / 'r1_src' / rel
    if p.is_file():
        b = raw(p)
        source_pins.append(dict(path=rel, status='MATCH' if hashlib.sha256(b).hexdigest() == expected else 'MISMATCH'))
    else:
        source_pins.append(dict(path=rel, status='UNVERIFIABLE-HERE'))
add('R1 source copies', dict(counts=dict(collections.Counter(x['status'] for x in source_pins)), files=source_pins), 'Check staged files against original source manifest. An unstaged remote file is UNVERIFIABLE-HERE, not missing.')

lp = Path('/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl')
mp = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
gp = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets/GT_SET_PRIMARY_296.json')
labs = jl(lp); lab = {r['id']: r for r in labs}
man = js(mp); reg = js(gp)
caps = {c['canonical']: c for c in man['captures']}
table_dir = Path('/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/data/caps_raw')
table_names = sorted(p.name for p in table_dir.iterdir())
listing = '\n'.join(table_names)
INPUTS[str(table_dir) + '/ [directory names only]'] = dict(sha256=hashlib.sha256(listing.encode()).hexdigest(), names=table_names)
table_caps = {f[:-8].replace('__', '/', 1) for f in table_names}
sets = {}; counts = {}
boxspec = read(ROOT / 'inputs/KIT_SPEC_box_ladder_k1_v2.md')
for p in sorted(ROWSETS.glob('*.txt')):
    content = read(p); ids = content.splitlines(); sets[p.name] = set(ids)
    is_cap = 'CAPTURES' in p.name
    cc = set(ids) if is_cap else {lab[i]['capture'] for i in ids}
    split = 'heldout' if 'HELDOUT' in p.name else 'train'
    expected = {c for c in reg if caps[c]['k1_split'] == split} if is_cap else {r['id'] for r in labs if r['split'] == split and r['capture'] in reg}
    if 'TABLES' in p.name:
        expected = {i for i in expected if lab[i]['capture'] in table_caps}
    counts[p.name] = dict(rows=len(ids), unique=len(set(ids)), captures=len(cc), rooms=len({caps[c]['room'] for c in cc}), sha256=INPUTS[str(p)]['sha256'], matches_registry=expected == set(ids), sorted_unique=ids == sorted(set(ids)), hash_in_spec=INPUTS[str(p)]['sha256'] in boxspec if not is_cap else None)
exc = js(ROWSETS / 'K1_EXCLUSIONS.json')
add('K1 rowsets', counts, 'Hash original bytes (no trailing-newline normalization), count splitlines, join each id to corrected labels and capture manifest, intersect PRIMARY_296 and raw-table filenames.')
add('K1 exclusions and intersections', dict(excluded_rows=len(exc), excluded_by_capture=dict(collections.Counter(r['capture'] for r in exc)), excluded_match={r['id'] for r in exc} == {r['id'] for r in labs if r['capture'] not in reg}, train_heldout_overlap=len(sets['K1_TRAIN_1037.txt'] & sets['K1_HELDOUT_216.txt']), capture_registry_count=len(reg), manifest_count=len(caps), missing_table_train_captures=counts['K1_TRAIN_1037.txt']['captures']-counts['K1_TRAIN_TABLES_883.txt']['captures']), 'Set equality and intersections, without constructing substitute rows.')

# Reuse the designer parser only after hashing its source and all its inputs; it prints but writes nothing.
designer = PACK / 'tools/recompute_designer_reads.py'
src = read(designer)
saved_argv = sys.argv; sys.argv = [str(designer), str(PACK)]
stdout = io.StringIO(); ns = {'__name__': '__audit__'}
with contextlib.redirect_stdout(stdout):
    exec(compile(src, str(designer), 'exec'), ns)
sys.argv = saved_argv
(ROOT / 'out/DESIGNER_READS.log').write_text(stdout.getvalue())
summary = {}
for step in (544, 200):
    rows = ns['gaps'](step)
    objs = [o for r in rows for o in r['objs'].values()]
    bands = {}
    for band, pred in [('frames_under3', lambda r:min(o['nfr'] for o in r['objs'].values())<3), ('margin_under1', lambda r:any(o['margin'] is not None and o['margin']<1 for o in r['objs'].values())), ('truth_under1m', lambda r:r['truth']<1)]:
        rr = [r for r in rows if pred(r)]; other = [r for r in rows if not pred(r)]
        bands[band] = dict(n=len(rr), mra=100*statistics.mean(r['s'] for r in rr), other_n=len(other), other_mra=100*statistics.mean(r['s'] for r in other), overestimated=sum(r['gap']>r['truth'] for r in rr))
    summary[str(step)] = dict(n=len(rows), mra=100*statistics.mean(r['s'] for r in rows), bands=bands, operands=len(objs), chosen_frames_median=statistics.median(o['nfr'] for o in objs), proposed_frames_median=statistics.median(o['sam_frames'] for o in objs), singleton_operands=sum(o['nfr']==1 for o in objs), candidate_count_bands=[sum(o['ncand']==1 for o in objs),sum(1<o['ncand']<=3 for o in objs),sum(o['ncand']>=4 for o in objs)])
add('gap diagnostics', summary, 'Run the staged diagnostic parser on hashed per-item traces; reaggregate its returned rows, not copied summary tables.')

camera = jgz(PACK / 'ROUTED_544_devS1.jsonl.gz'); cam = {}
for typ in ['camera_displacement', 'camera_rotation']:
    rr = [r for r in camera if r['type'] == typ]
    low = [r for r in rr if (float(r['gt']) <= .25 if typ == 'camera_displacement' else abs(float(r['gt'])) < 5)]
    cam[typ] = dict(n=len(rr), score=100*statistics.mean(r['score'] for r in rr), median_abs_error=statistics.median(abs(float(r['answer'])-float(r['gt'])) for r in rr), low_n=len(low), low_score=100*statistics.mean(r['score'] for r in low), low_loss_share=sum(1-r['score'] for r in low)/sum(1-r['score'] for r in rr))
add('camera diagnostics', cam, 'Aggregate staged per-item scores, truths and model answers; this verifies correlations, not a causal noise floor.')

r0 = jl('/scratch/jjyeung/orch_n30/b10_reserve/out/qsets/R0_QUESTIONS_dev_f32.jsonl')
direct = jgz(PACK / 'DIRECT_R1_200_R0dev.jsonl.gz')
dt = {}
for typ in sorted({r['type'] for r in direct}):
    rr = [r for r in direct if r['type']==typ]
    dt[typ] = dict(n=len(rr), score=100*statistics.mean(r['score'] for r in rr))
relrows = [r for r in direct if r['type']=='object_rel_distance']
parses = [re.search(r'nearest-to-farthest order from (.+?) is: (.+?)\.\s', r['text'].replace('\n',' ')+' ') for r in relrows]
add('R0 direct and parser', dict(items=len(r0), scenes=len({r['scene'] for r in r0}), direct=dt, join_matches=sum(r0[r['source_line']-1]['qid']==r['qid'] and r0[r['source_line']-1]['question']==r['question'] for r in direct), duplicate_qids={k:v for k,v in collections.Counter(r['qid'] for r in r0).items() if v>1}, rel_parses=sum(m is not None for m in parses), rel_total=len(parses), rel_order_lengths=dict(collections.Counter(len(re.split(r',\s*then\s+|,\s*', m.group(2))) for m in parses if m))), 'Read existing direct records only; no candidate route is scored and no new R0 route look is consumed.')

score_checks = {}
for name, data in [('R0', direct), ('devS1', jgz(PACK / 'DIRECT_R1_200_devS1.jsonl.gz'))]:
    rr = [r for r in data if r['type'] in ('object_counting','object_size_estimation')]
    wrong=[]
    for r in rr:
        try:
            err=abs(float(r['pred'])-float(r['gt_released']))/float(r['gt_released'])
            cs=[.5 + i * ((.95-.5)/9) for i in range(10)]; cs[-1]=.95
            score=sum(err <= 1-c for c in cs)/10
        except (ValueError,TypeError,ZeroDivisionError): score=0.
        if abs(score-r['score'])>1e-10: wrong.append(r['id'])
    score_checks[name]=dict(n=len(rr), mismatches=wrong)
add('numeric scorer parity', score_checks, 'Recreate the ten float64 linspace thresholds and inclusive inequality from O2 section 6; compare to each stored direct score.')
add('size join evidence level', js(PACK / 'designer_evidence/SIZE_BOXHEAD_JOIN.json'), 'This artifact contains rounded aggregate values only, not the 58 item joins. Exploratory qualification is adequate; raw-instance verification remains UNVERIFIABLE-HERE.', 'SOURCE-SUMMARY')

steps = [('tower_A', .5, .75), ('tower_B', 2.5, 3), ('K1_track',1.3,1.75), ('R0_base',3,3.5), ('R0_track',3,3.25), ('R0_94',2.8,3), ('camera_C',.6,.75), ('devS1',2,2), ('devS1_track',1,1)]
scenarios = {}
for mode in ['expected', 'hard_stops']:
    used = 0.; admitted=[]; skipped=[]
    for name, estimate, stop in steps:
        if used + stop <=16:
            admitted.append(name); used += estimate if mode=='expected' else stop
        else: skipped.append(name)
    scenarios[mode] = dict(used=round(used,3), admitted=admitted, skipped=skipped)
add('GPU budget', dict(parts=[dict(name=n, estimate=e, stop=s) for n,e,s in steps], base_expected=sum(e for n,e,s in steps if n not in ['R0_track','R0_94','devS1_track']), all_expected=sum(e for n,e,s in steps), all_stops=sum(s for n,e,s in steps), scenarios=scenarios, paired_reader_read_not_in_ledger=2.5, admitted_expected_plus_reader_read=round(scenarios['expected']['used']+2.5,3)), 'Sum specified GPU-hours and simulate the admission rule sequentially. This does not assert measured runtime or authorization for GPU work.')
add('Inherited old evidence', dict(old_inputs=prior['inputs'], old_results=[r for r in prior['results'] if r['claim'] in ['K1 corrected GT-mask distance: 75.05 deployed, 91.99 GT; Pi3X 73.38, DA3 71.02', 'K1 lift variants: plain 28.6 and hull 39.1', 'Presence 32.9 vs 71.3; GT-presence counting 24.8']]), 'Reuse prior hashed per-item recomputation rather than rerun unchanged pricing reads. Original input hashes and original command are retained.', 'PRIOR-RECOMPUTATION')

out = dict(command=CMD, inputs=INPUTS, results=RESULTS, review_code=dict(path=str(Path(__file__)), sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
(ROOT / 'out/RECOMPUTE.json').write_text(json.dumps(out, indent=2, allow_nan=False)+'\n')
for r in RESULTS:
    if r['claim'] != 'Inherited old evidence':
        print(r['claim'], json.dumps(r['values'])[:3500])
