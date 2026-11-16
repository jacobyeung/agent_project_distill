from pathlib import Path
import collections,gzip,json,re,sys,time
L=Path(__file__).resolve().parents[1];T=L/'work/trees/r3_proof/base';X=L/'work/real/x'
sys.path.insert(0,str(T))
from student_pilot.training_contract import audit_training_contract,call_responses,admission_phrases
from student_pilot.s1_grounding import build_backend
from student_pilot.phrases import normalize_phrase,annotation_labels
from student_pilot.routed_features import select_instances
manifest=json.loads((X/'66caacf5c9191457.json').read_text())
counts={};phrases={};failures=[];deferred={};members=[]
class Passed(Exception):pass
class Stop:
    def has(self,k):raise Passed()
for dataset in manifest['sets']:
    for role,pin in dataset['files'].items():
        p=X/(pin['sha256'][:16]+'.jsonl.gz');c=collections.Counter();members.append(str(p))
        with gzip.open(p,'rt') as f:
            for line_no,line in enumerate(f,1):
                row=json.loads(line);c['rows_read']+=1
                typ=row.get('question_type',row.get('type'))
                raw=[]
                for value in row.get('roles',{}).values():
                    raw.extend(value if isinstance(value,list) else [value])
                pairs=list(call_responses(row))
                for call,_ in pairs:
                    if isinstance(call,str):raw.extend(re.findall(r'(?:obj|a|b)="([^"]+)"',call))
                for phrase in raw:
                    if not isinstance(phrase,str) or not phrase.strip():continue
                    normalized=normalize_phrase(phrase)
                    assert normalize_phrase(normalized)==normalized,(phrase,normalized)
                    assert annotation_labels(phrase,[normalized],lambda *args:[])==[normalized]
                    phrases.setdefault(phrase,dict(normalized=normalized,source=str(p),line=line_no))
                if typ not in ('object_abs_distance','room_size_estimation','route_planning'):continue
                reason=audit_training_contract([row])[0]
                c[typ+':'+(reason or 'admitted')]+=1
                if reason:
                    entry=deferred.setdefault(reason,dict(count=0,qids=[]));entry['count']+=1
                    if len(entry['qids'])<50:entry['qids'].append(dict(qid=row['qid'],source=str(p),line=line_no))
                if typ!='object_abs_distance' or role!='packed':continue
                names=[re.search(r'obj="([^"]+)"',call)[1] for call,_ in pairs if re.search(r'^<ground obj="',call)]
                inputs=dict(question=row['question'],options=row.get('options',[]))
                admitted=admission_phrases(inputs['question'],inputs['options'],row.get('candidate_phrases'))
                backend=build_backend(dict(row,student_input=inputs),dict(frame_indices=list(range(32)),video_sha256='a'*64),dict(sha256='b'*64),L/'work/tmp/real_membership_r3')
                backend.geometry_error=None
                assert list(admitted)==backend.config['candidate_universe']
                for name in names:
                    try:select_instances(backend,name,Stop())
                    except Passed:pass
                    else:raise AssertionError((row['qid'],name))
                    assert normalize_phrase(name) in admitted
                    c['runtime_operands_checked']+=1
                c['runtime_rows_checked']+=1
        counts[dataset['name']+':'+role]=dict(c)
        print(dataset['name'],role,dict(c),flush=True)
report=dict(source_archive=str(L/'work/real/eb3429c5.tar'),source_manifest=str(X/'66caacf5c9191457.json'),
    source=str(Path(__file__)),tree=str(T),counts=counts,deferred=deferred,failures=failures,
    unique_phrases=len(phrases),phrase_checks=phrases,annotation_labels_checked=True,
    candidate_check='Native MDG parser and runtime membership; POOL does not bind a mask cache. Cache deployment requires an explicit cache manifest, tested using separate reads in test_review_r3.py.',
    cache_test_source=str(L/'work/tests_r3/test_review_r3.py'))
(L/'out/REAL_ROW_AUDIT_R3.json').write_text(json.dumps(report,indent=2)+'\n')
