"""Reconstruct authenticated bytes with their sealed producer."""
from pathlib import Path
from copy import deepcopy
import json
import subprocess
import sys
import tarfile
import os
import importlib
import importlib.machinery
import importlib.util
import time

DB = "4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84"
TREE = "e5be8157d855b4c9f611876b7fde5d0c7d8bd11def319e15c00e37daef2c3536"


def selection_check(selection, recipe):
    expected, actual = recipe["pool_selection_counts"], selection["sources"]
    fields = ("status", "reason", "retained", "per_type")
    for name in sorted(set(expected) | set(actual)):
        if (name not in expected or name not in actual or
                {k: actual[name][k] for k in fields if k in actual[name]} !=
                {k: expected[name][k] for k in fields if k in expected[name]}):
            raise ValueError("R1_RECONSTRUCTION_SELECTION_DIFFERS:"+name)


def statuses(actual, expected):
    for name in sorted(set(actual) | set(expected)):
        if (name not in actual or name not in expected or
                actual[name].get("status") != expected[name].get("status")):
            raise ValueError("R1_ROUTING_SOURCE_STATUS_DIFFERS:"+name)


def routing_status(cfg):
    from student_pilot.p3_provenance import load, pinned
    if not cfg.get("s1_routing"):
        return
    p = load(pinned(cfg["r1_training"]["p_run"]["config"]))
    expected = load(pinned(p["s1_routing"]["selection"]))
    if p["s1_routing"]["selection"]["sha256"] != "5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af":
        raise ValueError("R1_ROUTING_REFERENCE_DIFFERS")
    statuses(load(pinned(cfg["s1_routing"]["selection"]))["sources"], expected["sources"])


def mount_inputs(p, recipe):
    from student_pilot.p3_provenance import load, pinned
    mounts = {}
    def add(pin):
        target = Path(pin["path"])
        if not target.is_absolute() or ".." in target.parts:
            raise ValueError("R1_RECONSTRUCTION_PATH_INVALID")
        source = str(pinned(pin))
        item = dict(source=source, sha256=pin["sha256"])
        if str(target) in mounts and mounts[str(target)] != item:
            raise ValueError("R1_RECONSTRUCTION_PATH_CONFLICT")
        mounts[str(target)] = item
    def visit(value):
        if isinstance(value, dict):
            if "path" in value and "sha256" in value:
                add({k:value[k] for k in ("path", "sha256")})
            else:
                for v in value.values(): visit(v)
        elif isinstance(value, list):
            for v in value: visit(v)
    for key in ("remove_files", "dev_scene_exclusions", "benchmark_scene_exclusions", "s1_route_policy"):
        visit(p.get(key))
    for key in ("inputs", "legacy", "division", "base_model"):
        visit(recipe[key])
    for h, path in recipe["inputs"].get("catalog", {}).items():
        add(dict(path=path, sha256=h))
    legacy = load(pinned(recipe["legacy"]))
    visit({k:legacy[k] for k in ("database", "division")})
    selection = load(pinned(recipe["inputs"]["selection"]))
    selection_check(selection, recipe)
    visit(selection["manifest"])
    visit(selection["remove_files"])
    visit(selection.get("tokenizer"))
    for value in selection["sources"].values():
        if value["status"] == "ELIGIBLE":
            visit({k:value[k] for k in ("source", "selection")})
    manifest = load(pinned(selection["manifest"]))
    for value in manifest["exclusions"].values():
        if not isinstance(value, dict): continue
        for key in ("list", "withhold", "v2"):
            if key in value: add(dict(path=value[key], sha256=value[key+"_sha256"]))
    model = load(pinned(recipe["base_model"]))
    for name, h in model["files"].items():
        if name.endswith((".json", ".txt", ".jinja", ".model")):
            add(dict(path=str(Path(model["root"])/name), sha256=h))
    return mounts



