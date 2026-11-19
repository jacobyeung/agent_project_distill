from pathlib import Path
L=Path(__file__).resolve().parents[1]
source=Path('/scratch/jjyeung/orch_n30/so_xstore/in/tree21b/work/build21/native21.py').read_text()
body=source[source.index('from student_pilot.p3_provenance'):source.index('\ndef twins(')]
body=body.replace('torch.set_num_interop_threads(1)',"if torch.get_num_interop_threads()!=1:torch.set_num_interop_threads(1)")
header='''"""Tiny native mode-p fixture derived from build 21's native21 host/producer fixture.

The model/processor constructors and RGB are synthetic. Preparation, handover,
source authentication, filtering, routing composition and frame audits are real.
"""
from pathlib import Path
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch
import json, os, sys, sqlite3, tarfile, traceback, gzip
L=Path(os.environ['MODEP_FIXTURE_LANE'])
B=Path(os.environ['MODEP_FIXTURE_BUILD'])
O=Path(os.environ['MODEP_FIXTURE_OUTPUT'])
T=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(B),str(L/'work/build17'),str(L/'work/n1fix2')]

def guard(stage):
    print('FIXTURE_STAGE '+stage,flush=True)

def population(path,row,stream,check):
    counts={'pose':32,'vqa':32,'routing':32,'pointing':8}
    with path.open('w') as f:
        for i in range(counts[stream]):f.write(json.dumps(dict(row,qid=stream+str(i)))+'\\n')

def pose_manifests(root,row,make):
    return [make(root/('pose_source'+str(group)),
                 [dict(row,qid='pose'+str(group*4+i)) for i in range(4)],'pose','pose'+str(group))
            for group in range(8)]

'''
(L/'work/tree/tests/modep_native_fixture.py').write_text(header+body)
