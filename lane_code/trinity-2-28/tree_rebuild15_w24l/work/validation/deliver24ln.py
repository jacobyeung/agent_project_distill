"""Seal, compare and package the combined tree without Git or deleting files."""
import ast,collections,copy,difflib,hashlib,io,json,os,re,sys,tarfile
from pathlib import Path
J=Path(__file__).resolve().parents[2];T=J/'work/tree_r1';B=J/'work/tree_r1_base';O=J/'out'
sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,sha256

def put(name,value):
    (O/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def record(label):return json.loads((O/(label+'.json')).read_text())
base,after=inventory(B),inventory(T)
assert digest(base)=='189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710'
assert base==json.loads((O/'BEFORE24L.json').read_text())
changed=[n for n in sorted(base.keys()|after.keys()) if base.get(n)!=after.get(n)]
assert changed==['launch_r1/entry.py','launch_r1/production_proof.py','student_pilot/r1_handover.py','tests/test_host24l.py','tests/test_host24n.py'],changed
seal=digest(after)
protected={}
for filename,names in {'launch_r1/entry.py':['admit','frame_host','temporary_paths','fresh_tmp'],
    'launch_r1/production_proof.py':['bind_handover','forward','verify_staging'],
    'student_pilot/carrier_c1_run.py':['identity','prepared','train'],
    'student_pilot/r1_handover.py':['compare_configs','pin_values','progress','bind_target'],
    'student_pilot/r1_training.py':['validate','target_identity','boundary','start']}.items():
    for name in names:
        hashes=[]
        for root in (B,T):
            text=(root/filename).read_text();node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
            hashes.append(hashlib.sha256(ast.get_source_segment(text,node).encode()).hexdigest())
        assert hashes[0]==hashes[1],(filename,name)
        protected[filename+':'+name]=dict(before=hashes[0],after=hashes[1],identical=True)
class RestorePinComparisons(ast.NodeTransformer):
    def visit_UnaryOp(self,node):
        if isinstance(node.op,ast.Not) and isinstance(node.operand,ast.Call) and isinstance(node.operand.func,ast.Name) and node.operand.func.id=='_same_pin_bytes':
            return ast.Compare(left=node.operand.args[0],ops=[ast.NotEq()],comparators=[node.operand.args[1]])
        return self.generic_visit(node)
functions=[]
for root in (B,T):
    node=next(n for n in ast.parse((root/'student_pilot/r1_handover.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_donor')
    functions.append(ast.dump(RestorePinComparisons().visit(node),include_attributes=False))
assert functions[0]==functions[1]
put('TREE24LN_SEAL.json',dict(tree_sha256=seal,commit='sha256:'+seal,file_count=len(after),files=after,
    base_tree_sha256=digest(base),base_file_count=len(base),method='student_pilot.source_seal.inventory + student_pilot.p3_provenance.digest'))
put('UNCHANGED24LN.json',dict(before_tree_sha256=digest(base),after_tree_sha256=seal,changed=changed,
    files={n:dict(before=base.get(n),after=after.get(n),unchanged=base.get(n)==after.get(n)) for n in sorted(base.keys()|after.keys())},
    protected_functions=protected,donor_body_identical_except_two_preparation_pin_comparisons=True))
patch=[]
for name in changed:
    old=(B/name).read_text().splitlines(keepends=True) if name in base else []
    new=(T/name).read_text().splitlines(keepends=True)
    patch.extend(difflib.unified_diff(old,new,fromfile='a/'+name if name in base else '/dev/null',tofile='b/'+name))
(O/'HOST24LN.patch').write_text(''.join(patch))
# Independently replay each unified hunk against the base in memory.
lines=''.join(patch).splitlines(keepends=True);i=0;rebuilt={}
while i<len(lines):
    assert lines[i].startswith('--- ');old_name=lines[i][4:].strip();i+=1
    assert lines[i].startswith('+++ b/');name=lines[i][6:].strip();i+=1
    old=(B/name).read_text().splitlines(keepends=True) if old_name!='/dev/null' else []
    output=[];cursor=0
    while i<len(lines) and not lines[i].startswith('--- '):
        m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[i]);assert m,lines[i]
        start=int(m[1]);count=int(m[2] or 1);position=start-1 if count else start
        output.extend(old[cursor:position]);cursor=position;i+=1
        while i<len(lines) and not lines[i].startswith(('@@ ','--- ')):
            op,line=lines[i][0],lines[i][1:]
            if op in (' ','-'):assert old[cursor]==line;(cursor:=cursor+1)
            if op in (' ','+'):output.append(line)
            i+=1
    output.extend(old[cursor:]);raw=''.join(output).encode();assert hashlib.sha256(raw).hexdigest()==after[name]
    rebuilt[name]=hashlib.sha256(raw).hexdigest()
put('PATCH_CHECK24LN.json',dict(status='PASS',method='unified hunks replayed against base in memory',files=rebuilt))
# Test accounting: final host tests and final independent pin/q tests.
focused=record('focused_final24ln');pins=record('native_gate24ln')
assert not focused['errors'] and not focused['failures'] and not pins['errors'] and not pins['failures']
host_tests=[n for n in focused['passed'] if '.test_host24n.' not in n]
assert len(host_tests)==27 and len(pins['passed'])==10
old,new=record('regression_base24ln'),record('regression_after24ln')
def outcomes(v):return (v['tests_run'],sorted(v['passed']),sorted((x['test'],x['traceback'].strip().splitlines()[-1]) for x in v['errors']),v['failures'],v['skipped'])
assert outcomes(old)==outcomes(new)
causes=collections.Counter(x['traceback'].strip().splitlines()[-1] for x in new['errors'])
assert all(c.startswith('FileNotFoundError:') for c in causes),causes
put('TESTS24LN.json',dict(host_tests=host_tests,pin_and_native_q_tests=pins['passed'],focused_unique_passed=37,
    regression_tests_run=new['tests_run'],regression_passed=len(new['passed']),regression_errors=len(new['errors']),
    regression_failures=len(new['failures']),baseline_outcomes_identical=True,error_causes=dict(causes),
    fixture_seed=record('SCOPED_FIXTURE_SEED24LN'),
    evidence={name:sha256(O/name) for name in ('focused_final24ln.json','focused_final24ln.log','native_gate24ln.json','native_gate24ln.log','regression_base24ln.json','regression_base24ln.log','regression_after24ln.json','regression_after24ln.log')}))
# Final-tree routing experiment: three separate interpreters; roots retained by rename.
from student_pilot.s1_pool import implementation
area=J/'work/validation/routing24ln'
selection=json.loads((area/'inputs/pool/receipt.json').read_text())
assert selection['implementation']==implementation()
runs=[json.loads((area/(label+'.json')).read_text()) for label in ('first','second','third')]
assert runs[0]['root']==runs[1]['root'] and runs[0]['digest']==runs[1]['digest'] and runs[0]['digest']!=runs[2]['digest']
assert len({runs[0]['pid'],runs[1]['pid']})==2
fields=[k for k in runs[1]['receipt'] if runs[1]['receipt'][k]!=runs[2]['receipt'][k]]
put('ROUTING_DIGEST_STABILITY.json',dict(status='MEASURED_CPU_FIXTURE',source_tree_sha256=seal,
    same_path_fresh_roots_equal=True,other_path_equal=False,rows_per_build=1,audit_only=False,
    runs=[{k:r[k] for k in ('pid','root','digest')} for r in runs],changed_top_level_fields=fields,
    database_hash_equal=len({r['receipt']['database']['sha256'] for r in runs})==1,
    source_implementation_sha256=digest(implementation()),
    input_file_hashes=inventory(area/'inputs'),
    executed='native s1_routing.build(cfg, root/selection, division, model) in three independent Python processes; each root renamed away before reuse',
    fixture_standins=['tiny canonical calculator program uses routing.check_row as the packed-source validator','fixed processor token IDs and deterministic character suffix tokenizer','synthetic frame addresses; no RGB reads or model weights'],
    interpretation='Same paths, staged input bytes and source implementation reproduced the digest in separate processes. Another output root changes receipt paths and transitive metadata hashes, while the row database bytes stay equal.',
    additional_dependencies='The receipt embeds input pin paths, including fixture inputs outside the output root, and the pool implementation source hashes. These must be identical too. No time/PID/hostname field is added by build/relocate; the fixture tests process/time variation, not different machines or library versions.',
    production_selection_pin=None,production_P_row_equality_executed=False,
    independent_production_review_required=True,script='work/validation/routing_stability24ln.py',script_sha256=sha256(J/'work/validation/routing_stability24ln.py')))
# Record audit candidates against the final source, so every location is current.
candidates=[]
for filename in ('launch_r1/production_proof.py','launch_r1/entry.py','student_pilot/r1_persisted.py',
                 'student_pilot/r1_handover.py','student_pilot/r1_components.py','student_pilot/carrier_c1_run.py',
                 'student_pilot/r1_population.py','launch_r1/p_opener_witness.py'):
    text=(T/filename).read_text()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node,ast.Compare) and any(isinstance(op,(ast.Eq,ast.NotEq)) for op in node.ops):
            expression=ast.get_source_segment(text,node)
            if any(k in expression for k in ('pin','preparation','receipt','binding','source','bound','cfg','artifact','stream','model')):
                candidates.append(dict(file=filename,line=node.lineno,expression=expression))
put('PIN_AUDIT_CANDIDATES.json',candidates)
from launch_r1.entry import verify_host_staging
try:
    verify_host_staging({'e':dict(archive=dict(sha256='0'*64,parts=[dict(sha256='1'*64,bytes=1)]),inventory={'artifact':'2'*64})},J/'work/validation/kit_probe')
except ValueError as error:refusal=str(error)
else:raise AssertionError('24k plan was unexpectedly accepted')
assert refusal.startswith('R1_HOST_STAGING_DIFFERS:e:')
put('KIT_PLAN_PROBE24LN.json',dict(status='REFUSE',refusal=refusal,
    shape_source='in24kr/kit_n_go/b/pl.py:186-188',payload='synthetic hashes; refusal precedes any payload read',
    other_non_native_targets=['n.json','source_code.json','f/...'],
    scene_evidence_fields={k:json.loads((J/'work/validation/decoded24ln/c.json').read_text())[k] for k in ('r2_all_stream_exclusions','r2_scene_rebuild','scene_coverage')}))
report=[
'Combined TREE 24l/24n CPU build completed; production integration remains blocked by the kit items below.',
f'Tree seal: {seal}; {len(after)} files. Base seal remains {digest(base)}; {len(base)} files.',
'Changed production files: launch_r1/entry.py, launch_r1/production_proof.py, student_pilot/r1_handover.py.',
'Added tests: tests/test_host24l.py and tests/test_host24n.py. All other 937 source files are byte-identical.',
'24l: q checks scenes before twins and again after native augmentation; host.json records the checked VQA/routing/division pins.',
'24l: host.json records routing_selection, regenerated_sha256, routing substitution pins/digests and routing_substituted without a new routing refusal.',
'24l: the tree rechecks hook-staged archives, inventories and targets and records stager=native|hook; wrong bytes refuse by name.',
'24l: mode-p receipt bytes match the untouched base across PASS/refusal fixtures; both existing namespace/token tests pass unchanged.',
'24n: only two donor preparation comparisons ignore location; exact pin structure, SHA256, preparation schema and both config identities remain checked.',
'24n: pinned() verifies preparation bytes before _donor reads them; persisted verification independently hashes the staged preparation.',
'24n: each comparison has a base-failing relocation test, an isolated different-hash refusal and a wrong-byte/same-stated-hash refusal.',
'24n: native q fixtures pass compare_configs, bind_target, final bind_handover and persisted admission in proof and fresh-training modes with localized p_run.',
'PIN_COMPARISONS_24N.md lists 104 inspected comparisons/delegations, including unchanged whole-pin and nested-pin checks and verification file:line locations.',
'Identity, admit(), row legality, exclusions, routing policy, sampling, scoring, opener rows, step-544 lineage and DEFERRED evidence definitions are unchanged.',
'UNCHANGED24LN.json records every before/after file hash and protected function hashes; the donor body differs only at the two pin comparisons.',
'Focused tests: all 27 host tests and all 10 final donor/q tests pass; no skips or assertion failures.',
'Q fixtures stub capacity producers, routing, room/component authority and opener generation; byte, donor, config, mapping and persisted gates run natively.',
f'Existing scoped suite: {new["tests_run"]} tests per tree; {len(new["passed"])} pass and the same {len(new["errors"])} error in both; no new failures.',
'All scoped errors require absent archived fixtures: 35 need work/base/tree_b01ce449/student_pilot/carrier_c1_run.py; the rest need config, room, source or script fixtures.',
'SCOPED_FIXTURE_SEED24LN.json documents synthetic import/config seeds; TESTS24LN.json records complete outcomes and error causes.',
'Routing: three fresh-process builds on the final source give equal digests at the same path and unequal digests at another path; database hashes match.',
'Routing stability also requires identical input pin paths and implementation hashes. ROUTING_DIGEST_STABILITY.json names the fixture stand-ins and limits.',
'Kit action: 24k pl.py uses a non-native hook plan (e/n.json/source_code.json/f paths); the new tree verifier refuses it. KIT_WIRING_24LN.md specifies the native-layout adapter.',
'Kit evidence gap: supplied N configs have null r2_scene_rebuild/scene_coverage with r2_all_stream_exclusions=true; no gate was weakened to accept missing evidence.',
'No production routing pin, P-row equality, real-frame preparation, GPU forward, independent review PASS or launch GO is claimed.',
'HOST24LN.patch replays against the base in memory. The tar contains work/tree_r1, required outputs and retained validation scripts/logs.',
'All work stayed under J with nice 10, one-thread numeric libraries and a 19,000,000-KiB address-space ceiling; no forbidden services, Git, deletion or other agents were used.'
]
assert len(report)<40
(O/'BUILD24LN_REPORT.md').write_text('\n'.join(report)+'\n')
required=['HOST24LN.patch','TREE24LN_SEAL.json','UNCHANGED24LN.json','ROUTING_DIGEST_STABILITY.json','PIN_COMPARISONS_24N.md','KIT_WIRING_24LN.md','BUILD24LN_REPORT.md']
extras=['TESTS24LN.json','PATCH_CHECK24LN.json','KIT_PLAN_PROBE24LN.json','SCOPED_FIXTURE_SEED24LN.json','PIN_AUDIT_CANDIDATES.json',
    'focused_final24ln.json','focused_final24ln.log','native_gate24ln.json','native_gate24ln.log',
    'regression_base24ln.json','regression_base24ln.log','regression_after24ln.json','regression_after24ln.log']
support=['work/validation/run_tests.py','work/validation/routing_stability24ln.py','work/validation/write_audit24ln.py','work/validation/deliver24ln.py']
files={**{'work/tree_r1/'+n:T/n for n in after},**{'out/'+n:O/n for n in required+extras},**{n:J/n for n in support}}
for label in ('first','second','third'):
    files['work/validation/routing24ln/'+label+'.json']=area/(label+'.json')
# Retain the small exact experiment inputs and products so path-caused hash differences can be inspected.
for folder in ('inputs','first_retained','second_retained','third_retained'):
    for path in sorted((area/folder).rglob('*')):
        if path.is_file():files[str(path.relative_to(J))]=path
manifest={name:sha256(path) for name,path in sorted(files.items())}
put('DELIVERY_MANIFEST24LN.json',dict(tree_sha256=seal,members=manifest))
files['out/DELIVERY_MANIFEST24LN.json']=O/'DELIVERY_MANIFEST24LN.json'
archive=O/f'tree_rebuild_b24ln_{seal[:8]}.tar'
with tarfile.open(archive,'x') as tar:
    for name,path in sorted(files.items()):
        raw=path.read_bytes();entry=tarfile.TarInfo(name);entry.size=len(raw);entry.mode=0o755 if os.access(path,os.X_OK) else 0o644
        tar.addfile(entry,io.BytesIO(raw))
with tarfile.open(archive,'r') as tar:
    actual={m.name:hashlib.sha256(tar.extractfile(m).read()).hexdigest() for m in tar}
assert actual=={name:sha256(path) for name,path in files.items()}
assert inventory(B)==base and inventory(T)==after
put('ARCHIVE_CHECK24LN.json',dict(status='PASS',archive=str(archive),sha256=sha256(archive),bytes=archive.stat().st_size,members=len(actual),tree_sha256=seal))
print(json.dumps(dict(seal=seal,file_count=len(after),changed=changed,archive=str(archive),archive_bytes=archive.stat().st_size,
    focused_passed=37,regression_passed=len(new['passed']),preexisting_errors=len(new['errors']))))
