"""Classify T1's own S2 selections using the fixed round-6 pixel rules."""
from round7_common import *
from collections import Counter, defaultdict
import time
from analyze_s2_round6 import object_analysis

def main():
    started=time.monotonic()
    funnel=read(OUT/'FUNNEL_T1.json');selected=read(OUT/'T1_S2_SELECTED.json')
    stages=[o for o in funnel['objects']['t1'] if o['stage']=='S2']
    refs,score_rows=inputs(); scores={r['item_id']:r for r in score_rows};boot=Bootstrap(refs)
    paths={e['capture']:ROOT.parent/'gt'/e['relative_path'] for e in read(ROOT/'kit2/kit/rerun2/gt_staging.json')['files']}
    groups=defaultdict(list)
    for stage in stages: groups[stage['capture']].append(stage)
    objects=[];npz_hashes={}
    for capture,group in sorted(groups.items()):
        path=paths[capture];npz_hashes[str(path)]=sha(path)
        with np.load(path,allow_pickle=False) as z:
            raster=z['inst'];sources=z['frame_indices'].tolist()
        for stage in group:
            obj=selected[stage['key']];assert obj['source_indices']==sources
            r=object_analysis(stage,obj,raster,sources,[None]*32,scores[stage['item_id']]['t1'],baseline=True)
            r.update(arm='t1',baseline_stage='S2',point_role='Not applicable: deployed text selections had no point prompt',
                pool_had_target=stage['evidence']['proposed'],best_pool_iou=stage['best_raw_proposal'][2] if stage['best_raw_proposal'] else 0,
                matching_proposal_count=stage['matching_proposal_count'])
            r.pop('t2_cohort_stage');r.pop('t2_cohort_arm')
            # Every selected-mask value must reproduce the serialized funnel evidence.
            old={x['frame']:x for x in stage['selected_frame_evidence']}
            for fr in r['frames']:
                if fr['frame'] in old:
                    assert abs(fr['bound_iou']-old[fr['frame']]['iou'])<1e-12
            assert r['pool_had_target'] and r['best_pool_iou']>.5
            objects.append(r)
    cells=[]
    classes=sorted({o['summary']['majority_class'] for o in objects}|{'part of the object','superset/background bleed','another instance','empty/other','empty','mixed'})
    for cls in classes:
        for pool in (True,False):
            oo=[o for o in objects if o['summary']['majority_class']==cls and o['pool_had_target']==pool]
            ids=sorted({o['item_id'] for o in oo});rr=[scores[i] for i in ids]
            cells.append(dict(mask_class=cls,pool_had_target=pool,objects=len(oo),distinct_items=len(ids),
                score=boot.metric(rr,'t1'),item_scores=[dict(item_id=i,score=scores[i]['t1']) for i in ids],object_keys=[o['key'] for o in oo]))
    prior=read(CAP/'score_t2/S2_ANALYSIS.json')
    pp=[o for o in prior['objects'] if o['arm']=='points' and o['t2_cohort_stage']=='S2']
    class_compare=[]
    for cls in classes:
        aa=[o for o in objects if o['summary']['majority_class']==cls];bb=[o for o in pp if o['summary']['majority_class']==cls]
        class_compare.append(dict(mask_class=cls,t1_objects=len(aa),point_objects=len(bb),
            t1_item_score=boot.metric([scores[i] for i in sorted({o['item_id'] for o in aa})],'t1'),
            point_item_score=boot.metric([scores[i] for i in sorted({o['item_id'] for o in bb})],'points')))
    shared=set(o['key'] for o in objects)&set(o['key'] for o in pp)
    result=dict(schema='t1-s2-r7',objects=objects,class_x_pool=cells,class_comparison=class_compare,
        counts=dict(objects=len(objects),distinct_items=len({o['item_id'] for o in objects}),
            relaxed_matches=sum(o['summary']['matches_gt_in_at_least_half_nonempty_frames'] for o in objects),
            point_objects=len(pp),point_relaxed_matches=sum(o['summary']['matches_gt_in_at_least_half_nonempty_frames'] for o in pp),
            shared_t1_point_s2_objects=len(shared)),
        point_round6_class_x_point=next(r['class_x_point'] for r in prior['summary'] if r['arm']=='points' and r['cohort_stage']=='S2'),
        definitions=prior['definitions']|dict(baseline='T1 own S2 cohort, not the point S2 cohort',
            point='Not applicable; no point prompt',
            pool='Any captured retained raw proposal IoU >0.5 with the bound target. Every S2 object has one by first-failure definition; absent target proposals are S1.',
            comparison='T1 and point S2 cohorts differ; class comparison is descriptive. Shared object keys are recorded.'),
        provenance={**npz_hashes,str(CAP/'score_t2/S2_ANALYSIS.json'):sha(CAP/'score_t2/S2_ANALYSIS.json')},
        validation=dict(selected_ious_match_funnel=True,all_s2_pools_have_target=True),
        runtime_seconds=time.monotonic()-started,max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write(OUT/'S2_T1.json',result)
    text=['# T1 deployed-selection S2 split\n',
        f"T1 has {len(objects)} S2 objects. {result['counts']['relaxed_matches']} match the bound instance at IoU >0.25 in at least half of nonempty selected frames. Point-arm S2 has {result['counts']['point_relaxed_matches']}/{len(pp)} relaxed matches; {len(shared)} objects belong to both S2 cohorts.\n",
        'Every T1 S2 pool contains a proposal with target IoU >0.5. This follows from the first-failure rule: objects without one are S1. A pool target lost during early lifting/linking remains a selection-path loss, not necessarily a selector-head error. Point-in-GT does not apply.\n',
        'Each frame is classified in this order: another instance if its IoU exceeds 0.5, or bound precision <0.2 and another-instance precision >0.5; part if bound precision ≥0.8 and coverage <0.5; superset if coverage ≥0.8 and precision <0.5; otherwise empty/other. A strict majority of nonempty frames sets the object class; ties are mixed, and no nonempty selection is empty.\n',
        table(['Class','Pool had target','Objects','Distinct items','T1 item score [95% CI]'],[[r['mask_class'],r['pool_had_target'],r['objects'],r['distinct_items'],fmt(r['score'])] for r in cells]),
        'The following comparison uses each arm’s own S2 cohort. Means deduplicate items within each class; an item can appear in multiple classes.\n',
        table(['Class','T1 objects','Point objects','T1 item score','Point item score'],[[r['mask_class'],r['t1_objects'],r['point_objects'],fmt(r['t1_item_score']),fmt(r['point_item_score'])] for r in class_compare]),
        table(['Object','Class','Best selected IoU','Share IoU >0.25','Best pool IoU','Item score'],
            [[o['key'],o['summary']['majority_class'],f"{o['summary']['best_selected_iou']:.4f}",o['summary']['iou_gt_025_share'],f"{o['best_pool_iou']:.4f}",o['item_score']] for o in objects]),
        'JSON records all 32 frames per object, target coverage/precision, best other-instance overlap, every cell’s item scores, and the point arm’s round-6 class-by-point table.\n']
    (OUT/'S2_T1.md').write_text('\n'.join(text))
    print(json.dumps(result['counts']))

if __name__=='__main__': main()
