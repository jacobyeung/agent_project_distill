from copy import deepcopy
import hashlib
import json
import math
import torch


SCHEMA = "s1-trained-groups-v1"


def group(name):
    if name.startswith("pose.cam_token_connector."):
        return "camera_connector"
    if name.startswith("pose."):
        return "pose"
    if name.startswith(("depth.", "depth_fov.")):
        return "depth"
    if name.startswith("gf1."):
        return "fusion"
    if name.startswith(("mdg.", "mdg_new_tokens.", "ground_tokens.")):
        return "grounding"
    return None


def parameters(model):
    result = {}
    for name, value in model.auxiliary_heads.named_parameters():
        kind = group(name)
        if kind and value.requires_grad:
            result.setdefault(kind, {})[name] = value
    return result


def fingerprint(values):
    digest = hashlib.sha256()
    nonzero = False
    for name, tensor in sorted(values.items()):
        value = tensor.detach().cpu().contiguous()
        if not torch.isfinite(value).all():
            raise ValueError("Trained group contains nonfinite tensors: " + name)
        nonzero |= bool(torch.count_nonzero(value))
        digest.update(json.dumps([name, list(value.shape), str(value.dtype)]).encode())
        digest.update(value.reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest(), nonzero


def capture(model):
    groups = {}
    for name, values in parameters(model).items():
        groups[name] = dict(names=sorted(values), initial_sha256=fingerprint(values)[0], gradient_steps=0)
    model.trained_group_state = dict(schema=SCHEMA, groups=groups)


def observe(model):
    state = getattr(model, "trained_group_state", None)
    if state is None:
        return {}
    values = parameters(model)
    if values.keys() != state["groups"].keys():
        raise ValueError("Trained group configuration changed during the run")
    norms = {}
    for name, entries in values.items():
        squared = sum(float(value.grad.detach().double().square().sum())
                      for value in entries.values() if value.grad is not None)
        if not math.isfinite(squared):
            raise ValueError("Trained group gradient is nonfinite: " + name)
        norms[name] = math.sqrt(squared)
        state["groups"][name]["gradient_steps"] += int(squared > 0)
    return norms


def restore(model, saved):
    from torch.distributed.fsdp import FullyShardedDataParallel
    from torch.nn.parallel import DistributedDataParallel
    while isinstance(model, (FullyShardedDataParallel, DistributedDataParallel)):
        model = model.module
    current = getattr(model, "trained_group_state", None)
    if current is None:
        if saved is not None:
            raise ValueError("Checkpoint trained-group contract is unexpected")
        return
    if not isinstance(saved, dict) or saved.get("schema") != SCHEMA or saved["groups"].keys() != current["groups"].keys():
        raise ValueError("Checkpoint lacks the matching trained-group contract")
    for name, value in current["groups"].items():
        incoming = saved["groups"][name]
        if (incoming["names"] != value["names"] or incoming["initial_sha256"] != value["initial_sha256"]
                or type(incoming["gradient_steps"]) is not int or incoming["gradient_steps"] < 0):
            raise ValueError("Checkpoint trained-group initialization differs: " + name)
    model.trained_group_state = deepcopy(saved)


def publish(model, full_state, step):
    original = getattr(model, "trained_group_state", None)
    if original is None:
        return None
    result = deepcopy(original)
    result["step"] = int(step)
    for name, entry in result["groups"].items():
        values = {key: full_state["auxiliary_heads."+key] for key in entry["names"]}
        final, nonzero = fingerprint(values)
        entry.update(final_sha256=final, nonzero=nonzero, changed=final != entry["initial_sha256"])
    return result


def validate(model, state, contract, step):
    expected = parameters(model)
    if (not isinstance(contract, dict) or contract.get("schema") != SCHEMA
            or contract.get("step") != step or type(step) is not int or step <= 0
            or set(contract.get("groups", {})) != set(expected)):
        raise ValueError("Evaluator lacks the complete trained-group contract")
    for name, values in expected.items():
        entry = contract["groups"][name]
        if entry.get("names") != sorted(values) or any(key not in state for key in values):
            raise ValueError("Evaluator trained group is missing tensors: " + name)
        final, nonzero = fingerprint({key: state[key] for key in values})
        if not nonzero:
            raise ValueError("Evaluator trained group is zero: " + name)
        if final != entry.get("final_sha256"):
            raise ValueError("Evaluator trained group differs from its export: " + name)
        if (final == entry.get("initial_sha256") or not entry.get("changed")
                or type(entry.get("gradient_steps")) is not int or not 0 < entry["gradient_steps"] <= step):
            raise ValueError("Evaluator trained group is cold: " + name)
    return sorted(expected)


def init_groups(receipt):
    groups = {"pose"}
    if receipt.get("depth_enabled"):
        groups.add("depth")
    if receipt.get("geometry_online"):
        groups.add("camera_connector")
        if receipt["geometry_online"].get("gf1"):
            groups.add("fusion")
    if receipt.get("mdg"):
        groups.add("grounding")
    return sorted(groups)
