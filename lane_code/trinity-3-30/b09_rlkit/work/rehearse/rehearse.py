import json, shutil, sys
from pathlib import Path
from rltests.fixture import FixtureBackend, prompt, sampler_config
from rlkit import sampler
from rlkit.towerfactory import s1_grounding
out = Path('/scratch/jjyeung/orch_n30/b09_rlkit/work/rehearse/run')
assert not out.exists(), 'fresh dir'
prompts = [prompt('p1'), prompt('p2'), prompt('p3', qtype='counting')]
Path('/scratch/jjyeung/orch_n30/b09_rlkit/work/rehearse/pool.jsonl').write_text(''.join(json.dumps(p) + '\n' for p in prompts))
be = FixtureBackend()
print(sampler.run(sampler_config(), prompts, out, backend=be))
print('factory on a non-3.14 model:', s1_grounding(be.model, be.processor, prompts[0], {}, cache=None, key='k', backend_cfg={}))
