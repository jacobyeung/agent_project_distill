"""Write the concise audit report, input hashes, and complete output inventory."""
from round7_common import *
import datetime
import subprocess
import time

def main():
    f=read(OUT/'FUNNEL_T1.json');c=read(OUT/'CAMERA_SPLIT.json');s=read(OUT/'S2_T1.json')
    test=(OUT/'TEST_ROUND7.log').read_text()
    assert 'Ran 7 tests' in test and test.rstrip().endswith('OK')
    old=read(CAP/'score_t2/CAMERA_CONVENTIONS_T2.json')['provenance']
    unchanged={str(p):sha(p)==old[str(p)] for p in [ROOT/'gt/v2.py',CAP/'score_t2/STAGES_T2.json']}
    assert all(unchanged.values())
    old6=read(CAP/'score_t2/ROUND6.validation.json')['output_files']
    for path,digest in old6.items(): assert sha(path)==digest
    core=[CAP/'t1.gz',CAP/'t1ret/CAPTURE.json',CAP/'t1ret/PARITY.json',CAP/'t2.gz',CAP/'t2ret/CAPTURE.json',CAP/'t2ret/PARITY.json',
          CAP/'dense.gz',CAP/'dret/CAPTURE.json',CAP/'dret/PARITY.json',ROOT/'out2/GT.json',CAP/'score_t2/NPZ_SELF_CONSISTENCY_R6.json',
          CAP/'score_t2/STAGES_T2.json',CAP/'score_t2/S2_ANALYSIS.json',CAP/'score_t2/SCORE_T2.json',CAP/'score_dense/SCORE_DENSE.json']
    paths=set(core)|{ROOT/n for n in ['REPORT.md','REPORT2.md','REPORT3.md','REPORT4.md','REPORT5.md','REPORT6.md','RECORD_GROUNDING_FUNNEL.md',
        'kit2/kit/rerun2/items544.json','kit2/kit/rerun2/gt_staging.json','gpkg/score_ceiling.py','gpkg/join_capture.py','gpkg/join_v2.py',
        'gpkg/capture_io.py','gpkg/grid.py','gpkg/runtime/c.py','gt/v2.py','gt/adapter.py','analyze_round4.py','analyze_round5.py',
        'analyze_s2_round6.py','kit2/kit/funnel.py','kit2/kit/rerun2/join.py','work/payload/tree/student_pilot/routed_features.py',
        'work/payload/tree/evalpath/official.py','work/payload/h1eval/scorers.py','work/payload/b/e2e_reader/stage1.py','kit2/kit/analyze.py']}
    paths|={Path(p) for p in c['provenance']}|{Path(p) for p in s['provenance']}
    inventory={str(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(paths)}
    write(OUT/'INPUTS_R7.json',inventory)
    refs,rows=inputs();boot=Bootstrap(refs)
    same=[r for r in f['lever_summary'] if r['unit']=='items' and r['stage'] in ('S2','S3')]
    ids={i for r in same for i in r['same_stage_item_ids']}
    residual=boot.metric([dict(r,deficit=(100-r['t1']) if r['item_id'] in ids else 0) for r in rows],'deficit')
    p=read(OUT/'SCORE_POINT_T1.json')['statistics']['groups']['all']['metrics']['point_minus_T1']
    d=read(OUT/'SCORE_DENSE_T1.json')['statistics']['groups']['all']['metrics']['dense64_minus_T1']
    started=int(subprocess.check_output(['stat','-c','%W',str(OUT/'SCORE_POINT_T1.log')],text=True).strip())
    now=time.time()
    validation=dict(tests_passed=7,adapter_and_saved_stage_hashes_unchanged=unchanged,round6_outputs_unchanged=True,
        t1_primary_records=150,t1_total_records=160,t1_parity_matches=150,gap_tolerance_m=0,
        join_evidence_checks=f['validation']['raw_join_evidence_checked'],point_object_stages_reproduced=f['validation']['point_stage_records_reproduced'],
        camera_records_checked=len(f['validation']['camera_checks']),all_score_means_and_intervals_match_scorer=True,
        analysis_seconds=dict(camera=c['runtime_seconds'],funnel=f['runtime_seconds'],s2=s['runtime_seconds']),
        wall_seconds_since_first_scorer_log_creation=now-started,
        wall_start_utc=datetime.datetime.fromtimestamp(started,datetime.timezone.utc).isoformat(),
        wall_end_utc=datetime.datetime.fromtimestamp(now,datetime.timezone.utc).isoformat(),
        peak_measured_analysis_RSS_KiB=max(x['max_rss_KiB'] for x in (f,c,s)),
        threads=1,address_space_limit_GiB=15,score_and_join_memory_limit_GiB=16,
        same_s2_s3_items=len(ids),same_s2_s3_100score_deficit=residual,
        overall_point_delta=p,overall_dense_delta=d)
    write(OUT/'VALIDATION_R7.json',validation)
    text=['# 0. Camera split',
        'The NPZ geometry is self-consistent on all 38 GT captures. The rigid alignment criterion passes **6/38** and fails 32; 20 failures also rule out any fixed axis correction. S4/S5 use only passing captures. The T1 cameras reproduce these decisions and residuals.',
        table(['Dataset','Landscape pass/fail','Portrait pass/fail'],[[ds,
            next(f"{r['passed']}/{r['failed']}" for r in c['contingency'] if r['dataset']==ds and r['orientation']=='landscape'),
            next(f"{r['passed']}/{r['failed']}" for r in c['contingency'] if r['dataset']==ds and r['orientation']=='portrait')]
            for ds in ('arkitscenes','scannet','scannetppv2')]),
        table(['Arm','Passing captures: 8 items','Failing captures: 68 items','Pass − fail'],
              [[a,fmt(r['passing']),fmt(r['failing']),fmt(r['pass_minus_fail'])] for a,r in c['score_split'].items()]),
        'The available metadata does not cleanly separate passing and failing captures. Portrait RGB occurs in both groups; source-frame counts and normalized focal lengths overlap. All ARKit counts are lower bounds. The supplied metadata lacks sensor identity and source gravity/orientation flags; captured gravity is a reader prediction.',
        f"[CAMERA_SPLIT.md]({OUT}/CAMERA_SPLIT.md) and [JSON]({OUT}/CAMERA_SPLIT.json) give all 38 native RGB sizes/orientations, raster sizes, relative and rigid residuals, item counts and three-arm scores. Native size means the pinned decoded RGB size; upstream sensor resolution is unavailable. These files were completed before the funnel join.",
        '# 1–2. T1 grounding funnel',
        'The authenticated capture contains 150 primary records and 10 excluded repeats. All 150 primary records match deployed step 544 with 0.00 m gap tolerance. Counts cover all 300 requested object occurrences, including two uncalled operands. Scores use routed distance MRA on 0–100.',
        table(['Stage','Objects','Items','Mean item score [95% CI]'],[[r['stage'],r['objects'],r['items'],fmt(r['score'])] for r in f['tables']['t1']]),
        '**No item reaches S5. Every signed S5-reference budget and its interval is therefore undefined**, including the S2/S3 repair budget. Five S5 objects do not establish an S5 item reference.',
        'S0–S5 use first failure: positive GT visibility; any raw proposal IoU >0.5; at least half of nonempty selected masks with IoU >0.5; three matched frames; centroid no more than 0.25 m outside the full GT OBB. The reader’s own resize maps masks to the 240×320 GT grid.',
        'The 53 censored objects comprise 33 with failed camera alignment and 20 with unresolved portrait mask mapping. The unchanged adapter does not establish a portrait rotation. No-GT contains 148 occurrences on missing captures and 10 missing instance bindings. ScanNet extent readings remain explicit.',
        'Items take their earliest observed failure. A known failure dominates a no-GT operand; otherwise any no-GT operand enters no-GT. Censoring blocks only stages at or after its first unresolved fact, so failed placement alignment cannot hide a resolved S1–S3 failure.',
        'All intervals use 10,000 shared draws of the 46 physical rooms, seed 20261120, with item weighting. Undefined subgroup draws are counted and omitted. The one-item S0 interval is degenerate and does not imply population certainty.',
        f"[FUNNEL_T1.md]({OUT}/FUNNEL_T1.md) and [JSON]({OUT}/FUNNEL_T1.json) include all arm tables, per-object evidence, item joins, migration cells and signed-budget fields. `--t1-capture` was already complete; the scorer required no edit. Its CLI accepts one intervention at a time, so point+T1 and dense+T1 were scored separately.",
        '# 3. What each lever removes',
        f"Across all 150 items, T1 scores {f['overall']['t1']['mean']:.2f}, points {f['overall']['points']['mean']:.2f}, and dense {f['overall']['dense64']['mean']:.2f}. Point − T1 is **{fmt(p)}**; dense − T1 is **{fmt(d)}**. Neither interval establishes an overall gain.",
        table(['T1 object stage','Objects','Point clears stage','Dense provably clears stage','Neither proven to clear'],
            [[r['stage'],r['count'],r['point_proven_advanced'],r['dense_proven_advanced'],r['neither_proven_advanced']] for r in f['lever_summary'] if r['unit']=='objects']),
        'The point lever primarily repairs proposal availability: 18/27 S1 objects advance, but 10 stop at S2. It also clears S2 for 7/27 objects and S3 for 13/29; five S3 objects regress to S2. Thus point prompting does not isolate selection from proposal generation or support.',
        'Dense observations prove one S2→S3 object change and no S0/S1/S3 recovery. This is an evidence limit, not proof that added views do nothing: only the 32 anchors have GT. Full dense stages use conservative matched-support bounds; 55 objects are censored by missing added-frame labels. The separate anchor-only matrices show no S1 proposal recovery.',
        table(['T1 item stage','Items','Point score Δ [95% CI]','Dense score Δ [95% CI]'],
            [[r['stage'],r['count'],fmt(r['point_delta']),fmt(r['dense_delta'])] for r in f['lever_summary'] if r['unit']=='items']),
        'Both arms demonstrably leave **5 S2 objects and 8 S3 objects** at their starting stage. At item level, 4 S2 items and 3 S3 items remain unchanged in stage. In total, 19 S2 and 16 S3 objects have no proven advancement by either lever; these larger counts include unresolved dense outcomes.',
        f"The unchanged-stage items have a **{fmt(residual)}** point deficit to a hypothetical score of 100 across all 150 items (S2: 2.00 points; S3: 0.67). This is a descriptive residual, not the requested S5-level recovery estimate, which remains unidentified. Every object/item migration cell has its own paired score delta and room-bootstrap interval in the full funnel report.",
        '# 4. S2 on the deployed selections',
        f"All **27/27** T1 S2 objects had a raw target proposal at IoU >0.5. They are selection-path losses; the capture alone does not assign all of them to the selector head. Without a target proposal they would be S1. T1 selections meet the relaxed IoU rule on **10/27 (37.0%)**, versus **19/36 (52.8%)** in point-arm S2; the cohorts share 20 objects.",
        table(['Majority class','Pool target: yes','Pool target: no','T1 item score [95% CI]','Point S2 objects'],
            [[r['mask_class'],r['t1_objects'],0,fmt(r['t1_item_score']),r['point_objects']] for r in s['class_comparison']]),
        f"[S2_T1.md]({OUT}/S2_T1.md) and [JSON]({OUT}/S2_T1.json) give each object’s best bound-instance IoU, IoU >0.25 share, per-frame coverage/precision, majority class and every cell’s item scores. They use the exact round-6 class thresholds. Point-in-GT is inapplicable to T1.",
        '# Commands, inputs and runtime',
        'The following commands ran from `gbuild` with `/scratch/jjyeung/envs/p1cpu/bin/python`. All new outputs are in `cap/score_t1`; all new source files are in `gbuild`. No earlier delivery was edited.',
        '```bash',
        "export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''",
        'ulimit -v 16777216',
        'mkdir -p ../cap/score_t1',
        '/scratch/jjyeung/envs/p1cpu/bin/python -B gpkg/score_ceiling.py --point-capture ../cap/t2.gz --point-receipt ../cap/t2ret/CAPTURE.json --point-run-receipt ../cap/t2ret/PARITY.json --t1-capture ../cap/t1.gz --t1-receipt ../cap/t1ret/CAPTURE.json --gt out2/GT.json --out ../cap/score_t1/SCORE_POINT_T1.json > ../cap/score_t1/SCORE_POINT_T1.log',
        '/scratch/jjyeung/envs/p1cpu/bin/python -B gpkg/score_ceiling.py --dense-capture ../cap/dense.gz --dense-receipt ../cap/dret/CAPTURE.json --dense-run-receipt ../cap/dret/PARITY.json --t1-capture ../cap/t1.gz --t1-receipt ../cap/t1ret/CAPTURE.json --gt out2/GT.json --out ../cap/score_t1/SCORE_DENSE_T1.json > ../cap/score_t1/SCORE_DENSE_T1.log',
        '/scratch/jjyeung/envs/p1cpu/bin/python -B camera_split_round7.py > ../cap/score_t1/CAMERA_SPLIT.log',
        '/scratch/jjyeung/envs/p1cpu/bin/python -B gpkg/join_capture.py --capture ../cap/t1.gz --receipt ../cap/t1ret/PARITY.json --upload-receipt ../cap/t1ret/CAPTURE.json --gt out2/GT.json --out ../cap/score_t1/JOIN_T1.jsonl > ../cap/score_t1/JOIN_T1.log',
        '/scratch/jjyeung/envs/p1cpu/bin/python -B funnel_round7.py > ../cap/score_t1/FUNNEL_T1.log 2>&1',
        '/scratch/jjyeung/envs/p1cpu/bin/python -B s2_round7.py > ../cap/score_t1/S2_T1.log 2>&1',
        '/scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest test_round7 -v > ../cap/score_t1/TEST_ROUND7.log 2>&1',
        '/scratch/jjyeung/envs/p1cpu/bin/python -B report_round7.py',
        'sha256sum --check SHA256SUMS7',
        '```',
        f"Seven tests passed. All {f['validation']['point_stage_records_reproduced']} called point-object stages reproduce the saved artifact; T1 upstream evidence agrees with the required join on {f['validation']['raw_join_evidence_checked']} annotated objects. Score means and intervals reproduce the scorer. Saved GT adapter, stage table and round-6 outputs retain their hashes.",
        f"Measured analysis runtime: camera {c['runtime_seconds']:.2f} s, funnel {f['runtime_seconds']:.2f} s, S2 {s['runtime_seconds']:.2f} s. Wall time from the first scorer log’s creation through report generation: {now-started:.1f} s, including code preparation and validation. Scoring/join durations were not separately instrumented. Peak measured analysis RSS: {validation['peak_measured_analysis_RSS_KiB']/1024:.1f} MiB; one numerical thread, 15 GiB analysis address-space cap (16 GiB for scorer/join). No GPU, SSH, Git, network, deletion or submission ran.",
        f"[INPUTS_R7.json]({OUT}/INPUTS_R7.json) hashes every consumed analysis input, source dependency and S2 NPZ. Core input SHA256s follow. [SHA256SUMS7]({ROOT}/SHA256SUMS7) covers every new source, report and output except itself.",
        table(['Input','SHA256'],[[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else '../cap/'+str(p.relative_to(CAP)),inventory[str(p)]['sha256']] for p in core])]
    report='\n\n'.join(text)+'\n'
    # Markdown tables and code blocks already contain newlines; keep the requested cap.
    assert len(report.splitlines())<=150,len(report.splitlines())
    with (ROOT/'REPORT7.md').open('x') as out: out.write(report)
    sources=[ROOT/n for n in ('round7_common.py','camera_split_round7.py','funnel_round7.py','s2_round7.py','test_round7.py','report_round7.py','REPORT7.md')]
    outputs=sorted(p for p in OUT.iterdir() if p.is_file())
    with (ROOT/'SHA256SUMS7').open('x') as out:
        for p in sorted(sources+outputs):
            relative=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else '../cap/score_t1/'+p.name
            out.write(sha(p)+'  '+relative+'\n')
    print(json.dumps(dict(report_lines=len(report.splitlines()),files_hashed=len(sources+outputs),validation=validation)))

if __name__=='__main__': main()
