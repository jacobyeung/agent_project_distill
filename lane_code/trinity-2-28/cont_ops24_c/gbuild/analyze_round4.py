"""CPU-only T2 GT stage analysis; writes only the requested analysis directory."""
import os
for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[k] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import resource
resource.setrlimit(resource.RLIMIT_AS, (15 * 1024**3, 15 * 1024**3))
import hashlib
import json
import random
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from gpkg.capture_io import Records
from gpkg.grid import resize
from gpkg.runtime.c import unrle
from gpkg.score_ceiling import gap_score, name_key
from gpkg.join_v2 import join as reference_join, legacy
from gt.v2 import alignment
from funnel import stage, worse, outside_obb

ROOT = Path(__file__).resolve().parent
CAP = ROOT.parent / 'cap'
OUT = CAP / 'score_t2'
STAGES = ['S0', 'S1', 'S2', 'S3', 'S4', 'S5', 'U']
ARMS = ['points', 'restricted_selector']
EXPECTED_SHA = '2406c812f4d7c615a49d151f9038fdd1575f61479e8cdca60c3154fbeb5a8b08'

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def dist(values):
    x = np.asarray(values, float)
    if not len(x):
        return dict(n=0, mean=None, min=None, p25=None, median=None, p75=None, p95=None, max=None)
    return dict(n=len(x), mean=float(x.mean()), **dict(zip(
        ('min', 'p25', 'median', 'p75', 'p95', 'max'), np.percentile(x, [0, 25, 50, 75, 95, 100]).tolist())))

def point_diagnostics(obj):
    decisions = obj.get('frame_decisions')
    if decisions is None:
        return None
    counts = Counter(d['reason'] for d in decisions)
    chosen = [p for p in obj['proposals'] if p.get('chosen')]
    areas = {f: int(unrle(m).sum()) for f, m in obj['selected_masks'].items()}
    nonnull = sum(d['point'] is not None for d in decisions)
    cause = None
    if not any(areas.values()):
        if not nonnull:
            cause = 'all points null'
        elif not chosen:
            cause = 'no retained mask'
        elif all(not p.get('contains_point') for p in chosen):
            cause = 'mask without the point; selected mask empty at lift grid'
        else:
            cause = 'retained mask becomes empty at selected-mask grid'
    return dict(nonnull_points=nonnull, null_points=32-nonnull, reasons=dict(counts),
                retained_proposals=len(obj['proposals']), chosen_proposals=len(chosen),
                chosen_without_point=sum(not p.get('contains_point') for p in chosen),
                selected_mask_areas=areas, nonempty_selected_frames=sum(v>0 for v in areas.values()),
                no_mask_cause=cause, decisions=decisions,
                chosen_proposal_evidence=[dict(frame=p['frame'], contains_point=p['contains_point'],
                    pixels=int(unrle(p['mask']).sum()), score=p['score'], presence=p['presence']) for p in chosen])