def environment():
    import site
    # Capture the interpreter's effective paths, including overlays added by its
    # launcher. The active source tree and kit directory are code, not sites.
    from student_pilot import p3_provenance
    code = Path(p3_provenance.__file__).resolve().parents[1]
    helper = Path(__file__).resolve().parent
    launcher = Path(sys.argv[0]).resolve().parent
    paths = []
    for value in list(sys.path) + site.getsitepackages():
        if not value:
            continue
        path = Path(value).absolute()
        if path.resolve() in (code, helper, launcher) or not path.exists():
            continue
        if str(path) not in paths:
            paths.append(str(path))
    binds = []
    for value in [sys.base_prefix, sys.prefix, str(Path(sys.executable).resolve().parent.parent)] + paths:
        if value not in binds and Path(value).exists():
            binds.append(value)
    return dict(paths=paths, binds=binds, executable=sys.executable)


def tree_names(tree):
    names = set()
    for p in Path(tree).iterdir():
        if p.is_file() and p.suffix == ".py":
            names.add(p.stem)
        elif p.is_dir() and any(p.rglob("*.py")):
            names.add(p.name)
    return sorted(names)


def import_probe(tree, paths, modules):
    tree = Path(tree).resolve()
    names = set(tree_names(tree))
    for name in sorted(names):
        for path in paths:
            if Path(path).resolve() == tree:
                continue
            if importlib.machinery.PathFinder.find_spec(name, [path]) is not None:
                raise ValueError("R1_RECONSTRUCTION_MODULE_SHADOWED:"+name)
        loaded = importlib.util.find_spec(name)
        if loaded is not None and loaded.origin is not None:
            if not Path(loaded.origin).resolve().is_relative_to(tree):
                raise ValueError("R1_RECONSTRUCTION_MODULE_SHADOWED:"+name)
    # No site.addsitedir: .pth startup hooks must not mutate the sealed producer.
    sys.path[:] = [str(tree)] + [p for p in paths if Path(p).resolve() != tree]
    importlib.invalidate_caches()
    for name in modules:
        try:
            spec = importlib.util.find_spec(name)
        except Exception as error:
            missing = (error.name if isinstance(error, ImportError) else None) or name
            raise ValueError("R1_RECONSTRUCTION_IMPORT_MISSING:"+missing) from error
        if spec is None:
            raise ValueError("R1_RECONSTRUCTION_IMPORT_MISSING:"+name)
    result = {}
    for name, module in load_modules():
        location = getattr(module, "__file__") if hasattr(module, "__file__") else None
        version = getattr(module, "__version__") if hasattr(module, "__version__") else None
        result[name] = dict(path=location, version=version)
        if name.split(".")[0] in names:
            places = list(getattr(module, "__path__")) if hasattr(module, "__path__") else []
            if location:
                places.append(location)
            if not places or any(not Path(p).resolve().is_relative_to(tree) for p in places):
                raise ValueError("R1_RECONSTRUCTION_MODULE_SHADOWED:"+name.split(".")[0])
    return result



