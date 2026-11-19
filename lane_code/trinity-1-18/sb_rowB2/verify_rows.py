"""Independently recompute delivered labels and check all row transformations."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
TREE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
sys.path.insert(0,str(TREE))
from student_pilot.carrier_c1_routing import direct_row
from student_pilot.trace_grammar import validate_row
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    rows=[json.loads(s) for s in (OUT/'rows.jsonl').read_text().splitlines()]
    source={r['qid']:r for r in map(json.loads,(ROOT/'inputs/sources.jsonl').read_text().splitlines())}
    facts={r['old_qid']:r for r in map(json.loads,(OUT/'GT_FACTS.jsonl').read_text().splitlines())}
    mapping=[json.loads(s) for s in (OUT/'QID_MAP.jsonl').read_text().splitlines()]
    removals=[json.loads(s) for s in (OUT/'REMOVE.json').read_text().splitlines()]
    plan=json.loads((OUT/'PLAN.json').read_text())['expected_cells']
    groups=collections.defaultdict(list);hist=collections.defaultdict(collections.Counter)
    old_ids=set();new_ids=set();cids=set();source_semantic_changes=0;rank_checks=0
    for row in rows:
        edit=row['provenance']['sb_rowB2'];old=edit['source_qid'];src=source[old];fact=facts[old]
        assert old not in old_ids and row['qid'] not in new_ids and row['candidate_id'] not in cids
        old_ids.add(old);new_ids.add(row['qid']);cids.add(row['candidate_id'])
        assert row['candidate_id']==candidate_identity(edit['candidate_identity_input'])
        reduced={k:v for k,v in row.items() if k not in {'qid','candidate_id','answer','target','student_input','provenance'}}
        assert reduced=={k:v for k,v in src.items() if k not in {'qid','candidate_id','answer','target','student_input','provenance'}}
        assert {k:v for k,v in row['student_input'].items() if k not in {'question','options'}}=={k:v for k,v in src['student_input'].items() if k not in {'question','options'}}
        assert {k:v for k,v in row['provenance'].items() if k!='sb_rowB2'}==src['provenance']
        assert sorted(s[3:] for s in row['student_input']['options'])==sorted(s[3:] for s in src['student_input']['options'])
        if row['question_type'].startswith('camera_'):
            assert re.sub(r'\([^()]*\)','(OPTIONS)',row['student_input']['question'])==re.sub(r'\([^()]*\)','(OPTIONS)',src['student_input']['question'])
        else:assert row['student_input']['question']==src['student_input']['question']
        assert not validate_row(row)
        assert direct_row(row)['target']==row['target']
        k=src['provenance']['camera_frame']
        question=row['student_input']['question']
        assert set(re.findall(r'frame (\d+)',question))=={str(k)}
        subjects=[o['label'] for o in src['provenance']['instances']]
        if row['question_type'].endswith('_nf'):
            parsed=re.search(r'is (.+?) \[Near/Far\] compared to (.+?)\?',question)
            assert parsed and list(parsed.groups())==subjects
        elif row['question_type'].endswith(('_lr','_ud')):
            parsed=re.search(r'relative to (.+?), is (.+?) to the \[',question)
            assert parsed and list(reversed(parsed.groups()))==subjects
        else:
            assert set(subjects)=={s[3:] for s in row['student_input']['options']}
        assert re.search(r'frame (\d+) of 32',row['target']).group(1)==str(k)
        assert set(re.findall(r'frame (\d+)',row['target']))=={str(k)}
        assert 'seconds' not in row['target'] and 'first seen' not in row['target']
        assert all('locate the '+o['label']+' relative to the camera viewpoint of frame '+str(k) in row['target'] for o in src['provenance']['instances'])
        hist[row['question_type']][row['answer']]+=1
        groups[fact['source_gt']['path']].append(row)
    for family,counts in plan.items():assert {key:hist[family][key] for key in counts}==counts
    assert {m['old_qid'] for m in mapping}==old_ids and {m['new_qid'] for m in mapping}==new_ids
    assert len(mapping)==len(rows)
    assert {r['row_key'] for r in removals}==set(source) and len(removals)==len(source)
    assert all(set(r)=={'pool','question_type','reason','row_key','scene'} for r in removals)
    indexed=set()
    for p in Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/FAMILY_QIDS').glob('*.txt'):
        indexed.update(p.read_text().splitlines())
    assert not new_ids & indexed
    for path,group in groups.items():
        with np.load(path,allow_pickle=False) as archive:
            poses=archive['c2w'].astype(float);indices=list(map(int,archive['frame_indices']))
            ids=list(map(int,archive['ids']));centers=archive['obb_centroid'].astype(float)
            lengths=archive['obb_lengths'].astype(float);axes_all=archive['obb_axes'].astype(float)
        assert sha(path)==facts[group[0]['provenance']['sb_rowB2']['source_qid']]['source_gt']['sha256']
        for row in group:
            old=row['provenance']['sb_rowB2']['source_qid'];src=source[old];fact=facts[old]
            assert indices==src['student_input']['frame_indices']
            k=src['provenance']['camera_frame'];pose=poses[k-1];up=np.asarray(fact['geometry_audit']['up']);values=[]
            family=row['question_type'];labels=[]
            for obj in src['provenance']['instances']:
                j=ids.index(obj['id']);center=centers[j];axis=axes_all[j].reshape(3,3)
                if fact['geometry_audit']['axes_layout']=='columns':axis=axis.T
                half=lengths[j]*fact['geometry_audit']['box_half_factor']
                delta=pose[:3,3]-center
                squared=0.
                for d in range(3):
                    component=sum(float(axis[d,c])*float(delta[c]) for c in range(3))
                    residual=max(0.,abs(component)-float(half[d]));squared+=residual*residual
                distance=math.sqrt(squared)
                camera=np.linalg.inv(pose[:3,:3])@(center-pose[:3,3])
                bearing=math.atan2(float(camera[0]),float(camera[2]))
                height=sum(float(center[d]-pose[d,3])*float(up[d]) for d in range(3))
                value=distance if family.startswith('camera_') or family.endswith('_nf') else bearing if family.endswith('_lr') else height
                values.append(value);labels.append(obj['label'])
                measured=next(o for o in fact['objects'] if o['id']==obj['id'])
                assert math.isclose(distance,measured['nearest_obb_distance'],rel_tol=1e-8,abs_tol=1e-8)
                if family.endswith('_lr'):
                    direction='left' if bearing<0 else 'right'
                    assert 'locate the '+obj['label'] in row['target']
                    line=next(l for l in row['target'].splitlines() if 'locate the '+obj['label']+' relative' in l)
                    assert 'centre of this object is to the '+direction in line
                if family.endswith('_ud'):
                    line=next(l for l in row['target'].splitlines() if 'locate the '+obj['label']+' relative' in l)
                    assert 'centre of this object is '+('above' if height>0 else 'below') in line
            if family.startswith('camera_'):
                order=[labels[i] for i in sorted(range(len(values)),key=values.__getitem__)];semantic=order[0]
                assert 'the objects are '+', then '.join(order)+'.' in row['target'];rank_checks+=1
                for i,label in enumerate(order):
                    line=next(l for l in row['target'].splitlines() if 'locate the '+label+' relative' in l)
                    if i>0:assert 'farther than the '+order[i-1] in line
                    if i+1<len(order):assert 'nearer than the '+order[i+1] in line
            elif family.endswith('_nf'):semantic='Near' if values[0]<values[1] else 'Far'
            elif family.endswith('_lr'):semantic='Left' if values[0]<values[1] else 'Right'
            else:semantic='Up' if values[0]>values[1] else 'Down'
            assert row['student_input']['options'][ord(row['answer'])-65][3:]==semantic
            assert fact['semantic']==semantic
            source_semantic_changes+=src['student_input']['options'][ord(src['answer'])-65][3:]!=semantic
    result=dict(status='PASS',input_sha256={str(p):sha(p) for p in [Path(__file__),OUT/'rows.jsonl',OUT/'GT_FACTS.jsonl',OUT/'PLAN.json',OUT/'INPUTS.json',ROOT/'inputs/sources.jsonl',OUT/'QID_MAP.jsonl',OUT/'REMOVE.json']},
        rows_independently_recomputed=len(rows),distance_rankings_checked=rank_checks,source_semantic_answers_changed=source_semantic_changes,
        full_store_index_qids=len(indexed),unique_new_ids=True,source_use_ceiling=1,exact_cell_counts=True,
        full_field_diff=True,all_object_claims_at_k=True,native_direct_pack_validate=True,remove_schema_and_coverage=True)
    (OUT/'INDEPENDENT_CHECK.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