def object_join(row, obj, gt):
    key = row['item_id'] + ':' + obj['name']
    target = (gt or {}).get('targets', {}).get(key)
    value = dict(key=key, item_id=row['item_id'], capture=row['capture'], arm=row['arm'], name=obj['name'],
                 stage='U', reason=None, evidence={}, gt_available=gt is not None,
                 orientation=(gt or {}).get('orientation'), binding=(target or {}).get('binding'),
                 extent_ambiguous=(gt or {}).get('dataset') == 'scannet',
                 extent_rule=(target or {}).get('extent_rule'),
                 raw_proposals_present='proposals' in obj, raw_proposal_count=len(obj.get('proposals', [])),
                 selected_mask_count=len(obj.get('selected_masks', {})), selector=obj.get('selector'),
                 lift=obj.get('lift'), fitted_box=obj.get('fitted_box'),
                 point_diagnostics=point_diagnostics(obj))
    # Keep the selector decision without duplicating its 58-dimensional feature matrix.
    if value['selector']:
        value['selector'] = {k:v for k,v in value['selector'].items() if k != 'inputs'}
    if gt is None:
        value['reason'] = 'missing GT capture'
        return value
    assert gt['source_indices'] == row['source_indices']
    if gt['orientation']['status'] == 'U':
        value['reason'] = 'portrait orientation U'
        return value
    if not target or not target.get('binding_reviewed'):
        value['reason'] = 'missing reviewed instance binding: ' + str((target or {}).get('binding', {}).get('reason'))
        return value
    if not target.get('annotation_complete'):
        value['reason'] = 'incomplete GT annotation'
        return value
    masks = [unrle(target['masks'][str(s)]['240x320']) for s in row['source_indices']]
    visible_frames = [i+1 for i,m in enumerate(masks) if m.any()]
    def compare(mask, f):
        pred = resize(unrle(mask), (240, 320))
        truth = masks[int(f)-1]
        union = np.logical_or(pred, truth).sum()
        return float(np.logical_and(pred, truth).sum()/union) if union else 0., bool(pred.any())
    proposals = []
    for p in obj.get('proposals', []):
        iou, active = compare(p['mask'], p['frame'])
        proposals.append((p['id'], p['frame'], iou))
    selected = []
    for f,m in obj['selected_masks'].items():
        iou, active = compare(m, f)
        selected.append(dict(frame=int(f), iou=iou, nonempty=active))
    active = [v for v in selected if v['nonempty']]
    matched = [v['frame'] for v in active if v['iou'] > .5]
    raw_matched = [p for p in proposals if p[2] > .5]
    evidence = dict(visible=bool(visible_frames), proposed=bool(raw_matched) if 'proposals' in obj else None,
                    selected_correct=bool(active) and 2*len(matched)>=len(active),
                    selected_correct_frames=len(set(matched)), outside_box_m=None)
    value.update(evidence=evidence, visible_frames=visible_frames, selected_frame_evidence=selected,
                 matching_proposal_count=len(raw_matched), matching_proposal_frames=sorted({p[1] for p in raw_matched}),
                 best_raw_proposal=max(proposals,key=lambda x:x[2]) if proposals else None,
                 selected_matched_frames=matched, nonempty_selected_frames=len(active),
                 alignment_accepted=gt['alignment']['accepted'])
    box = obj.get('fitted_box')
    if box and gt['alignment']['accepted'] and target.get('full_obb'):
        T = np.asarray(gt['alignment']['reader_world_to_gt_world'])
        centroid = (T @ np.r_[box['world']['centroid'],1])[:3].tolist()
        evidence['outside_box_m'] = outside_obb(centroid, **target['full_obb'])
        value['centroid_gt_world_m'] = centroid
        value['centroid_to_gt_center_m'] = float(np.linalg.norm(np.asarray(centroid)-target['full_obb']['center']))
    value['stage'], value['reason'] = stage(evidence)
    if value['stage']=='U' and value['reason']=='outside_box_m':
        value['reason'] = 'alignment residual exceeds ruling' if not gt['alignment']['accepted'] else 'missing fitted box or GT extent'
    if gt['dataset']=='scannet':
        half = dict(evidence)
        if evidence['outside_box_m'] is not None and target.get('half_extent_obb'):
            half['outside_box_m'] = outside_obb(value['centroid_gt_world_m'], **target['half_extent_obb'])
        hs,hr = stage(half)
        value['extent_readings'] = dict(as_full=dict(stage=value['stage'], evidence=dict(evidence)),
                                       as_half=dict(stage=hs, evidence=half))
        if hs != value['stage']:
            value.update(stage='U', reason='ScanNet extent readings disagree')
    return value

def bootstrap(items, objects, population, multiplicity, rooms):
    lookup = {r:i for i,r in enumerate(rooms)}
    global_n = np.zeros(len(rooms))
    for row in items:
        global_n[lookup[row['room']]] += 1
    global_draw_n = multiplicity @ global_n
    result = {}
    for scope in ('gt_available', 'landscape_gt', 'all_150'):
        ii = [r for r in items if scope=='all_150' or r[scope]]
        oo = [r for r in objects if scope=='all_150' or population[r['item_id']][scope]]
        scope_n = np.zeros(len(rooms))
        for r in ii: scope_n[lookup[r['room']]] += 1
        scope_draw_n = multiplicity @ scope_n
        table = []
        for s in STAGES:
            group = [r for r in ii if r['stage']==s]
            og = [r for r in oo if r['stage']==s]
            n = np.zeros(len(rooms)); arm_sum=n.copy(); base_sum=n.copy()
            for r in group:
                i=lookup[r['room']];n[i]+=1;arm_sum[i]+=r['score'];base_sum[i]+=r['baseline']
            draw_n=multiplicity@n;draw_loss=multiplicity@(base_sum-arm_sum)
            def metric(total, denominator, sample_total, sample_denominator):
                defined=sample_denominator>0
                vals=sample_total[defined]/sample_denominator[defined]
                return dict(mean=float(total/denominator) if denominator else None,
                    ci95=np.percentile(vals,[2.5,97.5]).tolist() if len(vals) else None,
                    defined_draws=int(defined.sum()),undefined_draws=int((~defined).sum()))
            table.append(dict(stage=s, objects=len(og), items=len(group),
                objects_with_U=int(s=='U')*len(og), items_with_U_operand=sum(r['has_U_operand'] for r in group),
                objects_ambiguous_extents=sum(r['extent_ambiguous'] for r in og),
                items_ambiguous_extents=sum(r['extent_ambiguous'] for r in group),
                score=metric(arm_sum.sum(),n.sum(),multiplicity@arm_sum,draw_n),
                baseline=metric(base_sum.sum(),n.sum(),multiplicity@base_sum,draw_n),
                paired_loss=metric((base_sum-arm_sum).sum(),n.sum(),draw_loss,draw_n),
                population_loss_contribution=metric((base_sum-arm_sum).sum(),len(ii),draw_loss,scope_draw_n),
                all150_loss_contribution=metric((base_sum-arm_sum).sum(),len(items),draw_loss,global_draw_n),
                unknown_reason_counts=dict(Counter(r['reason'] for r in og if r['stage']=='U'))))
        result[scope] = dict(items=len(ii), objects=len(oo), captures=len({r['capture'] for r in ii}),
            rooms=len({r['room'] for r in ii}), table=table)
    return result

