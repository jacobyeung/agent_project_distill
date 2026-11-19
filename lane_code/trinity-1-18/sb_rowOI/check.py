"""Independent raw-raster recount, bounded source diffs and sealed-kit checks."""
import os
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import sys,json,hashlib,re,copy,collections,importlib.util,sqlite3
from pathlib import Path
import numpy as np
from generate import ROOT,TREE,native,identity
from student_pilot.r1_rooms import Rooms
from student_pilot import r1_counting
def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def norm(s):return re.sub(r'\s+',' ',str(s).strip().lower().replace('_',' '))
def diff(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        return [z for k in a.keys()|b.keys() for z in diff(a.get(k),b.get(k),path+'.'+k)]
    return [] if a==b else [path]
def main():
    rows=[json.loads(l) for l in open('out/rows.jsonl')];srcs={r['qid']:r for r in map(json.loads,open('inputs/sources.jsonl'))}
    inv=json.load(open('inputs/inventory.json'));build=json.load(open('out/BUILD.json'));rooms=Rooms(inv['room_authority'])
    excluded=set(inv['excluded_rooms']);qids=set();cids=set();uses=collections.Counter();cells=collections.Counter();answers=collections.Counter();positions=collections.Counter();pairs=collections.defaultdict(list);byr=collections.defaultdict(list);changed=collections.Counter();counts=collections.Counter()
    inputs={str((ROOT/p).resolve()):sha(p) for p in ['out/rows.jsonl','out/BUILD.json','inputs/inventory.json','inputs/sources.jsonl','inputs/wordings.json','check.py','generate.py']}
    scorer_path=ROOT/'inputs/scorer/h1read7/kit/reader/evaluator/evalpath/official.py'
    spec=importlib.util.spec_from_file_location('oi_official',scorer_path);scorer=importlib.util.module_from_spec(spec);spec.loader.exec_module(scorer)
    inputs[str(scorer_path)]=sha(scorer_path)
    seal=json.load(open(TREE.parents[1]/'out/TREE_SEAL.json'))
    for rel in ['student_pilot/ground_rows.py','student_pilot/trace_grammar.py','student_pilot/r1_rooms.py','student_pilot/r1_counting.py','generator/derivgen_v7/derivgen/ground_v312_quality.py','trace_format/ground_v312.py']:
        h=sha(TREE/rel);assert h==seal['files'][rel];inputs[str(TREE/rel)]=h
    proto=ROOT/'inputs/procedure_sources.jsonl';inputs[str(proto)]=sha(proto)
    for prototype in map(json.loads,proto.open()):
        native(prototype);r1_counting.admit(prototype,'counting');counts['store_procedure_examples_validated']+=1
    assert any(re.fullmatch(r'<think>\nStep 1: find each distinct .+?, across the frames, and count it once\.\n</think>\n\n\d+',r['target']) for r in map(json.loads,proto.open()))
    for r in rows:
        p=r['provenance']['sb_rowOI'];s=srcs[p['source_qid']];uses[s['qid']]+=1
        assert r['qid'] not in qids and r['candidate_id'] not in cids;qids.add(r['qid']);cids.add(r['candidate_id'])
        assert identity(r)==r['candidate_id'];native(r);counts['new_pack_validate']+=1
        assert scorer.parse_answer_v1(r['target'],'numeric')['parsed_answer']==r['answer'];counts['numeric_scorer_parse']+=1
        if uses[s['qid']]==1:native(s);counts['source_pack_validate']+=1
        allowed={'.qid','.answer','.target','.candidate_id','.count_kind','.count_arity','.student_input.question','.provenance.instances','.provenance.total_categories','.provenance.count_kind','.provenance.sb_rowOI'}
        ds=diff(s,r);assert set(ds)<=allowed,(r['qid'],ds);changed.update(ds)
        assert r['student_input']['frame_indices']==s['student_input']['frame_indices']
        state,canon,_=rooms.status(r);assert state=='ok' and rooms.room(canon) not in excluded and canon not in excluded
        assert rooms.room(canon)==p['room'];counts['rooms_pass']+=1
        cats=[c['name'] for c in r['provenance']['total_categories']];k=len(cats)
        assert not set(cats)&{'furniture','toilet paper','paper','clothing','clothes','laundry','bedding','food','trash','garbage','clutter','equipment','luggage','cookware','cutlery','silverware','glassware','kitchenware'}
        procedures=re.findall(r'^Step (\d+): find each distinct (.+?), across the frames, and count it once\.$',r['target'],re.M)
        assert procedures==[(str(i+1),c) for i,c in enumerate(cats)]
        assert len(r['target'].splitlines())==k+5
        assert p['normalized_edit_distance']>.20
        cells[f'{k}|{p["mode"]}|{p["repeated_count"]}|{p["template_id"]}']+=1
        answers[r['answer']]+=1;pairs[p['pair_id']].append(r);byr[p['raster']].append(r)
        try:r1_counting.admit(r,'totals')
        except ValueError as e:assert str(e).startswith('R1_TOTALS_ROW_REFUSED');counts['launch_policy_refused']+=1
        else:raise AssertionError('Unexpected launch admission')
    assert len(rows)==1008 and len(qids)==len(cids)==1008 and len(pairs)==504
    assert max(uses.values())<=4
    original=ROOT/'inputs/b12/out/PACKET_b12_v4/rows.sqlite'
    inputs[str(original)]=sha(original)
    assert inputs[str(original)]==inv['input_sha256'][str(original)]
    connection=sqlite3.connect('file:'+str(original)+'?mode=ro',uri=True)
    found=set()
    for (raw,) in connection.execute('select row from rows'):
        source=json.loads(raw)
        if source['qid'] in uses:
            assert source==srcs[source['qid']];found.add(source['qid'])
    connection.close();assert found==set(uses);counts['sources_equal_original_database']=len(found)
    scene_counts=collections.Counter(r['provenance']['canonical'] for r in rows)
    assert max(scene_counts.values())<=24
    semantic_keys=[(r['provenance']['canonical'],tuple(sorted(x['name'] for x in r['provenance']['total_categories']))) for r in rows]
    assert len(set(semantic_keys))==1008
    for k in (2,3,4):
        for t in range(6):
            assert cells[f'{k}|singleton|1|{t}']==28
            for n in (2,3):assert cells[f'{k}|control|{n}|{t}']==14
    for pair in pairs.values():
        assert len(pair)==2
        a,b=sorted(pair,key=lambda r:r['provenance']['sb_rowOI']['mode'],reverse=True)
        pa,pb=a['provenance']['sb_rowOI'],b['provenance']['sb_rowOI']
        assert pa['mode']=='singleton' and pb['mode']=='control'
        assert pa['source_qid']==pb['source_qid'] and pa['template_id']==pb['template_id']
        ac=[x['name'] for x in a['provenance']['total_categories']];bc=[x['name'] for x in b['provenance']['total_categories']]
        assert sum(x!=y for x,y in zip(ac,bc))==1
        positions[f'{len(bc)}|{pb["repeated_count"]}|{pb["repeated_position"]}']+=1
    for k in (2,3,4):
        for n in (2,3):
            for pos in range(k):assert positions[f'{k}|{n}|{pos}']==84//k
    for path,rs in byr.items():
        h=sha(path);inputs[path]=h
        with np.load(path) as z:
            labels={int(i):norm(l) for i,l in zip(z['ids'],z['labels'])}; masks=z['inst'];fi=z['frame_indices'].tolist()
            valid=np.asarray(z['valid'],dtype=bool)&np.any(z['depth']>0,axis=(1,2)) if 'valid' in z.files else np.ones(len(fi),bool)
            # Count labels independently; the generator's category counts are never read.
            bylabel=collections.defaultdict(set)
            for i,l in labels.items():bylabel[l].add(i)
            visible={}
            for i in labels:
                pins=[]
                for f,frame in enumerate(masks):
                    if np.count_nonzero(frame==i)>=.002*frame.size:pins.append(f+1)
                visible[i]=pins
            for r in rs:
                assert fi==r['student_input']['frame_indices'] and h==r['provenance']['raster_sha256']
                ns=[]
                for cat in r['provenance']['total_categories']:
                    ids=bylabel[cat['name']];assert set(cat['ids'])==ids
                    assert all(visible[i] and all(valid[:visible[i][0]]) for i in ids)
                    assert cat['frames']==[visible[i][0] for i in cat['ids']]
                    ns.append(len(ids))
                p=r['provenance']['sb_rowOI'];assert sum(ns)==int(r['answer'])
                assert ns==[1]*len(ns) if p['mode']=='singleton' else sorted(ns)==[1]*(len(ns)-1)+[p['repeated_count']]
                counts['independent_gt_recomputed']+=1
    # Select 30 full rows covering all arities, modes, repeated counts and templates.
    samples=[]
    for k in (2,3,4):
      groups=[('singleton',1,4),('control',2,3),('control',3,3)]
      for mode,n,num in groups:
        pool=[r for r in rows if r['count_arity']==k and r['provenance']['sb_rowOI']['mode']==mode and r['provenance']['sb_rowOI']['repeated_count']==n]
        pool.sort(key=lambda r:(r['provenance']['sb_rowOI']['template_id'],r['qid']))
        for t in range(num):samples.append(next(r for r in pool if r['provenance']['sb_rowOI']['template_id']==(t+k)%6))
    assert len(samples)==30
    Path('out/READ30.md').write_text('# Thirty complete rows\n\n'+ '\n\n'.join('```json\n'+json.dumps(r,ensure_ascii=False,indent=1)+'\n```' for r in samples)+'\n')
    summary=dict(status='PASS',input_sha256=inputs,counts=counts,exact_cells=cells,answer_histogram=answers,dataset_histogram=collections.Counter(r['dataset'] for r in rows),repeated_positions=positions,source_use=dict(unique=len(uses),maximum=max(uses.values())),scene_use=dict(unique=len(scene_counts),maximum=max(scene_counts.values())),semantic_duplicates=0,field_diffs=changed,
        normalized_edit_distance=dict(threshold=.20,reference_wordings=build['wordings'],minimum=build['min_normalized_edit_distance'],removed=build['removed']),
        native_validation='Store direct grammar plus ground_rows.pack/validate using a lossless body adapter to the mandatory answer-tag envelope; no claim of native launch admission.',
        launch_policy='REFUSED: R1_TOTALS_ROW_REFUSED for all 1008 rows; kit only.',
        operator_gate='NOT RUN: truth-2 R0-dev multiple overcounts <20/44; single-category truth-2 must not start answering 1.',
        human_grammar_review='PENDING',read30_sha256=sha('out/READ30.md'))
    Path('out/CHECKS.json').write_text(json.dumps(summary,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('input_sha256','field_diffs','exact_cells')},indent=1))
    Path('STATUS.md').write_text('Independent checks passed for all 1,008 rows: raw-raster counts, source diffs, room exclusions, paired cells, identifiers, and sealed-kit validation. Thirty complete rows are ready for grammar review. Launch admission and model gates remain unrun because this is a kit-only task.\n')
if __name__=='__main__':main()
