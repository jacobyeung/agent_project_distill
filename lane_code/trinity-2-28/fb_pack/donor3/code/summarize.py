from pathlib import Path
import collections, hashlib, json, re
W=Path(__file__).resolve().parents[1];O=W/'out';D=W.parent/'donor2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs={str(Path(__file__).resolve()):sha(__file__)}
def read(name):
    p=O/name;inputs[str(p)]=sha(p);return json.loads(p.read_text())
def norm(text):
    text=re.sub(re.escape(str(W))+r'/work/(?:live_base|live|base|new)(?=/)', '<tree>',text)
    text=re.sub(re.escape(str(W))+r'/work/focused_(?:live_base|live|base|new)/[^/\s\"\']+/', '<fixture>/',text)
    text=re.sub(r'/tmp/headcall_test_cache/hcfull_frames_[a-z0-9_]{8}(?=$|[ /\"\'])','/tmp/headcall_test_cache/hcfull_frames_<temporary>',text)
    return re.sub(r'focused_(?:live_base|live|base|new)', '<suite>',text)
def events(r):
    out=[]
    for kind in ('errors','failures'):
        for name,trace in r[kind]:
            if name=='failed' or 'raise RuntimeError(message)' in trace:
                paths=re.findall(r'/work/(?:live_base|live|base|new)/(tests/[^"\n]+\.py)',trace)
                name='collection:'+paths[0].replace('/','.') if paths else 'collection:'+trace.splitlines()[-1]
            lines=trace.strip().splitlines();marks=[i for i,line in enumerate(lines) if re.match(r'^(?:[\w.]+(?:Error|Exception)|SystemExit):',line)]
            cause=' '.join(lines[marks[-1]:]) if marks else lines[-1]
            out.append(dict(test=norm(name),kind=kind,cause=norm(cause),traceback=trace))
    return out
runs=read('RUNS.json');assert len(runs['runs'])==10 and all(r['returncode']==0 for r in runs['runs'])
for p,h in runs['input_sha256'].items():assert sha(p)==h,p
unit={}
for name in ('unit_new','unit_live'):
    p=O/(name+'.log');inputs[str(p)]=sha(p);s=p.read_text();assert s.strip().endswith('OK')
    unit[name]=dict(tests=int(re.search(r'Ran (\d+) tests',s)[1]),status='PASS',command=next(r['command'] for r in runs['runs'] if r['name']==name))
reports={t:read('FOCUSED_'+t.upper()+'.json') for t in ('base','new','live_base','live')}
comparisons={};parity={}
for a,b in [('base','new'),('live_base','live')]:
    sig=lambda r:collections.Counter((v['test'],v['kind'],v['cause']) for v in events(r))
    added=sig(reports[b])-sig(reports[a]);assert not added,list(added)
    comparisons[a+'_'+b]=dict(status='PASS',new_failure_signatures=[list(k) for k in added],preexisting=events(reports[a]))
    pa=read('PARITY_'+a+'.json');pb=read('PARITY_'+b+'.json');assert pa['outputs']==pb['outputs']
    out=pa['outputs']
    parity[a+'_'+b]=dict(status='PASS',byte_identical=True,fields=len(out),state_tensors=len(out['state2']),optimizer_tensors=len(out['opt2']),exported_head_tensors=len(out['export_heads']),commands=[pa['command'],pb['command']])
patches=read('FILES_TOUCHED.json');recipe=read('RECIPE_CHECK.json');stage=read('STAGING.json')
assert patches['status']==recipe['status']==stage['status']=='PASS'
# Record package documentation separately from the repository patch paths.
for name in ('READER_REQUEST.md','REAL_WEIGHT_COMMAND.sh'):
    for p in (O/name,D/'out'/name):inputs[str(p)]=sha(p)
