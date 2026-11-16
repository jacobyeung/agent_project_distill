import json,subprocess,sys,os
from pathlib import Path
L=Path(__file__).resolve().parents[1]
cases={
 'H-1':'sensor313_off_provider_and_audit',
 'H-2':'calculator_field_scope',
 'M-1':'shared_binding_served_or_deferred or manifest_superset or phrases_superset',
 'M-2':'rerender_depth_arguments',
 'L-1':'pose_identity_and_later_centre',
 'L-2a':'standalone_generator_imports',
 'L-2b':'generator_refusal_type',
 'L-2c':'legacy_gap_off_grammar',
 'L-2d':'vocabulary_and_suffix_exclusions',
 'L-2e':'cache_lookup_preserves_caller',
}
records={}
for item,selector in cases.items():
    tag='R4_REJECT_'+item.replace('-','_')+'_R5';log=L/'work/test_artifacts_r5'/(tag+'.log')
    command=[sys.executable,'-I','-s','-B',str(L/'work/run_tests_r5.py'),'r4_applied',tag,'contract','-k',selector]
    result=subprocess.run(command,env=dict(os.environ,R5_NO_TRACE='1'),capture_output=True,text=True)
    log.write_text(result.stdout+result.stderr)
    tests=json.loads((L/f'work/{tag}_results.json').read_text())
    records[item]=dict(command=command,returncode=result.returncode,log=str(log),results=tests,
                       rejects_r4=any(v['outcome']=='failed' for v in tests.values()))
    assert records[item]['rejects_r4'],item
    print(item,'R4 REJECTED',flush=True)
(L/'out/R4_REGRESSION_PROOF_R5.json').write_text(json.dumps(records,indent=2))
