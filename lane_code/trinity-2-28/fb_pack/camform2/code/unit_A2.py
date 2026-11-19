"""Run focused camera, subset, and A2 compatibility tests on the A2 overlay."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'code/unit.py';source=p.read_text()
source=source.replace("tree=ROOT/'work/new'", "tree=ROOT/'work/newA2'").replace("work/unit_tmp", "work/unit_tmp_A2").replace("'tests.test_r1_subset']", "'tests.test_r1_subset','tests.test_r1_patch_a2']").replace("out/UNIT.json", "out/UNIT_A2.json").replace("code/unit.py'", "code/unit_A2.py'")
try:exec(compile(source,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
except SystemExit as e:code=e.code
p=ROOT/'out/UNIT_A2.json';v=json.loads(p.read_text());v['input_sha256'][str(Path(__file__))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();v['input_sha256'][str(ROOT/'work/newA2/tests/test_r1_patch_a2.py')]=hashlib.sha256((ROOT/'work/newA2/tests/test_r1_patch_a2.py').read_bytes()).hexdigest();p.write_text(json.dumps(v,indent=2)+'\n')
raise SystemExit(code)
