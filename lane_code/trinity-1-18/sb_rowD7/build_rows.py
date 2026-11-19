"""Build fixed-quota easy/hard half-turn twins under N's sealed direct-row contract."""
import ast, collections as C, copy, ctypes, hashlib, heapq, json, re, sqlite3, sys
from pathlib import Path
import cpu_native
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
from survey import d, options, objects, authority
from student_pilot import scene_division_gate, r2_grammar
OUT=BASE/'out'
COMMAND='PYTHONDONTWRITEBYTECODE=1 python build_rows.py'
LABELS={'easy':('left','right'),'hard':('front-left','front-right','back-left','back-right')}
FLIP={'left':'right','right':'left','front':'back','back':'front'}
QUOTAS={(branch,family,label):(2000 if family=='easy' else 1000)
        for branch in ('a',) for family,labels in LABELS.items() for label in labels}
EDITED={'qid','pool','answer','target','facing','candidate_id','label_row_keys','student_input','provenance'}
# Load the exact CPU-only native pack functions without importing the trainer's torch dependency.
_pack_tree=ast.parse((d.TREE/'student_pilot/carrier_c1_routing.py').read_text())
_pack_nodes=[x for x in _pack_tree.body if isinstance(x,ast.FunctionDef) and x.name in ('require_training_think','direct_row')]
_pack_env=dict(__package__='student_pilot',THINK='<think>\n')
exec(compile(ast.Module(body=_pack_nodes,type_ignores=[]),str(d.TREE/'student_pilot/carrier_c1_routing.py'),'exec'),_pack_env)
native_pack=_pack_env['direct_row']

def sha(value):return hashlib.sha256(value.encode() if isinstance(value,str) else value).hexdigest()
def half(label):return '-'.join(FLIP[x] for x in label.split('-'))
def dump(name,**value):
    (OUT/name).write_text(json.dumps(dict(command=COMMAND,input_sha256=d.PINS,**value),indent=2,sort_keys=True)+'\n')
def cells(c,fields=('opening','clause','family','label')):
    return [dict(zip((*fields,'rows'),(*k,v))) for k,v in sorted(c.items())]
def row_cell(r):return (d.classify(r)[0],d.classify(r)[2],r['question_type'].rsplit('_',1)[1],options(r)[r['answer']])
def meta_cell(m):return (m['opening'],m['clause'],m['family'],m['label'])

def native_check(r):
    d.r2_contract.validate(r,'vqa',require_frames=False)
    assert not d.trace_grammar.validate_row(r),r['qid']
    assert 'canonical' not in r
    packed=native_pack(r)
    assert packed['target']==r['target']
    assert packed['student_input']['frames']==r['student_input']['frames']
    assert packed['student_input']['frame_indices']==r['student_input']['frame_indices']
    assert r2_grammar.validate_direct(packed['target'],packed['student_input']['question'],len(packed['student_input']['frames']))==r['answer']
    assert packed['routing']['answer']==packed['routing']['gt_answer']==r['answer']

def independent_truth(r,branch):
    """Read the source's reference-heading relation; rotate signed axes independently."""
    line=r['target'].splitlines()[2]
    z=objects(r)[2]
    # Isolate relation text so object names cannot supply direction words.
    tail=line.split(' would be ',1)[1] if branch=='b' else line.split(f'I find the {z} ',1)[1]
    tail=tail.split(' when I stand at the ',1)[0]
    lr=re.findall(r'\b(left|right)\b',tail)
    assert len(lr)==1,(r['qid'],line)
    x=-1 if lr[0]=='left' else 1
    family=r['question_type'].rsplit('_',1)[1]
    if family=='hard':
        front=bool(re.search(r'\bin front\b|\bahead\b',tail));back=bool(re.search(r'\bbehind\b|\bback\b',tail))
        assert front!=back,(r['qid'],line)
        y=1 if front else -1
    else:y=0
    baseline=('front-' if y>0 else 'back-' if y<0 else '')+('left' if x<0 else 'right')
    source_expected=baseline if branch=='a' else ('front-' if -y>0 else 'back-' if -y<0 else '')+('left' if -x<0 else 'right')
    assert source_expected==options(r)[r['answer']],(r['qid'],'source truth disagrees',baseline)
    if branch=='a':x,y=-x,-y
    target=('front-' if y>0 else 'back-' if y<0 else '')+('left' if x<0 else 'right')
    return target,baseline

