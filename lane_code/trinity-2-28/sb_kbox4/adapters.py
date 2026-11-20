"""Import unedited vendor functions with explicit, recorded workspace bindings."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parent
TREE = Path('/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449')
READER = Path('/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook')
sys.path[:0] = [str(TREE), str(ROOT/'vendor')]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def dependencies():
    package = types.ModuleType('kit_reader')
    package.__path__ = [str(ROOT/'vendor')]
    sys.modules['kit_reader'] = package
    G = load('kit_reader.grounding', ROOT/'vendor/grounding.py')
    load('kit_reader.geometry', ROOT/'vendor/geometry.py')
    # Copy only declarations; do not execute the harness's inventory, writer,
    # global audit installation, environment changes, or hardcoded root assertion.
    import numpy as np
    from collections import defaultdict
    from student_pilot import camera_targets, ground_lifting, tower_scale_rule
    from student_pilot.ground_profiles import load_geometry
    from student_pilot.scene_state import FrameMap
    from trace_format.ground_v313 import Session
    from trace_format import room_v314 as room
    from rk import programs
    import io, time, math, re, warnings
    h = types.ModuleType('kit_harness')
    h.__dict__.update(globals())
    h.__dict__.update(locals())
    h.__dict__.update(ROOT=ROOT, OUT=ROOT/'work', TREE=TREE, TIMINGS=defaultdict(float),
                      __file__=str(ROOT/'vendor/harness.py'))
    tree = ast.parse((ROOT/'vendor/harness.py').read_text())
    declarations = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    exec(compile(ast.Module(declarations, []), str(ROOT/'vendor/harness.py'), 'exec'), h.__dict__)
    l = types.ModuleType('kit_lift')
    l.__dict__.update(np=np, Session=Session, ground_lifting=ground_lifting,
                      lift_plain=G.lift_plain, mask_pixels=G.mask_pixels, MinAreaBoxProvider=G.MinAreaBoxProvider)
    tree = ast.parse((ROOT/'vendor/lift_price.py').read_text())
    declarations = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    exec(compile(ast.Module(declarations, []), str(ROOT/'vendor/lift_price.py'), 'exec'), l.__dict__)
    return h, l, G


def reviewed_loader():
    from types import FunctionType, SimpleNamespace
    from student_pilot import geometry_profiles as GP
    from student_pilot.ground_profiles import load_geometry
    import gravity_guard
    class ReviewedContract(GP.GeometryContract):
        pass
    recorder = gravity_guard.Recorder()
    gravity_guard.install(SimpleNamespace(GeometryContract=ReviewedContract, GeometryError=GP.GeometryError), recorder)
    def bind(fn, **replacements):
        return FunctionType(fn.__code__, dict(fn.__globals__, **replacements), fn.__name__, fn.__defaults__, fn.__closure__)
    loader = bind(load_geometry,
                  legacy_from_heads=bind(GP.legacy_from_heads, GeometryContract=ReviewedContract),
                  scaled_from_heads=bind(GP.scaled_from_heads, GeometryContract=ReviewedContract))
    return loader, gravity_guard, recorder


def source_hashes():
    paths = [ROOT/'KIT_SPEC_box_ladder_k1.md', ROOT/'HEAD_ACCURACY_DESIGN_20261119.md']
    paths += [ROOT/'SPEC_APPLIED.md']
    paths += list((ROOT/'vendor').glob('*.py')) + list(ROOT.glob('*.py')) + [ROOT/'run.sh']
    for module in list(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path and str(path).startswith((str(TREE),str(READER))) and str(path).endswith('.py'):
            paths.append(Path(path))
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}
