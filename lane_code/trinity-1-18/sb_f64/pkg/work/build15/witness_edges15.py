"""Run the witness CLI and reject contradictory metadata from a native export."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys,os,json,runpy
L=Path(__file__).resolve().parents[2];B=L/'work/build15';T=L/'work/tree_r1';O=B/'proofs/witness_edges';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(L/'work/n1fix2')];os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
m=Monitor(T)
from student_pilot import carrier_c1_run as R,p3_provenance as V
from launch_r1 import p_opener_witness as W,p_handover_receipt as P
from tests.test_r2_build_n1 import write
from tests.test_carrier_c1 import fixture
from tests.test_carrier_c1_run import RunnerTests
from transformers import PreTrainedTokenizerFast
cfg=V.load(B/'proofs/final_focused/n1fix/b15_witness/witness_config.json')
def processor(path):return SimpleNamespace(tokenizer=PreTrainedTokenizerFast.from_pretrained(path,local_files_only=True))
with patch.object(R,'processor_for',processor),patch.object(V,'write',write),patch.object(sys,'argv',[
        'p_opener_witness','--config',str(B/'proofs/final_focused/n1fix/b15_witness/witness_config.json'),'--output',str(O/'v.json')]):
    runpy.run_module('launch_r1.p_opener_witness',run_name='__main__')
artifact=V.load(V.pinned(cfg['init_artifact']['artifact']))
# Negative fixture: append a contradictory declaration to an otherwise native export.
artifact['routing_vocabulary']={'vocabulary_sha256':'f'*64,'tokens':{'ids':{'<move':0}}}
cfg['init_artifact']['artifact']=write(O/'forged_export.json',artifact)
with patch.object(P,'write',write):
    cfg['r1_training']['handover_receipt']=P.produce(cfg['r1_training']['p_run'],cfg['init_artifact']['artifact'],O/'handover.json',job_id='cpu-proof',trainer_commit='fixture')
with patch.object(R,'processor_for',processor):
    try:W.produce(cfg,O/'wrong.json')
    except ValueError as e:assert str(e)=='P_EXPORT_OPENER_VOCABULARY_MISMATCH';reason=str(e)
    else:raise AssertionError('Contradictory export vocabulary admitted')
write(O/'RESULT.json',dict(cli_witness=V.file_pin(O/'v.json'),refusal=reason,
    stand_ins='The prior native CPU export supplies the closure. The negative fixture adds a false vocabulary declaration; the real receipt producer and witness producer reject it. A local small tokenizer replaces only the pretrained processor boundary in the witness CLI.'))
m.save(O);print(reason)
