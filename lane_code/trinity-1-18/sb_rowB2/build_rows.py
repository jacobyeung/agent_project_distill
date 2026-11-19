"""Audit and rebuild VSTI direct rows from hash-pinned local GT, on CPU."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import collections
import copy
import ctypes
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import re
import sqlite3
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from stage_inputs import sha

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
TREE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
STORE=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7')
ORIGINAL_CODE=Path('/scratch/jjyeung/n30_mirror/rows_a2/v4/vsti/code')
CONFIG=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/build19/inputs/config.json')
N=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/records/n.json')
SEED=20261119
THRESHOLD=.05
FAMILIES=['camera_obj_rel_dist_v1','camera_obj_rel_dist_v2','camera_obj_rel_dist_v3',
          'obj_obj_relative_pos_lr','obj_obj_relative_pos_nf','obj_obj_relative_pos_ud']
EXPECTED=dict(zip(FAMILIES,[1951,1983,1998,1998,2000,1996]))
sys.path.insert(0,str(TREE))
sys.path.insert(0,str(ORIGINAL_CODE))
import geometry as reference
from student_pilot import trace_grammar, r2_grammar
from student_pilot.carrier_c1_routing import direct_row
from student_pilot.r1_training import row_check
from student_pilot.r1_rooms import Rooms
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity

def dump(path,data):
    path.write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n')
def canonical_bytes(data):return json.dumps(data,sort_keys=True,separators=(',',':')).encode()
def dh(data):return hashlib.sha256(canonical_bytes(data)).hexdigest()
def normalize(text):return ' '.join(unicodedata.normalize('NFKC',text).casefold().split())
def load_rows():
    con=sqlite3.connect('file:'+str(STORE/'vqa/rows.sqlite')+'?mode=ro',uri=True)
    ranges=json.loads((STORE/'FAMILY_INDEX_RANGES.json').read_text())['families']
    discovered={k for k in ranges if k.startswith(('camera_obj_rel_dist','obj_obj_relative_pos'))}
    assert discovered==set(FAMILIES), discovered
    rows=[]
    for family in FAMILIES:
        for a,b in ranges[family]:
            rows.extend(json.loads(s) for s, in con.execute('SELECT row FROM rows WHERE i BETWEEN ? AND ? ORDER BY i',(a,b)))
    assert dict(collections.Counter(r['question_type'] for r in rows))==EXPECTED
    assert con.execute('SELECT COUNT(*) FROM rows').fetchone()[0]==204413
    con.close()
    return rows

def inputs():
    paths=[Path(__file__),ROOT/'stage_inputs.py',ROOT/'collect_wordings.py',ROOT/'wording_filter.cpp',
           STORE/'vqa/rows.sqlite', STORE/'BUILD_MANIFEST.json',STORE/'COUNTS_V7.json',
           STORE/'FAMILY_INDEX_RANGES.json',N,CONFIG,ORIGINAL_CODE/'generate.py',
           ORIGINAL_CODE/'geometry.py',ORIGINAL_CODE/'sources.py',ORIGINAL_CODE/'rewrite_v4.py',
           ROOT/'inputs/GT_RESOLUTION.json',ROOT/'inputs/WORDING_CORPUS.json',
           ROOT/'inputs/COVERAGE_V2_PUB.tar',ROOT/'inputs/coverage_rows_v2.py',
           TREE.parent/'build19/seal.log']
    pins={str(p):sha(p) for p in paths}
    assert pins[str(STORE/'vqa/rows.sqlite')]=='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and str(p).startswith(str(TREE)) and Path(p).is_file():pins[p]=sha(p)
    return pins

def room_authorities(pins):
    cfg=json.loads(CONFIG.read_text())
    authorities=cfg['r1_training']['room_authority']
    for v in authorities.values():
        assert sha(v['path'])==v['sha256'];pins[v['path']]=v['sha256']
    rooms=Rooms(authorities)
    paths={'withheld80':TREE/'student_pilot/r2_withheld.json',
           'dev_s1':ROOT/'inputs/dev_scene_exclusions.json',
           'benchmark':Path(cfg['benchmark_scene_exclusions']['path'])}
    expected={'withheld80':'634820b4','dev_s1':'969cdb56','benchmark':'3119aa4a'}
    excluded={}
    for kind,p in paths.items():
        h=sha(p);assert h.startswith(expected[kind]);pins[str(p)]=h
        data=json.loads(p.read_text());names=set()
        for key in ('rooms','physical_groups','scenes','canonical','natives'):
            values=data.get(key,[])
            names.update(values if isinstance(values,(list,dict)) else [])
        for a,bs in data.get('aliases',{}).items():names.add(a);names.update(bs)
        converted=set()
        for name in names:
            if not isinstance(name,str) or '/' not in name:continue
            ds,sc=name.split('/',1)
            ds={'d1':'scannet','d2':'scannetpp','d3':'arkitscenes','scannetppv2':'scannetpp'}.get(ds,ds)
            native=ds+'/'+sc
            converted.add(native)
            if ds=='scannet':converted.add(re.sub(r'_\d+$','',native))
            elif ds=='arkitscenes' and sc.isdigit():converted.add(rooms.room(native))
        excluded[kind]=converted
    return rooms,excluded

def room_reasons(r,rooms,excluded):
    status,canonical,_=rooms.status(r)
    result=[] if status=='ok' else [status]
    if canonical:
        room=rooms.room(canonical)
        names={room,canonical, r['dataset']+'/'+r['scene']}
        result += [kind for kind,values in excluded.items() if names & values]
    return result

def native_validate(r):
    errors=trace_grammar.validate_row(r)
    if errors:raise ValueError([(e.rule_id,e.line,e.detail) for e in errors])
    packed=direct_row(r)
    assert packed['target']==r['target']
    assert packed['routing']['answer']==r['answer']
    assert r2_grammar.validate_direct(packed['target'],r['student_input']['question'],32)==r['answer']
    row_check(r,'vqa')
    return packed

def audit(rows,pins):
    stats={};examples=[]
    for fam in FAMILIES:
        rr=[r for r in rows if r['question_type']==fam]
        c=collections.Counter()
        for r in rr:
            k=r['provenance']['camera_frame']
            cited=[int(x) for x in re.findall(r'first seen in frame (\d+)',r['target'])]
            assert len(cited)==len(r['provenance']['instances'])
            c['rows']+=1;c['any_object_cited_other_than_k']+=any(f!=k for f in cited)
            c['no_object_cited_at_k']+=all(f!=k for f in cited)
            c['all_object_citations_at_k']+=all(f==k for f in cited)
            c['object_citations']+=len(cited);c['object_citations_other_than_k']+=sum(f!=k for f in cited)
            native_validate(r);c['native_source_pack_validate_pass']+=1
        stats[fam]=dict(c)
        examples.append('## '+fam)
        for r in rr[:10]:
            examples.extend(['',r['qid'],r['student_input']['question'],' | '.join(r['student_input']['options']),r['target']])
    dump(OUT/'AUDIT.json',dict(input_sha256=pins, families=stats))
    (OUT/'EXAMPLES60.md').write_text('\n\n'.join(examples)+'\n')
    (ROOT/'STATUS.md').write_text('The source audit covers all 11,926 VSTI rows. Counts and ten complete question/trace examples per family are in out/AUDIT.json and out/EXAMPLES60.md. Every source passed N’s native direct pack and grammar checks. GT recomputation and exclusion checks are pending.\n')
    print('AUDIT',json.dumps(stats),flush=True)
    return stats

def scene_facts(task):
    original,location,rows=task
    assert sha(location['path'])==location['sha256']
    with np.load(location['path'],allow_pickle=False) as zf:z={key:zf[key] for key in zf.files}
    audit=reference.verify_source(z)
    if not audit['passed']:return [],{r['qid']:'GT_source_audit:'+audit['reason'] for r in rows}
    ids={int(i):j for j,i in enumerate(z['ids'])}
    out=[];refused={}
    for r in rows:
        try:
            p=r['provenance']; k=p['camera_frame'];family=r['question_type']
            assert 1<=k<=32 and len(z['c2w'])==32
            assert list(map(int,z['frame_indices']))==r['student_input']['frame_indices']
            assert bool(z.get('valid',np.ones(32,bool))[k-1])
            pose=z['c2w'][k-1].astype(float);camera=pose[:3,3]; rotation=pose[:3,:3]
            up=np.asarray(audit['up'],float);values=[];checks=[];objects=[]
            for obj in p['instances']:
                j=ids[obj['id']];label=normalize(str(z['labels'][j]).replace('_',' '))
                assert label==obj['label'],(label,obj['label'])
                center=z['obb_centroid'][j].astype(float)
                axes=z['obb_axes'][j].reshape(3,3).astype(float)
                if audit['axes_layout']=='columns':axes=axes.T
                half=z['obb_lengths'][j]*audit['box_half_factor']
                assert np.isfinite(center).all() and np.isfinite(half).all() and min(half)>0
                distance=reference.box_distance(camera,center,axes,half)
                local=axes@(camera-center);closest=center+axes.T@np.clip(local,-half,half)
                independent_distance=float(np.linalg.norm(camera-closest))
                coords=reference.camera_coords(center,pose)
                delta=center-camera
                columns=[rotation[:,d] for d in range(3)]
                determinant=float(np.dot(columns[0],np.cross(columns[1],columns[2])))
                independent_coords=np.array([np.dot(delta,np.cross(columns[(d+1)%3],columns[(d+2)%3]))/determinant for d in range(3)])
                bearing=math.atan2(coords[0],coords[2])
                bearing2=math.atan2(independent_coords[0],independent_coords[2])
                height=float((center-camera)@up)
                height2=float(sum(float(center[d]-camera[d])*float(up[d]) for d in range(3)))
                assert np.allclose(coords,independent_coords[:3],rtol=1e-8,atol=1e-8)
                # Rotations in the generator are accepted within 0.02; GT boxes here are substantially tighter.
                assert math.isclose(distance,independent_distance,rel_tol=2e-5,abs_tol=2e-5)
                assert math.isclose(bearing,bearing2,rel_tol=1e-8,abs_tol=1e-8)
                assert math.isclose(height,height2,rel_tol=1e-10,abs_tol=1e-10)
                value=distance if family.startswith('camera_') or family.endswith('_nf') else bearing if family.endswith('_lr') else height
                independent=independent_distance if family.startswith('camera_') or family.endswith('_nf') else bearing2 if family.endswith('_lr') else height2
                values.append(value);checks.append(independent)
                objects.append(dict(id=obj['id'],label=label,center_world=center.tolist(),
                    camera_xyz=coords.tolist(),nearest_obb_distance=distance,independent_distance=independent_distance,
                    bearing_rad=bearing,height_from_camera=height,frame=k,
                    visibility_share=float(np.count_nonzero(z['inst'][k-1]==obj['id'])/z['inst'][k-1].size)))
            labels=[o['label'] for o in objects]
            def decision(v):
                if family.startswith('camera_'):return labels[int(np.argmin(v))]
                if family.endswith('_nf'):return 'Near' if v[0]<v[1] else 'Far'
                if family.endswith('_lr'):return 'Left' if v[0]<v[1] else 'Right'
                return 'Up' if v[0]>v[1] else 'Down'
            semantic=decision(values)
            assert semantic==decision(checks)
            order=list(np.argsort(values).astype(int))
            if family.startswith('camera_') or family.endswith('_nf'):
                assert all(reference.separated(values[a],values[b]) for a,b in zip(order,order[1:]))
            elif family.endswith('_lr'):
                assert all(o['camera_xyz'][2]>0 for o in objects) and abs(values[0]-values[1])>=math.radians(10)
            else:assert abs(values[0]-values[1])>=.25
            out.append(dict(old_qid=r['qid'],family=family,k=k,semantic=semantic,objects=objects,
                            order=[labels[i] for i in order],values=values,independent_values=checks,
                            camera_world=camera.tolist(),camera_rotation=rotation.tolist(),up=up.tolist(),
                            geometry_audit=audit,source_gt=location,source_raster=original,
                            input_sha256={str(STORE/'vqa/rows.sqlite'):sha_cache,location['path']:location['sha256'],
                                          str(ORIGINAL_CODE/'geometry.py'):geometry_sha}))
        except (AssertionError,KeyError,ValueError,IndexError) as e:
            import traceback
            refused[r['qid']]='GT_recompute_refused:line_'+str(traceback.extract_tb(e.__traceback__)[-1].lineno)+':'+str(e)
    return out,refused

def recompute(rows,pins,resolution):
    global sha_cache,geometry_sha
    sha_cache=pins[str(STORE/'vqa/rows.sqlite')];geometry_sha=pins[str(ORIGINAL_CODE/'geometry.py')]
    grouped=collections.defaultdict(list);refused={}
    for r in rows:
        original=r['provenance']['raster']
        if original not in resolution['resolved']:refused[r['qid']]='MISSING_GT'
        else:grouped[original].append(r)
    facts=[]
    tasks=[(p,resolution['resolved'][p],rs) for p,rs in sorted(grouped.items())]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,(ff,rr) in enumerate(pool.map(scene_facts,tasks),1):
            facts.extend(ff);refused.update(rr)
            if i%50==0:print('GT scenes',i,'/',len(tasks),flush=True)
    with (OUT/'GT_FACTS.jsonl').open('w') as f:
        for fact in sorted(facts,key=lambda x:x['old_qid']):f.write(json.dumps(fact,sort_keys=True,allow_nan=False)+'\n')
    dump(OUT/'GT_REFUSALS.json',dict(input_sha256=pins,refused=refused,missing_inputs=resolution['missing']))
    (ROOT/'STATUS.md').write_text(f'GT recomputation produced independently checked facts for {len(facts)} rows and refused {len(refused)} rows. Every refusal and missing raster path is recorded. Room and wording filters, balancing, and final validation are pending.\n')
    return {x['old_qid']:x for x in facts},refused

class WordingFilter:
    def __init__(self):
        self.data=json.loads((ROOT/'inputs/WORDING_CORPUS.json').read_text())
        assert not self.data['parse_failures'],self.data['parse_failures']
        self.by_length=collections.defaultdict(list)
        for s in self.data['questions']:
            b=s.encode('utf-32-le') # Python normalization uses Unicode codepoints; C uses bytes for ASCII below.
            # All actual VSTI questions are ASCII. Non-ASCII held-out wording is handled by the Python path.
            self.by_length[len(s)].append(s)
        lib=ctypes.CDLL(str(ROOT/'inputs/wording_filter.so'))
        self.within=lib.within;self.within.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int];self.within.restype=ctypes.c_int
        self.cache={}
    def hit(self,question):
        q=normalize(question)
        if q in self.cache:return self.cache[q]
        n=len(q)
        for m in range(math.ceil(n*(1-THRESHOLD)), math.floor(n/(1-THRESHOLD))+1):
            k=math.floor(THRESHOLD*max(n,m)+1e-12)
            for other in self.by_length[m]:
                if q.isascii() and other.isascii():d=self.within(q.encode(),other.encode(),k)
                else:
                    prev=list(range(m+1))
                    for i,ch in enumerate(q,1):
                        cur=[i]
                        for j,ch2 in enumerate(other,1):cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(ch!=ch2)))
                        prev=cur
                    d=prev[m]
                if d<=k:
                    self.cache[q]=dict(normalized_edit_distance=d/max(n,m),heldout_wording_sha256=hashlib.sha256(other.encode()).hexdigest())
                    return self.cache[q]
        self.cache[q]=None
        return None

def option_permutation(r,fact,position):
    choices=[x.split('. ',1)[1] for x in r['student_input']['options']]
    assert fact['semantic'] in choices and len(set(choices))==len(choices)
    choices.remove(fact['semantic'])
    rng=random.Random(str(SEED)+'|'+r['question_type']+'|'+r['qid'])
    rng.shuffle(choices);choices.insert(position,fact['semantic'])
    question=r['student_input']['question']
    if r['question_type'].startswith('camera_'):
        question,n=re.subn(r'\([^()]+\)', '('+', '.join(choices)+')',question,count=1)
        assert n==1
    return choices,question

def render(r,fact,position,pin):
    x=copy.deepcopy(r);fam=r['question_type'];k=fact['k']
    choices,question=option_permutation(r,fact,position)
    x['student_input']['options']=[f'{chr(65+i)}. {v}' for i,v in enumerate(choices)]
    x['student_input']['question']=question
    x['answer']=chr(65+position)
    x['qid']='sb_rowB2_'+hashlib.sha256((str(SEED)+'|'+r['qid']+'|'+question+'|'+str(choices)).encode()).hexdigest()[:24]
    objects={o['label']:o for o in fact['objects']};labels=[o['label'] for o in fact['objects']]
    lines=[f'Step 1: take the camera viewpoint of frame {k} of 32.']
    locate=choices if fam.startswith('camera_') else labels
    for label in locate:
        if fam.startswith('camera_'):
            ordered=fact['order'];at=ordered.index(label)
            comparisons=[]
            if at>0:comparisons.append('farther than the '+ordered[at-1])
            if at<len(ordered)-1:comparisons.append('nearer than the '+ordered[at+1])
            clause='the closest point of this object is '+' and '.join(comparisons)+' relative to that camera'
        elif fam.endswith('_nf'):
            other=next(s for s in labels if s!=label)
            relation='nearer' if objects[label]['nearest_obb_distance']<objects[other]['nearest_obb_distance'] else 'farther'
            clause=f'the closest point of this object is {relation} than the {other} relative to that camera'
        elif fam.endswith('_lr'):
            angle=objects[label]['bearing_rad']
            clause='the centre of this object is to the '+('left' if angle<0 else 'right')+" of that camera's forward axis"
        else:
            height=objects[label]['height_from_camera']
            clause='the centre of this object is '+('above' if height>0 else 'below')+" that camera's level horizon"
        lines.append(f'Step {len(lines)+1}: locate the {label} relative to the camera viewpoint of frame {k}; {clause}.')
    step=len(lines)+1;sem=fact['semantic']
    if fam.startswith('camera_'):
        lines.append(f'Step {step}: ordered nearest to farthest from the camera viewpoint of frame {k}, the objects are '+', then '.join(fact['order'])+'.')
        lines.append(f'So the closest object to that camera viewpoint is the {sem}.')
    else:
        a,b=labels
        if fam.endswith('_nf'):
            near,far=(a,b) if sem=='Near' else (b,a)
            lines.append(f'Step {step}: from the camera viewpoint of frame {k}, the closest point of the {near} is nearer than the closest point of the {far}.')
            lines.append(f'So the closest point of the {a} is {"nearer" if sem=="Near" else "farther"} than the closest point of the {b} relative to that camera viewpoint.')
        elif fam.endswith('_lr'):
            lines.append(f'Step {step}: from the camera viewpoint of frame {k}, the centre of the {a} is to the {sem.lower()} of the centre of the {b}.')
            lines.append(f'So the centre of the {a} is {sem.lower()} relative to the centre of the {b}.')
        else:
            lines.append(f'Step {step}: in frame {k}\'s level horizon, the centre of the {a} is {"higher" if sem=="Up" else "lower"} than the centre of the {b}.')
            lines.append(f'So the centre of the {a} is {sem.lower()} relative to the centre of the {b}.')
    x['target']='<think>\n'+'\n'.join(lines)+'\n</think>\n\n'+x['answer']
    cid_input=dict(qid=x['qid'],scene=x['scene'],frame_indices=x['student_input']['frame_indices'],
                   type=fam,question=question,options=x['student_input']['options'],trace_revision='3.14')
    x['candidate_id']=candidate_identity(cid_input)
    x['provenance']['sb_rowB2']=dict(source_qid=r['qid'],source_row_sha256=dh(r),
        input_sha256={str(STORE/'vqa/rows.sqlite'):pin['store'],str(OUT/'INPUTS.json'):pin['manifest'],
                      fact['source_gt']['path']:fact['source_gt']['sha256']},
        generator_sha256=sha(Path(__file__)),seed=SEED,geometry_frame=k,ground_truth_fact_sha256=dh(fact),
        semantic_answer=sem,option_position=position+1,source_option_position=ord(r['answer'])-64,
        candidate_identity_input=cid_input,option_permutation=[r['student_input']['options'].index(next(o for o in r['student_input']['options'] if o.split('. ',1)[1]==c))+1 for c in choices])
    return x

def main():
    OUT.mkdir(exist_ok=True)
    pins=inputs();rows=load_rows();stats=audit(rows,pins)
    rooms,excluded=room_authorities(pins)
    resolution=json.loads((ROOT/'inputs/GT_RESOLUTION.json').read_text())
    if '--reuse-gt' in sys.argv:
        facts={x['old_qid']:x for x in map(json.loads,(OUT/'GT_FACTS.jsonl').read_text().splitlines())}
        refusals=json.loads((OUT/'GT_REFUSALS.json').read_text())['refused']
        for f in facts.values():assert f['input_sha256'][str(STORE/'vqa/rows.sqlite')]==pins[str(STORE/'vqa/rows.sqlite')]
    else:facts,refusals=recompute(rows,pins,resolution)
    pins[str(OUT/'GT_FACTS.jsonl')]=sha(OUT/'GT_FACTS.jsonl')
    dump(OUT/'INPUTS.json',dict(input_sha256=pins,gt_archive_sha256=resolution['input_sha256'],
         gt_rasters={v['path']:v['sha256'] for v in resolution['resolved'].values()},
         wording_input_sha256=json.loads((ROOT/'inputs/WORDING_CORPUS.json').read_text())['input_sha256']))
    pin=dict(manifest=sha(OUT/'INPUTS.json'),store=pins[str(STORE/'vqa/rows.sqlite')])
    common={'input_sha256':{str(OUT/'INPUTS.json'):pin['manifest']}}
    reasons={r['qid']:[] for r in rows};wording_hits={};eligible=collections.defaultdict(list)
    wf=WordingFilter()
    for r in rows:
        qid=r['qid'];reasons[qid]=room_reasons(r,rooms,excluded)
        if qid in refusals:reasons[qid].append(refusals[qid])
        if reasons[qid]:continue
        # Reject a source if any position's deterministic permutation is near a held-out question.
        # This fixes membership before balancing and prevents a short final cell.
        for pos in range(len(r['student_input']['options'])):
            _,question=option_permutation(r,facts[qid],pos)
            hit=wf.hit(question)
            if hit:
                reasons[qid].append('heldout_wording_distance_le_0.05');wording_hits[qid]=hit;break
        if not reasons[qid]:eligible[r['question_type']].append(r)
    plan={};scheduled=[]
    for fam in FAMILIES:
        rr=sorted(eligible[fam],key=lambda r:r['qid']);rng=random.Random(str(SEED)+'|'+fam);rng.shuffle(rr)
        nopt={'camera_obj_rel_dist_v1':4,'camera_obj_rel_dist_v2':3}.get(fam,2)
        positions=list(range(nopt));rng.shuffle(positions)
        allocation=[positions[i%nopt] for i in range(len(rr))]
        plan[fam]={chr(65+p):allocation.count(p) for p in range(nopt)}
        scheduled.extend((r,facts[r['qid']],pos) for r,pos in zip(rr,allocation))
    dump(OUT/'PLAN.json',dict(**common,seed=SEED,expected_cells=plan,source_use_ceiling=1,
                            rule='All admitted sources once; position counts differ by at most one when not divisible.'))
    replacements=[];mapping=[];errors=[];diff_counts=collections.Counter();before=collections.defaultdict(collections.Counter)
    after=collections.defaultdict(collections.Counter);all_before=collections.defaultdict(collections.Counter)
    corrected=collections.Counter()
    for r in rows:all_before[r['question_type']][r['answer']]+=1
    for r,fact,pos in scheduled:
        x=render(r,fact,pos,pin)
        native_validate(x)
        assert not room_reasons(x,rooms,excluded)
        assert wf.hit(x['student_input']['question']) is None
        assert set(re.findall(r'frame (\d+)',x['target']))=={str(fact['k'])}
        assert re.search(r'frame \d+ of 32',x['target']) and 'first seen' not in x['target'] and 'seconds' not in x['target']
        labels=[o.split('. ',1)[1] for o in x['student_input']['options']]
        assert labels[ord(x['answer'])-65]==fact['semantic']
        assert x['candidate_id']==candidate_identity(x['provenance']['sb_rowB2']['candidate_identity_input'])
        original_semantic=r['student_input']['options'][ord(r['answer'])-65].split('. ',1)[1]
        corrected[r['question_type']]+=original_semantic!=fact['semantic']
        changed={k for k in set(r)|set(x) if r.get(k)!=x.get(k)}
        assert changed <= {'qid','candidate_id','answer','student_input','target','provenance'}
        assert {k for k in r['student_input'] if r['student_input'][k]!=x['student_input'][k]} <= {'question','options'}
        assert {k:v for k,v in x['provenance'].items() if k!='sb_rowB2'}==r['provenance']
        diff_counts.update(changed);before[r['question_type']][r['answer']]+=1;after[r['question_type']][x['answer']]+=1
        replacements.append(x);mapping.append(dict(**common,old_qid=r['qid'],new_qid=x['qid'],candidate_id=x['candidate_id']))
    for fam in FAMILIES:
        assert {letter:after[fam][letter] for letter in plan[fam]}==plan[fam],('short cell',fam)
        assert max(plan[fam].values())-min(plan[fam].values())<=1
    assert len({r['qid'] for r in replacements})==len(replacements)
    assert len({r['candidate_id'] for r in replacements})==len(replacements)
    assert not {r['qid'] for r in replacements} & {r['qid'] for r in rows}
    assert len({m['old_qid'] for m in mapping})==len(mapping)
    for name,data in [('rows.jsonl',replacements),('QID_MAP.jsonl',mapping)]:
        with (OUT/name).open('w') as f:
            for row in data:f.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
    n_schema=set(json.loads(N.read_text().splitlines()[0]));assert n_schema=={'pool','question_type','reason','row_key','scene'}
    with (OUT/'REMOVE.json').open('w') as f:
        for r in rows:
            reason='replaced_frame_k_trace' if not reasons[r['qid']] else ';'.join(reasons[r['qid']])
            item=dict(pool=r['pool'],question_type=r['question_type'],reason=reason,row_key=r['qid'],scene=r['dataset']+'/'+r['scene'])
            assert set(item)==n_schema;f.write(json.dumps(item,sort_keys=True)+'\n')
    dump(OUT/'REMOVE.provenance.json',dict(**common,removal_sha256=sha(OUT/'REMOVE.json'),schema_source_sha256=pins[str(N)],
         format='JSON Lines despite .json suffix; exact five-key N schema',rows=len(rows)))
    dump(OUT/'REFUSALS.json',dict(**common,rows={q:rs for q,rs in reasons.items() if rs},wording_hits=wording_hits))
    balanced={fam:dict(source_all_before=dict(all_before[fam]),admitted_sources_before=dict(before[fam]),after=plan[fam]) for fam in FAMILIES}
    counts={fam:dict(source=stats[fam]['rows'],admitted=len(eligible[fam]),
           refused=stats[fam]['rows']-len(eligible[fam]),gt_recomputed=sum(f['family']==fam for f in facts.values()),
           missing_gt=sum(r['question_type']==fam and refusals.get(r['qid'])=='MISSING_GT' for r in rows)) for fam in FAMILIES}
    checks=dict(**common,status='PASS',families=counts,position_histograms=balanced,seed=SEED,
         exact_cell_counts_asserted=plan,source_use_ceiling=1,max_source_uses=1,
         source_native_pack_validate=sum(s['native_source_pack_validate_pass'] for s in stats.values()),
         replacement_native_pack_validate=len(replacements),ground_truth_independent_checks=len(replacements),
         gt_recomputed_total=len(facts),gt_refused_total=len(refusals),missing_gt_rows=sum(v=='MISSING_GT' for v in refusals.values()),
         unique_qids=True,unique_candidate_ids=True,new_ids_disjoint_from_source=True,
         edited_top_level_fields=dict(diff_counts),room_rule_pass=True,source_semantic_answers_corrected=dict(corrected),
         candidate_id_formula='kit ground_v312_quality.candidate_identity, trace_revision=3.14',
         validator='kit carrier_c1_routing.direct_row + r2_grammar.validate_direct + trace_grammar.validate_row + r1_training.row_check',
         routed_ground_pack='Not applicable to direct VSTI schema; native direct pack used.',
         wording_filter=dict(threshold=THRESHOLD,metric='Levenshtein/max Unicode codepoint length after NFKC/casefold/whitespace normalization',
           unique_heldout_wordings=len(wf.data['questions']),input_files=len(wf.data['input_sha256']),
           refused=len(wording_hits),all_final_questions_checked=True,all_permutation_positions_prefiltered=True),
         read30='PENDING_HUMAN_AGENT_READ',missing_inputs=len(resolution['missing']),
         refusal_counts=dict(collections.Counter(reason for rs in reasons.values() for reason in rs)),
         output_sha256={name:sha(OUT/name) for name in ('rows.jsonl','QID_MAP.jsonl','REMOVE.json','PLAN.json','GT_FACTS.jsonl')})
    dump(OUT/'CHECKS.json',checks)
    chosen=[]
    for fam in FAMILIES:
        rr=[r for r in replacements if r['question_type']==fam]
        assert len(rr)>=5,('READ30 short family',fam)
        chosen.extend(rr[:5])
    # Full machine rows and a complete readable question/options/trace/answer rendering.
    with (OUT/'READ30.md').open('w') as f:
        for i,r in enumerate(chosen,1):
            f.write(f'## {i}. {r["question_type"]}: {r["qid"]}\n\n')
            f.write(r['student_input']['question']+'\n\n'+'\n'.join(r['student_input']['options'])+'\n\n'+r['target']+'\n\n')
            f.write('Full row:\n```json\n'+json.dumps(r,sort_keys=True)+'\n```\n\n')
    (ROOT/'STATUS.md').write_text(f'The build emitted {len(replacements)} validated replacements and a removal entry for all {len(rows)} source rows. Exact planned position cells, unique identities, field restrictions, GT agreement, room exclusions, and wording checks passed. Reading the 30 full samples and packaging remain.\n')
    print('BUILD',json.dumps(dict(rows=len(replacements),families=counts,refusals=checks['refusal_counts'],histograms=balanced)),flush=True)

if __name__=='__main__':main()
