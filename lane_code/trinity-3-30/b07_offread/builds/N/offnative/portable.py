"""Assemble relative source roots and an opaque reviewable worker packet."""
from pathlib import Path
import json
from .paths import ROOT,OFFKIT,R,C8,V1,REVSI,VSI,B04,TREE
from .io import load,sha,dump,digest
from .transport import packet
from .opacity import path_name,pack

ROOTS={'OFFKIT':'d/00','R':'d/01','C8':'d/02','V1':'d/03','REVSI':'d/04',
       'B04':'d/05','TREE':'d/06','VSI':'d/07','RET544':'a/00','TOKENIZER':'a/01'}


def sources():
    files={};pins=[]
    def add(source,target):
        p=Path(source);raw=p.read_bytes();files[target]=raw
        import hashlib
        pins.append({'logical_path':target,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
    for p in sorted((ROOT/'offnative').glob('*.py')):add(p,'offnative/'+p.name)
    # offkit stays owner-supplied: import it unchanged; never copy or fork it.
    for p in sorted((R/'kit').rglob('*')):
        if p.is_file() and p.suffix in ('.py','.json','.jsonl','.sh'):add(p,'d/01/kit/'+str(p.relative_to(R/'kit')))
    add(R/'out/OFFKIT_PINS.json','d/01/out/OFFKIT_PINS.json')
    for p in sorted(C8.glob('*.py')):add(p,'d/02/'+p.name)
    for name in ('RUNTIME_TREE.json','CAMERA_SHORTCUTS.json'):
        add(C8/name,'d/02/'+name)
    for p in sorted((C8/'mask_kit').rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:add(p,'d/02/mask_kit/'+str(p.relative_to(C8/'mask_kit')))
    for p in sorted(V1.rglob('*.py')):add(p,'d/03/'+str(p.relative_to(V1)))
    for p in sorted((REVSI/'reader/evaluator').rglob('*.py')):add(p,'d/04/reader/evaluator/'+str(p.relative_to(REVSI/'reader/evaluator')))
    for p in sorted((B04/'e2e_reader').glob('*.py')):add(p,'d/05/e2e_reader/'+p.name)
    for name in sorted(load(C8/'RUNTIME_TREE.json')['sources']):add(TREE/name,'d/06/'+name)
    for name in ('REGISTERED_FRAME_INDICES.json','REGISTERED_FRAME_INDICES_PIN.json',
                 'REVSI_DENSE_MAPPING.json','REVSI_MEDIA_MANIFEST.json','VSI_COHORT.json',
                 'VSI_MEDIA_MANIFEST.json','VSI_NAME_INVENTORY.json','OFFKIT_EXTERNAL_PINS.json',
                 'PROOF_MASKS_LOST.json','PROOF_POLICY_PINS.json','PROOF_KEYS.json','N4_MEDIA_EVIDENCE.json'):
        if (ROOT/'out'/name).exists():add(ROOT/'out'/name,'out/'+name)
    for root in (R,C8,V1,B04,TREE):
        add(root/'PIN.json','pins/'+root.name+'.json')
    return files,{'schema':'orchkit-pins-v1','entries':pins}


def build(destination,config,binding,items,inputs):
    d=Path(destination)
    files,pins=sources()
    if inputs and inputs.get('uploaded_media_root'):
        from .stage_plan import prepare
        _,boot=prepare(binding,inputs,d/'reviewed_stage',config['token'],config['pool'])
        for name,raw in boot.items():files['work/runtime/'+name]=raw
        inputs=dict(inputs,reviewed_stage_config='work/runtime/bootstrap/CONFIG.json')
    # The full operator BINDING.json stays local. The worker receives a minimal read spec.
    spec={'schema':'orchkit-read-v1','x0':binding['binding_sha256'],
          'benchmark_code':int(binding['benchmark']=='vsibench5130'),'reader_code':int(binding['reader']['kind']=='e2e'),
          'mode_code':{'fixture':0,'proof':1,'production':2}[binding['mode']],
          'export':{'kind':binding['export']['kind'],'sha256':binding['export']['sha256']},
          'frames':binding['read_config']['frames'],'g3t':binding['read_config']['g3t'],
          'freeze_values':binding['reader'].get('freeze_values'),
          'arms':binding['arms']}
    data={'config_sha256':sha(d/'CONFIG.json'),'config':config,'spec':spec,'items':items,'inputs':inputs}
    files['p.json']=json.dumps(data,sort_keys=True).encode()
    files['r.json']=json.dumps(ROOTS,sort_keys=True).encode()
    files['xnames.py']=(ROOT/'offnative/opacity.py').read_bytes()
    files['0.py']=b"import xnames; xnames.install('.')\nimport os\nos.environ['A0_ROOTS']='r.json'\nfrom offnative.bootstrap import main\nmain()\n"
    files['pins.json']=json.dumps(pins,sort_keys=True).encode()
    files,archive_pins=pack(files)
    files['out/ARCHIVE_TRANSPORT.json']=json.dumps(archive_pins,sort_keys=True).encode()
    dump(d/'ARCHIVE_TRANSPORT.json',archive_pins)
    receipt=packet(files,d/'packet.tar',config['token'])
    dump(d/'PACKET_PINS.json',pins)
    return receipt
