"""Worker-side stub: argv is -B -I 5.py NN.json, as runner.commands builds it. Only the reader is a
stub; it fails the way the served type-3 ground call fails on CPU (174264), and answers other items."""
import json, runpy, sys, time
P = '/scratch/jjyeung/orch_n30/lever7/nfa/ref/payload'
sys.path[:0] = [P + '/b', P + '/tree', P]
from h1eval.h10 import launch, parity_adapter
def map_items(items, settings, *, name='devs1_routed'):
    return {r['id']: dict(r) for r in items}, dict(sha256='0' * 64)
parity_adapter.map_items = map_items
def maker(export, artifact, items, perception_factory=None, device=None, settings=None):
    assert device == "cpu"
    time.sleep(3.0)  # the served load takes minutes between the binding and the first item
    def gen(item):
        if item['question_type'] == 'object_abs_distance':
            raise RuntimeError('No CUDA GPUs are available')
        time.sleep(1.0)
        return dict(text='<answer>A</answer>', finish='eos', timings=dict(total_s=1.0), calls=dict(records=[]))
    return gen
kept = launch.run_types
launch.run_types = lambda args, **k: kept(args, make_real=maker)
argv = [a for a in sys.argv[1:] if a not in ('-B', '-I')]
assert argv[0] == '5.py' and len(argv) == 2, argv
sys.argv = argv
runpy.run_path('5.py', run_name='__main__')