def load_modules():
    names = probe_modules()
    current = names[0]
    try:
        current = names[0]
        import PIL as q0
        yield current, q0
        current = names[1]
        import generator.derivgen_v7.derivgen as q1
        yield current, q1
        current = names[2]
        import generator.derivgen_v7.derivgen.box_v313 as q2
        yield current, q2
        current = names[3]
        import generator.derivgen_v7.derivgen.calculator as q3
        yield current, q3
        current = names[4]
        import generator.derivgen_v7.derivgen.gaps_v314 as q4
        yield current, q4
        current = names[5]
        import generator.derivgen_v7.derivgen.ground_v312 as q5
        yield current, q5
        current = names[6]
        import generator.derivgen_v7.derivgen.ground_v312_balance as q6
        yield current, q6
        current = names[7]
        import generator.derivgen_v7.derivgen.ground_v312_degenerate as q7
        yield current, q7
        current = names[8]
        import generator.derivgen_v7.derivgen.ground_v312_io as q8
        yield current, q8
        current = names[9]
        import generator.derivgen_v7.derivgen.ground_v312_quality as q9
        yield current, q9
        current = names[10]
        import generator.derivgen_v7.derivgen.ground_v312_tokens as q10
        yield current, q10
        current = names[11]
        import generator.derivgen_v7.derivgen.ground_v313 as q11
        yield current, q11
        current = names[12]
        import generator.derivgen_v7.derivgen.ground_v313_distance as q12
        yield current, q12
        current = names[13]
        import generator.derivgen_v7.derivgen.ground_v313_tokens as q13
        yield current, q13
        current = names[14]
        import generator.derivgen_v7.derivgen.instance_policy314 as q14
        yield current, q14
        current = names[15]
        import generator.derivgen_v7.derivgen.paraphrase as q15
        yield current, q15
        current = names[16]
        import generator.derivgen_v7.derivgen.room_rows_v314 as q16
        yield current, q16
        current = names[17]
        import generator.derivgen_v7.derivgen.room_v314 as q17
        yield current, q17
        current = names[18]
        import launch_s1.b.q0 as q18
        yield current, q18
        current = names[19]
        import numpy as q19
        yield current, q19
        current = names[20]
        import scipy as q20
        yield current, q20
        current = names[21]
        import scipy.spatial.distance as q21
        yield current, q21
        current = names[22]
        import scipy.spatial.transform as q22
        yield current, q22
        current = names[23]
        import student_pilot as q23
        yield current, q23
        current = names[24]
        import student_pilot.auxiliary_config as q24
        yield current, q24
        current = names[25]
        import student_pilot.auxiliary_losses as q25
        yield current, q25
        current = names[26]
        import student_pilot.auxiliary_reason as q26
        yield current, q26
        current = names[27]
        import student_pilot.batches as q27
        yield current, q27
        current = names[28]
        import student_pilot.c1_pose_mix as q28
        yield current, q28
        current = names[29]
        import student_pilot.camera_config as q29
        yield current, q29
        current = names[30]
        import student_pilot.camera_head as q30
        yield current, q30
        current = names[31]
        import student_pilot.camera_targets as q31
        yield current, q31
        current = names[32]
        import student_pilot.carrier_c1 as q32
        yield current, q32
        current = names[33]
        import student_pilot.carrier_c1_data as q33
        yield current, q33
        current = names[34]
        import student_pilot.carrier_c1_routing as q34
        yield current, q34
        current = names[35]
        import student_pilot.carrier_c1_run as q35
        yield current, q35
        current = names[36]
        import student_pilot.carrier_c1_sweep as q36
        yield current, q36
        current = names[37]
        import student_pilot.common as q37
        yield current, q37
        current = names[38]
        import student_pilot.decoupled_resume as q38
        yield current, q38
        current = names[39]
        import student_pilot.decoupled_v as q39
        yield current, q39
        current = names[40]
        import student_pilot.decoupled_v_run as q40
        yield current, q40
        current = names[41]
        import student_pilot.decoupled_vc as q41
        yield current, q41
        current = names[42]
        import student_pilot.full_ft as q42
        yield current, q42
        current = names[43]
        import student_pilot.geometry_input as q43
        yield current, q43
        current = names[44]
        import student_pilot.ground_rows as q44
        yield current, q44
        current = names[45]
        import student_pilot.ground_tokens as q45
        yield current, q45
        current = names[46]
        import student_pilot.head_programs as q46
        yield current, q46
        current = names[47]
        import student_pilot.mdg_decode_tokens as q47
        yield current, q47
        current = names[48]
        import student_pilot.next_gpu_check as q48
        yield current, q48
        current = names[49]
        import student_pilot.orchard_paths as q49
        yield current, q49
        current = names[50]
        import student_pilot.p3_geometry as q50
        yield current, q50
        current = names[51]
        import student_pilot.p3_grammar as q51
        yield current, q51
        current = names[52]
        import student_pilot.p3_heads as q52
        yield current, q52
        current = names[53]
        import student_pilot.p3_printed_calculator as q53
        yield current, q53
        current = names[54]
        import student_pilot.p3_printed_calculator_v2 as q54
        yield current, q54
        current = names[55]
        import student_pilot.p3_provenance as q55
        yield current, q55
        current = names[56]
        import student_pilot.point_depth_head as q56
        yield current, q56
        current = names[57]
        import student_pilot.readout_geometry as q57
        yield current, q57
        current = names[58]
        import student_pilot.rehearsal as q58
        yield current, q58
        current = names[59]
        import student_pilot.row_removals as q59
        yield current, q59
        current = names[60]
        import student_pilot.s1_exclusions as q60
        yield current, q60
        current = names[61]
        import student_pilot.s1_pool as q61
        yield current, q61
        current = names[62]
        import student_pilot.s1_pool_relocate as q62
        yield current, q62
        current = names[63]
        import student_pilot.s1_route_policy as q63
        yield current, q63
        current = names[64]
        import student_pilot.s1_routing as q64
        yield current, q64
        current = names[65]
        import student_pilot.s1_scene_census as q65
        yield current, q65
        current = names[66]
        import student_pilot.students as q66
        yield current, q66
        current = names[67]
        import student_pilot.trace_contract as q67
        yield current, q67
        current = names[68]
        import tokenizers as q68
        yield current, q68
        current = names[69]
        import torch as q69
        yield current, q69
        current = names[70]
        import trace_format as q70
        yield current, q70
        current = names[71]
        import trace_format.calculator as q71
        yield current, q71
        current = names[72]
        import trace_format.ground_v312 as q72
        yield current, q72
        current = names[73]
        import trace_format.room_v314 as q73
        yield current, q73
        current = names[74]
        import transformers as q74
        q74.AutoProcessor
        q74.AddedToken
        yield current, q74
    except Exception as error:
        missing = (error.name if isinstance(error, ImportError) else None) or current
        raise ValueError("R1_RECONSTRUCTION_IMPORT_MISSING:"+missing) from error


