"""Attribute failures and report bounded CPU validation with input hashes."""
import collections, hashlib, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'out'
PREFIX='env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B '
COMMAND=PREFIX+'work/summarize.py'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(name):return json.loads((OUT/(name+'.json')).read_text())
def put(name,obj):
    obj['command']=COMMAND;obj.setdefault('inputs_sha256',{})[str(Path(__file__))]=sha(__file__)
    (OUT/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
labels=['must_final_'+t for t in ('base','patch_a','new','live')]
labels += [g+'_'+t for g in ('subset','focused','integration','real_declared') for t in ('base','new','live')]
labels += ['host_live_base','host_live','host_ref_live_base','host_ref_live','camform_regression','full_base','full_new','full_live']
runs={n:read(n) for n in labels}
inputs={str(OUT/(n+'.json')):sha(OUT/(n+'.json')) for n in labels}
BAD={'FAIL','ERROR','SUBTEST_FAILURE','UNEXPECTED_SUCCESS'}
def failures(r):return [x for x in r['outcomes'] if x['status'] in BAD]
def key(x):return re.sub(r"(\w+)=['\"]/[^'\"]*['\"]",r"\1='<absolute-path>'",x['test'])
def normalize(s):
    s=re.sub(re.escape(str(ROOT))+r'/work/test_runs/[^/\s\'\"]+/tmp/[^/\s\'\"]+','<TMP>',s)
    s=re.sub(re.escape(str(ROOT))+r'/work/test_runs/[^/\s\'\"]+','<RUN>',s)
    s=re.sub(re.escape(str(ROOT))+r'/work/(?:base|new|live_base|live|new_camform)(?=/|\b)','<TREE>',s)
    s=re.sub(r'(\.pruned_step_\d+_)[0-9a-f]{32}',r'\1<TEMP_UUID>',s)
    s=re.sub(r'(/tmp/headcall_test_cache/hcfull_frames_)[a-z0-9_]{8}',r'\1<TEMP_SUFFIX>',s)
    return s
def cause(x):
    trace=x.get('traceback','');lines=[l.strip() for l in trace.splitlines() if l.strip()]
    exceptions=[l for l in lines if re.match(r'(?:[\w.]+(?:Error|Exception)|AssertionError):',l)]
    last=exceptions[-1] if exceptions else lines[-1] if lines else x['status']
    if 'CPU_TEST_WORKERS_UNAVAILABLE' in trace:category='WORKER_PROCESSES_UNAVAILABLE'
    elif any(k in trace for k in ('FORBIDDEN:','OUTSIDE_WRITE:','NFS_READ:')):category='DISPATCH_RESTRICTION'
    elif any(k in trace for k in ('FileNotFoundError:','ModuleNotFoundError:','PackageNotFoundError:')):category='MISSING'
    elif 'Missing or changed pinned input:' in trace:category='MISSING_OR_CHANGED_PIN'
    elif 'KeyError:' in trace:category='FIXTURE_FIELD_OR_ENVIRONMENT'
    else:category='EXISTING_TEST_OR_FIXTURE_FAILURE'
    paths=sorted(set(re.findall(r"FileNotFoundError:.*?: '([^']+)'",trace)+re.findall(r'Missing or changed pinned input: ([^\n\"]+)',trace)))
    return dict(category=category,cause=last,normalized_cause=normalize(last),paths=paths)
comparisons={}
def harness_core(run):
    h=run['inputs_sha256'][str(ROOT/'work/run_tests.py')]
    p=ROOT/'work/run_tests.py'
    if sha(p)!=h:p=ROOT/'work/harness_snapshots'/(h+'.py')
    assert sha(p)==h
    inputs[str(p)]=h
    source=re.sub(r'^# OPTIONAL_LIVE_BASE_BEGIN\n.*?^# OPTIONAL_LIVE_BASE_END\n','',p.read_text(),flags=re.M|re.S)
    return hashlib.sha256(source.encode()).hexdigest()
pairs=[('focused_base','focused_new'),('focused_base','focused_live'),('integration_base','integration_new'),('integration_base','integration_live'),('full_base','full_new'),('full_base','full_live'),('host_live_base','host_live'),('host_ref_live_base','host_ref_live')]
for a,b in pairs:
    old=collections.defaultdict(list);new=collections.defaultdict(list)
    for x in failures(runs[a]):old[(key(x),x['status'])].append(cause(x))
    for x in failures(runs[b]):new[(key(x),x['status'])].append(cause(x))
    new_failures=[];changed=[];resolved=[]
    for k in set(old)|set(new):
        aa=old[k];bb=new[k]
        if len(bb)>len(aa):new_failures.append(dict(test=k[0],status=k[1],base_count=len(aa),new_count=len(bb)))
        if len(bb)<len(aa):resolved.append(dict(test=k[0],base_count=len(aa),new_count=len(bb)))
        if aa and bb and collections.Counter(c['normalized_cause'] for c in aa)!=collections.Counter(c['normalized_cause'] for c in bb):
            changed.append(dict(test=k[0],base=aa,new=bb))
    comparisons[a+'__'+b]=dict(new_failures=new_failures,changed_causes=changed,resolved=resolved,
        identical_failure_counts_and_causes=not(new_failures or changed or resolved),
        base_harness_sha256=runs[a]['inputs_sha256'].get(str(ROOT/'work/run_tests.py')),
        new_harness_sha256=runs[b]['inputs_sha256'].get(str(ROOT/'work/run_tests.py')),
        base_execution_core_sha256=harness_core(runs[a]),new_execution_core_sha256=harness_core(runs[b]))
    if a=='full_base':
        assert comparisons[a+'__'+b]['base_execution_core_sha256']==comparisons[a+'__'+b]['new_execution_core_sha256']
base_reports={}
for name in ('focused_base','integration_base','real_declared_base','full_base','host_live_base'):
    entries=[dict(x,**cause(x)) for x in failures(runs[name])]
    base_reports[name]=dict(counts={k:runs[name][k] for k in ('tests','failures','errors','skipped')},causes=dict(collections.Counter(x['category'] for x in entries)),failures=entries)
put('BASE_FAILURES',dict(inputs_sha256=inputs,runs=base_reports,comparisons=comparisons))
missing=collections.defaultdict(list);dependencies=collections.defaultdict(list)
for label,run in runs.items():
    for x in failures(run):
        why=cause(x)
        for p in why['paths']:missing[p].append(dict(run=label,test=x['test'],cause=why['cause']))
        for match in re.findall(r"No module named '([^']+)'|No package metadata was found for ([\w.-]+)",x.get('traceback','')):
            dependencies[next(k for k in match if k)].append(dict(run=label,test=x['test']))
coverage_root=ROOT.parent/'ro/n30_mirror/dist_diag/coverage_v2h'
for filename in ('COVERAGE_DISTANCE_V2H.jsonl','COVERAGE_UNITS_V2H.jsonl'):
    missing[str(coverage_root/filename)].append(dict(run='camera_full_six_family',test='validate_binding without coverage-read isolation',cause='MISSING before camera authentication'))
put('MISSING_INPUTS',dict(status='MISSING',inputs_sha256=inputs,
    paths=[dict(path=p,status='MISSING' if not p.startswith(('/home','/data')) and not Path(p).is_file() else 'UNAVAILABLE_OR_REFUSED',affected=v) for p,v in sorted(missing.items())],
    dependencies=[dict(name=k,status='MISSING',expected_interpreter='/scratch/jjyeung/envs/p1cpu/bin/python',affected=v) for k,v in sorted(dependencies.items())],
    review_gate_manifest=dict(status='MISSING',name='32-module gate set',expected_location='No manifest path was supplied; no module list was invented',fallback='All locally available tree test modules were attempted'),
    review_source_names_corpus=dict(status='MISSING',name='Original 1,280-case review corpus',expected_location='No corpus file path was supplied',fallback='Explicit 256-subset x five-config matrix in work/support/patch_a2_checks.py')))
summaries={}
for n,r in runs.items():
    bad=failures(r)
    status='PASS' if r['successful'] else 'MISSING' if any(cause(x)['category'] in ('MISSING','MISSING_OR_CHANGED_PIN') for x in bad) else 'FAIL'
    summaries[n]=dict(status=status,**{k:r[k] for k in ('tests','failures','errors','skipped','command')},report=str(OUT/(n+'.json')),report_sha256=sha(OUT/(n+'.json')),module_or_selector_count=len(r['names']))
gates={n:dict(request='full tree discovery',modules=runs[n]['names'],module_count=len(runs[n]['names'])) for n in ('full_base','full_new','full_live')}
host_coverage={}
for tree,initial,reference in (('live_base','host_live_base','host_ref_live_base'),('live','host_live','host_ref_live')):
    outcomes={x['test']:x for x in runs[initial]['outcomes']}
    for x in runs[reference]['outcomes']:
        assert x['test'] in outcomes and outcomes[x['test']]['status']=='SKIP'
        outcomes[x['test']]=x
    host_coverage[tree]=dict(distinct_tests=len(outcomes),statuses=dict(collections.Counter(x['status'] for x in outcomes.values())),
        commands=[runs[n]['command'] for n in (initial,reference)],reports=[str(OUT/(n+'.json')) for n in (initial,reference)],
        scope='Union of host suite and its separate sealed-base byte comparison; each test identity is counted once')
put('TESTS',dict(status='MISSING_INTEGRATION_INPUTS',inputs_sha256={**inputs,str(OUT/'PATCH_VALIDATION.json'):sha(OUT/'PATCH_VALIDATION.json')},runs=summaries,comparisons=comparisons,full_discovery=gates,
    host_coverage=host_coverage,
    must_unit_pass=all(runs['must_final_'+t]['successful'] for t in ('new','live')),
    source_names_matrix_cases=1280,coverage_authentication_scope='Six-family camera unit tests isolate only the two missing coverage-file pinned() calls; camera bytes and SHA256 authentication run unchanged. Camera-only tests use no mocks. Full six-family validation is MISSING.',
    limits='CPU only; no network, process workers, NFS reads, outside writes or deletion. Thread pools are capped at 16 for final MUST and full runs.'))
print(json.dumps({k:dict(new=len(v['new_failures']),changed=len(v['changed_causes']),resolved=len(v['resolved'])) for k,v in comparisons.items()},indent=2))
