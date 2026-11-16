"""Replay both reviewer sets serially with in-memory mutations and behavioral tests."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];W=ROOT/'work';OUT=ROOT/'out/MUTANTS_R3'
OUT.mkdir(exist_ok=True)
FIRST=['M1','M2','M3','M4','M5','M6','M7','M8','M9','M10','M10b','M11','M11b','M12','M14','M15']
SECOND=['N1','N2','N2b','N3','N4','N5','N6','N7','N8','N8b','N9']
TESTS={
 'M1':'test_probe.FeatureTests.test_pack_row_major_and_duplicate','M2':'test_probe.FeatureTests.test_pack_row_major_and_duplicate',
 'M3':'test_probe.FeatureTests.test_tiny_vit_hooks_and_mdg_grid',
 'M4':'test_r2.EntryTests.test_t1_entry_training_budget_phrase_and_candidate_order',
 'M5':'test_r2.EntryTests.test_t1_entry_training_budget_phrase_and_candidate_order',
 'M6':'test_r2.EntryTests.test_extractor_entry_masks_match_frames_and_sam_candidates',
 'M7':'test_r2.EntryTests.test_extractor_entry_masks_match_frames_and_sam_candidates',
 'M8':'test_r2.ProviderTests.test_hf_layers_and_prefix_removal',
 'M9':'test_r2.EntryTests.test_t1_entry_training_budget_phrase_and_candidate_order',
 'M10':'test_r2.BoundaryTests.test_bootstrap_room_clustering_and_pairing','M10b':'test_r2.BoundaryTests.test_bootstrap_room_clustering_and_pairing',
 'M11':'test_r2.BoundaryTests.test_injected_tuning_and_evaluation_room_train_rows','M11b':'test_r2.BoundaryTests.test_injected_tuning_and_evaluation_room_train_rows',
 'M12':'test_r2.BoundaryTests.test_card_thresholds_below_boundary_and_uncertainty',
 'M14':'test_r2.R2Features.test_quarter_taps_and_equal_head_capacity','M15':'test_probe.FeatureTests.test_pool_onehot_empty_and_bilinear',
 'N1':'test_r2.EntryTests.test_extractor_entry_masks_match_frames_and_sam_candidates',
 'N2':'test_r2.ProviderTests.test_sam_documented_input_and_taps','N2b':'test_r2.R2Features.test_quarter_taps_and_equal_head_capacity',
 'N3':'test_r2.R2Features.test_quarter_taps_and_equal_head_capacity',
 'N4':'test_r2.BoundaryTests.test_bootstrap_room_clustering_and_pairing',
 'N5':'test_r3.Decisions.test_challenger_positive_point_straddles_zero',
 'N6':'test_r2.BoundaryTests.test_card_own_preference_and_low_pass_high_fail',
 'N7':'test_r2.EntryTests.test_t1_entry_training_budget_phrase_and_candidate_order',
 'N8':'test_r2.ProviderTests.test_sam_documented_input_and_taps','N8b':'test_r2.ProviderTests.test_sam_documented_input_and_taps',
 'N9':'test_r3.Decisions.test_high_resolution_positive_point_straddles_zero'}

def specs():
    values=[]
    for name in FIRST+SECOND:
        p=ROOT.parent/'own_probe_review2/mutants'/(name+'.json')
        if not p.exists():p=OUT/(name+'.json')
        m=json.loads(p.read_text());m['reviewer_spec']=str(p);m['adaptation']='Unchanged reviewer edit'
        e=m['edits'][0]
        if name=='M12':
            e.update(old="    r1=[parity_verdict(parity,-cfg['R1']['reference_max_deficit'])]",new="    r1=[parity_verdict(parity,-(cfg['R1']['reference_max_deficit']+.03))]")
            m['adaptation']='R1 now uses paired parity; loosen the permitted deficit by the same 3 points'
        if name=='N1':
            e.update(old="            maps=readout_maps(raw_maps,statistics=statistics);final_maps=readout_maps(raw_maps,'final',statistics)",
                new="            maps=readout_maps(raw_maps,statistics=statistics) if args.arm!='A5' else [__import__('own_feats.core',fromlist=['x']).channel_reduce(m.float(),256) for m in raw_maps];final_maps=readout_maps(raw_maps,'final',statistics)")
            m['adaptation']='Skip the normalization path on A5 at the extraction boundary'
        if name in ('N5','N6'):
            e.update(old="                if allowed(arm,provisional) and delta['lo']>0:",
                new="                if allowed(arm,provisional) and delta['"+('value' if name=='N5' else 'hi')+"']>0:")
            m['adaptation']='Same decision fault at the T1/R3-only choice boundary'
        if name=='N9':
            e.update(old="            if delta['hi']<0 and allowed('A2',provisional):",new="            if delta['value']<0 and allowed('A2',provisional):")
            m['adaptation']='Same A2 point-estimate fault at the T1/R3-only choice boundary'
        values.append(m)
    return values

def run():
    results=[]
    for m in specs():
        for e in m['edits']:
            source=ROOT/'out/room_gate.py' if e['module']=='room_gate' else W/(e['module'].replace('.','/')+'.py')
            if source.read_text().count(e['old'])!=1:raise ValueError('Nonunique mutation site '+m['id'])
        spec=OUT/(m['id']+'.json');spec.write_text(json.dumps(m,indent=2)+'\n')
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',CUDA_VISIBLE_DEVICES='',
            PYTHONPATH=':'.join(map(str,[W/'mutation_support_r3',W,ROOT/'out',W/'tests'])),R2_MUTATION=str(spec))
        start=time.monotonic();p=subprocess.run([sys.executable,'-m','unittest',TESTS[m['id']],'-v'],cwd=ROOT,env=env,capture_output=True,text=True)
        if p.returncode<0 or p.returncode>=128:raise RuntimeError('Process killed; no retry: '+m['id'])
        log=p.stdout+p.stderr;(OUT/(m['id']+'.log')).write_text(log)
        failures=[line for line in log.splitlines() if line.startswith(('FAIL:','ERROR:'))]
        harness=any(x in log for x in ('MUTATION SITE NOT UNIQUE','SyntaxError','ImportError','ModuleNotFoundError'))
        result=dict(id=m['id'],caught=bool(p.returncode and failures and not harness),harness_error=harness,
            failing=failures,test=TESTS[m['id']],seconds=time.monotonic()-start,adaptation=m['adaptation'])
        results.append(result);print(json.dumps(result),flush=True)
        (ROOT/'out/MUTATIONS_R3.json').write_text(json.dumps(results,indent=2)+'\n')
    if not all(r['caught'] for r in results):raise SystemExit('Some behavioral mutants survived')

def positive_control():
    # Reviewer 1 labels M13 a benign normalization fix, not a fault to kill.
    m=dict(id='M13',description='Normalize the already canonical candidate phrase; expected to stay green',
        adaptation='Apply the benign normalization to candidate_phrase(g) at the current payload lookup',
        edits=[dict(module='online_probe',old="['phrases'][candidate_phrase(g)]",new="['phrases'][normalize_name(candidate_phrase(g))]")])
    spec=OUT/'M13.json';spec.write_text(json.dumps(m,indent=2)+'\n')
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',CUDA_VISIBLE_DEVICES='',
        PYTHONPATH=':'.join(map(str,[W/'mutation_support_r3',W,ROOT/'out',W/'tests'])),R2_MUTATION=str(spec))
    p=subprocess.run([sys.executable,'-m','unittest','test_r2.EntryTests.test_online_first_tuning_scene_end_to_end_both_tasks','test_r3.Spatial','test_r3.Decisions.test_card_prints_t1_choice_intervals_and_two_controls_without_teacher','-v'],cwd=ROOT,env=env,capture_output=True,text=True)
    log=p.stdout+p.stderr;(OUT/'M13.log').write_text(log)
    value=dict(id='M13',expected='PASS (benign control)',passed=p.returncode==0,returncode=p.returncode)
    (ROOT/'out/M13_CONTROL_R3.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
    if p.returncode:raise SystemExit('M13 control failed; inspect log without automatic retry')


if __name__=='__main__':
    if '--positive-control' in sys.argv:positive_control()
    else:run()
