"""Build truthful frame-k VSTI rows using the sealed N kit and pinned B2 inputs."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
import collections as C
import copy,hashlib,json,math,random,re,sys
from pathlib import Path
import base_rows as B
from stage_inputs import sha
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
B2=Path('/scratch/jjyeung/orch_n30/sb_rowB2')
SEED=20261119
CEILING=3
RULE='For an out-of-view object, cite the latest raster frame before k with share >= visibility_floor (0.002); if none, cite its first visible frame after k.'
SIGHTINGS={}
REVIEW=Path('/scratch/jjyeung/orch_n30/sb_brev3')
B3=Path('/scratch/jjyeung/orch_n30/sb_rowB3')
FAMILIES=B.FAMILIES

def dump(name,data):B.dump(OUT/name,data)
def status(s):(ROOT/'STATUS.md').write_text(s+'\n')
def load(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]
def semantics(r):return r['student_input']['options'][ord(r['answer'])-65][3:]
def rank_cell(r,semantic):
    p=r['provenance'];fs=p['first_seen'];objs=p['instances']
    if r['question_type'].startswith('camera_'):
        ordered=sorted(objs,key=lambda o:(fs[o['label']],o['id']))
        rank=next(i+1 for i,o in enumerate(ordered) if o['label']==semantic)
        return ('tied' if len(set(fs.values()))<len(fs) else 'untied',str(rank))
    a,b=[fs[o['label']] for o in objs]
    return ('earlier' if a<b else 'later' if a>b else 'tied',semantic)

def prepare_sightings(eligible,facts):
    import numpy as np
    groups=C.defaultdict(list)
    for rr in eligible.values():
        for r in rr:groups[facts[r['qid']]['source_gt']['path']].append(r)
    for i,(path,rr) in enumerate(sorted(groups.items()),1):
        assert sha(path)==facts[rr[0]['qid']]['source_gt']['sha256']
        wanted={o['id'] for r in rr for o in r['provenance']['instances']}
        with np.load(path,allow_pickle=False) as z:raster=z['inst']
        assert len(raster)==32
        counts={obj:[] for obj in wanted}
        for frame in raster:
            ids,nums=np.unique(frame,return_counts=True)
            shares=dict(zip(map(int,ids),nums/frame.size))
            for obj in wanted:counts[obj].append(float(shares.get(obj,0)))
        for r in rr:
            p=r['provenance'];k=p['camera_frame']
            for obj in p['instances']:
                shares=counts[obj['id']]
                assert math.isclose(shares[k-1],p['frame_n_share'][obj['label']],abs_tol=1e-12)
                if shares[k-1]>=p['visibility_floor']:continue
                visible=[j+1 for j,share in enumerate(shares) if share>=p['visibility_floor']]
                assert visible,('MISSING raster sighting',r['qid'],obj['label'])
                before=[j for j in visible if j<k]
                f=max(before) if before else min(visible)
                assert before or f>k
                SIGHTINGS[r['qid'],obj['label']]=(f,'last_before' if before else 'first_after')
        if i%100==0:print('raster sighting groups',i,'/',len(groups),flush=True)

def sighting(r,label):
    return SIGHTINGS[r['qid'],label]

def geometry(r,fact):
    p=r['provenance'];labels=[o['label'] for o in p['instances']];v=p['geometry_values'];fam=r['question_type']
    if fam.startswith('camera_'):
        # Camera provenance stores sorted distances. The original trace binds labels to that ordering.
        m=re.search(r'the objects are (.+?)\.',r['target']);assert m
        ordered=m[1].split(', then ')
        assert set(ordered)==set(labels) and ordered==fact['order']
        by=dict(zip(ordered,v));assert len(by)==len(labels)
    else:by=dict(zip(labels,v))
    if fam.endswith('_ud'):
        assert math.isclose(v[0]-v[1],fact['values'][0]-fact['values'][1],abs_tol=1e-5)
    else:
        for label,val in zip(labels,fact['values']):assert math.isclose(by[label],val,rel_tol=1e-5,abs_tol=1e-5),(r['qid'],by,val)
    if fam.startswith('camera_'):sem=min(by,key=by.get)
    elif fam.endswith('_nf'):sem='Near' if v[0]<v[1] else 'Far'
    elif fam.endswith('_lr'):sem='Left' if v[0]<v[1] else 'Right'
    else:sem='Up' if v[0]>v[1] else 'Down'
    assert sem==fact['semantic']==semantics(r)
    return by

def render(r,fact,pos,rep,pins):
    x=copy.deepcopy(r);p=r['provenance'];fam=r['question_type'];k=p['camera_frame']
    choices,question=B.option_permutation(r,fact,pos)
    x['student_input']['question']=question
    x['student_input']['options']=[f'{chr(65+i)}. {s}' for i,s in enumerate(choices)]
    x['answer']=chr(65+pos)
    x['qid']='sb_rowB4_'+B.dh([SEED,r['qid'],pos,rep,question,choices])[:24]
    vals=geometry(r,fact);labels=list(vals);ordered=sorted(vals,key=vals.get)
    lines=[f'Step 1: take the camera viewpoint of frame {k} of 32. Sighting references use raster visibility.']
    evidence={}
    for label in (choices if fam.startswith('camera_') else [o['label'] for o in p['instances']]):
        visible=p['frame_n_share'][label]>=p['visibility_floor']
        name='the object labelled "'+label+'"'
        if visible:
            visibility=f'{name} is in view in frame {k}'
            evidence[label]=dict(in_view=True,share=p['frame_n_share'][label])
        else:
            f,rule=sighting(r,label)
            visibility=f'{name} is out of view in frame {k}'
            if rule=='last_before':visibility+=f'; it was last seen in frame {f}'
            evidence[label]=dict(in_view=False,share=p['frame_n_share'][label],recorded_frame=f,rule=rule)
        if fam.startswith('camera_'):
            j=ordered.index(label);parts=[]
            if j>0:parts.append('farther than the '+ordered[j-1])
            if j+1<len(ordered):parts.append('nearer than the '+ordered[j+1])
            relation='relative to that camera, its closest point is '+' and '.join(parts)
        else:
            other=next(a for a in labels if a!=label)
            if fam.endswith('_nf'):
                rel='nearer' if vals[label]<vals[other] else 'farther'
                relation=f'relative to that camera, its closest point is {rel} than the closest point of the {other}'
            elif fam.endswith('_lr'):
                rel='left' if vals[label]<vals[other] else 'right'
                relation=f'from that camera viewpoint, its centre is to the {rel} of the centre of the {other}'
            else:
                rel='higher' if vals[label]>vals[other] else 'lower'
                relation=f'in that camera\'s level horizon, its centre is {rel} than the centre of the {other}'
        lines.append(f'Step {len(lines)+1}: {visibility}; {relation}.')
        if not visible and rule=='first_after':
            instance_name='the object instance labelled "'+label+'"'
            lines.append(f'Step {len(lines)+1}: for {instance_name}, it first appears in frame {f}, after frame {k}.')
    sem=fact['semantic']
    if fam.startswith('camera_'):
        lines.append(f'Step {len(lines)+1}: ordered nearest to farthest from that camera, the objects are '+', then '.join(ordered)+'.')
        lines.append(f'So the closest object to that camera is the {sem}.')
    else:
        a,b=[o['label'] for o in p['instances']]
        if fam.endswith('_nf'):lines.append(f'So relative to that camera, the closest point of the {a} is {"nearer" if sem=="Near" else "farther"} than the closest point of the {b}.')
        elif fam.endswith('_lr'):lines.append(f'So from that camera viewpoint, the centre of the {a} is to the {sem.lower()} of the centre of the {b}.')
        else:lines.append(f'So the centre of the {a} is {"higher" if sem=="Up" else "lower"} than the centre of the {b} in that camera\'s level horizon.')
    x['target']='<think>\n'+'\n'.join(lines)+'\n</think>\n\n'+x['answer']
    ci=dict(qid=x['qid'],scene=x['scene'],frame_indices=x['student_input']['frame_indices'],type=fam,question=question,options=x['student_input']['options'],trace_revision='3.14')
    x['candidate_id']=B.candidate_identity(ci)
    x['provenance']['sb_rowB4']=dict(source_qid=r['qid'],source_row_sha256=B.dh(r),
        input_sha256=pins,source_gt=fact['source_gt'],ground_truth_fact_sha256=B.dh(fact),seed=SEED,
        occurrence=rep,source_use_ceiling=CEILING,candidate_identity_input=ci,semantic_answer=sem,
        first_seen_cell=list(rank_cell(r,sem)),sighting_rule=RULE,visibility=evidence)
    return x

def hist(rows):
    result={}
    for fam in FAMILIES:
        rr=[r for r in rows if r['question_type']==fam]
        positions=C.Counter();ranks=C.Counter();joint=C.Counter();semantic=C.Counter();visibility=C.Counter();earliest=C.Counter()
        for r in rr:
            p=r['provenance'];s=semantics(r);a,b=rank_cell(r,s)
            positions[r['answer']]+=1;ranks[a+'|'+b]+=1;joint[a+'|'+b+'|'+r['answer']]+=1
            if not fam.startswith('camera_'):semantic[s]+=1
            flags=[p['frame_n_share'][o['label']]>=p['visibility_floor'] for o in p['instances']]
            visibility['all_out_of_view' if not any(flags) else 'all_in_view' if all(flags) else 'mixed']+=1
            if fam.startswith('camera_'):
                fs=p['first_seen'];minf=min(fs.values());ismin=fs[s]==minf
                earliest['earliest_including_ties' if ismin else 'later']+=1
                if a=='untied':earliest['untied_earliest' if ismin else 'untied_later']+=1
        result[fam]=dict(rows=len(rr),position=dict(positions),first_seen=dict(ranks),joint=dict(joint),semantic=dict(semantic),visibility=dict(visibility),earliest=dict(earliest))
    return result

def balanced_schedule(eligible,facts):
    schedule=[];plan={};uses=C.Counter()
    for fam in FAMILIES:
        groups=C.defaultdict(list);nopt={'camera_obj_rel_dist_v1':4,'camera_obj_rel_dist_v2':3}.get(fam,2)
        for r in eligible[fam]:groups[rank_cell(r,facts[r['qid']]['semantic'])].append(r)
        expected_strata=['tied','untied'] if fam.startswith('camera_') else ['earlier','later','tied']
        categories=[str(i+1) for i in range(nopt)] if fam.startswith('camera_') else {'lr':['Left','Right'],'nf':['Near','Far'],'ud':['Up','Down']}[fam[-2:]]
        plan[fam]={}
        for a in expected_strata:
            assert all(groups[a,b] for b in categories),('short stratum',fam,a)
            target=nopt*math.ceil(max(len(groups[a,b]) for b in categories)/nopt)
            for b in categories:
                rr=sorted(groups[a,b],key=lambda r:r['qid']);rng=random.Random(f'{SEED}|{fam}|{a}|{b}');rng.shuffle(rr)
                full,extra=divmod(target,len(rr));degree=[full+(i<extra) for i in range(len(rr))]
                assert min(degree)>=1 and max(degree)<=min(CEILING,nopt)
                remaining={p:target//nopt for p in range(nopt)}
                # A bipartite degree construction gives each source distinct option positions.
                for r,d in sorted(zip(rr,degree),key=lambda t:-t[1]):
                    ties={p:rng.random() for p in remaining}
                    pos=sorted(remaining,key=lambda p:(-remaining[p],ties[p]))[:d]
                    assert all(remaining[p]>0 for p in pos)
                    for p in pos:
                        remaining[p]-=1;uses[r['qid']]+=1
                        schedule.append((r,facts[r['qid']],p,uses[r['qid']]))
                assert all(v==0 for v in remaining.values())
                for p in range(nopt):plan[fam][a+'|'+b+'|'+chr(65+p)]=target//nopt
    assert max(uses.values())<=CEILING
    return schedule,plan,uses

def main():
    OUT.mkdir(exist_ok=True)
    inputs=[ROOT/n for n in ['build_rows.py','base_rows.py','stage_inputs.py','wording_filter.cpp','inputs/wording_filter.so','inputs/sources.jsonl','inputs/GT_FACTS.jsonl','inputs/GT_REFUSALS.json','inputs/GT_RESOLUTION.json','inputs/WORDING_CORPUS.json','inputs/dev_scene_exclusions.json','prompts/sb_rowB4.md','out/CODE_ORIGIN.json']]
    inputs += [B.STORE/n for n in ['vqa/rows.sqlite','BUILD_MANIFEST.json','COUNTS_V7.json','FAMILY_INDEX_RANGES.json']]
    inputs += [B.N,B.CONFIG,B.ORIGINAL_CODE/'generate.py',B.ORIGINAL_CODE/'geometry.py',B2/'out/rows.jsonl',B2/'out/INPUTS.json',B.TREE.parents[1]/'out/TREE_SEAL.json']
    inputs += [REVIEW/'REMOVE_PROPOSED.json',B3/'out/REMOVE.json']
    pins={str(p):sha(p) for p in inputs}
    assert pins[str(B.STORE/'vqa/rows.sqlite')]=='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
    seal=json.loads((B.TREE.parents[1]/'out/TREE_SEAL.json').read_text());matched={}
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and str(p).startswith(str(B.TREE)) and Path(p).is_file():
            rel=str(Path(p).relative_to(B.TREE));h=sha(p);assert seal['files'][rel]==h
            pins[p]=h;matched[rel]=h
    rooms,excluded=B.room_authorities(pins)
    rows=B.load_rows();local=load(ROOT/'inputs/sources.jsonl')
    assert {r['qid']:r for r in rows}=={r['qid']:r for r in local}
    facts={f['old_qid']:f for f in load(ROOT/'inputs/GT_FACTS.jsonl')}
    missing=json.loads((ROOT/'inputs/GT_REFUSALS.json').read_text())['refused']
    resolution=json.loads((ROOT/'inputs/GT_RESOLUTION.json').read_text())
    nrows=load(B.N);outside={r['row_key'] for r in nrows if r['reason']=='outside_native_training_division'}
    proposed=load(REVIEW/'REMOVE_PROPOSED.json');dropped={r['row_key'] for r in proposed}&outside
    assert len(dropped)==117 and len({r['scene'] for r in proposed if r['row_key'] in dropped})==10
    wf=B.WordingFilter();eligible=C.defaultdict(list);reasons={};hits={}
    for i,r in enumerate(rows):
        B.native_validate(r);qid=r['qid'];why=B.room_reasons(r,rooms,excluded)
        if qid not in facts:why.append(missing[qid])
        if not why:
            geometry(r,facts[qid])
            for pos in range(len(r['student_input']['options'])):
                _,q=B.option_permutation(r,facts[qid],pos);hit=wf.hit(q)
                if hit:why.append('heldout_wording_distance_le_0.05');hits[qid]=hit;break
        if qid in dropped:why.append('outside_native_training_division')
        if why:reasons[qid]=why
        else:eligible[r['question_type']].append(r)
        if i%2000==0:print('sources validated',i,flush=True)
    # Preserve every B2-admitted source, including every all-out-of-view source.
    b2=load(B2/'out/rows.jsonl');b2ids={r['provenance']['sb_rowB2']['source_qid']:r['qid'] for r in b2}
    assert set(b2ids)-dropped=={r['qid'] for rr in eligible.values() for r in rr}
    schedule,plan,uses=balanced_schedule(eligible,facts)
    prepare_sightings(eligible,facts)
    dump('INPUTS.json',dict(input_sha256=pins,kit_tree_sha256=seal['tree_sha256'],kit_modules=matched,
        gt_rasters={p['path']:p['sha256'] for p in resolution['resolved'].values()},
        wording_input_sha256=wf.data['input_sha256'],source_use_ceiling=CEILING))
    common={str(OUT/'INPUTS.json'):sha(OUT/'INPUTS.json'),str(ROOT/'build_rows.py'):sha(ROOT/'build_rows.py')}
    dump('PLAN.json',dict(input_sha256=common,expected_joint_cells=plan,source_use_ceiling=CEILING,
        rule='Keep every eligible source; oversample within first-seen strata to exact rank/semantic by option-position cells. Tie ranks sort by (first_seen, numeric instance id).'))
    status(f'The census and source validators passed for {len(rows):,} sources. Room and wording filters admit {len(uses):,} sources. PLAN.json fixes {len(schedule):,} output rows with exact joint cells and at most {CEILING} uses per source. Rendering and independent checks remain.')
    output=[];mapping=[]
    for r,fact,pos,rep in schedule:
        x=render(r,fact,pos,rep,common)
        B.native_validate(x);assert not B.room_reasons(x,rooms,excluded)
        assert wf.hit(x['student_input']['question']) is None
        assert set(re.findall(r'frame (\d+)',x['target']))<=set(map(str,range(1,33)))
        assert 'located in frame' not in x['target'] and 'locate the' not in x['target']
        output.append(x);mapping.append(dict(input_sha256=common,old_qid=r['qid'],sb_rowB2_qid=b2ids[r['qid']],new_qid=x['qid'],candidate_id=x['candidate_id'],occurrence=rep))
    assert len({r['qid'] for r in output})==len(output)==len({r['candidate_id'] for r in output})
    after=hist(output);all_before=hist(rows);admitted_before=hist([r for rr in eligible.values() for r in rr])
    for fam in FAMILIES:
        assert after[fam]['joint']==plan[fam],('short cell',fam)
        assert len(set(after[fam]['position'].values()))==1
        assert after[fam]['visibility']['all_out_of_view']>=admitted_before[fam]['visibility']['all_out_of_view']
    for name,rr in [('rows.jsonl',output),('QID_MAP.jsonl',mapping)]:
        with (OUT/name).open('w') as f:
            for r in rr:f.write(json.dumps(r,sort_keys=True,allow_nan=False)+'\n')
    schema=set(json.loads(B.N.read_text().splitlines()[0]));assert schema=={'pool','question_type','reason','row_key','scene'}
    remove=[r for r in proposed if r['row_key'] not in dropped]
    assert {r['row_key'] for r in remove}==set(uses) and len(remove)==6710
    old_remove=load(B3/'out/REMOVE.json')
    wording=[r for r in old_remove if r['reason']=='heldout_wording_distance_le_0.05']
    missing_remove=[r for r in old_remove if r['row_key'] in missing]
    assert len(wording)==679 and len(missing_remove)==4420
    output_removals={'REMOVE.json':remove,'REMOVE_WORDING.json':wording,'REMOVE_MISSING_GT.json':missing_remove}
    for name,items in output_removals.items():
        with (OUT/name).open('w') as f:
            for item in items:
                assert set(item)==schema
                f.write(json.dumps(item,sort_keys=True,separators=(',',':'))+'\n')
    dump('REMOVE.provenance.json',dict(input_sha256={**common,str(B.N):pins[str(B.N)],str(REVIEW/'REMOVE_PROPOSED.json'):pins[str(REVIEW/'REMOVE_PROPOSED.json')],str(B3/'out/REMOVE.json'):pins[str(B3/'out/REMOVE.json')]},
        output_sha256={n:sha(OUT/n) for n in output_removals},counts={n:len(rr) for n,rr in output_removals.items()},dropped_native_sources=len(dropped),dropped_native_scenes=10,schema=sorted(schema),format='Compact JSON Lines; exact N n.json schema; hashes in this sidecar'))
    dump('REFUSALS.json',dict(input_sha256=common,rows=reasons,wording_hits=hits,missing_inputs=resolution['missing']))
    dump('HISTOGRAMS.json',dict(input_sha256={**common,str(OUT/'rows.jsonl'):sha(OUT/'rows.jsonl')},source_all_before=all_before,admitted_sources_before=admitted_before,after=after,
        rank_rule='Camera: ascending first_seen, break ties by numeric instance id; report tied and untied separately. Pair families: subject first_seen earlier/later/tied relative to reference; semantic answers balanced within each stratum.'))
    dump('KIT_CHECK.json',dict(input_sha256=common,status='PASS',tree_sha256=seal['tree_sha256'],matched_modules=matched))
    dump('CHECKS.json',dict(input_sha256=common,status='PENDING_INDEPENDENT_AND_READ30',families={f:after[f]['rows'] for f in FAMILIES},source_rows=len(rows),source_native_pack_validate=len(rows),replacement_native_pack_validate=len(output),
        unique_qids=True,unique_candidate_ids=True,exact_joint_cells=True,source_use_ceiling=CEILING,max_source_uses=max(uses.values()),source_use_histogram=dict(C.Counter(uses.values())),admitted_unique_sources=len(uses),
        all_admitted_sources_retained=True,all_out_of_view_sources_retained=True,room_rule_pass=True,sighting_rule=RULE,
        wording_filter=dict(threshold=B.THRESHOLD,metric='Levenshtein / max codepoint length; NFKC casefold collapsed whitespace',unique_heldout_wordings=len(wf.data['questions']),input_files=len(wf.data['input_sha256']),refused_sources=len(hits),all_permutations_prefiltered=True),
        refusal_counts=dict(C.Counter(s for rr in reasons.values() for s in rr)),missing_gt_rows=len(missing),missing_gt_rasters=len(resolution['missing']),
        next_read_gate=dict(baseline_changes=18,pairs=59,criterion='On dev camera-item pairs from the same room with different k and changing true winner, the model top shared object should change on more than 18 of 59 fixed pairs; also report correctness and denominator. No next read performed.'),
        output_sha256={n:sha(OUT/n) for n in ['rows.jsonl','QID_MAP.jsonl','REMOVE.json','PLAN.json','HISTOGRAMS.json']}))
    chosen=[]
    for fam in FAMILIES:
        rr=[r for r in output if r['question_type']==fam];used=set()
        # Cover in-view, all-out, mixed, future reference, and a general example when available.
        selectors=[lambda r:all(o['in_view'] for o in r['provenance']['sb_rowB4']['visibility'].values()),
          lambda r:not any(o['in_view'] for o in r['provenance']['sb_rowB4']['visibility'].values()),
          lambda r:0<sum(o['in_view'] for o in r['provenance']['sb_rowB4']['visibility'].values())<len(r['provenance']['instances']),
          lambda r:any(o.get('recorded_frame',0)>r['provenance']['camera_frame'] for o in r['provenance']['sb_rowB4']['visibility'].values()),lambda r:True]
        for pred in selectors:
            r=next((r for r in rr if r['qid'] not in used and pred(r)),None)
            if r is None:r=next(r for r in rr if r['qid'] not in used)
            used.add(r['qid']);chosen.append(r)
    with (OUT/'READ30.md').open('w') as f:
        for i,r in enumerate(chosen,1):
            f.write(f'## {i}. {r["question_type"]}: {r["qid"]}\n\n'+r['student_input']['question']+'\n\n'+'\n'.join(r['student_input']['options'])+'\n\n'+r['target']+'\n\nFull row:\n```json\n'+json.dumps(r,sort_keys=True)+'\n```\n\n')
    status(f'The generator emitted {len(output):,} rows from all {len(uses):,} eligible sources. Every source and replacement passes the sealed N pack and validators. Exact joint cells and the {CEILING}-use ceiling pass. Independent geometry/visibility checks, the full thirty-row review, and archive sealing remain.')
    print('BUILD',json.dumps(dict(rows=len(output),families={f:after[f]['rows'] for f in FAMILIES},uses=dict(C.Counter(uses.values())))),flush=True)
if __name__=='__main__':main()
