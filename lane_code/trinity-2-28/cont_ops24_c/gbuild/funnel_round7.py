"""Join real T1 selections; compare point and partially annotated dense arms."""
from round7_common import *
from collections import Counter, defaultdict
import copy
import time
from gpkg.capture_io import Records
from gpkg.runtime.c import unrle
from gpkg.grid import resize
from gt.adapter import names
from gt.v2 import alignment
from analyze_round4 import object_join
from analyze_s2_round6 import object_analysis

ARMS=('t1','points','dense64')

def item_stage(objects):
    """Known earlier failures dominate later censoring; no-GT obeys the brief."""
    failures=[o['stage'] for o in objects if o['stage'] in LABELS[:5]]
    first=min(failures) if failures else None
    unknown=[o.get('censored_from','S0') for o in objects if o['stage']=='censored']
    if first is not None and (not unknown or first < min(unknown)):
        return first
    if any(o['stage']=='no-GT' for o in objects):
        return 'no-GT' if first is None else 'censored'
    if unknown or not objects:
        return 'censored'
    return first or 'S5'

def normalize(value, target, annotation):
    value['original_stage']=value['stage']
    if annotation is None or not target or not target.get('binding_reviewed'):
        value.update(stage='no-GT',reason='missing GT capture' if annotation is None else 'missing unique GT instance binding')
    elif value['stage']=='U':
        value.update(stage='censored',censored_from='S4' if value.get('evidence',{}).get('selected_correct_frames',0)>=3 and value['evidence'].get('selected_correct') else 'S0')
    return value

def anchor_object(row, obj):
    """Project dense observations onto annotated sources, without inventing GT."""
    mapping={slot+1:i+1 for i,slot in enumerate(row['anchor_slots'])}
    v=dict(obj,proposals=[dict(p,frame=mapping[int(p['frame'])]) for p in obj['proposals'] if int(p['frame']) in mapping],
           selected_masks={str(mapping[int(f)]):m for f,m in obj['selected_masks'].items() if int(f) in mapping})
    return v

def dense_stage(row, obj, anchor, gt):
    """Resolve only stages invariant to all labels on unannotated extra frames."""
    v=copy.deepcopy(anchor)
    v['anchor_stage']=anchor['stage'];v['anchor_reason']=anchor['reason']
    if row['ground_frame_count']==32 or v['stage']=='no-GT' or not v.get('evidence'):
        return v
    known={s+1 for s in row['anchor_slots']}
    extra_active=sum(bool(unrle(m).any()) for f,m in obj['selected_masks'].items() if int(f) not in known)
    total_active=v['nonempty_selected_frames']+extra_active
    matched=len(v['selected_matched_frames']);upper=matched+extra_active
    v['support_bounds']=dict(annotated_matched=matched,unannotated_nonempty=extra_active,
                             matched_lower=matched,matched_upper=upper,all_nonempty=total_active)
    def censor(at,why):
        v.update(stage='censored',censored_from=at,reason=why)
        return v
    e=v['evidence']
    if not e['visible']:
        return censor('S0','GT has no annotations for 32 added ground frames; visibility unresolved')
    if not e['proposed']:
        extra_proposals=any(int(p['frame']) not in known for p in obj['proposals'])
        if extra_proposals:
            return censor('S1','No target proposal on anchors; added-frame proposal IoUs are unannotated')
        v.update(stage='S1',reason=None)
        return v
    if not total_active or 2*upper < total_active:
        v.update(stage='S2',reason=None)
        return v
    if 2*matched < total_active:
        return censor('S2','Full-track identity depends on unannotated added-frame masks')
    if upper<3:
        v.update(stage='S3',reason=None)
        return v
    if matched<3:
        return censor('S3','Correct support may cross three only on unannotated added frames')
    if not gt['alignment']['accepted']:
        return censor('S4','NPZ self-consistent; reader camera alignment fails round-5 criterion')
    if e['outside_box_m'] is None:
        return censor('S4','Missing fitted centroid or reviewed GT extent')
    # The anchor analysis already applies both ScanNet extent readings.
    if anchor['stage']=='censored':
        return v
    v.update(stage='S4' if e['outside_box_m']>.25 else 'S5',reason=None)
    return v

