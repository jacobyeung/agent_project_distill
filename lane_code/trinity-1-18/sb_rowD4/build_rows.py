"""Gate the requested answer-label half turn against every existing paired clause.
Exit 2 means the exactness gate failed; no training rows are emitted.
"""
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
sys.path.insert(0, '/scratch/jjyeung/orch_n30/sb_rowD3')
import d2_support as d

d.BASE = Path('/scratch/jjyeung/orch_n30/sb_rowD2')
COMMAND = 'PYTHONDONTWRITEBYTECODE=1 python build_rows.py'

def dump(name, value):
    (OUT/name).write_text(json.dumps(dict(command=COMMAND, input_sha256=d.PINS, **value), indent=2, sort_keys=True)+'\n')

def names(row):
    first=row['target'].splitlines()[1]
    if first.startswith('Seen:'):
        m=re.fullmatch(r'Seen: (.+?) in frame (\d+); (.+?) in frame (\d+); (.+?) in frame (\d+)\.',first)
        assert m,first
        return (m[1],m[3],m[5])
    m=re.fullmatch(r'Step 1: (?:find|locate) the (.+?), the (.+?) and the (.+)\.',first)
    if not m:m=re.fullmatch(r'Step 1: (?:find|locate) the (.+?) and the (.+?), then the (.+)\.',first)
    assert m,first
    return m.groups()

def content(row):
    opts={x.split('. ',1)[0]:x.split('. ',1)[1] for x in row['student_input']['options']}
    return opts[row['answer']]

def flip(label):
    return '-'.join({'front':'back','back':'front','left':'right','right':'left'}[x] for x in label.split('-'))

def table(counter):
    return [dict(opening=o,clause=c,rows=counter[o,c]) for o in ('Step 1','Seen') for c in ('toward','away','opposite')]

