from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';B=L/'work/build24';sys.path.insert(0,str(B));import joblib as J
sources={
 'build22':L/'work/build22/proofs/new_tests/TESTS.json','build23':B/'proofs/tests23/TESTS.json',
 'build23b':D/'proofs/tests23b/TESTS.json','build23_resolver':B/'proofs/resolver23/RESOLVER_TESTS.json',
 'kit24':B/'KIT_TESTS.json','resolver24':B/'RESOLVER_TESTS.json',
 **{n:L/'work/build21/proofs'/n/'TESTS.json' for n in ('final_focused','edges','producer_edges')},
 **{'build24_'+n:L/'work/build21/proofs'/('build24_'+n)/'TESTS.json' for n in ('scanner','resolver','kit','naming21c','naming21d')}}
records={n:{k:J.load(p)[k] for k in ('tests','successful')} for n,p in sources.items()}
assert all(x['successful'] for x in records.values());assert sum(x['tests'] for x in records.values())==356
for name,path in {'init24b':D/'proofs/init/TESTS.json','pins24b':D/'PIN_TESTS.json','proof24b':D/'PROOF_TESTS.json',
 **{f'guard_{n}_{k}':D/('guard_'+n)/f for n in ('q','n') for k,f in [('new','GUARD_TESTS.json'),('legacy','LEGACY_GUARD_TESTS.json')]}}.items():
 records[name]={k:J.load(path)[k] for k in ('tests','successful')};sources[name]=path
assert all(x['successful'] for x in records.values())
J.write(D/'TEST_COUNTS.json',dict(successful=True,base_tests=356,tests=sum(x['tests'] for x in records.values()),suites={n:dict(v,evidence=str(sources[n].relative_to(L))) for n,v in records.items()}))
print('PASS:',sum(x['tests'] for x in records.values()),'tests, including build24\'s 356')