def main():
    start=time.monotonic()
    truth=read(ROOT/'out2/GT.json');audit=read(ROOT/'out2/GT_AUDIT.json')
    scores=read(OUT/'SCORE_T2.json');refs={r['item_id']:r for r in read(ROOT/'kit2/kit/rerun2/items544.json')['items']}
    by_score={r['item_id']:r for r in scores['rows']};receipt=read(CAP/'t2ret/PARITY.json')
    records=Records(CAP/'t2.gz',CAP/'t2ret/CAPTURE.json')
    assert records.report['raw_sha256']==EXPECTED_SHA==receipt['capture_sha256']
    assert sha(ROOT/'out2/GT.json')==scores['gt_sha256']
    cameras=defaultdict(list);counts=Counter();fields=defaultdict(Counter);seen=set()
    for row in records:
        counts[row['arm']]+=1
        assert (row['arm'],row['item_id']) not in seen
        seen.add((row['arm'],row['item_id']))
        ref=refs[row['item_id']]
        assert row['capture']==ref['capture'] and row['source_indices']==ref['source_indices']
        assert [(c['call'],c.get('served')) for c in row['calls']]==[(c['call'],c.get('served')) for c in ref['calls']]
        if row['arm'] not in ARMS: continue
        assert not row.get('excluded')
        score=gap_score(row['calls'],ref['task']['question'],by_score[row['item_id']]['truth']['scored'])
        assert score['score']==by_score[row['item_id']][row['arm']]
        if row['geometry'] is not None:
            assert row['geometry']['source_indices']==ref['source_indices']
            cameras[row['capture']].append(dict(item_id=row['item_id'],arm=row['arm'],
                poses=row['geometry']['camera_to_world_metric']))
        for obj in row['objects']:
            fields[row['arm']]['objects']+=1
            fields[row['arm']]['retained_proposals']+=len(obj.get('proposals',[]))
            for k in ('proposals','selected_masks','fitted_box','frame_decisions'):
                fields[row['arm']]['missing_'+k]+=k not in obj
    assert counts==dict(points=150,restricted_selector=150,text_noise=10)
    assert not records.report['salvaged'] and records.report['records']==receipt['capture_records']==310
    alignments=[]
    for capture,gt in sorted(truth.items()):
        rr=cameras[capture]
        if rr:
            a=alignment([pose for r in rr for pose in r['poses']], gt['c2w']*len(rr))
            a['camera_arrays_identical']=all(r['poses']==rr[0]['poses'] for r in rr)
            a['paired_observations']=32*len(rr)
            a['unique_anchor_observations']=32 if a['camera_arrays_identical'] else None
            a['translation_anchor_m']=a['translation_residual_m'][:32]
            a['rotation_anchor_deg']=a['rotation_residual_deg'][:32]
        else:
            a=dict(performed=False,accepted=False,reason='no captured cameras')
        a.update(capture=capture,orientation=gt['orientation'],records=[{k:v for k,v in r.items() if k!='poses'} for r in rr])
        gt['alignment']=a
        for t in gt['targets'].values():
            t['world_alignment_reviewed']=a['accepted'] and bool(t.get('full_obb'))
            if a.get('reader_world_to_gt_world'): t['reader_world_to_gt_world']=a['reader_world_to_gt_world']
        alignments.append(a)
    print(json.dumps(dict(event='alignments',accepted=sum(a['accepted'] for a in alignments),total=len(alignments))),flush=True)
    objects={arm:[] for arm in ARMS};items={arm:[] for arm in ARMS};reference_checks=0
    checked_stages={arm:set() for arm in ARMS}
    population={key:dict(gt_available=r['capture'] in truth,
        landscape_gt=r['capture'] in truth and truth[r['capture']]['orientation']['status']=='identity') for key,r in refs.items()}
    for row in records:
        arm=row['arm']
        if arm not in ARMS: continue
        gt=truth.get(row['capture']);ref=refs[row['item_id']];sc=by_score[row['item_id']]
        joined=[object_join(row,o,gt) for o in row['objects']]
        # The established join independently checks representative real records of each arm.
        if gt and gt['orientation']['status']=='identity' and (
                sum(i['reference_checked'] for i in items[arm])<4 or
                {o['stage'] for o in joined}-checked_stages[arm]):
            existing=reference_join(row,gt)
            assert [x['stage'] for x in joined]==[x['stage'] for x in existing]
            for x,y in zip(joined,existing):
                if y.get('evidence'): assert x['evidence']==y['evidence']
            checked=True;reference_checks+=1
            checked_stages[arm].update(o['stage'] for o in joined)
        else: checked=False
        objects[arm].extend(joined)
        ground_calls=[re.fullmatch(r'<ground obj="([^"]+)" mode="box">',c['call']).group(1)
                      for c in row['calls'] if c['call'].startswith('<ground ') and c.get('served')]
        missing_calls=[n for n in ground_calls if n not in [o['name'] for o in joined]]
        stages=[o['stage'] for o in joined]+['U']*len(missing_calls)
        item_stage=worse(stages)
        base=gap_score(ref['calls'],ref['task']['question'],sc['truth']['scored'])
        assert base['score']==sc['baseline']
        item=dict(item_id=row['item_id'],arm=arm,capture=row['capture'],room=sc['room'],
            question=ref['task']['question'],stage=item_stage,object_keys=[o['key'] for o in joined],
            object_stages={o['name']:o['stage'] for o in joined},missing_object_calls=missing_calls,
            has_U_operand=not stages or 'U' in stages, extent_ambiguous=any(o['extent_ambiguous'] for o in joined),
            no_recorded_object_call=not ground_calls, score=sc[arm],baseline=sc['baseline'],
            loss=sc['baseline']-sc[arm],gap_available=sc['gap_available'][arm],
            calls=row['calls'],baseline_calls=ref['calls'],truth=sc['truth'],reference_checked=checked,
            **population[row['item_id']])
        items[arm].append(item)
        if len(items[arm])%25==0: print(json.dumps(dict(event='joined',arm=arm,items=len(items[arm]))),flush=True)
    rooms=sorted({r['task']['room'] for r in refs.values()});assert len(rooms)==46
    rng=random.Random(20261120);multiplicity=np.zeros((10000,46),dtype=np.int16);lookup={r:i for i,r in enumerate(rooms)}
    for d in range(10000):
        for _ in rooms: multiplicity[d,lookup[rng.choice(rooms)]]+=1
    tables={arm:bootstrap(items[arm],objects[arm],population,multiplicity,rooms) for arm in ARMS}
    for arm in ARMS:
        assert np.isclose(sum(r['all150_loss_contribution']['mean'] for r in tables[arm]['all_150']['table']),
                          -scores['statistics']['groups']['all']['metrics'][('point' if arm=='points' else 'restricted')+'_minus_baseline']['mean'])
        room_n=np.zeros(46);room_loss=np.zeros(46)
        for item in items[arm]:
            ix=lookup[item['room']];room_n[ix]+=1;room_loss[ix]+=item['loss']
        total_loss_ci=np.percentile((multiplicity@room_loss)/(multiplicity@room_n),[2.5,97.5])
        old_ci=scores['statistics']['groups']['all']['metrics'][('point' if arm=='points' else 'restricted')+'_minus_baseline']['ci95']
        assert np.allclose(total_loss_ci,[-old_ci[1],-old_ci[0]])
    no_gap=[]
    point_obj={o['key']:o for o in objects['points']}
    for item in items['points']:
        if not item['gap_available']:
            evidence=[point_obj[k] for k in item['object_keys']]
            no_gap.append(dict(item_id=item['item_id'],capture=item['capture'],baseline=item['baseline'],score=item['score'],
                stage=item['stage'], no_recorded_object_call=item['no_recorded_object_call'],
                operands=[dict(name=o['name'],stage=o['stage'],reason=o['reason'],diagnostics=o['point_diagnostics'],lift=o['lift']) for o in evidence]))
    errors={}
    for arm in ARMS:
        errors[arm]={}
        for label in ('S4','S5'):
            group=[o for o in objects[arm] if o['stage']==label]
            errors[arm][label]=dict(objects=len(group),ambiguous_extents=sum(o['extent_ambiguous'] for o in group),
                outside_gt_box_m=dist([o['evidence']['outside_box_m'] for o in group]),
                centroid_to_gt_center_m=dist([o['centroid_to_gt_center_m'] for o in group]),
                half_extent_outside_gt_box_m=dist([o['extent_readings']['as_half']['evidence']['outside_box_m'] for o in group if o['extent_ambiguous']]))
    worst=sorted(items['points'],key=lambda r:(r['score'],-r['loss'],r['item_id']))[:10]
    worst_gt=sorted([r for r in items['points'] if r['landscape_gt']],key=lambda r:(r['score'],-r['loss'],r['item_id']))[:10]
    result=dict(schema='t2-gt-stages-v1',capture_read=dict(records.report, records=sum(counts.values()), analysis_stream_passes=2),arm_records=dict(counts),field_inventory={k:dict(v) for k,v in fields.items()},
        provenance={str(p):sha(p) for p in [CAP/'t2ret/CAPTURE.json',CAP/'t2ret/PARITY.json',OUT/'SCORE_T2.json',ROOT/'out2/GT.json',ROOT/'out2/GT_AUDIT.json',ROOT/'gpkg/join_capture.py',ROOT/'gpkg/join_v2.py',ROOT/'gt/v2.py',Path(__file__)]},
        parity=dict(trusted=receipt['trusted'],parity_gate_applies=receipt['parity_gate_applies'],failure=receipt['failure'],text_noise_matches=sum(x['discrete_match'] for x in receipt['text_noise'])),
        definitions=dict(stage='first failure using IoU >0.5, at least half of nonempty selected masks correct, >=3 matching frames, centroid <=0.25m outside GT OBB',
            item_stage='funnel.worse over called objects: S0 dominates, otherwise any U makes item U; else earliest stage',
            raw_proposals='retained detector proposals after joint-score floor and cap; pre-filter logits and rejected masks are not captured',
            unknown='U is never a success or a resolved loss stage; unknown rows keep their measured score',
            counts='object occurrences per item/call; items counted once by worse stage; no-call items have no object rows and item stage U',
            ambiguity='all ScanNet rows flagged; report both extents; disagreeing stages become U',
            paired_loss='recorded baseline score minus arm score on the same items; positive is loss, negative is gain; descriptive partition, not causal attribution',
            population_loss_contribution='sum paired losses in stage / all items in selected scope; stages partition the paired mean loss',
            all150_loss_contribution='sum paired losses in stage / all 150 items',
            bootstrap='10,000 shared draws of 46 physical rooms, random.Random(20261120), item weighted, percentile 95%; undefined group draws excluded and counted',
            alignment='one rigid Kabsch per capture over all point/restricted camera observations; no scale; rank>=2, translation RMS<=0.10m, every rotation<=5deg',
            centroid_error='distance outside GT box used for stage; distance to GT box center also reported, since correct centroids need not equal annotation centers'),
        bootstrap=dict(seed=20261120,draws=10000,rooms=rooms),gt_audit_summary={k:audit[k] for k in ('available_captures','portrait_unknown','unique_bindings','missing_captures','rulings')},
        tables=tables,alignments=alignments,
        alignment_distribution={scope:{metric:dist([a[metric] for a in alignments if a.get('performed') and (scope=='all_gt' or a['orientation']['status']=='identity')])
            for metric in ('translation_rms_m','rotation_rms_deg','rotation_max_deg')} for scope in ('all_gt','landscape_gt')},
        centroid_error=errors,objects=objects,items=items,no_numeric_gap_items=no_gap,worst_point_items=worst,worst_landscape_gt_point_items=worst_gt,
        validation=dict(reference_join_records=reference_checks,reference_checked_stages={a:sorted(v) for a,v in checked_stages.items()},
            all_arm_scores_match=True,all_baseline_scores_match=True,bootstrap_all_population_ci_matches=True,
            all_camera_arrays_identical=all(a.get('camera_arrays_identical') for a in alignments),
            thread_limit=1,address_space_limit_GiB=15,max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            seconds=time.monotonic()-start))
    (OUT/'STAGES_T2.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(event='complete',validation=result['validation'],stage_counts={a:{r['stage']:r['objects'] for r in tables[a]['gt_available']['table']} for a in ARMS})),flush=True)

if __name__=='__main__': main()