def main():
    OUT.mkdir(exist_ok=True)
    d.pin(__file__);d.pin(d.__file__);d.pin(d.DB,d.DB_SHA)
    for name in ('BUILD_MANIFEST.json','COUNTS_V7.json','FAMILY_INDEX_RANGES.json','EXCLUSIONS.json'):d.pin(d.STORE/name)
    seal=d.load(d.TREE.parents[1]/'out/TREE_SEAL.json')
    assert seal['tree_sha256'].startswith('8ea1fe6b')
    rooms,excluded=d.room_authority()
    removal_paths=[d.KIT/'inputs/records/n.json',d.KIT/'inputs/records/z.json',Path('/scratch/jjyeung/orch_n30/sb_k1list/out/u_union.json')]
    removals=d.row_removals.Removals([{k:v for k,v in d.pin(p).items() if k in ('path','sha256')} for p in removal_paths])
    before=C.Counter();eligible=C.Counter();families=C.Counter();blocked=C.Counter();validation=C.Counter()
    groups=C.defaultdict(dict);flat={};ids=set();all_n=0
    con=sqlite3.connect(d.DB.as_uri()+'?mode=ro&immutable=1',uri=True)
    for i,raw in con.execute('SELECT i,row FROM rows ORDER BY i'):
        all_n+=1;r=json.loads(raw)
        assert r['qid'] not in ids;ids.add(r['qid'])
        if not r.get('question_type','').startswith('object_rel_direction_'):continue
        opening,_,clause=d.classify(r);assert clause!='UNKNOWN'
        before[opening,clause]+=1
        canonical,_=rooms.canonical(r);room=rooms.room(canonical) if canonical else None
        assert room,r['qid']
        hits=[k for k,v in excluded.items() if room in v]
        rm=removals.match(r)
        allowed=not hits and not rm
        if allowed:eligible[opening,clause]+=1
        for h in hits:blocked['room:'+h]+=1
        for j in rm:blocked['removal:'+removal_paths[j].name]+=1
        d.r2_contract.validate(r,'vqa',require_frames=False)
        violations=d.trace_grammar.validate_row(r);assert not violations,(r['qid'],violations)
        validation['native_validator_pass']+=1;validation['trace_grammar_pass']+=1
        m=dict(i=i,qid=r['qid'],dataset=r['dataset'],scene=r['scene'],objects=names(r),
               family=r['question_type'].rsplit('_',1)[1],opening=opening,clause=clause,
               question=r['student_input']['question'],options=r['student_input']['options'],
               answer=r['answer'],label=content(r),target=r['target'],room=room,eligible=allowed,
               excluded_by=hits,removal_lists=[str(removal_paths[j]) for j in rm],
               row_sha256=hashlib.sha256(raw.encode()).hexdigest(),
               source=r['provenance']['source'],source_qid=r['provenance'].get('source_qid'),
               frames_sha256=hashlib.sha256(json.dumps({k:v for k,v in r['student_input'].items() if k not in ('question','options')},sort_keys=True).encode()).hexdigest())
        flat[r['qid']]=m;families[m['family'],opening,clause]+=1
        if opening=='Seen':
            key=(r['dataset'],r['scene'],r['question_type'],m['objects'],r['pair_id'])
            assert clause not in groups[key],key
            groups[key][clause]=m
    assert all_n==204413 and sum(before.values())==93370
    stats=C.Counter();trans=C.Counter();failures=[];pairs=[];identity_checks=0
    for key,g in groups.items():
        assert 'toward' in g and 'away' in g,key
        t=g['toward']
        for clause in ('away','opposite'):
            if clause not in g:continue
            a=g[clause]
            assert (t['frames_sha256'],t['source'],t['source_qid'])==(a['frames_sha256'],a['source'],a['source_qid']),key
            identity_checks+=1
            expected=flip(t['label']);passed=expected==a['label']
            rec=dict(family=t['family'],clause=clause,toward_qid=t['qid'],turn_qid=a['qid'],
                     toward_i=t['i'],turn_i=a['i'],toward_label=t['label'],expected_turn_label=expected,
                     stored_turn_label=a['label'],pass_exact=passed,both_eligible=t['eligible'] and a['eligible'])
            pairs.append(rec);stats[t['family'],clause,'pass' if passed else 'fail']+=1
            trans[t['family'],clause,t['label'],a['label']]+=1
            if not passed:failures.append(rec)
        if 'opposite' in g:assert g['away']['label']==g['opposite']['label'],key
    for mod in list(sys.modules.values()):
        path=getattr(mod,'__file__',None)
        if path and str(path).startswith(str(d.TREE)) and str(path).endswith('.py'):
            d.pin(path,seal['files'][str(Path(path).relative_to(d.TREE))])
    for rel in ('generator/derivgen_v7/derivgen/ground_v312.py','student_pilot/ground_rows.py'):
        d.pin(d.TREE/rel,seal['files'][rel])
    assert failures,'The gate passed; implement the authorized build before emitting any package.'
    # The task explicitly requires a stop on any disagreement. These are empty, unbindable artifacts.
    (OUT/'NEW_ROWS.jsonl').write_text('')
    (OUT/'SOURCE_MAP.jsonl').write_text('')
    dump('TRANSFORMATION_CHECK.json',dict(status='FAIL_STOP',tree_sha256=seal['tree_sha256'],
        rule='Rotate the stored toward answer label by 180 degrees; compare answer content, never answer letters.',
        pairing='Same dataset, scene, family, ordered object triple and pair_id; identical frames and provenance source identity asserted.',
        pairs=len(pairs),passed=len(pairs)-len(failures),failed=len(failures),identity_checks=identity_checks,
        both_eligible_pairs=sum(p['both_eligible'] for p in pairs),both_eligible_failed=sum(p['both_eligible'] for p in failures),
        by_family_clause=[dict(family=f,clause=c,result=r,rows=n) for (f,c,r),n in sorted(stats.items())],
        transitions=[dict(family=f,clause=c,toward_label=t,turn_label=a,rows=n) for (f,c,t,a),n in sorted(trans.items())],
        comparisons=pairs,disagreements=failures,
        examples=[dict(comparison=x,toward=flat[x['toward_qid']],turned=flat[x['turn_qid']]) for x in failures[:10]]))
    dump('COUNTS.json',dict(status='UNCHANGED_GATE_FAILED',store_rows=all_n,direction_rows=sum(before.values()),
        before=table(before),eligible_after_room_and_removal_lists=table(eligible),after=table(before),
        additions=table(C.Counter()),exclusion_hits=dict(blocked),
        family_counts=[dict(family=f,opening=o,clause=c,rows=n) for (f,o,c),n in sorted(families.items())]))
    checks={k:'NOT_RUN_GATE_FAILED' for k in ('exact_addition_cells','source_reuse','new_row_pack_validate','candidate_ids',
        'field_diff','independent_new_row_truth','new_row_room_and_removal_exclusions','wording_distance_filter','new_row_READ30')}
    dump('CHECKS.json',dict(status='FAIL_STOP',transformation_gate='FAIL',new_rows=0,replacements=0,
        source_checks=dict(validation),unique_source_qids=len(ids),removal_inputs=[str(p) for p in removal_paths],
        checks=checks,wording_threshold=0.10,wording_comparisons=0,wordings_removed=0,
        pack_note='Direct VQA sources pass N r2_contract.validate and trace_grammar. ground_rows.pack requires routed ground_record/events and is not applied to these direct sources.'))
    # Fifteen failing pairs give thirty complete source records for review.
    selected=[]
    for x in failures:
        if not x['both_eligible']:continue
        if x['toward_qid'] in {m['qid'] for m in selected}:continue
        selected.extend([flat[x['toward_qid']],flat[x['turn_qid']]])
        if len(selected)==30:break
    assert len(selected)==30
    with (OUT/'READ30.md').open('w') as f:
        f.write('These are 30 complete existing source rows (15 failing pairs), not generated rows. Frame files were not opened.\n\n')
        for m in selected:
            raw=con.execute('SELECT row FROM rows WHERE i=?',(m['i'],)).fetchone()[0]
            assert hashlib.sha256(raw.encode()).hexdigest()==m['row_sha256']
            f.write(f"### Store row {m['i']}: {m['qid']}\n\n```json\n{json.dumps(json.loads(raw),sort_keys=True)}\n```\n\n")
    con.close()
    (OUT/'READ30_REVIEW.txt').write_text('\n\n'.join(f"{m['i']} {m['qid']}\n{m['question']}\n{m['options']}\n{m['target']}" for m in selected)+'\n')
    (BASE/'STATUS.md').write_text(f"The required exactness gate failed on {len(failures):,} of {len(pairs):,} paired-clause comparisons; {sum(p['both_eligible'] for p in failures):,} failures survive N's room and removal filters. All 93,370 direction sources pass N's direct validator and trace grammar. No rows or replacements were generated. The final evidence package is pending.\n")
    print(json.dumps(dict(pairs=len(pairs),failures=len(failures),eligible_failures=sum(p['both_eligible'] for p in failures),stats={str(k):v for k,v in stats.items()},transitions={str(k):v for k,v in trans.items()}),indent=2))
    return 2

if __name__=='__main__':sys.exit(main())
