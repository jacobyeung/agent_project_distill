import importlib.util
import ast
import json
import os
import sys
from functools import lru_cache

from .io import ROOT, sha256
from .paths import mapped


class PathRebinder(ast.NodeTransformer):
    def visit_Constant(self, node):
        if isinstance(node.value, str):
            node.value = mapped(node.value)
        return node


@lru_cache(maxsize=1)
def modules():
    policy = os.environ.get("GEO_BAKEOFF_FUSION_SOURCE") == "policy"
    suffix = "_policy" if policy else ""
    root = ROOT / f"work/reference{suffix}"
    pin = json.loads((ROOT / f"out/receipts/reference{suffix}_pin.json").read_text())
    result = {}
    names = ("tplib", "programs", "common", "scene_gt", "prog_v2", "geomswap", "run_tg")
    for name in names + (("ladder_table", "setlib") if policy else ()):
        path = root / f"{name}.py"
        if sha256(path) != pin["files"][path.name]["sha256"]:
            raise ValueError(f"Pinned program changed: {path}")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        source = PathRebinder().visit(ast.parse(path.read_text(), filename=str(path)))
        exec(compile(source, str(path), "exec"), module.__dict__)
        result[name] = module
    result["prog_v2"].VOCAB = json.loads((root / "vsi_scannet_vocab.json").read_text())
    result["geomswap"].install()
    return result
