import json
import os
from pathlib import Path

import torch
import torch.distributed as dist

from . import full_ft


def plan(recipe, reserve_bytes=200_000_000_000):
    span = recipe["wall_seconds"]-recipe["stop_before_seconds"]
    interval = recipe["resume_every_seconds"]
    if type(span) is not int or type(interval) is not int or span <= 0 or interval <= 0:
        raise ValueError("A whole-leg disk plan needs positive integer timing")
    return dict(reserve_bytes=reserve_bytes, planned_full_states=(span+interval-1)//interval+2,
                extra_full_states=2, planned_weight_exports=len(set(recipe["milestones"]))+
                int(bool(recipe.get("export_at_stop"))))


class Budget:
    def __init__(self, policy=None):
        policy = {} if policy is None else policy
        counts = {"planned_full_states", "extra_full_states", "planned_weight_exports"}
        if not isinstance(policy, dict) or set(policy)-counts-{"reserve_bytes"}:
            raise ValueError("Unknown checkpoint disk guard policy")
        if set(policy) & counts and not counts <= set(policy):
            raise ValueError("Incomplete whole-leg checkpoint disk plan")
        self.policy = {"reserve_bytes": 1024**3, **policy}
        if any(type(value) is not int or value < 0 for value in self.policy.values()):
            raise ValueError("Checkpoint disk counts and reserve must be nonnegative integers")
        self.whole_leg = counts <= set(policy)
        if self.whole_leg and self.policy["planned_full_states"] < 1:
            raise ValueError("A whole-leg disk plan needs a full-state save")
        self.completed = dict(checkpoint=0, export=0)
        self.state_bytes = self.export_bytes = 0

    def remaining(self, kind):
        if not self.whole_leg:
            return int(kind == "checkpoint"), int(kind == "export")
        states = self.policy["planned_full_states"]+self.policy["extra_full_states"]-self.completed["checkpoint"]
        exports = self.policy["planned_weight_exports"]-self.completed["export"]
        if (states if kind == "checkpoint" else exports) <= 0:
            raise ValueError("Whole-leg disk write budget is exhausted")
        return max(0, states), max(0, exports)

    def complete(self, kind):
        self.completed[kind] += 1


def tensor_bytes(value):
    elements, storages = 0, {}
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, torch.Tensor):
            elements += item.numel()*item.element_size()
            storage = item.untyped_storage()
            storages[(str(item.device), storage.data_ptr())] = storage.nbytes()
        elif isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, (list, tuple)):
            pending.extend(item)
    return max(elements, sum(storages.values()))


def check(directory, named, optimizer, buffers, rank, world, policy=None, *, export_named=None, kind="checkpoint"):
    local = dict(rank=rank)
    budget = None
    try:
        budget = policy if isinstance(policy, Budget) else Budget(policy)
        if kind not in ("checkpoint", "export"):
            raise ValueError("Unknown disk write kind")
        remaining_states, remaining_exports = budget.remaining(kind)
        if optimizer is None and remaining_states:
            raise ValueError("Whole-leg disk admission needs optimizer-state measurement")
        selected = [(name, parameter) for name, parameter in named if rank == 0 or not full_ft.is_replicated(name)]
        weights = sum(parameter.numel()*parameter.element_size() for _, parameter in selected)
        buffer_bytes = sum(value.numel()*value.element_size() for _, value in buffers)
        estimated = weights+buffer_bytes
        if optimizer is not None:
            indices = full_ft.optimizer_indices(named, optimizer)
            own = {indices[name] for name, _ in selected}
            state = optimizer.state_dict()
            estimated += tensor_bytes({key: value for key, value in state["state"].items() if key in own})
            estimated += tensor_bytes(state["param_groups"])
        export_named = named if export_named is None else export_named
        exported = sum(value.numel()*value.element_size() for name, value in export_named
                       if rank == 0 or not full_ft.is_replicated(name))+buffer_bytes
        path = Path(directory).resolve()
        while not path.exists() and path != path.parent:
            path = path.parent
        usage = os.statvfs(path)
        local.update(state_tensor_bytes=estimated, export_tensor_bytes=exported,
                     free_bytes=usage.f_bavail*usage.f_frsize, policy=dict(budget.policy), completed=dict(budget.completed),
                     remaining_full_states=remaining_states, remaining_weight_exports=remaining_exports)
    except Exception as error:
        local["error"] = type(error).__name__+": "+str(error)
    records = [None]*world
    if dist.is_initialized():
        dist.all_gather_object(records, local)
    elif world == 1:
        records[0] = local
    else:
        raise ValueError("Disk admission needs the native process group")
    errors = [value["error"] for value in records if "error" in value]
    if errors:
        raise ValueError(f"Cannot verify {kind} disk space: "+"; ".join(errors))
    if any((value["policy"], value["completed"]) != (records[0]["policy"], records[0]["completed"])
           for value in records):
        raise ValueError("Ranks disagree on the whole-leg disk budget")
    measured = sum(value["state_tensor_bytes"] for value in records)
    exported = sum(value["export_tensor_bytes"] for value in records)
    budget.state_bytes = max(budget.state_bytes, (measured*5+3)//4+64*1024**2)
    budget.export_bytes = max(budget.export_bytes, (exported*10+3)//4+64*1024**2)
    states, exports = budget.remaining(kind)
    required = states*budget.state_bytes+exports*budget.export_bytes+budget.policy["reserve_bytes"]
    free = min(value["free_bytes"] for value in records)
    if free < required:
        raise ValueError(f"Insufficient {kind} disk space: need {required} bytes for the disk plan, available {free}")
    result = dict(schema="c1-checkpoint-disk-v2", required_bytes=required, available_bytes=free, ranks=records,
                  state_tensor_bytes=measured, export_tensor_bytes=exported, state_bytes=budget.state_bytes,
                  export_bytes=budget.export_bytes, remaining_full_states=states, remaining_weight_exports=exports,
                  policy=budget.policy, completed=dict(budget.completed), state_storage_margin=[5, 4],
                  export_copy_factor=2, serialization_allowance_bytes=64*1024**2)
    if rank == 0:
        print(json.dumps(dict(event=kind+"_disk_guard", **result)), flush=True)
    return result
