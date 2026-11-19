from pathlib import Path
import json,os,sys,subprocess,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build16';T=L/'work/tree_r1';M=B/'mutant';O=B/'proofs/mutations';O.mkdir(parents=True,exist_ok=True)
base=B/'base'
if not base.exists():base.symlink_to(L/'work/base',target_is_directory=True)
cases=[
 ('count_form','student_pilot/r1_counting.py',"if form.startswith('FS_LIST'):","if False:",'test_classifier_and_named_refusals'),
 ('producer_guard','student_pilot/r1_population.py',"if card.get('counting_admission') == 'procedure_only_v1':","if False:",'test_producer_refuses_without_z'),
 ('persisted_hash','student_pilot/r1_persisted.py',"if sha256(path) != pin['sha256']:","if False:",'test_persisted_forgery_and_mismatch'),
 ('state_pin','student_pilot/r1_persisted.py',"if pins.get(label,{}).get('sha256') != pin.get('sha256'):","if False:",'test_persisted_metadata_only_and_closure_refusals'),
 ('stage_pin','launch_r1/production_proof.py',"return [file_pin(pinned(pin)) for pin in entries]","return entries",'stage_test16.Staging.test_all_pins'),
 ('resume','student_pilot/carrier_c1_run.py',"if start_step:\n","if False:\n",'test_native_first_resumed_batch')]
cases.append(('handover_rebind','launch_r1/production_proof.py',
    "value['continuation_identity'] = training.target_identity(cfg)['config_identity']",
    "value['continuation_identity'] = '0'*64",'test_final_preparation_handover_binding'))
cases += [
 ('unassigned','student_pilot/r1_population.py','if unknown:','if False:','tests.test_r1_build13.PopulationTests.test_unassigned_type'),
 ('slice_identity','student_pilot/r1_population.py',"if marker != dict(family=kind, sha256=source_hash) or digest(row) != row_hash:",'if False:','tests.test_r1_build13.PopulationTests.test_slice_identity'),
 ('overlap','student_pilot/r1_mix.py','len(set(values)) != len(values)','False','tests.test_r1_build13.PopulationTests.test_overlap'),
 ('binding','student_pilot/r1_loader.py',"if cfg['r1_training'].get('row_plan_sha256') != digest(binding):",'if False:','tests.test_r1_build13.PopulationTests.test_binding_changed'),
 ('base_cell','student_pilot/r1_population.py',"if stream == 'routing' and kind in SLICE_CELLS:",'if False:','tests.test_r1_build13.PopulationTests.test_base_cells_refused'),
 ('base_composition','student_pilot/r1_routing.py',"if family(row, 'routing') in SLICE_CELLS:",'if False:','tests.test_r1_build13.PopulationTests.test_composition_replaces_base')]
files=[p for p in T.rglob('*') if p.is_file() and not set(p.relative_to(T).parts)&{'.git','__pycache__','artifacts'}]
for p in files:
    q=M/p.relative_to(T);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
results=[]
for name,source,before,after,test in cases:
    env={**os.environ,'R2_TREE':str(M),'B16_PROOF':'mutations/run'}
    cmd=[sys.executable,'-I','-s','-B',str(B/'test16.py'),test if '.' in test else 'tests.test_r1_build16.Build16.'+test]
    for phase in ('clean','mutant'):
        p=M/source;raw=(T/source).read_text();assert raw.count(before)==1
        p.write_text(raw if phase=='clean' else raw.replace(before,after))
        with (O/(name+'_'+phase+'.log')).open('w') as log:
            result=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode<0:raise SystemExit('Process killed; stop without rerun')
        if phase=='clean':assert result.returncode==0,(name,'clean failed')
        else:assert result.returncode!=0,(name,'mutation escaped')
    p.write_text(raw)
    results.append(dict(name=name,source=source,test=test,status='CAUGHT',source_sha256=hashlib.sha256(raw.encode()).hexdigest()))
    (O/'RESULT.json').write_text(json.dumps(dict(results=results),indent=2))
    print(name,'CAUGHT',flush=True)
