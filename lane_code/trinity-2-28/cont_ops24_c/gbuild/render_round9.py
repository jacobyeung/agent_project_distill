"""Render the binding evidence and concise round-9 report without overwrites."""
import json, time, hashlib
from pathlib import Path
from round7_common import read, write, table, fmt, sha

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'cap/score_bind'
NAMES={'arkitscenes':'ARKit','scannet':'ScanNet','scannetppv2':'ScanNet++'}
def number(v):return 'undefined' if v is None else f'{v:.3f}'
def comparison(g):return number(g['same_median'])+' / '+number(g['best_alternative_median'])
def best(a):
    if a['best_alternative'] is None:return 'undefined'
    ties=[m for m,v in a['modes'].items() if m!='same' and v['median']==a['best_alternative_median']]
    return a['best_alternative']+(' (tie)' if len(ties)>1 else '')+' / '+number(a['best_alternative_median'])

def main():
    x=read(OUT/'BINDING_R9.json')
    groups={(g['dataset'],g['camera_split'],g['arm']):g for g in x['dataset_table']}
    binding=[]
    for ds in NAMES:
        for split in ('all','pass','fail'):
            t=groups[ds,split,'t1_raw'];p=groups[ds,split,'points_raw']
            binding.append([NAMES[ds],split,t['captures'],comparison(t),comparison(p),f"{t['changed']} / {p['changed']}"])
    opening=table(['Dataset','Camera rule','Captures','T1 visible same / best alt IoU','Points visible same / best alt IoU','Changed T1 / points'],binding)
    method=('Entries are medians of capture medians. Each capture pools bound object-call/anchor rows with nonempty same-frame GT; missing proposals score zero. '
            '“Best alt” selects one shift or transform per capture. A change requires >0.2 median-IoU gain on the same eligible anchors; shifts omit only out-of-range edges. '
            'All 32 anchors, alternative medians, paired baselines, and conditional-on-proposal medians are in JSON. No alternative is applied to the GT or funnel.')
    ark=[c for c in x['captures'] if c['dataset']=='arkitscenes']
    recovered=[c for c in ark if c['arms']['t1_raw']['changed'] or c['arms']['points_raw']['changed']]
    if not recovered:
        assert all(c['arms'][a]['same_median']>c['arms'][a]['best_alternative_median'] for c in ark for a in ('t1_raw','points_raw'))
        conclusion=('**Image content supports ARKit’s same-frame, same-orientation mask binding:** all 23 captures prefer the same frame in both raw-proposal arms, including all 21 camera-rule failures. '
                    'ARKit’s same-frame medians are 0.618 (T1) and 0.626 (points), versus 0.083 and 0.205 for the best alternatives. '
                    'No tested shift or transform improves a capture by >0.2; the lower-overlap captures do not recover either. '
                    'These results do not support the tested frame/orientation-fault explanation or establish that the camera/S1 failures are binding artefacts. '
                    'They support the masks’ association with RGB content, but do not independently authenticate every native pose/RGB pair. ARKit’s eight S1 candidates remain in their own row.')
    else:
        conclusion=('A >0.2 median-IoU recovery occurs in '+str(len(recovered))+' ARKit captures: '+', '.join(c['capture'].split('/')[1] for c in recovered)+'. '
                    'The per-capture table identifies the recovering arm and transform. These recoveries support a frame/orientation mismatch for the affected captures; '
                    'their camera comparison and S1 counts under the original binding are artefacts. They do not establish a corrected binding for all ARKit captures.')
    identity=table(['Source file','Identity fields and comparison','Can hash-bind GT rows to RGB?'],[
        ['`../gt/arkit_gt/gt/<video>.npz`','All 23 contain `frame_indices`, `c2w`, `inst`, `valid`, instance labels/boxes and intrinsics. All 736 anchor indices agree; filenames agree with capture IDs. No sensor timestamps, native RGB names or RGB hashes exist.','No'],
        ['`kit2/kit/rerun2/gt_staging.json`','`capture`, source `path`, `relative_path`, `host`, and byte count locate the NPZ; `matched_frames_and_instances_verified=false`. No per-frame identity receipt exists.','No'],
        ['`gt/adapter.py`, `gt/v2.py`, `out2/GT.json`','Adapter inputs are staged NPZs plus `items544.json`. `source_indices` and `c2w` copy NPZ rows; target bindings map query names to unique instance IDs. Capture IDs/anchor order agree.','No; copied identifiers are not independent evidence'],
        ['`kit2/kit/rerun2/items544.json`','`capture`, `task.native`, `source_indices`, and `task.source_frame_indices` agree with each recorded reader call and the RGB manifest.','No GT RGB hash'],
        ['Reader `FRAMES.json`¹ and `DENSE_MANIFEST.json`²','`scene`, `native`, anchor/frame `index`, PNG `path` and `sha256` agree at all anchors. ARKit `timestamps=index/10` are synthetic; frame counts are lower bounds. Every anchor is listed in the JSON identity section.','Binds reader manifests to the same PNG identities only'],
        ['`../cap/t1.gz`, `../cap/t1ret/PARITY.json`','Record `capture`/`source_indices`, geometry indices and proposal `frame`/`source_index` agree. T1 has no per-anchor RGB hash field; its parity receipt authenticates deployed answers/capture bytes.','No'],
        ['`../cap/t2.gz`, `../cap/t2ret/PARITY.json`','Point records’ `binding.expected_anchor_sha256` and `bound_anchor_sha256` equal every manifest PNG hash; `frame_hashes_match=true`. Source/proposal indices agree.','Yes for reader inputs; no for GT poses'],
        ['Payload `tree/generator/derivgen_v7/derivgen/native.py`','A compatible builder accepts calibration, RGB, selection and visibility provenance. No matching preparation/registry/config sidecars for these NPZs are supplied. Both staged GT directories contain only NPZs.','Not with the supplied files'],
    ])
    fp='work/payload/b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json'
    dp='work/payload/b/work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json'
    identity_note=f'¹ `{fp}`. ² `{dp}`. The audit compares recorded PNG hashes; it does not reread PNG bytes. **No available check independently hash-binds an ARKit GT pose/mask row to the reader’s RGB.**'
    ftable=table(['Dataset group','Stage','Objects','Items','Mean score [95% CI]'],[
        [r['group'],r['reported_stage'],r['objects'],r['items'],fmt(r['score'])] for r in x['funnel_tables']])
    funnel_note=('ARKit rows reproduce the diagnostic labels under the recorded binding; they are not established grounding-failure counts. '
                 'The ARKit S1-candidate row is excluded from the accepted S1 count. Counts cover all 300 object occurrences and 150 items, including no-GT captures. '
                 'Scores and intervals use the REPORT7 item rules and 10,000 shared room-bootstrap draws (46 rooms, seed 20261120). '
                 'No item reaches S5; repair budgets remain undefined.')
    ctable=table(['Dataset group','GT captures','Pass','Moderate','Gross'],[
        [r['group'],r['captures'],r['pass'],r['moderate'],r['gross']] for r in x['camera_tables']])
    camera_note=('These are the 38 distance-reader capture fits. Pass requires centre rank ≥2, rigid translation RMS ≤0.10 m and every rotation ≤5°; '
                 'gross means rotation max >60°, and other failures are moderate. ARKit classes remain conditional on the unverified binding. '
                 'The REPORT8 camera-question corpus contains only ScanNet and ScanNet++; its score table is therefore already the non-ARKit result, and an ARKit camera-question score is undefined.')
    # Restate the requested camera-question table without conflating its population with distance captures.
    cam=read(ROOT.parent/'cap/score_cam/CAMERA_ITEMS_R8.json')
    rows=[]
    for step in (544,400):
        for cl in ('pass','moderate','gross','unclassified-GT','no-GT','all'):
            rr={r['type']:r for r in cam['tables'] if r['step']==step and r['dataset']=='all' and r['capture_class']==cl}
            def pct(k):
                v=rr[k]['accuracy'];return 'undefined' if v['mean'] is None else f"{100*v['mean']:.1f} [{100*v['ci95'][0]:.1f}, {100*v['ci95'][1]:.1f}]"
            rows.append([step,cl,rr['all']['captures'],rr['all']['items'],pct('displacement'),pct('rotation'),pct('direction'),pct('all')])
    qtable=table(['Step','Class','Captures','Items','Displacement % [95% CI]','Rotation % [95% CI]','Direction % [95% CI]','All % [95% CI]'],rows)
    qnote='Camera-question classes are approximate reconstructions on 15 overlapping captures; 19 GT captures remain unclassified and 18 lack GT. No ARKit camera-question records exist. The 10,000 room-bootstrap intervals are copied from the validated REPORT8 artifact.'
    percap=table(['Capture','Camera','Portrait','T1 same','T1 best alternative / IoU','T1 changed','Points same','Points best alternative / IoU','Points changed'],[
        [c['capture'],c['camera_class'],c['portrait'],number(c['arms']['t1_raw']['same_median']),best(c['arms']['t1_raw']),c['arms']['t1_raw']['changed'],
         number(c['arms']['points_raw']['same_median']),best(c['arms']['points_raw']),c['arms']['points_raw']['changed']] for c in x['captures']])
    selected=table(['Capture','Point selected same','Best alternative / IoU','Changed'],[
        [c['capture'],number(c['arms']['points_selected']['same_median']),best(c['arms']['points_selected']),c['arms']['points_selected']['changed']] for c in x['captures']])
    portrait_note=x['definitions']['portrait']+' '+x['definitions']['portrait_coordinates']
    all_anchor_values=[v['all_anchor_median'] for c in x['captures'] for a in ('t1_raw','points_raw') for v in c['arms'][a]['modes'].values()]
    assert all(v==0 for v in all_anchor_values)
    all_anchor_note=('The literal all-32-anchor median is **0.000 for every capture, arm and hypothesis**, with 0/38 class changes in both raw arms: most queried instances are invisible in most anchors, and empty/empty IoU is zero. '
                     'The visible-GT table avoids that floor. It contains 398 ARKit, 117 ScanNet and 407 ScanNet++ object-call/anchor rows per arm; ARKit captures contribute 5–45 such rows each. '
                     'The paired-edge and literal full-baseline definitions both give zero changed captures. Point-selected masks also give zero changes; their ARKit same-frame median is 0.621.')
    modes=table(['Dataset','Camera rule','Arm','Best alternative choices across captures'],[
        [NAMES[g['dataset']],g['camera_split'],g['arm'],json.dumps(g['best_alternative_counts'],sort_keys=True)] for g in x['dataset_table'] if g['camera_split']=='all'])
    inputs=table(['Input','SHA256'],[[Path(p).name,h] for p,h in x['input_sha256'].items() if Path(p).name in ('t1.gz','t2.gz','GT.json','FRAMES.json','DENSE_MANIFEST.json','FUNNEL_T1.json','CAMERA_SPLIT.json')])
    commands='''```bash
cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
mkdir -p ../cap/score_bind
/scratch/jjyeung/envs/p1cpu/bin/python -B analyze_round9.py > ../cap/score_bind/ANALYZE_COMPLETE_R9.log 2>&1
/scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest test_round9 -v > ../cap/score_bind/TEST_R9.log 2>&1
/scratch/jjyeung/envs/p1cpu/bin/python -B render_round9.py
sha256sum --check SHA256SUMS9
```'''
    rt=x['runtime'];wall=time.time()-(ROOT/'analyze_round9.py').stat().st_ctime
    runtime=(f"Completed analysis: {rt['seconds']:.2f} s; peak RSS {rt['max_rss_KiB']/1024:.1f} MiB; one numerical thread; 15 GiB address-space cap. "
             f"The audit read {rt['npz_compressed_member_bytes']:,} compressed bytes for the six hashed NPZ members per capture (some members were also loaded for scoring); it did not load depth or RGB pixels. "
             f"Both captures authenticate by SHA256; {x['validation']['landscape_proposed_checks']} landscape calls reproduce the T1 join’s proposal-availability decision. "
             'Four CPU tests pass. No GPU, SSH, Git, network, deletion or job submission ran; earlier deliveries remain unchanged.')
    provenance=('`BINDING_R9.json` records exact SHA256s for every analysis input/source and six uncompressed NPY members in each of the 38 NPZs. '
                'Those member hashes bind the consumed masks/indices/poses/inventories; they are not full-archive hashes or GT-to-RGB evidence. '
                '`SHA256SUMS9` covers all new sources, logs, tests and deliverables except itself.')
    common=[opening,method,all_anchor_note,conclusion,identity,identity_note,ftable,funnel_note,ctable,camera_note,qtable,qnote]
    report='\n\n'.join(common+[f'Per-capture results: [BINDING_R9.md]({OUT}/BINDING_R9.md). Every per-object/per-anchor value and identity comparison: [BINDING_R9.json]({OUT}/BINDING_R9.json).',portrait_note,commands,inputs,provenance,runtime])+'\n'
    assert len(report.splitlines())<=120,len(report.splitlines())
    with (ROOT/'REPORT9.md').open('x') as f:f.write(report)
    full='\n\n'.join(common+[portrait_note,percap,'Point-arm selected masks (one selected mask per frame, absent masks score zero):',selected,modes,commands,inputs,provenance,runtime])+'\n'
    with (OUT/'BINDING_R9.md').open('x') as f:f.write(full)
    files=[ROOT/p for p in ('analyze_round9.py','test_round9.py','render_round9.py','REPORT9.md')]+sorted(OUT.iterdir())
    with (ROOT/'SHA256SUMS9').open('x') as f:
        for p in files:
            if p.is_file():f.write(sha(p)+'  '+str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p)+'\n')
    print(json.dumps(dict(report_lines=len(report.splitlines()),files_hashed=len(files))))

if __name__=='__main__':main()
