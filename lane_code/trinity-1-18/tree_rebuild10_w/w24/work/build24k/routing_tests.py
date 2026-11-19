from pathlib import Path
import sys,json,time
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';F=D/'routing_test';F.mkdir()
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(L/'work/tree_r1'),str(L/'work/build24/kits/n/b')]
import native24 as N
import joblib as J
from i import refresh
from rg import regenerate
from student_pilot.r1_persisted import scope
from student_pilot.p3_provenance import pinned,load,digest
from student_pilot import s1_routing
from student_pilot.mdg_parent import model_pin
N.C.processor_for=N.processor
cfg=J.load(L/'work/build24/proofs/capacity/400/request_config.json')
pin=J.write(F/'input.json',cfg)
paths={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
with scope(paths),scope(cfg['r1_training']['persisted_files']):
 request=refresh(dict(config=pin,staged_pins=[pin]),F/'i')
 cfg=load(pinned(request['config']))
 root=F/'job';root.mkdir();started=time.monotonic()
 actual=regenerate(cfg,root,compare=False)
 (root/'selection').rename(F/'retained_selection')
 point=load(pinned(cfg['streams']['pointing']))
 expected=s1_routing.build(cfg,root/'selection',point['division'],model_pin(cfg))
 assert actual['regenerated_sha256']==digest(expected)
 assert actual['rows']==expected['count'] and len(actual['row_id_digest'])==64
 first=J.load(F/'routing_selection.json')
 assert first==actual
 J.write(D/'ROUTING_TESTS.json',dict(status='PASS',rows=actual['rows'],regenerated_sha256=actual['regenerated_sha256'],
     deterministic_exact_native_digest=True,row_id_digest=actual['row_id_digest'],elapsed_seconds=time.monotonic()-started,
     scope='Mode-r computational helper with native s1_routing.build and tiny model/store fixture; P production comparison requires Orchard'))
 print('native routing digest deterministic',actual['rows'],actual['regenerated_sha256'])
