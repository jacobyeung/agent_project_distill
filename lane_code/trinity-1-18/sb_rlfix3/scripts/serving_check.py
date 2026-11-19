"""Verify the sealed claimed-arm reader without loading weights or GPUs."""
from types import SimpleNamespace
from rl_on_n import provenance as P
from rl_on_n.serving import load_binding,default_binding,reader_runtime,perception_kwargs,PAYLOAD,ROOT
P.sha(__file__)
settings=load_binding()
from parity_kit.common import policy
from rl_on_n.serving import call_caps
# Construct A4's perception with build_reader's settings; G3T loads lazily and SAM 3 is omitted.
with reader_runtime():
    from e2e_reader import real
    from e2e_reader.stage1 import OwnDepthScale
    perception=real.real_perception(SimpleNamespace(),device='cpu',**perception_kwargs())
    own_heads=[name for name,own in (('gravity',perception.gravity is real.own_gravity),
                                    ('depth_for_scale',isinstance(perception.scale_head,OwnDepthScale))) if own]
for name in ('real.py','stage1.py'):P.sha(PAYLOAD/'b/e2e_reader'/name)
if settings['arm']!='own_depth' or own_heads!=['gravity','depth_for_scale']:
    raise ValueError('Claimed arm no longer uses own gravity and own depth for scale: '+str(own_heads))
P.write(ROOT/'out/SERVING_CHECK.json',dict(status='BOUND_NOT_GPU_REPLAYED',binding=default_binding(),
    reader_root=str(PAYLOAD),settings=settings,decode_budget=policy().DECODE_BUDGET,
    caps=call_caps(),own_heads=own_heads,
    own_heads_source='Perception built by sealed real_perception with build_reader settings: gravity=real.own_gravity, scale_head=stage1.OwnDepthScale',
    command='PYTHONPATH=overlay python -B scripts/serving_check.py'))
print('Sealed A4 reader and settings: BOUND; own heads',own_heads,'; GPU replay: NOT RUN')
