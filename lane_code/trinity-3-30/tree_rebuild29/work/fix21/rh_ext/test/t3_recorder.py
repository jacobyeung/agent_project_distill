"""Test 3: if a config carried r2_persistence (a durable upload binding), sx hands persistence.upload the local
recorder, never the pinned uploader: no byte moves, four part records land under <sink>/up.
usage: t3_recorder.py <t2 out folder> <kit>; runs on test 2's sink (a second archive copy of its tiny state)."""
import base64, json, sys
from pathlib import Path
import sx
import launch_r2.persistence as P
out, kit = Path(sys.argv[1]), Path(sys.argv[2])
v = json.loads((kit / 'k/n.json').read_text()); job = json.loads(base64.b64decode(v['payload']))
sink = out / 'sink'
state = sorted(sink.glob('checkpoint_*'))[0]
pcfg = dict(recipe=job['recipe'], r2_identity=job['r2_identity'], checkpoint_disk_guard=job['checkpoint_disk_guard'],
            r1_training={}, output=str(sink),
            r2_persistence=dict(sessions=dict(path='/nonexistent/a15/sessions.json', sha256='0' * 64),
                                uploader=dict(path='/nonexistent/a15/uploader.py', sha256='0' * 64)))
r = P.upload(pcfg, state, 'checkpoint', uploader=sx.local_recorder(sink))
print(json.dumps(dict(durable=r['durable'], parts=[dict(name=p['name'], bytes=p['bytes'], generation=p['generation'], uri=p['uri']) for p in r['parts']],
                      archive=r['archive']['path'])))