def probe_modules():
    import base64
    return json.loads(base64.b64decode("WyJQSUwiLCAiZ2VuZXJhdG9yLmRlcml2Z2VuX3Y3LmRlcml2Z2VuIiwgImdlbmVyYXRvci5kZXJpdmdlbl92Ny5kZXJpdmdlbi5ib3hfdjMxMyIsICJnZW5lcmF0b3IuZGVyaXZnZW5fdjcuZGVyaXZnZW4uY2FsY3VsYXRvciIsICJnZW5lcmF0b3IuZGVyaXZnZW5fdjcuZGVyaXZnZW4uZ2Fwc192MzE0IiwgImdlbmVyYXRvci5kZXJpdmdlbl92Ny5kZXJpdmdlbi5ncm91bmRfdjMxMiIsICJnZW5lcmF0b3IuZGVyaXZnZW5fdjcuZGVyaXZnZW4uZ3JvdW5kX3YzMTJfYmFsYW5jZSIsICJnZW5lcmF0b3IuZGVyaXZnZW5fdjcuZGVyaXZnZW4uZ3JvdW5kX3YzMTJfZGVnZW5lcmF0ZSIsICJnZW5lcmF0b3IuZGVyaXZnZW5fdjcuZGVyaXZnZW4uZ3JvdW5kX3YzMTJfaW8iLCAiZ2VuZXJhdG9yLmRlcml2Z2VuX3Y3LmRlcml2Z2VuLmdyb3VuZF92MzEyX3F1YWxpdHkiLCAiZ2VuZXJhdG9yLmRlcml2Z2VuX3Y3LmRlcml2Z2VuLmdyb3VuZF92MzEyX3Rva2VucyIsICJnZW5lcmF0b3IuZGVyaXZnZW5fdjcuZGVyaXZnZW4uZ3JvdW5kX3YzMTMiLCAiZ2VuZXJhdG9yLmRlcml2Z2VuX3Y3LmRlcml2Z2VuLmdyb3VuZF92MzEzX2Rpc3RhbmNlIiwgImdlbmVyYXRvci5kZXJpdmdlbl92Ny5kZXJpdmdlbi5ncm91bmRfdjMxM190b2tlbnMiLCAiZ2VuZXJhdG9yLmRlcml2Z2VuX3Y3LmRlcml2Z2VuLmluc3RhbmNlX3BvbGljeTMxNCIsICJnZW5lcmF0b3IuZGVyaXZnZW5fdjcuZGVyaXZnZW4ucGFyYXBocmFzZSIsICJnZW5lcmF0b3IuZGVyaXZnZW5fdjcuZGVyaXZnZW4ucm9vbV9yb3dzX3YzMTQiLCAiZ2VuZXJhdG9yLmRlcml2Z2VuX3Y3LmRlcml2Z2VuLnJvb21fdjMxNCIsICJsYXVuY2hfczEuYi5xMCIsICJudW1weSIsICJzY2lweSIsICJzY2lweS5zcGF0aWFsLmRpc3RhbmNlIiwgInNjaXB5LnNwYXRpYWwudHJhbnNmb3JtIiwgInN0dWRlbnRfcGlsb3QiLCAic3R1ZGVudF9waWxvdC5hdXhpbGlhcnlfY29uZmlnIiwgInN0dWRlbnRfcGlsb3QuYXV4aWxpYXJ5X2xvc3NlcyIsICJzdHVkZW50X3BpbG90LmF1eGlsaWFyeV9yZWFzb24iLCAic3R1ZGVudF9waWxvdC5iYXRjaGVzIiwgInN0dWRlbnRfcGlsb3QuYzFfcG9zZV9taXgiLCAic3R1ZGVudF9waWxvdC5jYW1lcmFfY29uZmlnIiwgInN0dWRlbnRfcGlsb3QuY2FtZXJhX2hlYWQiLCAic3R1ZGVudF9waWxvdC5jYW1lcmFfdGFyZ2V0cyIsICJzdHVkZW50X3BpbG90LmNhcnJpZXJfYzEiLCAic3R1ZGVudF9waWxvdC5jYXJyaWVyX2MxX2RhdGEiLCAic3R1ZGVudF9waWxvdC5jYXJyaWVyX2MxX3JvdXRpbmciLCAic3R1ZGVudF9waWxvdC5jYXJyaWVyX2MxX3J1biIsICJzdHVkZW50X3BpbG90LmNhcnJpZXJfYzFfc3dlZXAiLCAic3R1ZGVudF9waWxvdC5jb21tb24iLCAic3R1ZGVudF9waWxvdC5kZWNvdXBsZWRfcmVzdW1lIiwgInN0dWRlbnRfcGlsb3QuZGVjb3VwbGVkX3YiLCAic3R1ZGVudF9waWxvdC5kZWNvdXBsZWRfdl9ydW4iLCAic3R1ZGVudF9waWxvdC5kZWNvdXBsZWRfdmMiLCAic3R1ZGVudF9waWxvdC5mdWxsX2Z0IiwgInN0dWRlbnRfcGlsb3QuZ2VvbWV0cnlfaW5wdXQiLCAic3R1ZGVudF9waWxvdC5ncm91bmRfcm93cyIsICJzdHVkZW50X3BpbG90Lmdyb3VuZF90b2tlbnMiLCAic3R1ZGVudF9waWxvdC5oZWFkX3Byb2dyYW1zIiwgInN0dWRlbnRfcGlsb3QubWRnX2RlY29kZV90b2tlbnMiLCAic3R1ZGVudF9waWxvdC5uZXh0X2dwdV9jaGVjayIsICJzdHVkZW50X3BpbG90Lm9yY2hhcmRfcGF0aHMiLCAic3R1ZGVudF9waWxvdC5wM19nZW9tZXRyeSIsICJzdHVkZW50X3BpbG90LnAzX2dyYW1tYXIiLCAic3R1ZGVudF9waWxvdC5wM19oZWFkcyIsICJzdHVkZW50X3BpbG90LnAzX3ByaW50ZWRfY2FsY3VsYXRvciIsICJzdHVkZW50X3BpbG90LnAzX3ByaW50ZWRfY2FsY3VsYXRvcl92MiIsICJzdHVkZW50X3BpbG90LnAzX3Byb3ZlbmFuY2UiLCAic3R1ZGVudF9waWxvdC5wb2ludF9kZXB0aF9oZWFkIiwgInN0dWRlbnRfcGlsb3QucmVhZG91dF9nZW9tZXRyeSIsICJzdHVkZW50X3BpbG90LnJlaGVhcnNhbCIsICJzdHVkZW50X3BpbG90LnJvd19yZW1vdmFscyIsICJzdHVkZW50X3BpbG90LnMxX2V4Y2x1c2lvbnMiLCAic3R1ZGVudF9waWxvdC5zMV9wb29sIiwgInN0dWRlbnRfcGlsb3QuczFfcG9vbF9yZWxvY2F0ZSIsICJzdHVkZW50X3BpbG90LnMxX3JvdXRlX3BvbGljeSIsICJzdHVkZW50X3BpbG90LnMxX3JvdXRpbmciLCAic3R1ZGVudF9waWxvdC5zMV9zY2VuZV9jZW5zdXMiLCAic3R1ZGVudF9waWxvdC5zdHVkZW50cyIsICJzdHVkZW50X3BpbG90LnRyYWNlX2NvbnRyYWN0IiwgInRva2VuaXplcnMiLCAidG9yY2giLCAidHJhY2VfZm9ybWF0IiwgInRyYWNlX2Zvcm1hdC5jYWxjdWxhdG9yIiwgInRyYWNlX2Zvcm1hdC5ncm91bmRfdjMxMiIsICJ0cmFjZV9mb3JtYXQucm9vbV92MzE0IiwgInRyYW5zZm9ybWVycyJd"))