def candidate_id(r):
    return d.candidate_identity(dict(qid=r['qid'],scene=r['scene'],frame_indices=r['student_input']['frame_indices'],
        type=r['question_type'],question=r['student_input']['question'],options=r['student_input']['options']))

def generate(source,m,branch):
    x,y,z=m['objects'];new=copy.deepcopy(source)
    toward=branch=='b';clause='toward' if toward else 'away'
    expected=half(options(source)[source['answer']]);truth,baseline=independent_truth(source,branch)
    assert truth==expected
    om=options(source);mapped={k:[j for j,v in om.items() if v==half(label)] for k,label in om.items()}
    assert all(len(v)==1 for v in mapped.values()) and len({v[0] for v in mapped.values()})==len(om)
    answer=mapped[source['answer']][0]
    from substitution import rewrite_question
    q,edit=rewrite_question(source['student_input']['question'],m['objects'])
    first=source['target'].splitlines()[1] if toward else f'Step 1: find the {x}, the {y} and the {z}.'
    relation={'left':'to my left','right':'to my right','front-left':'in front of me, on my left',
              'front-right':'in front of me, on my right','back-left':'behind me, on my left','back-right':'behind me, on my right'}[baseline]
    second=f'Standing at the {x} facing the {y}, I find the {z} {relation}.' if toward else source['target'].splitlines()[2]
    heading=f'The question has me face toward the {y}; I keep that heading.' if toward else \
        f'Step 3: I face away from the {y} by making a half turn. Front and back swap, and left and right swap.'
    final=f'So I find the {z} '+(f'to my {truth}.' if m['family']=='easy' else f'at my {truth}.')
    new.update(qid=source['qid']+'_sb_rowD7_'+branch,pool='sb_rowD7',answer=answer,facing=clause,
        target='<think>\n'+'\n'.join((first,second,heading,final))+'\n</think>\n\n'+answer)
    new['student_input']['question']=q
    new['candidate_id']=candidate_id(new)
    lineage=set(source.get('label_row_keys',[]));lineage.add(source['qid'])
    for k in ('source_qid','pair_id'):
        if source.get(k):lineage.add(source[k])
    if source['provenance'].get('source_qid'):lineage.add(source['provenance']['source_qid'])
    new['label_row_keys']=sorted(lineage)
    new['provenance']['sb_rowD7']=dict(source_qid=source['qid'],source_store_i=m['i'],source_row_sha256=m['source_sha256'],
        branch=branch,rule='rows_r1_easy_hard_bijective_half_turn',input_sha256={str(d.DB):d.DB_SHA},
        source_answer=source['answer'],source_label=om[source['answer']],mapped_label=truth,
        clause_edit=edit, room_resolution=dict(method='N Rooms with explicit tiered aliases; source scene token unchanged', alias_map=d.pin(d.BASE/'alias_inputs/out/TIERED_ALIAS_MAP.json')),
        generator_sha256=d.PINS[str(BASE/'build_rows.py')]['sha256'])
    unchanged=copy.deepcopy(new)
    for k in EDITED:
        if k in source:unchanged[k]=source[k]
        else:unchanged.pop(k,None)
    assert unchanged==source
    assert {k:v for k,v in source['student_input'].items() if k!='question'}=={k:v for k,v in new['student_input'].items() if k!='question'}
    assert {k:v for k,v in new['provenance'].items() if k!='sb_rowD7'}==source['provenance']
    native_check(source);native_check(new)
    return new,truth

