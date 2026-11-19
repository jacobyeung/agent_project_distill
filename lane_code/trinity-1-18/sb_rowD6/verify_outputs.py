"""Independently verify emitted records, source identity, quotas and teaching balance."""
import ast, collections as C, copy, ctypes, hashlib, json, re, sqlite3, sys
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'reference'))
import d2_support as d
d.BASE=Path('/scratch/jjyeung/orch_n30/sb_rowD2')
from student_pilot import scene_division_gate, r2_grammar
OUT=BASE/'out'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def om(r):
    pairs=[re.fullmatch(r'([A-Z])\.\s+(.+)',v).groups() for v in r['student_input']['options']]
    assert len(dict(pairs))==len(pairs)
    return dict(pairs)
def changed(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(set(a)|set(b)):
            p=path+'.'+k if path else k
            if k not in a or k not in b:yield p
            else:yield from changed(a[k],b[k],p)
    elif a!=b:yield path
def main():
    checks=json.loads((OUT/'CHECKS.json').read_text())
    pins=copy.deepcopy(checks['input_sha256'])
    for name in ('verify_outputs.py','out/NEW_ROWS.jsonl','out/SOURCE_MAP.jsonl','out/TEACHING_SET.json','out/GATE.json','out/READ60.md','out/READ30.md'):
        p=BASE/name;pins[str(p)]=dict(sha256=digest(p),bytes=p.stat().st_size)
    records=[json.loads(x) for x in (OUT/'NEW_ROWS.jsonl').read_text().splitlines()]
    maps=[json.loads(x) for x in (OUT/'SOURCE_MAP.jsonl').read_text().splitlines()]
    assert len(records)==len(maps)==8000
    assert len({x['qid'] for x in records})==len({x['candidate_id'] for x in records})==8000
    assert len({x['source_qid'] for x in maps})==8000
    turn={'left':'right','right':'left','front-left':'back-right','front-right':'back-left','back-left':'front-right','back-right':'front-left'}
    bybranch=C.Counter();bycell=C.Counter();names={};triples={};diffs=C.Counter();originals=[]
    tree=ast.parse((d.TREE/'student_pilot/carrier_c1_routing.py').read_text())
    nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('require_training_think','direct_row')]
    env=dict(__package__='student_pilot',THINK='<think>\n')
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'native_direct_pack','exec'),env)
    con=sqlite3.connect(d.DB.as_uri()+'?mode=ro&immutable=1',uri=True)
    cfg=json.loads((d.KIT/'w19/work/build17/inputs/config.json').read_text())
    removal=d.row_removals.Removals(checks['removal_inputs'])
    rooms,exclude=d.room_authority()
    corpus=json.loads((OUT/'WORDING_CORPUS.json').read_text());words=sorted(set(d.norm(v['text']) for v in corpus['wordings']))
    cwords=(ctypes.c_char_p*len(words))(*(w.encode() for w in words));lib=ctypes.CDLL(str(BASE/'edit_distance.so'))
    near=lib.close_wording;near.argtypes=[ctypes.c_char_p,ctypes.POINTER(ctypes.c_char_p),ctypes.c_int,ctypes.c_double];near.restype=ctypes.c_int
    # Check the native distance routine against an independent full DP implementation.
    def lev(a,b):
        prev=list(range(len(b)+1))
        for i,c in enumerate(a,1):
            curr=[i]
            for j,e in enumerate(b,1):curr.append(min(curr[-1]+1,prev[j]+1,prev[j-1]+(c!=e)))
            prev=curr
        return prev[-1]
    distance_cases=0
    for text in ['', 'a', 'abcdefghij', 'headings and quadrants', *words[:10]]:
        for other in [text,text+'x',text[::-1],text[1:],'different words']:
            one=(ctypes.c_char_p*1)(other.encode())
            assert (near(text.encode(),one,1,0.10)>=0)==(lev(text,other)<=0.10*max(len(text),len(other))+1e-10)
            distance_cases+=1
    for r,m in zip(records,maps,strict=True):
        raw=con.execute('select row from rows where i=?',(m['source_i'],)).fetchone()[0];s=json.loads(raw)
        assert hashlib.sha256(raw.encode()).hexdigest()==m['source_row_sha256']
        assert s['qid']==m['source_qid'] and r['qid']==m['qid']==s['qid']+'_sb_rowD6_'+m['branch']
        originals.append(s)
        paths=list(changed(s,r));diffs.update(paths)
        allowed={'qid','pool','answer','target','facing','candidate_id','label_row_keys','student_input.question','provenance.sb_rowD6'}
        assert set(paths)<=allowed,(r['qid'],paths)
        assert s['dataset']==r['dataset'] and s['scene']==r['scene']
        assert s['student_input']['frames']==r['student_input']['frames']
        assert {k:v for k,v in s['student_input'].items() if k!='question'}=={k:v for k,v in r['student_input'].items() if k!='question'}
        labels=om(s);newlabels=om(r);assert labels==newlabels
        assert set(labels.values())==({'left','right'} if m['family']=='easy' else {'front-left','front-right','back-left','back-right'})
        values=[turn[v] for v in labels.values()];assert len(set(values))==len(labels) and set(values)==set(labels.values())
        want=turn[labels[s['answer']]];assert newlabels[r['answer']]==m['label']==want
        expected_cid=d.candidate_identity(dict(qid=r['qid'],scene=r['scene'],frame_indices=r['student_input']['frame_indices'],type=r['question_type'],
            question=r['student_input']['question'],options=r['student_input']['options']))
        assert expected_cid==r['candidate_id']==m['candidate_id']
        source_relation=s['target'].splitlines()[2]
        relation_to_label={'to my left':'left','to my right':'right','in front of me, on my left':'front-left','in front of me, on my right':'front-right',
                           'behind me, on my left':'back-left','behind me, on my right':'back-right'}
        hits=[v for k,v in relation_to_label.items() if k in source_relation]
        assert len(hits)==1,(r['qid'],hits)
        assert hits[0]==(labels[s['answer']] if m['branch']=='a' else want)
        q=r['student_input']['question'];body=r['target'].splitlines()
        x,y,z=m['objects']
        assert ((f'facing the {y} from the {x}, I find the {z} ' in source_relation)
            or (f'standing at the {x} and facing the {y}, I find the {z} ' in source_relation)
            or (f'I stand at the {x} facing the {y}; I find the {z} ' in source_relation)
            or (f'I find the {z} ' in source_relation and source_relation.endswith(f'when I stand at the {x} facing the {y}.'))
            or (source_relation.startswith(f'If I stood at the {x} facing the {y}, the {z} would be '))),r['qid']
        if m['branch']=='a':
            assert q.startswith(f'At the {x}, face away from the {y}.')
            assert body[1]==f'Step 1: find the {x}, the {y} and the {z}.'
            assert body[2]==s['target'].splitlines()[2]
            assert body[3]==f'Step 3: I face away from the {y} by making a half turn. Front and back swap, and left and right swap.'
            assert r['facing']=='away'
        else:
            assert q.startswith(f'At the {x}, face toward the {y}.')
            assert body[1]==s['target'].splitlines()[1]
            assert body[1].startswith('Seen:') and body[3]==f'The question has me face toward the {y}; I keep that heading.'
            assert 'half turn' not in r['target'] and r['facing']=='toward'
        end=f'So I find the {z} '+(f'to my {want}.' if m['family']=='easy' else f'at my {want}.')
        assert body[4]==end and r['target'].endswith('\n</think>\n\n'+r['answer'])
        for item in (s,r):
            d.r2_contract.validate(item,'vqa',require_frames=False);assert not d.trace_grammar.validate_row(item)
            packed=env['direct_row'](item);assert packed['target']==item['target']
            assert r2_grammar.validate_direct(packed['target'],packed['student_input']['question'],len(packed['student_input']['frames']))==item['answer']
            assert not removal.match(item)
            canon,_=rooms.canonical(item);room=rooms.room(canon);assert not any(room in v for v in exclude.values())
        assert near(d.norm(q).encode(),cwords,len(words),0.10)==-1
        assert s['qid'] in r['label_row_keys']
        key=(m['branch'],m['family'],want);bycell[key]+=1;bybranch[m['branch']]+=1
        for item in (s,r):
            opening,_,clause=d.classify(item);names.setdefault((opening,clause),C.Counter()).update(m['objects'])
            triples.setdefault((opening,clause),C.Counter()).update([tuple(m['objects'])])
    assert dict(bybranch)=={'a':4000,'b':4000}
    for (b,f,l),n in bycell.items():assert n==(1440 if f=='easy' else 280)
    assert len(bycell)==12
    newq={r['qid'] for r in records};newc={r['candidate_id'] for r in records}
    for raw, in con.execute('select row from rows'):
        old=json.loads(raw);assert old['qid'] not in newq and old.get('candidate_id') not in newc
    for op in ('Step 1','Seen'):
        assert names[op,'toward']==names[op,'away']
        assert triples[op,'toward']==triples[op,'away']
    for rows in (records,originals):
        result=scene_division_gate.check_rows(rows,cfg['scene_division'],removals=removal)
        assert result==dict(read=8000,filtered=0,removed=0,outside=0,heldout=0,admitted=8000)
    readtext=(OUT/'READ60.md').read_text();blocks=re.findall(r'```json\n(.*?)\n```',readtext,re.S)
    assert len(blocks)==60
    source_by_new={r['qid']:(s,m) for r,s,m in zip(records,originals,maps)};record_by_id={r['qid']:r for r in records};reviewcounts=C.Counter()
    review=[]
    for j,blob in enumerate(blocks,1):
        r=json.loads(blob);assert r==record_by_id[r['qid']];s,m=source_by_new[r['qid']]
        reviewcounts[m['branch'],m['family'],m['label']]+=1
        review.append(f'{j}. {r["qid"]} | {m["family"]} | source {s["answer"]}: {m["source_label"]} -> {r["answer"]}: {m["label"]}\n'
            +r['student_input']['question']+'\n'+'; '.join(r['student_input']['options'])+'\n'+r['target']+'\n'
            +f'Frame metadata: all {len(r["student_input"]["frames"])} frame pins and indices equal the source; dataset/scene {r["dataset"]}/{r["scene"]}; full record parsed and compared.\n')
    assert len(reviewcounts)==12 and set(reviewcounts.values())=={5}
    (OUT/'REVIEW_TEXT60.md').write_text('\n'.join(review))
    before=C.Counter();after=C.Counter();added=C.Counter();teaching=C.Counter()
    survey=json.loads((OUT/'SURVEY.json').read_text())
    for m in survey['rows']:
        if not m['refused']:before[m['opening'],m['clause'],m['family'],m['label']]+=1
    def key(r):return (*d.classify(r)[::2],r['question_type'].rsplit('_',1)[1],om(r)[r['answer']])
    added.update(map(key,records));after=before+added;teaching.update(map(key,records+originals))
    hist=json.loads((OUT/'HISTOGRAMS.json').read_text())
    def uncell(rows):return C.Counter({tuple(r[k] for k in ('opening','clause','family','label')):r['rows'] for r in rows})
    assert uncell(hist['before_admitted'])==before and uncell(hist['after_admitted'])==after
    assert uncell(hist['additions'])==added and uncell(hist['teaching'])==teaching
    for name,c in [('per_clause_before',before),('per_clause_after',after),('per_clause_additions',added)]:
        counts=C.Counter()
        for (o,cl,f,l),n in c.items():counts[cl,f,l]+=n
        hist[name]=[dict(clause=cl,family=f,label=l,rows=n) for (cl,f,l),n in sorted(counts.items())]
    hist['input_sha256'][str(BASE/'verify_outputs.py')]=pins[str(BASE/'verify_outputs.py')]
    hist['command']+='; PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py'
    (OUT/'HISTOGRAMS.json').write_text(json.dumps(hist,indent=2,sort_keys=True)+'\n')
    result=dict(command='PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py',input_sha256=pins,status='PASS',rows=8000,
        source_identity=8000,source_reuse_max=1,N_native_direct_pack_validate=16000,independent_truth=8000,
        distance_implementation_independent_cases=distance_cases,
        scene_division_each_population=8000,field_differences=dict(diffs),new_wording_distances_pass=8000,
        opening_conditional_name_and_triple_balance='PASS on 16,000-row teaching subset',
        READ60_full_records_parsed_and_compared=60,READ60_review_text=60,
        manual_review='PENDING: read out/REVIEW_TEXT60.md before marking CHECKS.json ready')
    (OUT/'VERIFY.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (BASE/'STATUS.md').write_text('Independent verification passes for all 8,000 emitted rows and their 8,000 sources, including native packing, validators, exact field differences, answer mapping, room/removal/scene gates, question-distance filtering, and opening-conditional name/triple balance. All 60 full review records match the output exactly; their questions and traces await semantic reading before the final archive.\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'}))

if __name__=='__main__':main()
