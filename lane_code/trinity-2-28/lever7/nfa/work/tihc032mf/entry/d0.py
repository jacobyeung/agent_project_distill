
import json, runpy, sys
sys.path[:0] = ['/scratch/jjyeung/orch_n30/lever7/nfa/ref/payload' + '/b', '/scratch/jjyeung/orch_n30/lever7/nfa/ref/payload' + '/tree', '/scratch/jjyeung/orch_n30/lever7/nfa/ref/payload']
from h1eval.h10 import launch
def maker(export, artifact, items, perception_factory=None, device=None):
    return lambda item: dict(text='<answer>A</answer>', finish='eos')
def main(argv):
    args = launch.parser().parse_args(argv)
    args.reader_entry = 'stub:maker'; args.reader_root = '/scratch/jjyeung/orch_n30/lever7/nfa/work/tihc032mf/entry/b'
    print(json.dumps(launch.run_types(args, make_real=maker)))
    return 0
launch.main = main
sys.argv = ['5.py', sys.argv[1]]
runpy.run_path('5.py', run_name='__main__')
