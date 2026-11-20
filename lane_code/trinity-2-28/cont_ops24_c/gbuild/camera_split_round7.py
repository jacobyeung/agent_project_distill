"""Finish the capture-level camera blocker before the grounding funnel."""
from round7_common import *
from collections import Counter, defaultdict
import time
from gpkg.capture_io import Records
from gt.v2 import alignment
from analyze_round5 import FRAMES

def main():
    started=time.monotonic()
    refs, scores=inputs(); boot=Bootstrap(refs)
    gt=read(ROOT/'out2/GT.json')
    r6=read(CAP/'score_t2/NPZ_SELF_CONSISTENCY_R6.json')
    metadata={r['scene']:r for r in read(FRAMES)['captures']}
    cams=defaultdict(list); gravity=defaultdict(list)
    records=Records(CAP/'t1.gz',CAP/'t1ret/CAPTURE.json')
    seen=set()
    for row in records:
        if row['pass_index']!=0: continue
        assert row['item_id'] not in seen
        seen.add(row['item_id'])
        g=row['geometry']
        if g:
            cams[row['capture']].append(g['camera_to_world_metric'])
            gravity[row['capture']].append(g['gravity_up'])
    assert len(seen)==150 and records.report['records']==160 and not records.report['salvaged']
    parity=read(CAP/'t1ret/PARITY.json')
    assert parity['trusted'] and parity['discrete_matches']==150 and parity['gap_atol_m']==0
    result=[]
    for r in r6['captures']:
        cap=r['capture'];m=metadata[cap]; h,w=m['hw']; g=gt[cap]
        a=r['reader_rigid_fit']; actual=alignment(cams[cap][0],g['c2w'])
        assert all(v==cams[cap][0] for v in cams[cap])
        assert actual['accepted']==a['accepted']
        for key in ('translation_rms_m','rotation_rms_deg','rotation_max_deg'):
            assert abs(actual[key]-a[key])<1e-5
        assert r['hypotheses']['c2w_cv']['overall']['bbox_iou_gt_025']['share']>.5
        group=[s for s in scores if s['capture']==cap]
        K=np.array(g['intrinsics']); rh,rw=r['raster_hw']
        result.append(dict(capture=cap,dataset=r['dataset'],orientation='portrait' if h>w else 'landscape',
            native_rgb_hw=[h,w],native_size_authority='pinned FRAMES.json hw of supplied RGB; upstream sensor resolution unavailable',
            raster_hw=r['raster_hw'],alignment_pass=a['accepted'],items=len(group),
            scores={arm:float(np.mean([s[arm] for s in group])) for arm in ('t1','points','dense64')},
            item_scores=group,relative_errors=r['reader_pair_errors'],rigid_fit=a,
            fixed_axis_exclusion=r['fixed_axis_exclusion'],
            metadata=dict(total_num_frames=m['total_num_frames'],frame_count_lower_bound=m.get('total_num_frames_lower_bound',False),
                anchor_frames=32,dense_frames=refs[group[0]['item_id']]['mapping']['dense_count'],fps=m['fps'],
                sensor=None,source_gravity_flag=None,source_orientation_flag=None,
                reader_predicted_gravity_up=gravity[cap],reader_gravity_is_source_metadata=False,
                K_first=K[0].tolist(),K_varies=bool(np.any(K!=K[0])),
                normalized_fx_range=[float(K[:,0,0].min()/rw),float(K[:,0,0].max()/rw)],
                normalized_fy_range=[float(K[:,1,1].min()/rh),float(K[:,1,1].max()/rh)])))
    contingency=[]; metadata_summary=[]
    for ds in sorted({r['dataset'] for r in result}):
        for orientation in ('landscape','portrait'):
            rr=[r for r in result if r['dataset']==ds and r['orientation']==orientation]
            contingency.append(dict(dataset=ds,orientation=orientation,passed=sum(r['alignment_pass'] for r in rr),failed=sum(not r['alignment_pass'] for r in rr)))
        for passed in (True,False):
            rr=[r for r in result if r['dataset']==ds and r['alignment_pass']==passed]
            metadata_summary.append(dict(dataset=ds,alignment_pass=passed,captures=len(rr),
                frame_count_range=[min(r['metadata']['total_num_frames'] for r in rr),max(r['metadata']['total_num_frames'] for r in rr)] if rr else None,
                lower_bound_flags=sum(r['metadata']['frame_count_lower_bound'] for r in rr),
                dense64_count=sum(r['metadata']['dense_frames']==64 for r in rr),
                K_varies_count=sum(r['metadata']['K_varies'] for r in rr),
                normalized_fx_range=[min(r['metadata']['normalized_fx_range'][0] for r in rr),max(r['metadata']['normalized_fx_range'][1] for r in rr)] if rr else None,
                normalized_fy_range=[min(r['metadata']['normalized_fy_range'][0] for r in rr),max(r['metadata']['normalized_fy_range'][1] for r in rr)] if rr else None))
    passing={r['capture'] for r in result if r['alignment_pass']}
    pa=[s for s in scores if s['capture'] in passing];fa=[s for s in scores if s['capture'] in gt and s['capture'] not in passing]
    split={arm:dict(passing=boot.metric(pa,arm),failing=boot.metric(fa,arm),pass_minus_fail=boot.contrast(pa,fa,arm)) for arm in ('t1','points','dense64')}
    notes=('All 38 NPZs pass internal consistency. The round-5 rigid criterion passes 6 captures and fails 32; '
           '20 of those failures additionally exclude any fixed axis correction. S4/S5 use only passing captures. '
           'Portrait RGB occurs in both groups. Both groups include 32- and 64-frame ground inputs and overlapping source-frame counts and normalized focal lengths. '
           'All ARKit source-frame counts are lower bounds, including passing captures. No sensor identity or source gravity/orientation flag is present in the supplied frame manifest, tasks or NPZ field inventory. '
           'Captured gravity_up is a reader prediction, not a source flag. The available metadata does not identify a property shared by every failure and absent from every pass. '
           'The supplied native RGB dimensions describe the pinned decoded images; original sensor resolution and EXIF are unavailable.')
    output=dict(schema='camera-split-r7',captures=result,contingency=contingency,score_split=split,
        passing_items=len(pa),failing_items=len(fa),metadata_summary=metadata_summary,interpretation=notes,
        bootstrap=dict(draws=10000,seed=20261120,rooms=boot.rooms,item_weighted=True),
        validation=dict(t1_scores_equal_recorded_baseline=True,t1_alignment_matches_round6=True,npz_consistent=38,primary_records=150,capture_read=records.report),
        provenance={str(p):sha(p) for p in [FRAMES,ROOT/'out2/GT.json',CAP/'score_t2/NPZ_SELF_CONSISTENCY_R6.json',OUT/'SCORE_POINT_T1.json',OUT/'SCORE_DENSE_T1.json']},
        runtime_seconds=time.monotonic()-started,max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write(OUT/'CAMERA_SPLIT.json',output)
    text=['# 0. Camera split\n',notes+'\n',
          'Scores use routed distance MRA on 0–100, item weighting, and 10,000 draws of the 46 physical rooms (seed 20261120). Differences are pass minus fail. These are descriptive groups, not camera-repair effects.\n',
          table(['Dataset','Native RGB orientation','Pass','Fail'],[[r[k] for k in ('dataset','orientation','passed','failed')] for r in contingency]),
          table(['Arm',f'Pass ({len(pa)} items)',f'Fail ({len(fa)} items)','Difference'],[[arm,fmt(s['passing']),fmt(s['failing']),fmt(s['pass_minus_fail'])] for arm,s in split.items()]),
          'Sizes below are height × width. Relative errors use all anchor pairs. Rigid residuals use no fitted scale.\n',
          table(['Capture','Dataset','Orientation','RGB H×W','Raster H×W','Alignment','Rel rot RMS °','Rel trans RMS m','Rigid trans RMS m','Rigid rot RMS/max °','Items','T1','Point','Dense'],
            [[r['capture'],r['dataset'],r['orientation'],'×'.join(map(str,r['native_rgb_hw'])),'×'.join(map(str,r['raster_hw'])),'pass' if r['alignment_pass'] else 'fail',
              f"{r['relative_errors']['rotation_deg']['rms']:.3f}",f"{r['relative_errors']['translation_m']['rms']:.3f}",f"{r['rigid_fit']['translation_rms_m']:.3f}",
              f"{r['rigid_fit']['rotation_rms_deg']:.3f}/{r['rigid_fit']['rotation_max_deg']:.3f}",r['items'],*[f"{r['scores'][a]:.2f}" for a in ('t1','points','dense64')]] for r in result]),
          table(['Dataset','Pass','Captures','Source frame-count range','Lower-bound flags','64-frame inputs','Varying K','fx / raster width range'],
            [[r['dataset'],r['alignment_pass'],r['captures'],r['frame_count_range'],r['lower_bound_flags'],r['dense64_count'],r['K_varies_count'],r['normalized_fx_range']] for r in metadata_summary]),
          'JSON includes each first intrinsic matrix, normalized focal ranges, predicted gravity vectors, per-item scores, complete rigid residuals, and input hashes.\n']
    (OUT/'CAMERA_SPLIT.md').write_text('\n'.join(text))
    print(json.dumps(dict(camera_split_complete=True,contingency=contingency,score_split=split,runtime_seconds=output['runtime_seconds'])))

if __name__=='__main__': main()