def stage_table(boot, items, objects):
    s5=[i for i in items if i['stage']=='S5']; sv,_=boot.samples(s5,'score')
    _,den=boot.samples(items,'score');out=[]
    for label in LABELS:
        ii=[i for i in items if i['stage']==label];oo=[o for o in objects if o['stage']==label]
        vv,nn=boot.samples(ii,'score');mean=boot.metric(ii,'score')
        budget=None
        if s5 and ii and label.startswith('S'):
            budget=boot.summarize(len(ii)/len(items)*(np.mean([i['score'] for i in s5])-mean['mean']),nn/den*(sv-vv))
        else:
            budget=dict(mean=None,ci95=None,defined_draws=0,undefined_draws=10000,
                        reason='No identifiable S5 item group' if not s5 else 'No stage observations or not a failure stage')
        out.append(dict(stage=label,objects=len(oo),items=len(ii),score=mean,signed_stage_budget=budget,
                        reasons=dict(Counter(o.get('reason') or 'resolved' for o in oo))))
    return out

def migration(boot, old, new, scores, arm, unit):
    key='key' if unit=='objects' else 'item_id'; dest={r[key]:r for r in new}
    cells=[];matrix=[]
    for a in LABELS:
        line=[]
        for b in LABELS:
            group=[r for r in old if r['stage']==a and dest[r[key]]['stage']==b]
            ids=sorted({r['item_id'] for r in group})
            rr=[dict(scores[i],delta=scores[i][arm]-scores[i]['t1']) for i in ids]
            cells.append(dict(from_stage=a,to_stage=b,count=len(group),distinct_items=len(ids),
                item_score_delta=boot.metric(rr,'delta'),baseline_item_score=boot.metric(rr,'t1'),arm_item_score=boot.metric(rr,arm),
                item_ids=ids,keys=[r[key] for r in group]))
            line.append(len(group))
        matrix.append(line)
    return dict(labels=LABELS,matrix=matrix,cells=cells,
                cell_item_weighting='Each distinct item counted once per cell; object cells can overlap in items')

def advanced(o, baseline_stage):
    if o['stage'].startswith('S'):
        return o['stage']>baseline_stage
    return o['stage']=='censored' and o.get('censored_from','S0')>baseline_stage

def lever_summary(boot, objects, items, scores):
    result=[]
    for unit,groups in [('objects',objects),('items',items)]:
        key='key' if unit=='objects' else 'item_id'
        lookup={a:{r[key]:r for r in groups[a]} for a in ARMS}
        for stage in LABELS[:4]:
            old=[r for r in groups['t1'] if r['stage']==stage]
            point=[r for r in old if advanced(lookup['points'][r[key]],stage)]
            dense=[r for r in old if advanced(lookup['dense64'][r[key]],stage)]
            neither=[r for r in old if not advanced(lookup['points'][r[key]],stage) and not advanced(lookup['dense64'][r[key]],stage)]
            same=[r for r in old if lookup['points'][r[key]]['stage']==stage and lookup['dense64'][r[key]]['stage']==stage]
            ids=sorted({r['item_id'] for r in old}); same_ids=sorted({r['item_id'] for r in same})
            rr=[dict(scores[i],point_delta=scores[i]['points']-scores[i]['t1'],dense_delta=scores[i]['dense64']-scores[i]['t1']) for i in ids]
            residual=[dict(scores[i],deficit=100-scores[i]['t1']) for i in same_ids]
            total=[dict(v,deficit=(100-v['t1']) if i in same_ids else 0.) for i,v in scores.items()]
            result.append(dict(unit=unit,stage=stage,count=len(old),point_proven_advanced=len(point),dense_proven_advanced=len(dense),
                neither_proven_advanced=len(neither),same_stage_in_both=len(same),same_stage_keys=[r[key] for r in same],
                same_stage_item_ids=same_ids,point_delta=boot.metric(rr,'point_delta'),dense_delta=boot.metric(rr,'dense_delta'),
                residual_score=boot.metric(residual,'t1'),residual_to_100_all150_points=boot.metric(total,'deficit'),
                residual_warning='100-score deficit is descriptive, not S5-level recoverable budget; object groups may overlap'))
    return result

