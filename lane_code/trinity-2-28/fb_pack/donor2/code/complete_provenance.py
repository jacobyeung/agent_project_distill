from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1];O=W/'out'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# The live overlay adds one host test beyond the base manifest used by the suite runner.
seal_path=Path('/scratch/jjyeung/orch_n30/tree_rebuild15_w24l/out24j/TREE24J_SEAL.json');seal=json.loads(seal_path.read_text())
for label in ('live_base','live'):
 p=O/('FOCUSED_'+label.upper()+'.json');r=json.loads(p.read_text());q=W/'work'/label/'tests/test_host24j.py'
 assert sha(q)==seal['files']['tests/test_host24j.py']
 r['input_sha256'].update({str(q):sha(q),str(seal_path):sha(seal_path),str(Path(__file__).resolve()):sha(__file__)})
 r['command']+='; python code/complete_provenance.py'
 r['additional_source_check']='Host test matches the authenticated live seal before staging and after testing.'
 p.write_text(json.dumps(r,indent=2)+'\n')
