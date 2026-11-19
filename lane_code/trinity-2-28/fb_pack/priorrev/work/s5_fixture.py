"""Plan bytes for prior2b's fixture binding under one tree. usage: s5_fixture.py {base|new}"""
import hashlib, json, sys
from pathlib import Path

W = Path(__file__).resolve().parent
sys.path.insert(0, str(W/sys.argv[1]))
from student_pilot.p3_provenance import load, pinned
from student_pilot.r1_mix import plans
from student_pilot.r1_training import STREAMS

fx = json.loads(Path('/scratch/jjyeung/orch_n30/fb_pack/prior2b/work/fixture/FIXTURE.json').read_text())
binding = fx['binding']
card, indices = load(pinned(binding['card'])), load(pinned(binding['indices']))
counts = {s: sum(len(indices['cells'][c['type']]) for c in card['cells'] if c['stream'] == s) for s in STREAMS}
plan = [[[s, list(o)] for s, o in p] for p in plans(binding, counts, 1000)]
raw = json.dumps(plan, separators=(',', ':')).encode()
print(json.dumps(dict(tree=sys.argv[1], counts=counts, slots=sum(len(o) for p in plan for _, o in p),
                      plan_sha256=hashlib.sha256(raw).hexdigest())))
