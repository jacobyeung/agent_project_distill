from pathlib import Path
import collections,gzip,hashlib,importlib.util,json,re,sys,time
L=Path(__file__).resolve().parents[1];tree=L/'work/trees/tree_r1_rehearsal';x=L/'work/real/x';out=L/'out'
sys.path.insert(0,str(tree))
from student_pilot.training_contract import audit_training_contract,call_responses,admission_phrases
from student_pilot.s1_grounding import build_backend,candidate_names
from student_pilot.phrases import normalize_phrase
from student_pilot.routed_features import select_instances
from trace_format.contracts import contract_epoch
spec=importlib.util.spec_from_file_location('student_pilot.b1_audit',L/'work/trees/patched/student_pilot/training_contract.py')
b1=importlib.util.module_from_spec(spec);spec.loader.exec_module(b1)
manifest=json.loads((x/'66caacf5c9191457.json').read_text())
exclusions=set()
for p in x.glob('*.tsv'):
    with p.open() as f:
        exclusions.update(tuple(line.strip().split('\t')[:2]) for line in f if line.strip())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
checks={}
for line in (x/'SHA256SUMS').read_text().splitlines():
    expected,name=line.split(None,1);checks[name]=sha(x/name)==expected
assert all(checks.values())
assert sha(L/'work/real/eb3429c5.tar')=='f0e715135f4b7cd8e38c046e2dd1a0a11ea98c2de4c5dbca53ee92f1a12f3e13'
report=dict(source_archive=str(L/'work/real/eb3429c5.tar'),manifest=str(x/'66caacf5c9191457.json'),member_hash_checks=checks,
    admission_path='s1_routing._build.add -> audit_training_contract([row], contract_manifest)[0]',
    candidate_source='Question parser; the package has no row candidate_phrases or candidate_manifest.',
    sealed_comparison_scope='Pool eligibility from manifest plus exclusion TSVs; training_admitted=False is a generator membership invariant, not proof of absence from training. Exact leg sampling/membership is not in this package.',
    sampling='Complete scan, no sampling',members={},totals={},findings=[],repaired_findings={},deferred_members={})
universe=dict(source=str(x),candidate_source=report['candidate_source'],runtime_path='s1_grounding.build_backend -> GroundV3.config -> routed_features.select_instances first membership check',
    scope='Membership only: stop at exact geometry access after the membership guard; no perception or lifting claim.',members={},disagreements=[])
class MembershipPassed(Exception):pass
class StopAtGeometry:
    def has(self,k):raise MembershipPassed()
def membership(backend,name):
    backend.geometry_error=None
    try:select_instances(backend,name,StopAtGeometry())
    except MembershipPassed:return True
    except ValueError as e:
        if 'fixed named candidate universe' in str(e):return False
        raise