def main():
    for p in (BASE/'build_rows.py',BASE/'survey.py',BASE/'edit_distance.cpp',BASE/'edit_distance.so',BASE/'substitution.py',BASE/'cpu_native.py',BASE/'reference/d2_support.py',BASE/'reference/check_away.py',BASE/'reference/build_away.py',BASE/'reference/COVERAGE_V2_PUB.tar',BASE/'reference/coverage_rows_v2.py'):
        d.pin(p)
    survey=d.load(OUT/'SURVEY.json');d.PINS.update(survey['input_sha256'])
    gate=d.load(Path('/scratch/jjyeung/orch_n30/sb_rowD5/out/GATE.json'))
    census=d.load(Path('/scratch/jjyeung/orch_n30/sb_rowD5/out/COUNTS.json'))
    d.pin('/scratch/jjyeung/orch_n30/sb_rowD5/out/EXAMPLES.json')
    d.pin(d.DB,d.DB_SHA)
    for name in ('BUILD_MANIFEST.json','FAMILY_INDEX_RANGES.json','COUNTS_V7.json','EXCLUSIONS.json'):d.pin(d.STORE/name)
    seal=d.load(d.TREE.parents[1]/'out/TREE_SEAL.json')
    assert seal['tree_sha256']=='780ca7b446a578c83a1b1a398a8d54c0503a7cca26309bae6a1b60f85ef2a278'
    con=sqlite3.connect(d.DB.as_uri()+'?mode=ro&immutable=1',uri=True)
    def get(i):
        raw=con.execute('select row from rows where i=?',(i,)).fetchone()[0]
        return json.loads(raw),sha(raw)
    # Execute the delivered original rule as well as the independent signed-axis diagnostic.
    tree=ast.parse((BASE/'reference/check_away.py').read_text())
    rule=next(x for x in ast.walk(tree) if isinstance(x,ast.If) and ast.unparse(x.test)=="typ == 'object_rel_direction_medium'")
    rulecode=compile(ast.Module(body=[rule],type_ignores=[]),'reference/check_away.py','exec')
    results=[];mismatches=C.Counter();exact=C.Counter()
    for rec in gate['comparisons']:
        t,ts=get(rec['toward_i']);a,ass=get(rec['away_i'])
        assert ts==rec['toward_row_sha256'] and ass==rec['away_row_sha256']
        forward=options(t)[t['answer']];stored=options(a)[a['answer']]
        literal=re.sub(r'\b(left|right|front|back)\b',lambda m:FLIP[m[0]],forward)
        if literal!=stored:mismatches[rec['family']]+=1
        env=dict(re=re,options=options,r=a,typ=a['question_type'],forward=forward)
        exec(rulecode,env);candidates=[k for k,v in options(a).items() if v in env['allowed']]
        om={}
        for v in options(t).values():
            env['forward']=v;exec(rulecode,env);om[v]=sorted(set(options(a).values()) & env['allowed'])
        bijective=all(len(v)==1 for v in om.values()) and len({v[0] for v in om.values() if len(v)==1})==len(om)
        passed=bijective and candidates==[a['answer']]
        if rec['family'] in LABELS:assert passed and literal==stored;exact[rec['family']]+=1
        else:assert not passed
        results.append(dict(toward_qid=t['qid'],away_qid=a['qid'],family=rec['family'],pass_exact_unique=passed,literal_match=literal==stored))
    assert dict(mismatches)=={'medium':1274} and dict(exact)=={'easy':3664,'hard':2182}
    dump('GATE.json',status='PASS',exact_unique=5846,required=5846,by_family=dict(exact),literal_disagreements=dict(mismatches),medium_pairs_refused=2665,comparisons=results)
    dump('PREFLIGHT.json',status='PASS',exact_unique=5846,literal_disagreements=dict(mismatches),medium_pairs_refused=2665)
    rooms,excluded,cfg,remove_pins,division=authority()
    removals=d.row_removals.Removals(remove_pins)
    for p in (cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions']):d.pin(p['path'],p['sha256'])
    corpus=d.load(OUT/'WORDING_CORPUS.json')
    words=sorted(set(d.norm(v['text']) for v in corpus['wordings']))
    # All collected and generated wording is ASCII after NFKC; byte distance equals character distance.
    assert all(w.isascii() for w in words)
    cwords=(ctypes.c_char_p*len(words))(*(w.encode() for w in words))
    lib=ctypes.CDLL(str(BASE/'edit_distance.so'));near=lib.close_wording
    near.argtypes=[ctypes.c_char_p,ctypes.POINTER(ctypes.c_char_p),ctypes.c_int,ctypes.c_double];near.restype=ctypes.c_int
    metadata=survey['rows'];byqid={m['qid']:m for m in metadata}
    candidates=[];refused=C.Counter();source_names=C.Counter();medium=sum(m['family']=='medium' for m in metadata)
    for m in metadata:
        if m['family']=='medium':continue
        if m['refused']:continue
        branch='a' if (m['opening'],m['clause'])==('Step 1','toward') else None
        if branch is None:continue
        m=dict(m,branch=branch,key=(branch,m['family'],half(m['label'])))
        candidates.append(m);source_names.update(set(m['objects']))
    heaps={branch:[] for branch in ('a',)}
    for j,m in enumerate(candidates):
        rarity=sum(1/source_names[n] for n in set(m['objects']))
        heapq.heappush(heaps[m['branch']],(-len(set(m['objects'])),-rarity,sha('sb_rowD7|'+m['qid']),j))
    out=[];sources=[];maps=[];filled=C.Counter();seen_names={b:set() for b in ('a',)};uses=C.Counter();attempted=0;word_checks=0;word_removed=[]
    before=C.Counter(tuple(c[k] for k in ('opening','clause','family','label')) for c in [])
    for m in metadata:
        if not m['refused']:before[meta_cell(m)]+=1
    allqids=set();allcids=set()
    for raw, in con.execute('select row from rows'):
        r=json.loads(raw);allqids.add(r['qid'])
        if r.get('candidate_id'):allcids.add(r['candidate_id'])
    for branch in ('a',):
        heap=heaps[branch]
        while heap and sum(filled[k] for k in QUOTAS if k[0]==branch)<8000:
            priority,rarity,h,j=heapq.heappop(heap);m=candidates[j];key=m['key']
            if filled[key]>=QUOTAS[key]:continue
            novelty=len(set(m['objects'])-seen_names[branch])
            if -priority!=novelty:
                heapq.heappush(heap,(-novelty,rarity,h,j));continue
            source,source_hash=get(m['i']);assert source_hash==m['source_sha256']
            attempted+=1
            assert not removals.match(source)
            # A mapped twin cannot shed an ancestor's removal key.
            lineage=[source.get('source_qid'),source.get('pair_id'),source['provenance'].get('source_qid')]
            if any(v and removals.match(dict(qid=v)) for v in lineage):
                refused['removed_ancestor']+=1;continue
            try:new,truth=generate(source,m,branch)
            except (AssertionError,ValueError) as exc:
                refused['source_or_native_check:'+str(exc)[:130]]+=1;continue
            normalized=d.norm(new['student_input']['question'])
            word_checks+=1;hit=near(normalized.encode(),cwords,len(words),0.10)
            if hit>=0:
                refused['wording_distance']+=1;word_removed.append(dict(source_qid=source['qid'],matching_wording=words[hit]));continue
            canonical,_=rooms.canonical(new);room=rooms.room(canonical) if canonical else None
            assert room and not any(room in v for v in excluded.values())
            assert not removals.match(new)
            assert new['qid'] not in allqids and new['candidate_id'] not in allcids
            if branch=='b':
                paired=byqid[source['pair_id']];assert not paired['refused']
                t,_=get(paired['i']);assert options(t)[t['answer']]==truth
                assert objects(t)==m['objects'] and t['scene']==source['scene']
                assert {k:v for k,v in t['student_input'].items() if k not in ('question','options')}=={k:v for k,v in source['student_input'].items() if k not in ('question','options')}
            maps.append(dict(qid=new['qid'],candidate_id=new['candidate_id'],source_qid=source['qid'],source_i=m['i'],source_row_sha256=source_hash,
                branch=branch,source_opening=m['opening'],source_clause=m['clause'],new_opening=d.classify(new)[0],new_clause=new['facing'],
                family=m['family'],source_answer=source['answer'],source_label=m['label'],answer=new['answer'],label=truth,objects=m['objects'],room=room,
                input_sha256={str(d.DB):d.DB_SHA,str(BASE/'build_rows.py'):d.PINS[str(BASE/'build_rows.py')]['sha256']}))
            out.append(new);sources.append(source);filled[key]+=1;uses[source['qid']]+=1;seen_names[branch].update(m['objects'])
            allqids.add(new['qid']);allcids.add(new['candidate_id'])
        assert all(filled[k]==n for k,n in QUOTAS.items() if k[0]==branch),('SHORT_CELL',branch,filled,refused)
    assert len(out)==8000 and max(uses.values())==1
    from student_pilot.s1_exclusions import Exclusions
    scene_filter=Exclusions(cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions'])
    gate_new=scene_division_gate.check_rows(out,cfg['scene_division'],removals=removals,scene_filter=scene_filter)
    gate_source=scene_division_gate.check_rows(sources,cfg['scene_division'],removals=removals,scene_filter=scene_filter)
    assert gate_new['admitted']==gate_source['admitted']==8000
    additions=C.Counter(map(row_cell,out));teaching=C.Counter(map(row_cell,sources+out));after=before+additions
    teaching_open=C.Counter((o,c) for o,c,f,l in map(row_cell,sources+out));assert set(teaching_open.values())=={8000}
    names_by_clause={c:C.Counter(n for r in sources+out if d.classify(r)[2]==c for n in objects(r)) for c in ('toward','away')}
    assert names_by_clause['toward']==names_by_clause['away']
    full_name_counts=C.Counter(n for m in metadata if not m['refused'] and m['opening']=='Step 1' and m['family'] in LABELS for n in m['objects'])
    seen_original_names={n for m in metadata if not m['refused'] and m['opening']=='Seen' and m['clause']=='away' and m['family'] in LABELS for n in m['objects']}
    for mod in list(sys.modules.values()):
        p=getattr(mod,'__file__',None)
        if p and str(p).startswith(str(d.TREE)) and str(p).endswith('.py'):d.pin(p,seal['files'][str(Path(p).relative_to(d.TREE))])
    d.pin(d.TREE/'student_pilot/carrier_c1_routing.py',seal['files']['student_pilot/carrier_c1_routing.py'])
    for name,rows in [('NEW_ROWS.jsonl',out),('SOURCE_MAP.jsonl',maps)]:
        (OUT/name).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows))
    dump('TEACHING_SET.json',status='PASS',new_rows=8000,existing_source_rows=8000,rows=16000,
        existing_sources=[dict(qid=m['source_qid'],store_i=m['source_i'],row_sha256=m['source_row_sha256']) for m in maps],
        new_rows_pin=d.pin(OUT/'NEW_ROWS.jsonl'),instruction='Pair these pinned existing v7 sources with the new rows. Existing sources are references, not additional new rows.',cells=cells(teaching))
    dump('HISTOGRAMS.json',status='PASS',before_admitted=cells(before),after_admitted=cells(after),additions=cells(additions),teaching=cells(teaching),
        v7_before=survey['before'],per_clause_before=cells(C.Counter({}),('clause','label')),
        names_by_clause={k:dict(v) for k,v in names_by_clause.items()},new_names_by_branch={k:sorted(v) for k,v in seen_names.items()},
        toward_only_source_name_population=len(full_name_counts),new_away_names=len(seen_names['a']),
        new_away_names_absent_from_old_away=sorted(seen_names['a']-seen_original_names))
    dump('REFUSALS.json',medium_direction_rows_refused=medium,medium_existing_pairs_refused=2665,
        room_removal_hits=survey['blocked'],candidate_refusals=dict(refused),wording_refusals=word_removed,
        candidate_count=len(candidates),attempted=attempted,selected=8000)
    # Five rows per branch/family/answer cell; sixty complete serialized records.
    selected=[]
    for key in sorted(QUOTAS):
        rows=[r for r,m in zip(out,maps) if (m['branch'],m['family'],m['label'])==key]
        selected.extend(sorted(rows,key=lambda r:sha('READ60|'+r['qid']))[:10])
    assert len(selected)==60
    for name,n in [('READ60.md',60),('READ30.md',30)]:
        text='Complete generated rows for grammar, heading, frame preservation and answer review.\n\n'
        for j,r in enumerate(selected[:n],1):text+=f'## {j}. {r["qid"]}\n\n```json\n'+json.dumps(r,ensure_ascii=False,indent=2)+'\n```\n\n'
        (OUT/name).write_text(text)
    dump('CHECKS.json',status='PENDING_INDEPENDENT_REVIEW',binding_ready=False,new_rows=8000,tree_sha256=seal['tree_sha256'],
        gate=dict(required=5846,exact_unique=5846,literal_disagreements=dict(mismatches),medium_pairs_refused=2665),
        exact_cell_counts=dict(status='PASS',cells=cells(filled,('branch','family','label'))),
        source_reuse=dict(status='PASS',max=1,sources=8000),N_direct_pack_validate=dict(status='PASS',new=8000,sources=8000,
            pack='carrier_c1_routing.direct_row (exact function AST, avoiding torch-only trainer import)',validators=['r2_contract.validate(vqa)','trace_grammar.validate_row','r2_grammar.validate_direct(packed target)']),
        unique_qids_candidate_ids='PASS; new identifiers do not collide with any v7 identifiers',candidate_formula='ground_v312_quality.candidate_identity; native direct input adapter; default revision 3.12.2',
        field_diff=dict(status='PASS',edited_fields=sorted(EDITED),student_input='question only',provenance='sb_rowD7 only'),
        independent_truth=dict(status='PASS',rows=8000,method='Parse source reference-heading relation and rotate signed axes.',
            authority='Pinned v7 answers under the authorized easy/hard mapping; no new geometry inference.'),
        scene_division=dict(status='PASS',new=gate_new,sources=gate_source,pin=cfg['scene_division']),removal_inputs=remove_pins,
        room_rule=dict(status='PASS',new_hits=0,source_hits=0,lists=list(excluded),alias_map=d.pin(d.BASE/'alias_inputs/out/TIERED_ALIAS_MAP.json'),native_strict_rooms='Measured separately in ROOM_RESOLUTION.json'),
        normalized_edit_distance=dict(status='PASS',threshold=0.10,rule='reject distance / max normalized character length <= threshold',
            normalization='NFKC, casefold, whitespace collapse',unique_wordings=len(words),candidate_questions=word_checks,
            logical_comparisons=word_checks*len(words),removed=len(word_removed),corpus=d.pin(OUT/'WORDING_CORPUS.json'),limitation=corpus['limitation']),
        teaching_balance=dict(status='PASS',opening_clause_cells=cells(teaching_open,('opening','clause')),object_name_histograms_identical_by_clause=True,
            scope='16,000-row source-plus-twin teaching subset; the 8,000 additions alone contain only Step 1/away.'),
        READ60=dict(status='PENDING',rows=60),outputs={p.name:d.pin(p) for p in (OUT/'NEW_ROWS.jsonl',OUT/'SOURCE_MAP.jsonl',OUT/'READ60.md',OUT/'READ30.md')})
    (BASE/'STATUS.md').write_text('The generator produced exactly 8,000 easy/hard twins with fixed answer-label quotas, balanced hard quadrants, and no source reuse. N’s direct pack and validators, full scene division, room gates, removal inheritance, field preservation and independent signed-axis truth checks pass. The 60 complete rows and independent verification remain for review before packaging.\n')
    print(json.dumps(dict(rows=len(out),filled=cells(filled,('branch','family','label')),refused=sum(refused.values()),names={k:len(v) for k,v in seen_names.items()},scene_gate=gate_new)))

if __name__=='__main__':main()
