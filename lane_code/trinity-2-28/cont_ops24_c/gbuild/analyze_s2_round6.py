"""Compare captured selected masks and normalized closed-model points to GT."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import json
from collections import Counter, defaultdict
from pathlib import Path
import resource
import time
import numpy as np
from gpkg.capture_io import Records
from gpkg.grid import resize
from gpkg.runtime.c import unrle
from gpkg.score_ceiling import gap_score
from analyze_round5 import sha

ROOT = Path(__file__).resolve().parent
CAP = ROOT.parent/'cap'
OUT = CAP/'score_t2'
REQUESTED = {'S2', 'S3', 'S5'}


def read(path):
    return json.loads(Path(path).read_text())


def majority(values):
    counts = Counter(values)
    if not counts:
        return 'empty'
    key, n = counts.most_common(1)[0]
    return key if 2*n > sum(counts.values()) else 'mixed'


def classify(pred_area, coverage, precision, other_iou, other_precision):
    if not pred_area:
        return 'empty/other'
    if other_iou > .5 or (precision < .2 and other_precision > .5):
        return 'another instance'
    if precision >= .8 and coverage < .5:
        return 'part of the object'
    if coverage >= .8 and precision < .5:
        return 'superset/background bleed'
    return 'empty/other'


def metrics(raster, iid, pred):
    ids, areas = np.unique(raster, return_counts=True)
    selected_ids, intersections = np.unique(raster[pred], return_counts=True)
    overlaps = dict(zip(map(int, selected_ids), map(int, intersections)))
    area_map = dict(zip(map(int, ids), map(int, areas)))
    pa = int(pred.sum()); ga = area_map.get(iid, 0); inter = overlaps.get(iid, 0)
    iou = inter/(pa+ga-inter) if pa+ga-inter else 0.
    coverage, precision = (inter/ga if ga else 0.), (inter/pa if pa else 0.)
    others = []
    for other, a in area_map.items():
        if other < 0 or other == iid:
            continue
        overlap = overlaps.get(other, 0)
        others.append(dict(instance_id=other, iou=overlap/(pa+a-overlap), precision=overlap/pa if pa else 0.,
                           coverage=overlap/a, intersection_pixels=overlap))
    best_iou = max(others, key=lambda x:x['iou']) if others else None
    best_precision = max(others, key=lambda x:x['precision']) if others else None
    oi, op = (best_iou['iou'] if best_iou else 0.), (best_precision['precision'] if best_precision else 0.)
    return dict(pred_pixels=pa, gt_pixels=ga, intersection_pixels=inter, bound_iou=iou,
                coverage=coverage, precision=precision, best_other_iou=best_iou,
                best_other_precision=best_precision, frame_class=classify(pa, coverage, precision, oi, op),
                iou_gt_025=bool(iou > .25), iou_gt_05=bool(iou > .5))


def summarize(frames):
    active = [r for r in frames if r['pred_pixels']]
    nonnull = [r for r in active if r['point_in_gt'] is not None]
    hits = sum(r['point_in_gt'] for r in nonnull)
    point_class = ('no point' if not nonnull else 'inside' if 2*hits > len(nonnull)
                   else 'outside' if 2*hits < len(nonnull) else 'tied')
    counts = Counter(r['frame_class'] for r in active)
    all_points = [r for r in frames if r['point_in_gt'] is not None]
    n025 = sum(r['iou_gt_025'] for r in active)
    return dict(nonempty_frames=len(active), empty_frames=len(frames)-len(active),
        best_selected_iou=max((r['bound_iou'] for r in frames), default=0.),
        mean_selected_iou=float(np.mean([r['bound_iou'] for r in active])) if active else None,
        median_selected_iou=float(np.median([r['bound_iou'] for r in active])) if active else None,
        mean_coverage=float(np.mean([r['coverage'] for r in active])) if active else None,
        mean_precision=float(np.mean([r['precision'] for r in active])) if active else None,
        iou_gt_025_frames=n025, iou_gt_025_share=n025/len(active) if active else None,
        matches_gt_in_at_least_half_nonempty_frames=bool(active and 2*n025 >= len(active)),
        frame_class_counts=dict(counts), majority_class=majority([r['frame_class'] for r in active]),
        all_anchor_class_counts=dict(Counter(r['frame_class'] for r in frames)),
        point_class=point_class, selected_nonnull_points=len(nonnull), selected_points_inside=hits,
        selected_point_in_gt_share=hits/len(nonnull) if nonnull else None,
        selected_null_points=len(active)-len(nonnull),
        all_anchor_nonnull_points=len(all_points), all_anchor_points_inside=sum(r['point_in_gt'] for r in all_points),
        correct_point_wrong_mask_frames=sum(r['point_in_gt'] is True and not r['iou_gt_025'] for r in active),
        wrong_point_wrong_mask_frames=sum(r['point_in_gt'] is False and not r['iou_gt_025'] for r in active),
        correct_point_good_mask_frames=sum(r['point_in_gt'] is True and r['iou_gt_025'] for r in active),
        wrong_point_good_mask_frames=sum(r['point_in_gt'] is False and r['iou_gt_025'] for r in active))


def object_analysis(stage, obj, raster, sources, points, score, baseline=False):
    iid = stage['binding']['instance_id']; h, w = raster.shape[1:]
    assert (h, w) == (240, 320), 'Adapter leaves portrait objects U; do not invent a rotation'
    frames = []
    for f, (truth, source, point) in enumerate(zip(raster, sources, points), 1):
        rle = obj['selected_masks'].get(str(f))
        pred = resize(unrle(rle), (h, w)) if rle is not None else np.zeros((h, w), dtype=bool)
        row = dict(frame=f, source_index=source, selected_mask_present=rle is not None,
                   stored_mask_hw=rle['size'] if rle else None, point_xy_normalized=point,
                   point_in_gt=None, point_raster_xy=None, point_instance_id=None)
        if point is not None:
            x, y = point
            assert 0 <= x <= 1 and 0 <= y <= 1
            px, py = min(int(x*w), w-1), min(int(y*h), h-1)
            row.update(point_raster_xy=[px, py], point_instance_id=int(truth[py, px]),
                       point_in_gt=bool(truth[py, px] == iid), point_in_selected_mask=bool(pred[py, px]))
        row.update(metrics(truth, iid, pred))
        frames.append(row)
    if not baseline:
        old = {r['frame']:r for r in stage['selected_frame_evidence']}
        assert set(old) == {int(f) for f in obj['selected_masks']}
        for row in frames:
            if row['frame'] in old:
                before = old[row['frame']]
                assert abs(row['bound_iou']-before['iou']) < 1e-12
                assert bool(row['pred_pixels']) == before['nonempty']
    return dict(key=stage['key'], item_id=stage['item_id'], capture=stage['capture'], name=stage['name'],
                arm='baseline' if baseline else stage['arm'], bound_instance_id=iid,
                t2_cohort_stage=stage['stage'], t2_cohort_arm=stage['arm'], item_score=score,
                frames=frames, summary=summarize(frames),
                point_role='diagnostic T2 point; baseline never received this point' if baseline else 'closed-model input point',
                baseline_stage=None if baseline else stage['stage'])


def group_summary(objects):
    result = []
    for arm in ('points', 'restricted_selector', 'baseline'):
        for stage in ('S2', 'S3', 'S5'):
            # Baseline objects occur once in each matched T2 arm cohort.
            cohorts = ('points', 'restricted_selector') if arm == 'baseline' else (arm,)
            for cohort in cohorts:
                rows = [o for o in objects if o['arm']==arm and o['t2_cohort_stage']==stage and o['t2_cohort_arm']==cohort]
                groups = defaultdict(list)
                for row in rows:
                    s = row['summary']; groups[(s['majority_class'], s['point_class'])].append(row)
                cells = []
                for (cls, point), members in sorted(groups.items()):
                    unique = {r['item_id']:r['item_score'] for r in members}
                    cells.append(dict(mask_class=cls, point_in_gt=point, objects=len(members),
                        distinct_items=len(unique), mean_item_score=float(np.mean(list(unique.values()))),
                        entries=[dict(key=r['key'], item_score=r['item_score']) for r in members]))
                count = sum(r['summary']['matches_gt_in_at_least_half_nonempty_frames'] for r in rows)
                result.append(dict(arm=arm, cohort_arm=cohort, cohort_stage=stage, objects=len(rows),
                    relaxed_matches=count, relaxed_match_share=count/len(rows) if rows else None,
                    class_x_point=cells,
                    frame_point_mask_counts={k:sum(r['summary'][k] for r in rows) for k in
                        ('correct_point_wrong_mask_frames', 'wrong_point_wrong_mask_frames',
                         'correct_point_good_mask_frames', 'wrong_point_good_mask_frames')}))
    return result


def main():
    started=time.monotonic()
    stage_paths=sorted(OUT.glob('STAGES_T2*.json'))
    stage_paths=[p for p in stage_paths if 'objects' in read(p)]
    assert stage_paths
    # Prefer a versioned stage artifact if present; preserve provenance of all inspected files.
    stage_path=stage_paths[-1]; stages=read(stage_path)
    wanted={(arm,o['key']):o for arm,rows in stages['objects'].items() for o in rows if o['stage'] in REQUESTED}
    items={(arm,r['item_id']):r for arm,rows in stages['items'].items() for r in rows}
    point_map={}; selected={}; reports={}
    records=Records(CAP/'t2.gz', CAP/'t2ret/CAPTURE.json')
    for row in records:
        if row['arm'] not in ('points','restricted_selector'):
            continue
        for obj in row['objects']:
            key=row['item_id']+':'+obj['name']
            if row['arm']=='points':
                point_map[key]=[v['point'] for v in obj['frame_decisions']]
            if (row['arm'],key) in wanted:
                assert wanted[(row['arm'],key)]['capture']==row['capture']
                selected[(row['arm'],key)]=dict(selected_masks=obj['selected_masks'], source_indices=row['source_indices'])
    reports['t2']=records.report
    assert not records.report['salvaged'] and set(selected)==set(wanted)
    baseline={}; baseline_scores={}; baseline_missing=[]
    if (CAP/'t1.gz').is_file() and (CAP/'t1ret/CAPTURE.json').is_file():
        parity=read(CAP/'t1ret/PARITY.json')
        assert parity['trusted'], 'Baseline must be authenticated and pass deployed parity'
        refs={r['item_id']:r for r in read(ROOT/'kit2/kit/rerun2/items544.json')['items']}
        scores={r['item_id']:r for r in read(OUT/'SCORE_T2.json')['rows']}
        wanted_keys={key for arm,key in wanted}
        records=Records(CAP/'t1.gz',CAP/'t1ret/CAPTURE.json')
        seen=set()
        for row in records:
            if row['pass_index']!=0:
                continue
            assert row['item_id'] not in seen
            seen.add(row['item_id'])
            ref=refs[row['item_id']]
            assert row['capture']==ref['capture'] and row['source_indices']==ref['source_indices']
            score=gap_score(row['calls'],ref['task']['question'],scores[row['item_id']]['truth']['scored'])['score']
            assert score==items[('points',row['item_id'])]['baseline']
            baseline_scores[row['item_id']]=score
            for obj in row['objects']:
                key=row['item_id']+':'+obj['name']
                if key in wanted_keys:
                    baseline[key]=dict(selected_masks=obj['selected_masks'],source_indices=row['source_indices'])
        reports['t1']=records.report
        assert not records.report['salvaged']
    paths={e['capture']:ROOT.parent/'gt'/e['relative_path'] for e in read(ROOT/'kit2/kit/rerun2/gt_staging.json')['files']}
    groups=defaultdict(list)
    for pair,stage in wanted.items():
        groups[stage['capture']].append((pair,stage))
    results=[]
    for capture, entries in sorted(groups.items()):
        with np.load(paths[capture],allow_pickle=False) as z:
            raster=z['inst']; sources=z['frame_indices'].tolist()
        for (arm,key),stage in entries:
            obj=selected[(arm,key)]
            assert obj['source_indices']==sources and len(point_map[key])==len(sources)==32
            item=items[(arm,stage['item_id'])]
            result=object_analysis(stage,obj,raster,sources,point_map[key],item['score'])
            result['baseline_item_score']=item['baseline']; results.append(result)
            if key in baseline:
                assert baseline[key]['source_indices']==sources
                results.append(object_analysis(stage,baseline[key],raster,sources,point_map[key],baseline_scores[stage['item_id']],True))
            else:
                baseline_missing.append(dict(arm=arm,key=key))
        print(json.dumps(dict(capture=capture,requested_objects=len(entries))),flush=True)
    result=dict(schema='s2-analysis-r6', stage_file=str(stage_path), objects=results,
        summary=group_summary(results),baseline_missing=baseline_missing,capture_reads=reports,
        definitions=dict(grid='Reader resize to 240x320 GT; unchanged adapter excludes portrait objects from S2/S3/S5',
            matching='IoU >0.25 in at least half of nonempty selected-mask frames; no nonempty frame means false',
            point='Normalized x,y; floor(x*W),floor(y*H), clamp upper boundary exactly as point prompt code; null stays unknown',
            majority='Strict majority (>half) of nonempty selected-mask frames; otherwise mixed. Empty selection is empty.',
            point_class='Majority inside/outside among nonnull points on nonempty selected frames; ties and no-point cases explicit',
            classes='Another instance: other IoU >0.5 OR bound precision <0.2 and other precision >0.5. Then part: bound precision >=0.8 and coverage <0.5. Then bleed: coverage >=0.8 and precision <0.5. Remainder empty/other.',
            zero_denominators='Empty-mask precision and invisible-GT coverage are recorded as zero; pixel counts identify undefined cases',
            scores='Per-item scores, not object-specific scores; cell means deduplicate items within cell. Items may occur in several cells.',
            baseline='Trusted T1 pass 0 selections for the exact same T2 object cohorts. Baseline received no points; T2 points serve only as a diagnostic reference. Its stage is not assumed to equal the cohort stage.',
            frames='All 32 anchor frames saved, including absent selected masks; best selected IoU is the maximum across frames'),
        provenance={str(p):sha(p) for p in [Path(__file__),ROOT/'gt/v2.py',*stage_paths]},
        validation=dict(all_t2_selected_ious_reproduce_stage_file=True,all_baseline_scores_reproduce=True,
            requested_objects=len(wanted),baseline_matched_cohort_objects=sum(o['arm']=='baseline' for o in results),
            distinct_baseline_objects=len(baseline)),
        resources=dict(seconds=time.monotonic()-started,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,threads=1,gpu_used=False))
    with (OUT/'S2_ANALYSIS.json').open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(result['validation']),flush=True)


if __name__=='__main__':
    main()
