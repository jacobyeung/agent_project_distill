"""Generate the fixture-only ownership override and its authenticated evidence."""
from pathlib import Path
import json, sys, hashlib, runpy

L=Path(__file__).resolve().parents[2]; D=L/'work/build24f'; R=D/'rehearsal2'
sys.path.insert(0,str(L/'work/build24'))
import joblib as J
R.mkdir(exist_ok=True)
(R/'tmp').mkdir(exist_ok=True)
ext=L.parent/'ext/m400real'
e=J.load(ext/'e.json')
def pinned_external(pin):
    path=ext/'files'/pin['path'].lstrip('/')
    assert J.sha(path)==pin['sha256']
    return J.load(path)
prep=pinned_external(e['pins']['preparation'])
manifest=pinned_external(prep['model'])
config=Path('/scratch/jjyeung/devs1c_models/cp1/base/config.json')
assert J.sha(config)==manifest['files']['config.json']
prod=J.load(config)
assert prod['tie_word_embeddings'] is False
assert prod['text_config'].get('tie_word_embeddings',False) is False
kitcfg=J.load(L/'out/kit_n_go/k/n.json')
assert kitcfg['base_identity']==manifest['base_identity']
assert kitcfg['r1_training']['handover_receipt']['sha256']==J.sha(ext/'e.json')
assert kitcfg['world_size']==4 and kitcfg['parallel']=='fsdp'
evidence=dict(production_config=dict(path=str(config),sha256=J.sha(config)),
    model_manifest=prep['model'],preparation=e['pins']['preparation'],
    export_receipt=dict(path=str(ext/'e.json'),sha256=J.sha(ext/'e.json')),
    base_identity=manifest['base_identity'],tie_word_embeddings=False,
    text_config_tie_word_embeddings='absent; Qwen3_5TextConfig default is false',
    production_world_size=kitcfg['world_size'],production_parallel=kitcfg['parallel'],
    production_verdict='The pinned 9B config does not share embedding/head parameters; NCCL does not create an alias.',
    distributed_reproduction='NOT RUN: lane must run go_rehearsal.sh outside the sandbox')
J.write(R/'PRODUCTION_EVIDENCE.json',evidence)
J.write(R/'model_override.json',dict(tie_word_embeddings=False,**{'text_config.tie_word_embeddings':False},
    apply='After native authenticated warm-start load, before optimizer/FSDP',
    lm_head_weight='Independent FP32 Parameter cloned from the loaded tied weight; equal values',
    source='work/build24/proofs/capacity/model/config.json',production=evidence['production_config']))
runpy.run_path(str(D/'make_rehearsal.py'),run_name='__main__')
overrides=J.load(D/'REHEARSAL_OVERRIDES.json')
overrides['model_boundary']=J.load(R/'model_override.json')
overrides['copier']['target']='rehearsal2/target'
J.write(D/'REHEARSAL_OVERRIDES.json',overrides)
print('Production config hash verified; fixture ownership override generated.')