def command(root, control, tree, mounts, env=None):
    import shutil
    binary = shutil.which("bwrap")
    if not binary: raise ValueError("R1_BINARY_MISSING:bwrap")
    # Native rows retain logical provenance paths. Bind the staged bytes there
    # in a private view instead of rewriting the paths embedded in those rows.
    roots = sorted({"/"+Path(p).parts[1] for p in mounts if not p.startswith("/tmp/")})
    if any(p not in ("/scratch", "/lustre", "/home", "/data", "/data2", "/data3", "/project") for p in roots):
        raise ValueError("R1_RECONSTRUCTION_PATH_INVALID")
    cmd = [binary, "--ro-bind", "/usr", "/usr", "--symlink", "usr/bin", "/bin",
           "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64",
           "--ro-bind", "/etc", "/etc", "--dev-bind", "/dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp"]
    env = environment() if env is None else env
    cmd += ["--bind", str(root), str(root)]
    for p in [*env["binds"], Path(__file__).resolve().parent, Path(tree)]:
        cmd += ["--ro-bind", str(p), str(p)]
    for target, item in sorted(mounts.items()): cmd += ["--ro-bind", item["source"], target]
    cmd += ["--chdir", str(root), env["executable"], "-I", "-s", "-S", "-B", str(Path(__file__).resolve()), str(control), str(tree)]
    return cmd


