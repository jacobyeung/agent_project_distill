"""Import stand-ins for transformers and peft on CPU hosts that lack them.

install() adds a module only when the real package is missing, so on a training host the real packages are used.
The stand-ins support importing the trainer modules; anything that needs real model or PEFT behaviour raises.
"""
import importlib.util
import random
import sys
import types


def missing(name):
    return name not in sys.modules and importlib.util.find_spec(name) is None


def unavailable(name):
    def call(*args, **kwargs):
        raise RuntimeError(f"{name} is a CPU test stand-in; the real package is not installed")
    return call


class Placeholder:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("CPU test stand-in class; the real package is not installed")

    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        raise RuntimeError("CPU test stand-in class; the real package is not installed")


def set_seed(seed, deterministic=False):
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


class TransformersModule(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        value = type(name, (Placeholder,), {})
        setattr(self, name, value)
        return value


def install():
    installed = []
    if missing("transformers"):
        transformers = TransformersModule("transformers")
        transformers.__path__ = []
        transformers.set_seed = set_seed
        video_utils = types.ModuleType("transformers.video_utils")
        video_utils.VideoMetadata = type("VideoMetadata", (Placeholder,), {})
        transformers.video_utils = video_utils
        sys.modules.update({"transformers": transformers, "transformers.video_utils": video_utils})
        installed.append("transformers")
    if missing("peft"):
        peft = types.ModuleType("peft")
        peft.__path__ = []
        peft.PeftModel = type("PeftModel", (Placeholder,), {})
        peft.LoraConfig = type("LoraConfig", (Placeholder,), {})
        peft.TaskType = types.SimpleNamespace(CAUSAL_LM="CAUSAL_LM")
        peft.get_peft_model = unavailable("peft.get_peft_model")
        peft.get_peft_model_state_dict = unavailable("peft.get_peft_model_state_dict")
        tuners = types.ModuleType("peft.tuners")
        tuners.__path__ = []
        tuners_utils = types.ModuleType("peft.tuners.tuners_utils")
        tuners_utils.check_target_module_exists = unavailable("peft.tuners.tuners_utils.check_target_module_exists")
        tuners.tuners_utils = tuners_utils
        peft.tuners = tuners
        sys.modules.update({"peft": peft, "peft.tuners": tuners, "peft.tuners.tuners_utils": tuners_utils})
        installed.append("peft")
    return installed
