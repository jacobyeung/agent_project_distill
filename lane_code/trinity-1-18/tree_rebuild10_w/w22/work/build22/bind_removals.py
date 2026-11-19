from pathlib import Path
import json,sys,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build22';I=D/'inputs';I.mkdir(exist_ok=True)
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/build21')]
import joblib as J
inventory=J.load(D/'INVENTORY.json');pin=inventory['V7_ROWS_NAMING_REMOVE.json'];src=Path(pin['path'])
p=I/'naming_remove.json';p.write_bytes(src.read_bytes());assert J.sha(p)==pin['sha256']
cfg=J.load(L/'work/build21/inputs/config.json')
cfg['remove_files'].append(dict(path=str(p),sha256=J.sha(p)))
cfg['r1_training']['launch22']=dict(removal_order=[x['sha256'] for x in cfg['remove_files']])
J.write(I/'config.json',cfg)
J.write(D/'REMOVALS.json',dict(source=pin,bound=cfg['remove_files'][-1],order=cfg['r1_training']['launch22']['removal_order']))