def main():
    started=time.monotonic()
    assert (OUT/'CAMERA_SPLIT.md').is_file() and (OUT/'CAMERA_SPLIT.json').is_file()
    refs,score_rows=inputs(); scores={r['item_id']:r for r in score_rows}; boot=Bootstrap(refs)
    gt=read(ROOT/'out2/GT.json');camera=read(OUT/'CAMERA_SPLIT.json')
    camera_map={r['capture']:r for r in camera['captures']}
    for cap,g in gt.items():
        g['alignment']=camera_map[cap]['rigid_fit']
        for target in g['targets'].values():
            target['world_alignment_reviewed']=g['alignment']['accepted'] and bool(target.get('full_obb'))
            target['reader_world_to_gt_world']=g['alignment']['reader_world_to_gt_world']
    raw_join={r['key']:r for r in map(json.loads,(OUT/'JOIN_T1.jsonl').read_text().splitlines())}
    old_point={r['key']:r for r in read(CAP/'score_t2/STAGES_T2.json')['objects']['points']}
    objects={a:[] for a in ARMS};items={a:[] for a in ARMS};anchor_objects=[];anchor_items=[]
    s2_selected={};capture_reports={};camera_checks=[];joined_checks=0;point_checks=0
    for arm,filename,receipt in [('t1','t1.gz','t1ret'),('points','t2.gz','t2ret'),('dense64','dense.gz','dret')]:
        records=Records(CAP/filename,CAP/receipt/'CAPTURE.json');seen=set()
        for row in records:
            if row['pass_index']!=0: continue
            iid=row['item_id'];ref=refs[iid];g=gt.get(row['capture'])
            assert iid not in seen;seen.add(iid)
            assert row['capture']==ref['capture'] and row['source_indices']==ref['source_indices']
            row['arm']=arm
            if g and row['geometry']:
                poses=row['geometry']['camera_to_world_metric']
                if arm=='dense64':
                    assert len(poses)==row['ground_frame_count']
                    poses=[poses[i] for i in row['anchor_slots']]
                fit=alignment(poses,g['c2w'])
                assert fit['accepted']==g['alignment']['accepted']
                for metric in ('translation_rms_m','rotation_rms_deg','rotation_max_deg'):
                    assert abs(fit[metric]-g['alignment'][metric])<1e-5
                camera_checks.append(dict(arm=arm,item_id=iid,accepted=fit['accepted']))
            by_name={o['name']:o for o in row['objects']};joined=[];anchors=[]
            for name in names(ref)[0]:
                key=iid+':'+name;target=(g or {}).get('targets',{}).get(key);obj=by_name.get(name)
                if obj is None:
                    val=dict(key=key,item_id=iid,capture=row['capture'],arm=arm,name=name,stage='censored',
                             reason='no recorded object call',censored_from='S0',evidence={})
                    if not g or not target or not target.get('binding_reviewed'):
                        val.update(stage='no-GT',reason='missing GT; no recorded object call')
                    av=copy.deepcopy(val)
                else:
                    ob=anchor_object(row,obj) if arm=='dense64' else obj
                    av=normalize(object_join(row,ob,g),target,g)
                    if av['stage']=='censored' and av.get('censored_from')=='S4' and not g['alignment']['accepted']:
                        av['reason']='NPZ self-consistent; reader camera alignment fails round-5 criterion'
                    val=dense_stage(row,obj,av,g) if arm=='dense64' else av
                    if arm=='t1':
                        raw=raw_join[key]
                        if raw.get('evidence'):
                            for k,v in raw['evidence'].items():
                                if k!='outside_box_m': assert v==val['evidence'][k],(key,k)
                            joined_checks+=1
                        if val['stage']=='S2': s2_selected[key]=dict(selected_masks=obj['selected_masks'],source_indices=row['source_indices'])
                    elif arm=='points':
                        previous=old_point[key]
                        assert previous['stage']==val['original_stage'],(key,previous['stage'],val['original_stage'])
                        assert previous['evidence'].keys()==val['evidence'].keys()
                        for k,v in previous['evidence'].items():
                            if k=='outside_box_m' and v is not None:
                                assert abs(v-val['evidence'][k])<1e-10,(key,k,v,val['evidence'][k])
                            else:
                                assert v==val['evidence'][k],(key,k,v,val['evidence'][k])
                        point_checks+=1
                val['room']=scores[iid]['room'];val['item_score']=scores[iid][arm]
                av['room']=scores[iid]['room'];av['item_score']=scores[iid][arm]
                # Avoid copying unrelated large selector and point-prompt diagnostics.
                for v in (val,av):
                    for k in ('point_diagnostics','selector','lift'):
                        v.pop(k,None)
                joined.append(val);anchors.append(av)
            assert len(joined)==2
            objects[arm].extend(joined)
            ir=dict(scores[iid],arm=arm,stage=item_stage(joined),score=scores[iid][arm],
                    object_keys=[o['key'] for o in joined],object_stages=[o['stage'] for o in joined])
            if ir['stage']=='censored':
                ir['censored_from']=min([o.get('censored_from','S0') for o in joined if o['stage']=='censored']+
                                        [o['stage'] for o in joined if o['stage'] in LABELS[:5]])
            items[arm].append(ir)
            if arm=='dense64':
                anchor_objects.extend(anchors)
                anchor_items.append(dict(ir,stage=item_stage(anchors)))
            if len(seen)%25==0: print(json.dumps(dict(arm=arm,items=len(seen))),flush=True)
        assert len(seen)==150 and not records.report['salvaged']
        capture_reports[arm]=records.report
    tables={a:stage_table(boot,items[a],objects[a]) for a in ARMS}
    migrations={a:{unit:migration(boot,objects['t1'] if unit=='objects' else items['t1'],objects[a] if unit=='objects' else items[a],scores,a,unit)
                      for unit in ('objects','items')} for a in ('points','dense64')}
    anchor_migrations={unit:migration(boot,objects['t1'] if unit=='objects' else items['t1'],anchor_objects if unit=='objects' else anchor_items,scores,'dense64',unit) for unit in ('objects','items')}
    levers=lever_summary(boot,objects,items,scores)
    definitions=dict(stages='First failing stage; IoU >0.5; at least half of nonempty selected masks match; count only matched support; full OBB outside distance >0.25m fails.',
        objects='300 requested question-operand occurrences, including the two uncalled operands; no-GT includes missing capture or missing unique instance binding.',
        item='Earliest known failure dominates no-GT. A censored operand blocks only failures that might occur later than its earliest unresolved stage. With no known failure, any no-GT operand makes no-GT.',
        cameras='NPZ self-consistent on 38/38; S4/S5 only on the six captures passing rank>=2, translation RMS<=0.10m and every rotation<=5deg. No scale fit.',
        portrait='Unchanged adapter leaves nine portrait raster-to-reader mappings unresolved; these are censored, not no-GT, when uniquely bound.',
        dense='Only 32 anchor frames have GT. Full 64-frame stages are resolved only when every possible labeling of extra masks gives the same first failure. Additional anchor-only matrices are diagnostics, not full dense stages.',
        extent='ARKit full lengths; ScanNet++ doubled half lengths; both ScanNet interpretations retained; disagreement censors placement.',
        scores='Routed distance official MRA, 0–100, released label authority, printed metres converted to requested units; missing gaps score zero.',
        budget='Signed (n_stage/N)*(mean_S5-mean_stage), recomputed per room draw. N=150. Undefined without an S5 item group.',
        bootstrap='10,000 draws of all 46 physical rooms; random.Random(20261120); item weighted; same draws in every table; undefined draws counted and omitted.')
    output=dict(schema='t1-funnel-r7',definitions=definitions,tables=tables,objects=objects,items=items,migrations=migrations,
        dense_anchor_only=dict(objects=anchor_objects,items=anchor_items,migrations=anchor_migrations,tables=stage_table(boot,anchor_items,anchor_objects)),
        lever_summary=levers,overall={a:boot.metric(score_rows,a) for a in ARMS},
        bootstrap=dict(seed=20261120,draws=10000,rooms=boot.rooms),capture_reads=capture_reports,
        validation=dict(raw_join_evidence_checked=joined_checks,point_stage_records_reproduced=point_checks,camera_checks=camera_checks,
                        all_scores_match=True,objects_per_arm=300,items_per_arm=150),
        runtime_seconds=time.monotonic()-started,max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write(OUT/'FUNNEL_T1.json',output)
    write(OUT/'T1_S2_SELECTED.json',s2_selected)
    render(output)
    print(json.dumps(dict(complete=True,t1_table=tables['t1'],runtime_seconds=output['runtime_seconds'])),flush=True)

def render(data):
    text=['# T1 grounding funnel\n']
    text.extend(k+': '+v+'\n' for k,v in data['definitions'].items())
    for arm,rows in data['tables'].items():
        text.append('\n## '+arm+'\n')
        text.append(table(['Stage','Objects','Items','Item score [95% CI]','Signed budget [95% CI]'],
                          [[r['stage'],r['objects'],r['items'],fmt(r['score']),fmt(r['signed_stage_budget'])] for r in rows]))
    text.append('\n## Stage migration and score changes\n')
    for arm,units in data['migrations'].items():
        for unit,m in units.items():
            text.append(f'\n### T1 → {arm}, {unit}\n')
            text.append(table(['T1 / destination']+LABELS,[[s]+line for s,line in zip(LABELS,m['matrix'])]))
            text.append(table(['T1','Destination','Count','Distinct items','Arm − T1 score [95% CI]'],
                [[c['from_stage'],c['to_stage'],c['count'],c['distinct_items'],fmt(c['item_score_delta'])] for c in m['cells'] if c['count']]))
    text.append('\n## Dense anchor-only diagnostic\nThese matrices ignore unannotated added masks; they cannot establish full 64-frame stage recovery.\n')
    for unit,m in data['dense_anchor_only']['migrations'].items():
        text.append(unit+'\n'+table(['T1 / anchor destination']+LABELS,[[s]+line for s,line in zip(LABELS,m['matrix'])]))
        text.append(table(['T1','Anchor destination','Count','Distinct items','Dense − T1 score [95% CI]'],
            [[c['from_stage'],c['to_stage'],c['count'],c['distinct_items'],fmt(c['item_score_delta'])] for c in m['cells'] if c['count']]))
    text.append('\n## Which stages each lever passes\nAdvancement includes censoring strictly after the starting stage. Unresolved dense identity is not counted as recovery.\n')
    text.append(table(['Unit','T1 stage','Count','Point passes stage','Dense passes stage','Neither proven','Same stage in both','Point score Δ','Dense score Δ'],
        [[r['unit'],r['stage'],r['count'],r['point_proven_advanced'],r['dense_proven_advanced'],r['neither_proven_advanced'],r['same_stage_in_both'],fmt(r['point_delta']),fmt(r['dense_delta'])] for r in data['lever_summary']]))
    (OUT/'FUNNEL_T1.md').write_text('\n'.join(text))

if __name__=='__main__': main()
