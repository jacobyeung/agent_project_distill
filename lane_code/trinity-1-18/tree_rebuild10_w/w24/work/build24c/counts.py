from pathlib import Path
import json,sys,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24c'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
sources={
 **{f'guard_{n}_{k}':D/('guard_'+n)/f for n in ('q','n') for k,f in [('new','GUARD_TESTS.json'),('legacy','LEGACY_GUARD_TESTS.json')]},
 'kit24':D/'KIT_TESTS.json','resolver24':L/'work/build24/RESOLVER_TESTS.json','resolver23':D/'proofs/resolver23/RESOLVER_TESTS.json','runtime24c':D/'RUNTIME_TESTS.json',
 **{n:L/'work/build21/proofs'/('build24c_'+n)/'TESTS.json' for n in ('scanner','resolver','kit','naming21c','naming21d')}}
records={}
for name,path in sources.items():
 v=J.load(path);assert v['successful'],(name,v)
 target=D/'results'/(name+'.json');target.parent.mkdir(exist_ok=True);shutil.copyfile(path,target)
 records[name]=dict(tests=v['tests'],successful=True,evidence=str(target.relative_to(L)))
assert all(x['returncode']==0 for x in J.load(D/'REGRESSIONS.json'))
assert all(x['returncode']==0 for x in J.load(D/'FINAL_CHECKS.json'))
for name in ('q','n'):
 assert J.load(D/('SCAN_'+name+'.json'))['status']=='PASS'
 assert J.load(D/('LOOKAHEAD_'+name+'.json'))['classification']=='boundary'
 assert J.load(D/('LOOKAHEAD_'+name+'.json'))['kit_seal']==J.seal(L/'work/build24/kits'/name)
 assert J.load(D/('SCAN_'+name+'.json'))['kit_seal']==J.seal(L/'work/build24/kits'/name)
records['decoded_sequence']=dict(tests=2,successful=True,evidence='work/build24c/SEQUENCE.json')
J.write(D/'TEST_COUNTS.json',dict(successful=True,tests=sum(x['tests'] for x in records.values()),suites=records))
print('PASS',sum(x['tests'] for x in records.values()),'tests')
