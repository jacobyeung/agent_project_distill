"""Run the exactness gate first. Exit 2 refuses a build that cannot reproduce all twins."""
import ast
import collections as C
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
OUT = BASE / 'out'
sys.path.insert(0, str(BASE / 'reference'))
import d2_support as d
d.BASE = Path('/scratch/jjyeung/orch_n30/sb_rowD2')
COMMAND = 'PYTHONDONTWRITEBYTECODE=1 python build_rows.py'

def dump(name, **value):
    (OUT/name).write_text(json.dumps(dict(command=COMMAND,input_sha256=d.PINS,**value),indent=2,sort_keys=True)+'\n')

def objects(r):
    line=r['target'].splitlines()[1]
    if line.startswith('Seen:'):
        m=re.fullmatch(r'Seen: (.+?) in frame (\d+); (.+?) in frame (\d+); (.+?) in frame (\d+)\.',line)
        assert m,line
        return (m[1],m[3],m[5])
    m=re.fullmatch(r'Step 1: (?:find|locate) the (.+?), the (.+?) and the (.+)\.',line)
    if not m:m=re.fullmatch(r'Step 1: (?:find|locate) the (.+?) and the (.+?), then the (.+)\.',line)
    assert m,line
    return m.groups()

def cell_rows(c):
    return [dict(opening=o,clause=k,answer_label=a,rows=n) for (o,k,a),n in sorted(c.items())]

