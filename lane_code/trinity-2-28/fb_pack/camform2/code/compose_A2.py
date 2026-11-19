"""Run the declaration harness on the authenticated A2 trees."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'code/compose_declaration.py'
source=p.read_text().replace("TREE=ROOT/'work/new'", "TREE=ROOT/'work/newA2'")
source=source.replace("code/compose_declaration.py '+label", "code/compose_A2.py'")
sys.argv=[str(p),'A2'];exec(compile(source,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
p=ROOT/'out/COMPOSITION_A2.json';v=json.loads(p.read_text());v['input_sha256'][str(Path(__file__))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();v['input_sha256'][str(ROOT/'out/A2_PACKAGING.json')]=hashlib.sha256((ROOT/'out/A2_PACKAGING.json').read_bytes()).hexdigest();p.write_text(json.dumps(v,indent=2)+'\n')