def reconstruct(cfg, root, *, directory="base"):
    from z import load, checked, write
    from student_pilot.p3_provenance import pinned, file_pin
    from student_pilot.source_seal import check_archive, inventory
    root = Path(root)
    p = load(pinned(cfg["r1_training"]["p_run"]["config"]))
    pin = p["streams"]["routing"]
    if pin["sha256"] != "ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984":
        raise ValueError("P_TRAINED_ROUTING_PIN_DIFFERS")
    receipt = load(pinned(pin))
    if receipt["database"]["sha256"] != DB:
        raise ValueError("P_TRAINED_ROUTING_DATABASE_DIFFERS")
    recipe = load(pinned(receipt["materialization"]))
    selection_check(load(pinned(recipe["inputs"]["selection"])), recipe)
    seal = load(pinned(p["code"]))
    tree_pin = cfg["r1_training"]["p_tree"]
    if tree_pin["sha256"] != TREE or seal["archive"]["sha256"] != TREE:
        raise ValueError("R1_RECONSTRUCTION_TREE_DIFFERS")
    check_archive(tree_pin, seal["files"])
    tree = root/(directory+"_tree")
    with tarfile.open(pinned(tree_pin)) as archive:
        archive.extractall(tree, filter="data")
    if inventory(tree) != seal["files"]:
        raise ValueError("R1_RECONSTRUCTION_TREE_DIFFERS")
    mounts = mount_inputs(p, recipe)
    control = root/(directory+"_input.json")
    env = environment()
    write(control, dict(config=p, recipe=recipe, root=str(root), directory=directory, environment=env))
    write(root/(directory+"_mounts.json"), mounts)
    subprocess.run(command(root, control, tree, mounts, env), check=True)
    result = load(root/directory/"receipt.json")
    path = root/directory/"rows.sqlite"
    if result["database"]["sha256"] != DB:
        raise ValueError("P_TRAINED_ROUTING_RECONSTRUCTION_DIFFERS:"+DB)
    checked(path, DB)
    return path