summary=lambda r:dict(tests=r['tests_run'],failures=len(r['failures']),errors=len(r['errors']),skips=len(r['skipped']),command=r['command'])
result=dict(input_sha256=inputs,status='PASS',command='python -B code/summarize.py',unit_tests=unit,focused_suites={k:summary(v) for k,v in reports.items()},focused_comparisons=comparisons,field_absent=parity,patch_applications=patches['applications'],runtime=dict(status='PASS',constructor='real CarrierC1 called by the actual load_runtime function body',base_load='real full_ft.load_export',adapter='test-only insertion at the strict head-load site',positive='all exported head tensor bytes equal after native two-step export reload',negative_cases=['attach before visual load/freeze','freeze only','load only','tampered visual','missing visual key','unpopped metadata','inconsistent metadata','tampered donor tensor'],documented_sequence_matches_test_exactly=True),training_code_changed_from_donor2=False,real_weights=dict(status='MISSING',step400_heads='/scratch/jjyeung/b01ec87a6f29b/d/m400/heads.pt',expected_sha256='e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7',step544_heads='MISSING: location not supplied',note='Availability limitation carried from supplied donor2 reader request; no unlisted location was searched.'),limitations='CPU tiny native weights; mocked bundle/processor/token boundaries and legacy reader guard; no installed production reader adapter, full production weights, GPU, network or distributed transport validation.')
(O/'TESTS.json').write_text(json.dumps(result,indent=2)+'\n')
lines=['M4 is fixed in the reader recipe and runtime regression. Donor training code is byte-identical to donor2.','',
'READER_REQUEST.md strictly loads `depth.model.visual.*` from `heads.pt`, strips that exact prefix, freezes the visual, then attaches the donor. It then pops and compares metadata, verifies the export and strict-loads all heads. Attachment still authenticates `visual_sha256`.',
'The test executes the actual runtime function body with the proposed reader adapter inserted at its strict-load site. It constructs real CarrierC1 on a differently initialized tiny base and runs real full_ft.load_export. Every exported head tensor matches after a native two-step export.',
'The eight negative cases reject the old order, freezing alone, loading alone, a tampered visual, an incomplete visual, unpopped metadata, inconsistent metadata and a tampered donor. `code/run_unit.py` produces these results.',
'The shipped runtime adapter is not changed. Bundle/processor/token boundaries and the legacy R2 entry guard are isolated in the test; the recipe states these limits. A production reader owner must install the authenticated adapter.','',
'`code/stage.py` verifies base seal `57a1f14d` and live seal `189df6ac`. `code/build_patch.py` produces the full replacement and delta patches and verifies zero-fuzz, zero-offset application and every resulting file.',
f"The full patch changes {len(patches['files'])} repository files against base; the delta changes only `tests/test_scale_donor.py` against base plus PATCH_DONOR2. The package also updates READER_REQUEST.md and the real-weight script usage comment.",
f"`code/run_unit.py` passes {unit['unit_new']['tests']} donor tests on the new tree and {unit['unit_live']['tests']} on live (set `DONOR_TREE=live`).",'']
for t,r in reports.items():lines.append(f"`code/run_focused.py {t}`: {r['tests_run']} tests, {len(r['failures'])} failures, {len(r['errors'])} errors, {len(r['skipped'])} skips.")
lines += ['Both focused comparisons have zero new failure signatures. Existing failures/errors remain explicit in TESTS.json; the focused suites do not fully pass. `code/summarize.py` compares test names, exception types and causes, normalizing only tree and temporary directory names.','',
'`code/parity_full.py base`, `new`, `live_base` and `live` show byte-identical field-absent outputs on both seals: both decode arms before/after training and reload, optimizer groups, handover table, model/optimizer tensors, exported heads and artifact keys.',
f"Each pair compares {parity['base_new']['fields']} output fields, including {parity['base_new']['state_tensors']} model tensors, {parity['base_new']['optimizer_tensors']} optimizer tensors and {parity['base_new']['exported_head_tensors']} exported head tensors. `code/summarize.py` computes these counts.",
'`code/check_recipe.py` verifies that the documented executable sequence equals the tested sequence, all nine feature-source hashes match, and `bash -n out/REAL_WEIGHT_COMMAND.sh` passes.',
'Invoke the real-weight command by absolute package path from the patched tree, with PYTHON and its required pinned inputs. Real-weight validation remains MISSING: donor2 names `/scratch/jjyeung/b01ec87a6f29b/d/m400/heads.pt`, SHA256 `e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7`. The step-544 location and production source/FoV decision are MISSING.','',
'All Python commands above use `nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B`. `code/validate.py` runs the ten validation commands sequentially; RUNS.json and the individual receipts retain exact commands and input SHA256 values.',
'`code/package.py` creates and verifies `out/fbp_donor3.tar` and writes `out/fbp_donor3.tar.sha256`. The archive retains patches, overlay, recipe, harness, validation evidence and native unit/parity fixture artifacts. Fixture artifact schemas remain native.',
'Borderline prose retained: the old-order comparison is a required negative control. No Git, SSH, network, GPU, signals, tmux operations or external writes were used.']
assert len(lines)<=40
(O/'REPORT.md').write_text('\n'.join(lines)+'\n')
(W/'STATUS.md').write_text('M4 passes with a real CarrierC1 runtime construction and real base export loading. Both trees pass every donor unit test; field-absent outputs are byte-identical on both seals, and focused suites have no new failure signature. Full and delta patches apply with zero fuzz and zero offset. Packaging remains; production weights and the production reader adapter remain outside this fixture validation.\n')
print(json.dumps(dict(status=result['status'],unit_tests=unit,focused=result['focused_suites'],parity=parity),indent=2))