def main():
    OUT.mkdir(exist_ok=True)
    for p in (Path(__file__),Path(d.__file__),BASE/'reference/build_away.py',BASE/'reference/check_away.py'):
        d.pin(p)
    record=json.loads((BASE/'reference/NFS_INPUTS.json').read_text())
    d.PINS.update(record['input_sha256'])
    for p in sorted((BASE/'reference').glob('*.md')):d.pin(p)
    d.pin(d.DB,d.DB_SHA)
    for name in ('BUILD_MANIFEST.json','COUNTS_V7.json','FAMILY_INDEX_RANGES.json','EXCLUSIONS.json'):d.pin(d.STORE/name)
    seal=d.load(d.TREE.parents[1]/'out/TREE_SEAL.json')
    assert seal['tree_sha256']=='8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa'
    rooms,excluded=d.room_authority()
    removal_paths=[d.KIT/'inputs/records/n.json',d.KIT/'inputs/records/z.json',Path('/scratch/jjyeung/orch_n30/sb_k1list/out/u_union.json')]
    removals=d.row_removals.Removals([{k:v for k,v in d.pin(p).items() if k in ('path','sha256')} for p in removal_paths])
    # Execute the exact option parser and type-specific rule from the delivered checker.
    tree=ast.parse((BASE/'reference/check_away.py').read_text())
    parser=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='options')
    rule=next(x for x in ast.walk(tree) if isinstance(x,ast.If) and ast.unparse(x.test)=="typ == 'object_rel_direction_medium'")
    env={'re':re}
    exec(compile(ast.Module(body=[parser],type_ignores=[]),'reference/check_away.py','exec'),env)
    options=env['options'];rulecode=compile(ast.Module(body=[rule],type_ignores=[]),'reference/check_away.py','exec')
    before=C.Counter();eligible=C.Counter();blocked=C.Counter();meta={};twins={};away=[];all_ids=set();validations=0
    con=sqlite3.connect(d.DB.as_uri()+'?mode=ro&immutable=1',uri=True)
    total=0
    for i,raw in con.execute('SELECT i,row FROM rows ORDER BY i'):
        total+=1;r=json.loads(raw);qid=r['qid'];assert qid not in all_ids;all_ids.add(qid)
        if not r.get('question_type','').startswith('object_rel_direction_'):continue
        opening,_,clause=d.classify(r);assert clause!='UNKNOWN'
        label=options(r)[r['answer']];before[opening,clause,label]+=1
        canonical,_=rooms.canonical(r);room=rooms.room(canonical) if canonical else None;assert room
        hits=[k for k,v in excluded.items() if room in v];rm=removals.match(r)
        allowed=not hits and not rm
        if allowed:eligible[opening,clause,label]+=1
        for h in hits:blocked['room:'+h]+=1
        for j in rm:blocked['removal:'+removal_paths[j].name]+=1
        d.r2_contract.validate(r,'vqa',require_frames=False)
        assert not d.trace_grammar.validate_row(r),qid
        validations+=1
        m=dict(i=i,qid=qid,answer=r['answer'],label=label,options=r['student_input']['options'],
            family=r['question_type'].rsplit('_',1)[1],pair_id=r.get('pair_id'),
            dataset=r['dataset'],scene=r['scene'],objects=objects(r),eligible=allowed,room=room,
            excluded_by=hits,removal_lists=[str(removal_paths[j]) for j in rm],
            source_row_sha256=hashlib.sha256(raw.encode()).hexdigest())
        meta[qid]=m
        if r.get('facing')=='toward':
            assert r['pair_id'] not in twins
            twins[r['pair_id']]=qid
        if r.get('pool')=='r1_away_opp':away.append(qid)
    assert total==204413 and validations==93370 and len(away)==8511
    (BASE/'STATUS.md').write_text('The pinned v7 store has 204,413 rows and 8,511 opposite-worded away twins. All 93,370 direction rows pass N’s direct schema and trace validators. Exact answer reproduction is being checked with the delivered type-specific rule.\n')
    def row(m):return json.loads(con.execute('SELECT row FROM rows WHERE i=?',(m['i'],)).fetchone()[0])
    comparisons=[];stats=C.Counter();trans=C.Counter();examples=[]
    for qid in away:
        a=meta[qid];t=meta[twins[a['pair_id']]];ar=row(a);tr=row(t)
        for k in ('dataset','scene','objects','pair_id','family'):assert a[k]==t[k],(qid,k)
        assert {k:v for k,v in ar['student_input'].items() if k not in ('question','options')}=={k:v for k,v in tr['student_input'].items() if k not in ('question','options')}
        assert ar['provenance']['source']==tr['provenance']['source']
        assert ar['provenance']['source_qid']==tr['provenance']['source_qid']
        original_qid=ar['provenance']['rendering']['derived_from_v6_qid']
        original=row(meta[original_qid])
        assert original['answer']==ar['answer'] and original['student_input']['options']==ar['student_input']['options']
        local=dict(env,r=ar,typ=ar['question_type'],forward=t['label'])
        exec(rulecode,local);allowed=local['allowed'];consistent=a['label'] in allowed
        candidates=[k for k,v in options(ar).items() if v in allowed]
        exact=len(candidates)==1 and candidates[0]==ar['answer']
        option_map={}
        for label in options(tr).values():
            local['forward']=label;exec(rulecode,local)
            option_map[label]=sorted(set(options(ar).values()) & local['allowed'])
        bijective=all(len(v)==1 for v in option_map.values()) and len({v[0] for v in option_map.values() if len(v)==1})==len(option_map)
        # This diagnostic is expressly not substituted for the supplied medium rule.
        literal=re.sub(r'\b(left|right|front|back)\b',lambda m:dict(left='right',right='left',front='back',back='front')[m[0]],t['label'])
        reason='PASS' if exact and bijective else 'AMBIGUOUS_MEDIUM_OPTIONS' if len(candidates)>1 else 'ANSWER_DISAGREEMENT'
        rec=dict(toward_qid=t['qid'],away_qid=qid,toward_i=t['i'],away_i=a['i'],family=a['family'],
            toward_answer=t['answer'],toward_label=t['label'],stored_away_answer=a['answer'],stored_away_label=a['label'],
            allowed_away_labels=sorted(allowed),candidate_away_answers=candidates,option_map=option_map,
            exact_unique_reproduction=exact,option_bijection=bijective,consistency_pass=consistent,reason=reason,
            literal_flip_diagnostic=literal,literal_flip_matches=literal==a['label'],
            both_eligible=t['eligible'] and a['eligible'],toward_row_sha256=t['source_row_sha256'],away_row_sha256=a['source_row_sha256'])
        comparisons.append(rec);stats[a['family'],reason]+=1;trans[a['family'],t['label'],a['label']]+=1
        if reason!='PASS' and len(examples)<12:examples.append(dict(comparison=rec,toward=tr,away=ar))
    con.close()
    for mod in list(sys.modules.values()):
        path=getattr(mod,'__file__',None)
        if path and str(path).startswith(str(d.TREE)) and str(path).endswith('.py'):
            d.pin(path,seal['files'][str(Path(path).relative_to(d.TREE))])
    failures=[x for x in comparisons if x['reason']!='PASS']
    mismatches=[x for x in comparisons if not x['literal_flip_matches']]
    assert failures,'Gate passed: implement the authorized build; do not emit an empty successful packet.'
    dump('GATE.json',status='FAIL_STOP',required_exact=8511,exact_unique=sum(x['exact_unique_reproduction'] and x['option_bijection'] for x in comparisons),
        ambiguous_or_disagreeing=len(failures),set_consistency_pass=sum(x['consistency_pass'] for x in comparisons),
        literal_flip_diagnostic_disagreements=len(mismatches),
        original_away_answer_preserved=8511,source_pair_identity_pass=8511,
        by_family=[dict(family=f,result=r,rows=n) for (f,r),n in sorted(stats.items())],
        transitions=[dict(family=f,toward_label=t,away_label=a,rows=n) for (f,t,a),n in sorted(trans.items())],
        comparisons=comparisons,failures=failures,literal_flip_disagreements=mismatches)
    dump('EXAMPLES.json',status='FAIL_STOP',examples=examples)
    dump('COUNTS.json',status='UNCHANGED_GATE_FAILED',store_rows=total,direction_rows=validations,
        before=cell_rows(before),after=cell_rows(before),admitted_before=cell_rows(eligible),admitted_after=cell_rows(eligible),
        exclusion_hits=dict(blocked),new_rows=0,split=dict(away=0,toward=0),
        label_note='Exact answer labels are retained; easy left/right and medium back/left/right are not four quadrants.')
    dump('CHECKS.json',status='FAIL_STOP',binding_ready=False,new_rows=0,gate='FAIL',tree_sha256=seal['tree_sha256'],
        gate_exact_unique=8511-len(failures),gate_required=8511,gate_ambiguous_or_disagreeing=len(failures),
        direct_source_validator_pass=validations,source_trace_grammar_pass=validations,unique_store_qids=len(all_ids),
        removal_inputs=[str(p) for p in removal_paths],room_and_removal_filters='APPLIED_TO_ALL_DIRECTION_SOURCES',
        required_new_row_checks={k:'NOT_RUN_GATE_FAILED' for k in ('exact_cell_counts','source_reuse','N_pack_validate','unique_qids_candidate_ids','field_diff','independent_GT','room_removal_inheritance','wording_distance','READ60')},
        new_rows_status='MISSING: mandatory exactness gate failed',
        direct_pack_note='Direct v7 rows have no ground_record/events; N r2_contract.validate and trace_grammar validate their existing schema. No new row pack is claimed.')
    (OUT/'NEW_ROWS.jsonl').write_text('');(OUT/'SOURCE_MAP.jsonl').write_text('')
    (OUT/'READ60.md').write_text('NOT RUN: the exactness gate failed before generation. No new rows exist for the required 60-row review. EXAMPLES.json contains complete existing source/twin records for the gate failure.\n')
    (BASE/'STATUS.md').write_text(f'The mandatory gate failed: {8511-len(failures):,} of 8,511 twins have an exact, unique answer mapping; {len(failures):,} fail that requirement. All 8,511 pass the supplied set-valued consistency rule. No new rows were generated. The failure evidence and unchanged histograms are written; artifact verification and packaging remain.\n')
    print(json.dumps(dict(status='FAIL_STOP',exact=8511-len(failures),failed=len(failures),literal_disagreements=len(mismatches),by_family={str(k):v for k,v in stats.items()},exclusions=dict(blocked))))
    return 2

if __name__=='__main__':sys.exit(main())
