"""Verify every delivered row independently against hash-pinned GT arrays and source metadata."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import collections as C
import hashlib,json,math,re,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out'
TREE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
sys.path.insert(0,str(TREE))
from student_pilot.carrier_c1_routing import direct_row
from student_pilot.trace_grammar import validate_row
from student_pilot.r2_grammar import validate_direct
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    return h.hexdigest()
def dh(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def load(p):return [json.loads(s) for s in p.read_text().splitlines()]
def main():
    rows=load(OUT/'rows.jsonl');sources={r['qid']:r for r in load(ROOT/'inputs/sources.jsonl')}
    facts={f['old_qid']:f for f in load(ROOT/'inputs/GT_FACTS.jsonl')}
    mapping=load(OUT/'QID_MAP.jsonl');removal=load(OUT/'REMOVE.json')
    plan=json.loads((OUT/'PLAN.json').read_text())['expected_joint_cells']
    checks=json.loads((OUT/'CHECKS.json').read_text());manifest=json.loads((OUT/'INPUTS.json').read_text())
    pin_cache={}
    source_uses=C.Counter();position=C.defaultdict(C.Counter);joint=C.defaultdict(C.Counter);groups=C.defaultdict(list)
    ids=set();cids=set();changes=C.Counter();viscounts=C.Counter();frames=C.Counter();unique_source=set();geom_count=0
    b2={r['provenance']['sb_rowB2']['source_qid']:r['qid'] for r in load(Path('/scratch/jjyeung/orch_n30/sb_rowB2/out/rows.jsonl'))}
    b2_qids=set(b2.values())
    all_ids=set()
    for p in Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/FAMILY_QIDS').glob('*.txt'):all_ids.update(p.read_text().splitlines())
    for row in rows:
        edit=row['provenance']['sb_rowB3'];old=edit['source_qid'];src=sources[old];p=src['provenance'];fam=row['question_type'];k=p['camera_frame'];fact=facts[old]
        assert edit['source_row_sha256']==dh(src) and edit['ground_truth_fact_sha256']==dh(fact)
        for path,digest in edit['input_sha256'].items():
            if path not in pin_cache:pin_cache[path]=sha(path)
            assert pin_cache[path]==digest
        assert row['qid'] not in ids and row['qid'] not in all_ids and row['qid'] not in b2_qids and row['candidate_id'] not in cids
        ids.add(row['qid']);cids.add(row['candidate_id']);source_uses[old]+=1;unique_source.add(old)
        assert 1<=k<=32 and len(row['student_input']['frame_indices'])==32 and p['visibility_floor']==0.002
        ci=dict(qid=row['qid'],scene=row['scene'],frame_indices=row['student_input']['frame_indices'],type=fam,question=row['student_input']['question'],options=row['student_input']['options'],trace_revision='3.14')
        assert ci==edit['candidate_identity_input'] and candidate_identity(ci)==row['candidate_id']
        excluded={'qid','candidate_id','answer','target','student_input','provenance'}
        assert {a:b for a,b in row.items() if a not in excluded}=={a:b for a,b in src.items() if a not in excluded}
        assert {a:b for a,b in row['student_input'].items() if a not in {'question','options'}}=={a:b for a,b in src['student_input'].items() if a not in {'question','options'}}
        assert {a:b for a,b in row['provenance'].items() if a!='sb_rowB3'}==p
        assert sorted(s[3:] for s in row['student_input']['options'])==sorted(s[3:] for s in src['student_input']['options'])
        if fam.startswith('camera_'):
            assert re.sub(r'\([^()]+\)','(OPTIONS)',row['student_input']['question'])==re.sub(r'\([^()]+\)','(OPTIONS)',src['student_input']['question'])
        else:assert row['student_input']['question']==src['student_input']['question']
        changes.update(a for a in row if row[a]!=src.get(a))
        assert not validate_row(row)
        assert direct_row(row)['target']==row['target']
        assert validate_direct(row['target'],row['student_input']['question'],32)==row['answer']
        trace=row['target'];assert re.search(r'frame (\d+) of 32',trace).group(1)==str(k)
        assert all(1<=int(f)<=32 for f in re.findall(r'frame (\d+)',trace))
        assert not any(t in trace for t in ['located in frame','locate the','seconds','lower left','upper right','upper left','lower right'])
        labels=[o['label'] for o in p['instances']]
        assert len(re.findall(' is (?:in view|out of view) in frame ',trace))==len(labels)
        for obj in p['instances']:
            label=obj['label'];name='the object labelled "'+label+'"'
            lines=[l for l in trace.splitlines() if re.match(r'Step \d+: '+re.escape(name)+r' is ',l)]
            assert len(lines)==1;line=lines[0];visible=p['frame_n_share'][label]>=p['visibility_floor']
            ev=edit['visibility'][label];assert ev['in_view']==visible and ev['share']==p['frame_n_share'][label]
            if visible:
                assert f'{name} is in view in frame {k};' in line and 'last seen' not in line
                viscounts['in_view_objects']+=1
            else:
                frames_available=[o['frame'] for o in p['instances'] if o['label']==label and o['share']>=p['visibility_floor']]
                prior=[f for f in frames_available if f<k]
                chosen=max(prior) if prior else sorted(frames_available,key=lambda f:(abs(f-k),f))[0]
                assert f'{name} is out of view in frame {k}; it was last seen in frame {chosen} (' in line
                assert ev['recorded_frame']==chosen
                if prior:assert '(latest recorded sighting before the queried frame)' in line;frames['latest_before']+=1
                else:
                    assert '(nearest recorded sighting' in line;frames['nearest_fallback']+=1
                    if chosen>k:assert 'later in the clip' in line;frames['future_reference_disclosed']+=1
                viscounts['out_of_view_objects']+=1
        sem=row['student_input']['options'][ord(row['answer'])-65][3:]
        fs=p['first_seen']
        if fam.startswith('camera_'):
            ordered=sorted(p['instances'],key=lambda o:(fs[o['label']],o['id']))
            a='tied' if len(set(fs.values()))<len(fs) else 'untied'
            b=str(next(i+1 for i,o in enumerate(ordered) if o['label']==sem))
        else:
            fs0,fs1=[fs[o['label']] for o in p['instances']];a='earlier' if fs0<fs1 else 'later' if fs0>fs1 else 'tied';b=sem
        assert edit['first_seen_cell']==[a,b]
        joint[fam][a+'|'+b+'|'+row['answer']]+=1;position[fam][row['answer']]+=1
        groups[fact['source_gt']['path']].append(row)
    for fam,cells in plan.items():
        assert dict(joint[fam])==cells and len(set(position[fam].values()))==1
        for stratum in {s.split('|')[0] for s in cells}:
            assert len({v for s,v in cells.items() if s.split('|')[0]==stratum})==1
    assert max(source_uses.values())<=3 and unique_source==set(b2)
    pairs=[(r['provenance']['sb_rowB3']['source_qid'],r['answer']) for r in rows];assert len(set(pairs))==len(pairs)
    assert len(removal)==len(sources) and {r['row_key'] for r in removal}==set(sources)
    for r in removal:
        assert set(r)=={'pool','question_type','reason','row_key','scene'}
        src=sources[r['row_key']];assert (r['pool'],r['question_type'],r['scene'])==(src['pool'],src['question_type'],src['dataset']+'/'+src['scene'])
    assert len(mapping)==len(rows)
    mapped={m['new_qid']:m for m in mapping}
    assert set(mapped)==ids
    for r in rows:
        e=r['provenance']['sb_rowB3'];m=mapped[r['qid']]
        assert m['old_qid']==e['source_qid'] and m['sb_rowB2_qid']==b2[e['source_qid']] and m['candidate_id']==r['candidate_id']
    gt_pins={};computed={};gt_visibility={};total_groups=len(groups)
    for index,(path,group) in enumerate(sorted(groups.items()),1):
        digest=sha(path);gt_pins[path]=digest
        assert digest==facts[group[0]['provenance']['sb_rowB3']['source_qid']]['source_gt']['sha256']
        with np.load(path,allow_pickle=False) as z:
            poses=z['c2w'].astype(float);ids_gt=list(map(int,z['ids']));centers=z['obb_centroid'].astype(float)
            axes=z['obb_axes'].astype(float);lengths=z['obb_lengths'].astype(float);raster=z['inst'];indices=list(map(int,z['frame_indices']))
            valid=z['valid'].astype(bool) if 'valid' in z else np.ones(32,dtype=bool)
        assert len(poses)==len(raster)==32
        for row in group:
            old=row['provenance']['sb_rowB3']['source_qid'];src=sources[old];p=src['provenance'];fact=facts[old];k=p['camera_frame'];fam=row['question_type']
            assert p['raster_sha256']==digest and indices==src['student_input']['frame_indices'] and valid[k-1]
            if old not in computed:
                vals=[];labels=[]
                for obj in p['instances']:
                    j=ids_gt.index(obj['id']);center=centers[j];ax=axes[j].reshape(3,3)
                    if p['geometry_audit']['axes_layout']=='columns':ax=ax.T
                    half=lengths[j]*p['geometry_audit']['box_half_factor'];pose=poses[k-1]
                    squared=0.
                    for d in range(3):
                        component=sum(float(ax[d,c])*float(pose[c,3]-center[c]) for c in range(3))
                        residual=max(0.,abs(component)-float(half[d]));squared+=residual**2
                    distance=math.sqrt(squared)
                    local=np.linalg.solve(pose[:3,:3],center-pose[:3,3]);bearing=math.atan2(float(local[0]),float(local[2]))
                    height=sum(float(center[c])*float(p['geometry_audit']['up'][c]) for c in range(3))
                    val=distance if fam.startswith('camera_') or fam.endswith('_nf') else bearing if fam.endswith('_lr') else height
                    vals.append(val);labels.append(obj['label'])
                    if fam.endswith('_lr'):assert local[2]>0
                    share=float(np.count_nonzero(raster[k-1]==obj['id'])/raster[k-1].size)
                    assert math.isclose(share,p['frame_n_share'][obj['label']],abs_tol=1e-12)
                    f=obj['frame'];seen=float(np.count_nonzero(raster[f-1]==obj['id'])/raster[f-1].size)
                    assert math.isclose(seen,obj['share'],abs_tol=1e-12) and seen>=p['visibility_floor'] and f==p['first_seen'][obj['label']]
                src_values=p['geometry_values']
                if fam.startswith('camera_'):
                    order=[labels[i] for i in sorted(range(len(vals)),key=vals.__getitem__)]
                    assert np.allclose(sorted(vals),src_values,atol=1e-5,rtol=1e-5)
                    assert re.search(r'the objects are (.+?)\.',src['target'])[1].split(', then ')==order
                    sem=order[0]
                else:
                    assert np.allclose(vals,src_values,atol=1e-5,rtol=1e-5)
                    if fam.endswith('_nf'):sem='Near' if vals[0]<vals[1] else 'Far'
                    elif fam.endswith('_lr'):sem='Left' if vals[0]<vals[1] else 'Right'
                    else:sem='Up' if vals[0]>vals[1] else 'Down'
                assert sem==fact['semantic'];computed[old]=(sem,dict(zip(labels,vals)))
            sem,values=computed[old];trace=row['target']
            assert row['student_input']['options'][ord(row['answer'])-65][3:]==sem
            for label,value in values.items():
                name='the object labelled "'+label+'"'
                line=next(l for l in trace.splitlines() if re.match(r'Step \d+: '+re.escape(name)+r' is ',l))
                if fam.startswith('camera_'):
                    order=sorted(values,key=values.get);i=order.index(label)
                    if i>0:assert 'farther than the '+order[i-1] in line
                    if i+1<len(order):assert 'nearer than the '+order[i+1] in line
                    assert 'the objects are '+', then '.join(order)+'.' in trace
                else:
                    other=next(s for s in values if s!=label)
                    if fam.endswith('_nf'):clause=('nearer' if value<values[other] else 'farther')+' than the closest point of the '+other
                    elif fam.endswith('_lr'):clause=('left' if value<values[other] else 'right')+' of the centre of the '+other
                    else:clause=('higher' if value>values[other] else 'lower')+' than the centre of the '+other
                    assert clause in line
            geom_count+=1
        if index%50==0:print('independent GT scenes',index,'/',total_groups,flush=True)
    assert geom_count==len(rows) and len(computed)==len(unique_source)
    pins={str(p):sha(p) for p in [Path(__file__),OUT/'rows.jsonl',OUT/'INPUTS.json',OUT/'PLAN.json',OUT/'QID_MAP.jsonl',OUT/'REMOVE.json',ROOT/'inputs/sources.jsonl',ROOT/'inputs/GT_FACTS.jsonl']}
    result=dict(status='PASS',input_sha256=pins,gt_input_sha256=gt_pins,rows_independently_recomputed=geom_count,unique_sources_recomputed=len(computed),gt_scenes=len(groups),
        frame_k_visibility_matches_rasters=True,recorded_sighting_share_matches_rasters=True,provenance_geometry_matches_gt=True,
        per_object_visibility_and_relation_checked=True,sighting_frame_rule_checked=True,visibility_objects=dict(viscounts),sighting_frames=dict(frames),
        unique_qids=True,unique_candidate_ids=True,full_store_index_qids=len(all_ids),candidate_ids_recomputed=True,field_diff=dict(changes),
        exact_joint_cells=True,max_source_uses=max(source_uses.values()),all_b2_sources_retained=True,no_repeated_source_position=True,
        native_pack_validate=True,removal_and_mapping_coverage=True)
    (OUT/'INDEPENDENT_CHECK.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (ROOT/'STATUS.md').write_text(f'Independent checks recomputed answers and object relations for all {len(rows):,} rows from {len(groups):,} pinned GT rasters. Frame-k visibility, sighting references, identities, field restrictions, exact joint cells, mappings, and removal schema passed. The thirty-row review and archive sealing remain.\n')
    print('INDEPENDENT PASS',len(rows),dict(viscounts),dict(frames),flush=True)
if __name__=='__main__':main()
