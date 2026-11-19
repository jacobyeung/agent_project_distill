"""D7's verify_outputs.py ported to the filtered sb_rowD7f rows: counts and cells come from FILTER.json,
traces copy the source's Step 1, Step 2 and final-line form, and twins carry no `facing` field."""
import ast, collections as C, copy, ctypes, hashlib, json, re, sqlite3, sys
from pathlib import Path
import cpu_native
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'reference'))
import d2_support as d
d.BASE=Path('/scratch/jjyeung/orch_n30/sb_rowD2')
from student_pilot import scene_division_gate, r2_grammar
OUT=BASE/'out'
FOUT=BASE.parent/'out'

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
    for p in (BASE/'verify_filtered.py',OUT/'NEW_ROWS.jsonl',OUT/'SOURCE_MAP.jsonl',OUT/'GATE.json',FOUT/'NEW_ROWS.jsonl',FOUT/'SOURCE_MAP.jsonl',FOUT/'TEACHING_SET.json',FOUT/'FILTER.json'):
        pins[str(p)]=dict(sha256=digest(p),bytes=p.stat().st_size)
    filt=json.loads((FOUT/'FILTER.json').read_text());N=filt['rows_out']
    rebuilt=set((OUT/'NEW_ROWS.jsonl').read_text().splitlines());rebuilt_maps=set((OUT/'SOURCE_MAP.jsonl').read_text().splitlines())
    lines=(FOUT/'NEW_ROWS.jsonl').read_text().splitlines();mlines=(FOUT/'SOURCE_MAP.jsonl').read_text().splitlines()
    # The filter re-cites nothing, so every delivered row and map line is byte-identical to the rebuilt one.
    assert all(x in rebuilt for x in lines) and all(x in rebuilt_maps for x in mlines)
    records=[json.loads(x) for x in lines]
    maps=[json.loads(x) for x in mlines]
    assert len(records)==len(maps)==N
    assert len({x['qid'] for x in records})==len({x['candidate_id'] for x in records})==N
    assert len({x['source_qid'] for x in maps})==N
    teach=json.loads((FOUT/'TEACHING_SET.json').read_text())
    assert [x['qid'] for x in teach['existing_sources']]==[m['source_qid'] for m in maps] and teach['rows']==2*N
    turn={'left':'right','right':'left','front-left':'back-right','front-right':'back-left','back-left':'front-right','back-right':'front-left'}
    bybranch=C.Counter();bycell=C.Counter();names={};triples={};diffs=C.Counter();originals=[]
    tree=ast.parse((d.TREE/'student_pilot/carrier_c1_routing.py').read_text())
    nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('require_training_think','direct_row')]
    env=dict(__package__='student_pilot',THINK='<think>\n')
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'native_direct_pack','exec'),env)
    con=sqlite3.connect(d.DB.as_uri()+'?mode=ro&immutable=1',uri=True)
    cfg=json.loads((d.KIT/'w20/work/build20/inputs/config.json').read_text())
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
    for text in ['', 'a', 'abcdefghij', 'headings and quadrants', 'left—right', 'café', '椅子', *words[:10]]:
        for other in [text,text+'x',text[::-1],text[1:],'different words']:
            one=(ctypes.c_char_p*1)(other.encode())
            assert (near(text.encode(),one,1,0.10)>=0)==(lev(text,other)<=0.10*max(len(text),len(other))+1e-10)
            distance_cases+=1
    for r,m in zip(records,maps,strict=True):
        raw=con.execute('select row from rows where i=?',(m['source_i'],)).fetchone()[0];s=json.loads(raw)
        assert hashlib.sha256(raw.encode()).hexdigest()==m['source_row_sha256']
        assert s['qid']==m['source_qid'] and r['qid']==m['qid']==s['qid']+'_sb_rowD7f_'+m['branch']
        assert 'facing' not in r and 'facing' not in s
        originals.append(s)
        paths=list(changed(s,r));diffs.update(paths)
        allowed={'qid','pool','answer','target','candidate_id','label_row_keys','student_input.question','provenance.sb_rowD7'}
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
            edit=r['provenance']['sb_rowD7']['clause_edit']
            sq=s['student_input']['question']
            assert sq[edit['start']:edit['end']]==edit['source_clause']
            assert q==sq[:edit['start']]+edit['new_clause']+sq[edit['end']:]
            assert edit['new_clause'] in ('face away from','facing away from')
            assert body[1]==s['target'].splitlines()[1]
            assert body[2]==s['target'].splitlines()[2]
            assert body[3]==f'Step 3: I face away from the {y} by making a half turn. Front and back swap, and left and right swap.'
        else:
            raise AssertionError('branch b is not built')
        sfinal=s['target'].splitlines()[4];prep='to' if m['family']=='easy' else 'at'
        sm=re.fullmatch(rf'(So I find (?:the position of )?the {re.escape(z)} {prep} my )([\w-]+)\.',sfinal)
        assert sm and sm[2]==labels[s['answer']],(r['qid'],sfinal)
        assert body[4]==sm[1]+want+'.' and r['target'].endswith('\n</think>\n\n'+r['answer'])
        assert len(body)==len(s['target'].splitlines()) and [i for i,(a,b) in enumerate(zip(body,s['target'].splitlines())) if a!=b][:3]==[3,4,7]
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
    assert dict(bybranch)=={'a':N}
    assert {f'{f}/{l}':n for (b,f,l),n in bycell.items()}==filt['cells_out']
    assert len(bycell)==6
    newq={r['qid'] for r in records};newc={r['candidate_id'] for r in records}
    for raw, in con.execute('select row from rows'):
        old=json.loads(raw);assert old['qid'] not in newq and old.get('candidate_id') not in newc
    for op in ('Step 1',):
        assert names[op,'toward']==names[op,'away']
        assert triples[op,'toward']==triples[op,'away']
    from student_pilot.s1_exclusions import Exclusions
    scene_filter=Exclusions(cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions'])
    for rows in (records,originals):
        result=scene_division_gate.check_rows(rows,cfg['scene_division'],removals=removal,scene_filter=scene_filter)
        assert result==dict(read=N,filtered=0,removed=0,outside=0,heldout=0,admitted=N),result
    def key(r):return (*d.classify(r)[::2],r['question_type'].rsplit('_',1)[1],om(r)[r['answer']])
    teaching=C.Counter(map(key,records+originals))
    clause_by_cell=C.defaultdict(C.Counter)
    for (o,cl,f,l),n in teaching.items():clause_by_cell[o,f][cl]+=n
    assert all(c['toward']==c['away'] for c in clause_by_cell.values()),dict(clause_by_cell)
    result=dict(command='nice -n 10 python d7/verify_filtered.py',input_sha256=pins,status='PASS',rows=N,
        rows_byte_identical_to_rebuild=N,source_identity=N,source_reuse_max=1,N_native_direct_pack_validate=2*N,independent_truth=N,
        distance_implementation_independent_cases=distance_cases,cells=filt['cells_out'],
        scene_division_each_population=N,field_differences=dict(diffs),new_wording_distances_pass=N,
        opening_conditional_name_and_triple_balance=f'PASS on {2*N:,}-row teaching subset',
        teaching_cells={'|'.join(k):v for k,v in sorted(teaching.items())},
        trace_lines_changed_vs_source='Step-3 line and final-line label only (target lines 3, 4 and the answer letter)')
    (FOUT/'VERIFY_FILTERED.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'}))

if __name__=='__main__':main()
