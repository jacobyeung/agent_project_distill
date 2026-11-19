"""Verify the sealed claimed-arm reader without loading weights or GPUs."""
from rl_on_n import provenance as P
from rl_on_n.serving import load_binding,default_binding,PAYLOAD,ROOT
P.sha(__file__)
settings=load_binding()
from parity_kit.common import policy
from rl_on_n.serving import call_caps
P.write(ROOT/'out/SERVING_CHECK.json',dict(status='BOUND_NOT_GPU_REPLAYED',binding=default_binding(),
    reader_root=str(PAYLOAD),settings=settings,decode_budget=policy().DECODE_BUDGET,
    caps=call_caps(),own_heads=['gravity','depth_for_scale'],
    command='PYTHONPATH=overlay python -B scripts/serving_check.py'))
print('Sealed A4 reader and settings: BOUND; GPU replay: NOT RUN')
