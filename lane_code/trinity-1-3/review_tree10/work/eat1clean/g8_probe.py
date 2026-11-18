"""Reviewer probes of the G8 fixed_math role (clean v7 copy + builder patch)."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import torch
from torch import nn
from eat1.artifact import Artifact, write_manifest
from eat1 import run as R, scan as S

def make(persistent=True, extra_files=None, key='math.scale', declare=None, file_in_manifest=True):
    class Math(nn.Module):
        def __init__(self):
            super().__init__()
            self.register_buffer('scale', torch.tensor(2., dtype=torch.float64), persistent=persistent)
        def forward(self, v):
            return v * self.scale
    model = nn.Module(); model.math = Math()
    root = Path(tempfile.mkdtemp())
    torch.save({'math.scale': torch.tensor(2., dtype=torch.float64)}, root/'buffers.pt')
    files = {'buffers.pt': 'head'} if file_in_manifest else {}
    (root/'other.pt').write_bytes(b'x'); files['other.pt'] = 'head'
    write_manifest(root/'ARTIFACT.json', root, files, {
        'math': dict(role='fixed_math', inputs=['v'], outputs=['s'],
                     buffers=declare if declare is not None else {'scale': dict(file='buffers.pt', key=key)})})
    return model, root

out = {}
def probe(name, fn):
    try:
        out[name] = fn()
    except Exception as e:
        out[name] = 'RAISE ' + type(e).__name__ + ': ' + str(e)

def mutate_after_check():
    m, root = make(); a = Artifact(root/'ARTIFACT.json'); a.module_roles(m)
    m.math.scale.fill_(7.)   # reader changes the buffer after resolution, e.g. during generate()
    return dict(a1=R.judge_a1([], a, [])['status'], output=float(m(torch.tensor(1.)) if False else m.math(torch.tensor(1.))))
probe('buffer_mutated_after_resolution', mutate_after_check)

def nonpersistent():
    m, root = make(persistent=False); a = Artifact(root/'ARTIFACT.json'); return a.module_roles(m) and 'accepted'
probe('nonpersistent_buffer', nonpersistent)

def undeclared_extra_buffer():
    m, root = make(); m.math.register_buffer('hidden', torch.tensor(500.))
    a = Artifact(root/'ARTIFACT.json'); return a.module_roles(m) and 'accepted'
probe('undeclared_extra_buffer', undeclared_extra_buffer)

def buffer_file_not_listed():
    m, root = make(file_in_manifest=False); a = Artifact(root/'ARTIFACT.json'); return a.module_roles(m) and 'accepted'
probe('buffer_file_not_in_manifest', buffer_file_not_listed)

def dtype_cast():
    m, root = make(); m.math.scale.data = m.math.scale.data.float(); a = Artifact(root/'ARTIFACT.json'); a.module_roles(m)
    return R.judge_a1([], a, [])['status']
probe('buffer_dtype_cast_bf16_style', dtype_cast)

def submodule_param():
    m, root = make(); m.math.inner = nn.Linear(1, 1); a = Artifact(root/'ARTIFACT.json'); return a.module_roles(m) and 'accepted'
probe('nested_parameter', submodule_param)

def frozen_param_as_buffer_name():
    m, root = make(); m.math.extra = nn.Parameter(torch.ones(1), requires_grad=False)
    a = Artifact(root/'ARTIFACT.json'); return a.module_roles(m) and 'accepted'
probe('frozen_parameter', frozen_param_as_buffer_name)

def no_inputs_declared():
    m, root = make(); d = json.loads((root/'ARTIFACT.json').read_text()); d['modules']['math']['inputs'] = []
    (root/'ARTIFACT.json').write_text(json.dumps(d)); return Artifact(root/'ARTIFACT.json') and 'accepted'
probe('empty_inputs', no_inputs_declared)

def py_constant_in_forward():
    p = Path(tempfile.mkdtemp())/'fm.py'
    p.write_text('import torch\nclass M(torch.nn.Module):\n    def forward(self, x):\n        return x * 500.0\n')
    return sorted({f['rule'] for f in S.scan([p])[0]})
probe('constant_inside_fixed_math_forward_static', py_constant_in_forward)

def status_in_formatter_name():
    p = Path(tempfile.mkdtemp())/'h.py'
    p.write_text("def format_status(x):\n    return 'box unavailable'\n")
    return sorted({f['rule'] for f in S.scan([p])[0]})
probe('status_literal_outside_registered_formatter', status_in_formatter_name)

print(json.dumps(out, indent=1))
