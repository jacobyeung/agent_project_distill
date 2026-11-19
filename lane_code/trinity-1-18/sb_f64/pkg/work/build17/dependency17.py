"""Try the native processor constructor; do not substitute an encoder."""
from pathlib import Path
import json,importlib.util,sys,traceback
L=Path(__file__).resolve().parents[2];B=L/'work/build17';O=B/'proofs/native';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(L/'work/tree_r1')
result=dict(status='BLOCKED',GO=False,complete_native_fixture=False,
            intended_standins=['synthetic frame host','reduced native model dimensions'],
            extra_encoder_standins_used=False,python=sys.executable,
            torchvision_spec=bool(importlib.util.find_spec('torchvision')))
try:
    from transformers import Qwen3VLVideoProcessor
    processor=Qwen3VLVideoProcessor(patch_size=2,temporal_patch_size=2,merge_size=2)
except (ImportError,RuntimeError) as error:
    result['refusal']=type(error).__name__+':'+str(error)
    result['traceback']=traceback.format_exc()
else:
    result['dependency']='available'
result['stages']={k:'not demonstrated in one native mode-q run' for k in (
    'verify_pins','s1_routing.build','r1_routing.compose_native','s1_admission.prepare',
    'r1_population.bind_prepared','r1_loader.production_audit','persisted_handover',
    'p_opener_witness','N_init','all_rank_forward_400','all_rank_forward_600')}
result['scope']='This dependency probe is not a native production fixture. Separate retained component tests do not close the requested end-to-end proof.'
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');m.save(O)
(B/'STATUS.md').write_text((B/'STATUS.md').read_text()+'\nStep 3 blocked: the native video processor constructor requires unavailable torchvision. No encoder stand-in was introduced. No complete native mode-q ADMIT at either milestone was demonstrated. Evidence: proofs/native/RESULT.json.\n')
print(result['refusal'])
