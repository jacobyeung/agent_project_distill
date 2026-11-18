from pathlib import Path
import json,hashlib,sys,collections
L=Path(__file__).resolve().parents[2];B=L/'work/merge11';T=L/'work/tree_r1'
E=Path('/scratch/jjyeung/orch_n30/review_tree10/work/parity')
O=B/'proofs/depth_sweep';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(L/'work/n1fix2'),str(T)]
from monitor9 import Monitor
monitor=Monitor(T)
source=(E/'geo_dump.py').read_text().split('out_rows = []')[0]
sys.argv=[str(B/'sweep.py'),str(T),'new',str(O/'unused.json'),'3000']
space={'__name__':'review_sweep'};exec(compile(source,str(E/'geo_dump.py'),'exec'),space)
expected=json.loads((E/'b9f_legacy.json').read_text());counts=collections.Counter();differences=[];actual_hash=hashlib.sha256();expected_hash=hashlib.sha256()
for row in expected:
    got=space['run'](row['seed'],row['epoch'])
    for (call,want),(same,actual) in zip(row['res'],got,strict=True):
        assert same==call
        counts['responses']+=1;counts['identical']+=want==actual;counts['different']+=want!=actual
        counts['invalid_depth']+=want=='error: invalid own depth'
        expected_hash.update(json.dumps([call,want],separators=(',',':')).encode())
        actual_hash.update(json.dumps([call,actual],separators=(',',':')).encode())
        if want!=actual and len(differences)<200:differences.append(dict(seed=row['seed'],epoch=row['epoch'],call=call,expected=want,actual=actual))
result=dict(counts=counts,expected_sha256=expected_hash.hexdigest(),actual_sha256=actual_hash.hexdigest(),differences=differences,
    source=str(E/'b9f_legacy.json'),source_sha256=hashlib.sha256((E/'b9f_legacy.json').read_bytes()).hexdigest(),
    generator=str(E/'geo_dump.py'),generator_sha256=hashlib.sha256((E/'geo_dump.py').read_bytes()).hexdigest(),
    standin='Reviewer seeded own-head outputs and float32 depth-query head; real OwnGeometry, respond, fixed readout modules and contract epochs execute. No real-scene or GPU qualification.')
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');monitor.save(O)
print(json.dumps(result));assert counts['different']==0