def child(control, tree):
    value = json.loads(Path(control).read_text())
    root = Path(value["root"]); directory = value["directory"]
    started = time.monotonic()
    probe_path = root/(directory+"_imports.json")
    probe = dict(status="REFUSE", elapsed_seconds=0)
    try:
        probe["modules"] = import_probe(tree, value["environment"]["paths"],
                                        value.get("probe_modules", probe_modules()))
        if not value.get("probe_only"):
            from student_pilot.carrier_c1_run import processor_for_receipt
            from student_pilot.p3_provenance import load, pinned
            try:
                processor_for_receipt(load(pinned(value["recipe"]["base_model"])), value["config"])
            except ImportError as error:
                raise ValueError("R1_RECONSTRUCTION_IMPORT_MISSING:"+(error.name or "transformers")) from error
        probe["status"] = "\x50ASS"
    except BaseException as error:
        probe["refusal"] = str(error)
        raise
    finally:
        probe["elapsed_seconds"] = time.monotonic()-started
        probe_path.write_text(json.dumps(probe, sort_keys=True, indent=2)+"\n")
    if value.get("probe_only"):
        return
    from student_pilot.p3_provenance import load, pinned, file_pin, write
    from student_pilot.s1_pool_relocate import relocate
    from student_pilot.s1_routing import build
    value = load(control); p = value["config"]; recipe = value["recipe"]
    root = Path(value["root"]); directory = value["directory"]
    pcfg = deepcopy(p); pcfg["s1_routing"] = deepcopy(recipe["inputs"])
    pcfg["streams"]["routing"] = recipe["legacy"]
    selected = load(pinned(recipe["inputs"]["selection"]))
    selection_check(selected, recipe)
    refresh = root/(directory+"_refresh"); refresh.mkdir()
    try:
        moved = relocate(recipe["inputs"]["selection"], recipe["inputs"].get("catalog", {}), refresh/"p")
        selected = load(pinned(moved["relocated"]))
        selection_check(selected, recipe)
        pcfg["s1_routing"]["selection"] = moved["relocated"]
        write(refresh/"r.json", dict(status="\x50ASS", prepared=False, selection=moved["relocated"]))
        build(pcfg, root/directory, recipe["division"], recipe["base_model"])
    except BaseException as error:
        if not (refresh/"r.json").exists():
            write(refresh/"r.json", dict(status="REFUSE", refusal=str(error), prepared=False))
        raise


if __name__ == "__main__": child(sys.argv[1], sys.argv[2])
