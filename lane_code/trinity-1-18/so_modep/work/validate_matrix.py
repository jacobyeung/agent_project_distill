from pathlib import Path
import os,sys,subprocess,json
L=Path(__file__).resolve().parents[1]
os.sched_setaffinity(0,range(8))
base=['tests.test_r1_build20','tests.test_r1_build19','tests.test_r1_build18','tests.test_r1_build17','tests.test_r1_export17','tests.test_r1_build16','tests.test_r1_build15','tests.test_r1_build14','tests.test_r2_build_n1','tests.test_r2_n1fix','tests.test_r2_n1fix3','tests.test_r2_build12','tests.test_r1_build13','tests.test_r2_build3.Build3.test_opener_export_keep_and_reset','export_mutation17.HashTwin.test_same_size_shard_refuses']
extra=['tests.test_s1_admission','tests.test_s1_scene_exclusions','tests.test_s1_target_filter','tests.test_s1_first_batch_progress','tests.test_modep_fast_paths','tests.test_modep_select_sql','tests.test_modep_gloo','tests.test_orchard.OrchardTests.test_remap_preserves_pins_rows_and_detects_corrupt_bytes','tests.test_deploy_alias','tests.test_s1_production_imports']
results=[]
for label,fast,sql in [('off','0','0'),('paths','1','0'),('sql','0','1'),('both','1','1')]:
 env={**os.environ,'MODEP_TREE':str(L/'work/delivery_tree'),'MODEP_TEST_LABEL':'final_native_'+label,'S1_PREP_FAST_PATHS':fast,'S1_PREP_SELECT_SQL':sql}
 cmd=[sys.executable,'-I','-s','-B',str(L/'work/run_native_tests.py'),*base,*extra]
 log=L/'out/tests'/('final_native_'+label+'.log')
 with log.open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 results.append(dict(label=label,returncode=r.returncode,command=cmd,switches={k:env[k] for k in ('S1_PREP_FAST_PATHS','S1_PREP_SELECT_SQL')},log=str(log)))
 (L/'out/tests/native_matrix.json').write_text(json.dumps(results,indent=2)+'\n')
 print(label,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