start=time.monotonic()
for dataset in manifest['sets']:
    for role,pin in dataset['files'].items():
        p=x/(pin['sha256'][:16]+'.jsonl.gz')
        counters={};examples={};u=collections.Counter()
        with gzip.open(p,'rt') as f:
            for line_no,line in enumerate(f,1):
                row=json.loads(line);typ=row.get('question_type',row.get('type'))
                if typ not in ('object_abs_distance','room_size_estimation','route_planning'):continue
                c=counters.setdefault(typ,collections.Counter());c['rows_read']+=1
                eligible=(dataset['name'],str(row['qid'])) not in exclusions
                c['sealed_pool_eligible']+=eligible
                reason=audit_training_contract([row])[0]
                before=b1.audit_training_contract([row])[0]
                c['admitted' if reason is None else 'deferred:'+reason]+=1
                c['sealed_pool_eligible_admitted' if reason is None else 'sealed_pool_eligible_deferred']+=eligible
                if before and not reason:
                    c['b1_false_positive:'+before]+=1
                    examples_before=report['repaired_findings'].setdefault(p.name,[])
                    if len(examples_before)<3:
                        examples_before.append(dict(qid=row['qid'],line=line_no,source=str(p),reason=before,
                            classification='audit false positive: no explicit manifest configured, runtime uses question parser',
                            question=row.get('question'),offending_span='candidate_phrases absent',
                            row_text=row.get('target',row.get('suffix')),events=list(call_responses(row)),
                            sealed_pool_eligible=eligible,final_verdict=reason))
                if reason:
                    example=dict(qid=row['qid'],source=str(p),line=line_no,reason=reason,question=row.get('question'),offending_spans=list(call_responses(row)),row_text=row.get('target',row.get('suffix')),sealed_pool_eligible=eligible)
                    ex=examples.setdefault(typ,{}).setdefault(reason,[])
                    if len(ex)<3:ex.append(example)
                    if eligible:report['findings'].append(dict(example,classification='unresolved contract violation'))
                if typ!='object_abs_distance' or role!='packed':continue
                operands=[re.search(r'obj="([^"]+)"',call)[1] for call,_ in call_responses(row) if re.search(r'^<ground obj="',call)]
                inputs=dict(question=row['question'],options=row.get('options',[]))
                admitted=admission_phrases(inputs['question'],inputs['options'],row.get('candidate_phrases'))
                b=build_backend(dict(row,student_input=inputs),dict(frame_indices=list(range(32)),video_sha256='a'*64),dict(sha256='b'*64),L/'work/tmp/real_membership')
                runtime=b.config['candidate_universe']
                passed=[membership(b,n) for n in operands]
                with contract_epoch(False):sealed=candidate_names(inputs['question'],inputs['options'])
                outside_keys=[normalize_phrase(n) not in ('bed','chair','counter','door','lamp','refrigerator','table','trash bin') for n in operands]
                refused=[normalize_phrase(n) not in sealed for n in operands]
                agree=list(admitted)==runtime and all(passed) and all(normalize_phrase(n) in admitted for n in operands)
                u['rows']+=1;u['agreement' if agree else 'disagreement']+=1;u['operands']+=len(operands)
                u['outside_sealed_eight_keys']+=sum(outside_keys);u['refused_by_sealed_question_universe']+=sum(refused)
                if eligible:
                    u['eligible_rows']+=1;u['eligible_operands']+=len(operands)
                    u['eligible_outside_sealed_eight_keys']+=sum(outside_keys)
                    u['eligible_refused_by_sealed_question_universe']+=sum(refused)
                if not agree:universe['disagreements'].append(dict(source=str(p),line=line_no,qid=row['qid'],question=row['question'],options=row['options'],operands=operands,admission=list(admitted),runtime=runtime,runtime_membership=passed))
        if counters:
            report['members'][p.name]=dict(source=str(p),set=dataset['name'],role=role,types={k:dict(v) for k,v in counters.items()},examples=examples)
        if u:universe['members'][p.name]=dict(source=str(p),set=dataset['name'],**dict(u))
        print(dataset['name'],role,{k:dict(v) for k,v in counters.items()},flush=True)
for p in sorted(x.glob('*.jsonl')):
    c=collections.Counter();examples=[]
    with p.open() as f:
        for line_no,line in enumerate(f,1):
            row=json.loads(line);reason=audit_training_contract([row])[0]
            c['rows_read']+=1;c['audit_noop_nontraining_metadata' if not row.get('events') else 'event_rows']+=1
            c['audit_returned_none' if reason is None else reason]+=1
            if len(examples)<3:examples.append(dict(line=line_no,row=row,verdict=reason))
    report['deferred_members'][p.name]=dict(source=str(p),counts=dict(c),examples=examples,
        classification='Label-removal/deferred metadata, without question/target/events; audit returns no verdict and does not admit these as training rows.')
totals={}
for v in report['members'].values():
    for typ,c in v['types'].items():totals.setdefault(v['role']+':'+typ,collections.Counter()).update(c)
report['totals']={k:dict(v) for k,v in totals.items()}
total=collections.Counter()
for v in universe['members'].values():total.update({k:n for k,n in v.items() if isinstance(n,int)})
universe['totals']=dict(total)
report['elapsed_seconds']=time.monotonic()-start
report['candidate_universe_report']=str(out/'REAL_CANDIDATE_UNIVERSE.json')
for name,data in [('REAL_ROW_AUDIT.json',report),('REAL_CANDIDATE_UNIVERSE.json',universe)]:
    (out/name).write_text(json.dumps(data,indent=2)+'\n')
print('TOTALS',report['totals'],universe['totals'],flush=True)
