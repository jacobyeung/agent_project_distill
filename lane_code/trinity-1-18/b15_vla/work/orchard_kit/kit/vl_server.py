"""StarVLA's policy server (deployment/model_server/server_policy.py) with the kit's framework.head_hook applied when the
checkpoint's framework is rebuilt, so evaluation runs the same head and proprio path as training. Same arguments."""
import importlib
import os
import runpy
import sys

os.environ["VLL_NO_FIT"] = "1"
import starVLA.model.framework.base_framework as BF  # noqa: E402

_orig = BF.build_framework


def build_framework(cfg):
    model = _orig(cfg)
    fw = cfg.framework
    hook = fw.get("head_hook", None) if hasattr(fw, "get") else getattr(fw, "head_hook", None)
    if hook:
        mod, fn = str(hook).split(":")
        model = getattr(importlib.import_module(mod), fn)(model, cfg)
        print(f"[vl_server] head_hook {hook} applied: {getattr(model, 'vl_head_hook', None)}", flush=True)
    return model


BF.build_framework = build_framework
if __name__ == "__main__":
    srv = os.path.join(os.environ["STARVLA_DIR"], "deployment/model_server/server_policy.py")
    sys.argv = [srv] + sys.argv[1:]
    runpy.run_path(srv, run_name="__main__")
