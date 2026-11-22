"""Fixture job folder for the resume test (Trinity CPU only): <run>/c.json (the kit's real source seal of tree
db42866f, so authenticate() runs for real), <run>/p/hr.json and <run>/p/pr.json (stand-ins for the host receipt and
the prepared receipt whose pin is cfg['preparation']) and <run>/v.json, the job config. The config carries N's own
schedule keys, recipe, disk policy and r2_identity from kit k/n.json, so recipe_for and the persistence plan see
N's numbers; paths are written under the fixed namespace <ns>, which each phase binds to its own run folder,
as the kit binds Q_ROOT at Q_NS.
usage: fx_job.py <work> <run folder> <ns> [host receipt variant]"""
import json, sys
from pathlib import Path
W, run, ns = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
variant = sys.argv[4] if len(sys.argv) > 4 else 'same'
sys.path.insert(0, str(W / 'tree'))
from student_pilot.p3_provenance import write, sha256
n = json.loads((W / 'dec/n.json').read_text())
seal = json.loads((W / 'dec/7.json').read_text())
seal['archive']['path'] = str(W / 'kit_orig/n_go' / seal['archive']['path'])
run.mkdir(parents=True)
write(run / 'c.json', seal)
write(run / 'p/hr.json', dict(status='PASS', fixture=True, variant=variant))
pin = lambda rel: dict(path=ns + '/' + rel, sha256=sha256(run / rel))
r1 = dict(fixture='persistence reads only the presence of this key', host_receipt=pin('p/hr.json'))
write(run / 'p/pr.json', dict(schema='c1-preparation-v1', fixture=True, r1_training=r1))
keys = ['training_mode', 'mix', 'world_size', 'recipe', 'weights', 'schedule', 'scheduled_sampling',
        'reference_world_size', 'steps', 'milestones', 'checkpoint_disk_guard', 'r2_identity', 'trace_program_version']
cfg = {k: n[k] for k in keys if k in n}
cfg.update(schema='rs36-fixture-job', base_identity='fixture', code=pin('c.json'), preparation=pin('p/pr.json'),
           output=ns + '/p/q/r', r1_training=r1)
write(run / 'v.json', cfg)
print('fixture job', run, 'variant', variant)
