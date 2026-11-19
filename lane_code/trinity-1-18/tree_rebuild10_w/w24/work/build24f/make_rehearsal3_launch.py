"""Select the regenerated fixture without editing a native or kit file."""
from pathlib import Path
import json
D=Path(__file__).resolve().parent
names=('rehearsal_runner.py','rehearsal_boundary.py','rehearsal_copier.py',
       'check_rehearsal.py','rehearsal_repro.py','go_rehearsal.sh')
for name in names:
    path=D/name
    source=path.read_text().replace("D/'rehearsal2'","D/'rehearsal3'").replace('build24f/rehearsal2/','build24f/rehearsal3/')
    if name=='rehearsal_boundary.py':
        source=source.replace('from rehearsal_model import install\ninstall(N.C)',
            'from rehearsal_model import install, install_preparation\ninstall(N.C)\ninstall_preparation()')
        source=source.replace("D/'rehearsal2/tmp'","D/'rehearsal3/tmp'")
    if name=='rehearsal_runner.py':
        source=source.replace("cfg=J.load(L/'work/build24d/go/input2.json')","cfg=J.load(root/'seed.json')")
    path.write_text(source)
path=D/'REHEARSAL_OVERRIDES.json';value=json.loads(path.read_text())
value['model_boundary']=dict(tie_word_embeddings=False,
    text_config_tie_word_embeddings=False,
    base_manifest=str(D/'rehearsal3/model.json'),
    construction='Untied base and donor before native export; native receipt and exact inventory load',
    preparation='Synthetic pose settings supply the untied base manifest before native preparation validates it',
    post_load_topology_change=False)
value['copier']['target']='rehearsal3/target'
path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
print('Selected rehearsal3 for preparation, reproduction, training, copier and checker.')
