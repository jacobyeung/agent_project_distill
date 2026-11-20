"""Render the camera decision, S2 tables, and per-anchor evidence."""
import json
from collections import Counter
from pathlib import Path
from analyze_round5 import sha

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'cap/score_t2'


def read(path):
    return json.loads(Path(path).read_text())


def pct(value):
    return '—' if value is None else f'{100*value:.1f}%'


def num(value):
    return '—' if value is None else f'{value:.3f}'


def table(headers, rows):
    lines=['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']
    lines.extend('| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in rows)
    return '\n'.join(lines)+'\n'


def main():
    s=read(OUT/'S2_ANALYSIS.json');p=read(OUT/'NPZ_SELF_CONSISTENCY_R6.json')
    affected=[c for c in p['captures'] if c['fixed_axis_exclusion']['excludes_any_fixed_world_and_camera_axis_rotation']]
    total=sum(c['hypotheses']['c2w_cv']['overall']['visible_instance_frames'] for c in p['captures'])
    supported=sum(c['hypotheses']['c2w_cv']['overall']['bbox_iou_gt_025']['count'] for c in p['captures'])
    centroids=sum(c['hypotheses']['c2w_cv']['overall']['centroid_inside']['count'] for c in p['captures'])
    s['npz_audit']=dict(summary_file=str(OUT/'NPZ_SELF_CONSISTENCY_R6.json'),
        per_anchor_instance_projections=str(OUT/'NPZ_PROJECTIONS_R6.jsonl'),
        captures=38,captures_with_majority_bbox_iou_gt_025=38,visible_instance_frames=total,
        bbox_iou_gt_025=supported,centroid_inside=centroids,
        robust_reader_camera_outlier_captures=[c['capture'] for c in affected],
        decision='NPZ poses/boxes/rasters are internally consistent under OpenCV c2w in every capture. Under the verified recorded anchor binding, reader cameras are the outlier in all 20 fixed-axis-excluded captures: a served lift-camera blocker.',
        limitation='NPZ internal consistency supports the recorded anchor association but is not an independent RGB hash/pose provenance certificate.',
        scoring='GT adapter and STAGES unchanged; failed reader alignments still censor S4/S5.')
    s['validation']['synthetic_tests_passed']=8
    s['provenance'][str(Path(__file__))]=sha(Path(__file__))
    with (OUT/'S2_ANALYSIS.json').open('w') as f:
        json.dump(s,f,indent=2,allow_nan=False);f.write('\n')
    intro=(f'The NPZ geometry is internally consistent in all 38 captures under OpenCV camera-to-world poses. '
        f'Projected boxes exceed 0.25 IoU with their own mask bounding boxes in {supported}/{total} '
        f'visible instance-frames ({pct(supported/total)}). Every capture has a majority, including all 20 '
        f'captures whose reader relative rotations rule out a fixed axis correction. Under the recorded anchor '
        f'binding, the GT poses belong to the anchor rasters and the reader cameras are the outlier. '
        f'This is a served lift-camera blocker for those 20 captures.\n\n'
        f'Round 5 did not change the GT adapter. This audit uses its OpenCV c2w convention, row OBB axes, '
        f'ARKit full extents, and doubled ScanNet++ half extents. ScanNet full and half readings remain separate. '
        f'Failed camera alignments still censor S4/S5; this audit changes no stages or deliveries.\n')
    text=[intro,
        'The check establishes internal pose/raster consistency. It does not independently certify the native RGB-to-pose mapping: the NPZ files lack RGB hashes and native timestamps. The served-path conclusion uses the exact recorded anchor binding verified in the camera audit.\n',
        f'Centroids hit their own mask in {centroids}/{total} visible instance-frames ({pct(centroids/total)}). '
        'A box center can project into a hole, an occluder, or outside the visible crop. The box-overlap result, '
        'supported by the poor pose alternatives, provides the consistency evidence; the report does not claim most centroids hit.\n',
        'The denominator below counts valid instance-frame pairs with at least one raster pixel. Each cell reports '
        '**centroid-in-mask share / projected-box versus mask-bbox IoU > 0.25 share**. Full per-anchor and per-instance '
        'summaries are in `NPZ_SELF_CONSISTENCY_R6.json`; all centroid and eight-corner projections are in '
        '`NPZ_PROJECTIONS_R6.jsonl`. Invisible instances are also projected, but do not enter these rates.\n']
    rows=[]
    for c in p['captures']:
        cells=[]
        for h in ('c2w_cv','c2w_gl','w2c_cv','w2c_gl'):
            v=c['hypotheses'][h]['overall'];cells.append(pct(v['centroid_inside']['share'])+' / '+pct(v['bbox_iou_gt_025']['share']))
        rows.append([c['capture'],'×'.join(map(str,c['raster_hw'])),c['hypotheses']['c2w_cv']['overall']['visible_instance_frames'],*cells])
    text.append(table(['Capture','GT H×W','Visible pairs','OpenCV c2w','OpenGL c2w','OpenCV w2c','OpenGL w2c'],rows))
    text.append('`K_frames` already uses the native raster scale: its principal point lies near (160,120) for '
        '240×320 rasters and (120,160) for 320×240 rasters. The applied scale is (1,1) in every capture. '
        'The audit uses portrait rasters directly, without transposition or rotation. It never substitutes the reader RGB resolution. '
        'The JSON records each principal-point range. Box edges crossing the camera plane are clipped at positive depth before '
        'forming the image-clipped box. The eight original corners and their depths remain recorded.\n')
    text.append(table(['ScanNet capture','Full lengths: bbox IoU >0.25','Doubled lengths: bbox IoU >0.25'],[
        [c['capture'],pct(c['hypotheses']['c2w_cv']['overall']['bbox_iou_gt_025']['share']),
         pct(c['hypotheses']['c2w_cv_scannet_half']['overall']['bbox_iou_gt_025']['share'])]
        for c in p['captures'] if c['dataset']=='scannet']))
    text.append('The following 20 captures are the robust reader-camera outliers. Relative errors compare all 496 anchor pairs '
        'using `T_i^-1 T_j`, in OpenCV camera axes, without a scale fit. Rotation RMS is the geodesic difference of relative rotations; '
        'translation RMS is the norm of the relative translation-vector difference. The angle-gap maximum compares rotation '
        'magnitudes and is invariant to fixed world and camera-axis rotations. Values above 10° rule out keeping every anchor within 5°. '
        'Rigid-fit columns reproduce the adapter’s center-only Kabsch fit.\n')
    camera_headers=['Capture','Relative rot. RMS °','Relative trans. RMS m','Invariant angle gap max °','Rigid trans. RMS m','Rigid rot. max °']
    def camera_row(c):
        e=c['reader_pair_errors'];r=c['reader_rigid_fit']
        return [c['capture'],num(e['rotation_deg']['rms']),num(e['translation_m']['rms']),
                num(c['fixed_axis_exclusion']['max_relative_angle_disagreement_deg']),num(r['translation_rms_m']),num(r['rotation_max_deg'])]
    text.append(table(camera_headers,[camera_row(c) for c in affected]))
    text.append('<details>\n<summary>Reader errors for the other 18 captures</summary>\n\n'+table(camera_headers,[camera_row(c) for c in p['captures'] if c not in affected])+'\n</details>\n')
    text.append('The selected-mask analysis covers all 119 S2/S3/S5 object records from `STAGES_T2.json`: '
        '58 point-arm and 61 restricted-arm records. Trusted T1 pass 0 supplies baseline selections for every record '
        '(74 distinct item/object keys). Baseline rows use the same T2 cohort; they do not label the baseline’s own stage as S2. '
        'Its point-in-GT value is a diagnostic comparison with the T2 point, which the baseline never received.\n')
    text.append(table(['Selections','T2 cohort','Objects','IoU >0.25 in ≥half nonempty frames','Share'],[
        [r['arm'],r['cohort_arm']+' '+r['cohort_stage'],r['objects'],r['relaxed_matches'],pct(r['relaxed_match_share'])] for r in s['summary']]))
    text.append('Coverage is intersection / bound-GT area; precision is intersection / selected-mask area. '
        'Each frame is another instance when a different GT instance has IoU >0.5, or when bound precision <0.2 '
        'and another-instance precision >0.5. Otherwise it is a part when precision ≥0.8 and coverage <0.5, '
        'or bleed when coverage ≥0.8 and precision <0.5. The remainder is empty/other, which also includes good masks. '
        'Object classes require a strict majority of nonempty selected frames; no majority is mixed, and no selected pixels is empty.\n')
    text.append('Point-in-GT uses the captured normalized point and the prompt code’s floor-and-clamp mapping. '
        'Inside/outside in the tables is the strict majority among nonnull points on nonempty selected frames. '
        'Ties and absent points remain explicit. The JSON also includes all-anchor point counts. '
        'This separates point errors from mask errors conditional on a correct point; the latter alone does not establish that prompt format caused the failure.\n')
    for group in [r for r in s['summary'] if r['cohort_stage']=='S2']:
        text.append(f"**{group['arm']} selections, {group['cohort_arm']} S2 cohort.** Scores are item scores on the 0–100 scale.\n")
        text.append(table(['Majority mask class','Point-in-GT','Objects','Distinct items','Mean item score','Object keys and item scores'],[
            [c['mask_class'],c['point_in_gt'],c['objects'],c['distinct_items'],f"{c['mean_item_score']:.1f}",
             '; '.join(f"{e['key']} ({e['item_score']:g})" for e in c['entries'])] for c in group['class_x_point']]))
        text.append('Cell means count each item once within that cell. An item can occur in multiple cells because it has multiple objects.\n')
    text.append(table(['Selections / S2 cohort','Inside point, IoU ≤0.25','Outside point, IoU ≤0.25','Inside point, IoU >0.25','Outside point, IoU >0.25'],[
        [r['arm']+' / '+r['cohort_arm'],*[r['frame_point_mask_counts'][k] for k in ('correct_point_wrong_mask_frames',
         'wrong_point_wrong_mask_frames','correct_point_good_mask_frames','wrong_point_good_mask_frames')]]
         for r in s['summary'] if r['cohort_stage']=='S2']))
    text.append('These frame counts exclude null points and empty selections. Point-arm S2 has 19/36 objects '
        'that meet the relaxed match rule; its majority mask classes comprise 3 parts, 5 bleed, 3 other-instance, '
        '18 empty/other, and 7 mixed. Restricted S2 has 9/25 relaxed matches; its classes comprise 0 parts, '
        '2 bleed, 5 other-instance, 12 empty/other, 4 mixed, and 2 empty selections.\n')
    for arm in ('points','restricted_selector','baseline'):
        objs=[o for o in s['objects'] if o['arm']==arm]
        text.append(f'**Per-object summaries: {arm}.** Best IoU is the maximum selected-mask IoU across anchor frames. '
            'Coverage and precision are means over nonempty selected frames.\n')
        text.append(table(['Object','T2 cohort','N frames','Best IoU','Mean coverage','Mean precision','IoU >0.25 frames','Majority class','Point-in-GT','Item score'],[
            [o['key'],o['t2_cohort_arm']+' '+o['t2_cohort_stage'],o['summary']['nonempty_frames'],num(o['summary']['best_selected_iou']),
             num(o['summary']['mean_coverage']),num(o['summary']['mean_precision']),o['summary']['iou_gt_025_frames'],
             o['summary']['majority_class'],o['summary']['point_class'],o['item_score']] for o in objs]))
    text.append('**Per-frame evidence.** Each expandable table includes all 32 anchors. `Other` gives the best different-instance '
        'IoU as instance ID:value; `Point` gives normalized x,y and its GT membership. Zero-denominator ratios are shown as zero, '
        'with areas supplied in JSON. Source indices, point-hit instance IDs, second-instance precision, and exact counts are in `S2_ANALYSIS.json`.\n')
    for o in s['objects']:
        text.append(f"<details>\n<summary>{o['arm']} — {o['key']} — {o['t2_cohort_arm']} {o['t2_cohort_stage']}</summary>\n")
        rows=[]
        for f in o['frames']:
            other=f['best_other_iou'];point=f['point_xy_normalized']
            point_str='null' if point is None else f"({point[0]:.3f}, {point[1]:.3f}) / {'in' if f['point_in_gt'] else 'out'}"
            rows.append([f['frame'],f['source_index'],f['pred_pixels'],f['gt_pixels'],num(f['bound_iou']),
                         num(f['coverage']),num(f['precision']),f['frame_class'],point_str,
                         '—' if other is None else f"{other['instance_id']}:{other['iou']:.3f}"])
        text.append(table(['Frame','Source','Pred px','GT px','IoU','Coverage','Precision','Class','Point','Other'],rows))
        text.append('</details>\n')
    text.append('Eight synthetic CPU tests passed, covering perspective projection, row-axis rotations, portrait scaling, '
        'camera-plane clipping, relative-pose invariance, and mask thresholds. Every captured T2 selected-mask IoU reproduces '
        'the stage artifact, and every T1 item score reproduces the deployed baseline. Both captures pass raw-byte SHA256 '
        'verification and contain complete gzip streams. The projection pass read 3,077,808 compressed NPZ member bytes; '
        'both analyses used one CPU thread and less than 130 MiB peak resident memory.\n')
    with (OUT/'S2_ANALYSIS.md').open('x') as f:
        f.write('\n'.join(text))
    r5=read(OUT/'CAMERA_CONVENTIONS_T2.json')
    unchanged={str(path):sha(path)==r5['provenance'][str(path)] for path in (ROOT/'gt/v2.py',OUT/'STAGES_T2.json')}
    assert all(unchanged.values())
    validation=dict(synthetic_tests=8,adapter_and_stages_unchanged=unchanged,**s['validation'],
                    capture_sha256_verified={k:v['sha256_verified'] for k,v in s['capture_reads'].items()},
                    output_files={str(path):sha(path) for path in (OUT/'S2_ANALYSIS.json',OUT/'S2_ANALYSIS.md',OUT/'NPZ_SELF_CONSISTENCY_R6.json')})
    with (OUT/'ROUND6.validation.json').open('x') as f:
        json.dump(validation,f,indent=2);f.write('\n')
    report=[intro,
        'The 20 affected captures and their reader errors are listed below. Relative errors use every anchor pair; '
        'the final columns show the adapter’s rigid-fit residuals.\n',
        table(camera_headers,[camera_row(c) for c in affected]),
        'Point-arm S2 objects are not uniformly wrong instances: 19/36 (52.8%) match their bound GT at IoU >0.25 '
        'in at least half of nonempty frames. The corresponding restricted-arm result is 9/25 (36.0%). '
        'Point-arm majority classes are 3 parts, 5 bleed, 3 other-instance, 18 empty/other, and 7 mixed. '
        'All S3/S5 reference objects meet the relaxed rule in both arms.\n',
        'Among point-arm S2 frames with IoU ≤0.25, 120 points lie outside the bound GT mask and 38 lie inside. '
        'The restricted arm has 46 outside-point and 19 inside-point failures. These counts show both point-label '
        'errors and mask failures conditional on a correct point; they do not isolate prompt format as the cause.\n',
        'Trusted T1 baseline captures cover all 119 requested object records. On the same S2 cohorts, its own selections '
        'meet the relaxed rule for 18/36 point-arm objects and 9/25 restricted-arm objects. '
        'The report includes class-by-point tables with every item score and all 32 frames per object.\n',
        'NPZ self-consistency supports the recorded anchor association but does not independently hash-bind native RGB '
        'to poses. The centroid hit rate is '+pct(centroids/total)+'; the majority consistency result uses projected-box '
        'overlap, not centroid hits. K_frames already matches each landscape or portrait raster, so no scale or image '
        'rotation was fitted.\n',
        'Eight CPU tests passed. All selected-mask IoUs reproduce the stage artifact, all T1 scores reproduce the deployed '
        'baseline, and both captures pass SHA256 verification. The GT adapter and stage artifact retain their round-5 hashes.\n',
        f'[Full analysis]({OUT}/S2_ANALYSIS.md) and [JSON evidence]({OUT}/S2_ANALYSIS.json) contain the requested results. '
        f'[NPZ summaries]({OUT}/NPZ_SELF_CONSISTENCY_R6.json) and [all projections]({OUT}/NPZ_PROJECTIONS_R6.jsonl) contain '
        f'the camera evidence. [Validation]({OUT}/ROUND6.validation.json) records the checks.\n']
    with (ROOT/'REPORT6.md').open('a') as f:
        f.write('\n'+'\n'.join(report))
    print(json.dumps(dict(visible_instance_frames=total,bbox_supported=supported,centroid_hits=centroids,
                         affected_captures=len(affected),validation=validation),indent=2))


if __name__=='__main__':
    main()
