import ast
from collections import Counter
from copy import deepcopy
import hashlib
from pathlib import Path

PILOT_COUNTS = dict(object_abs_distance=4, room_size_estimation=2,
                    camera_displacement=2, camera_movement_direction=1, camera_rotation=1)
DISTANCE_DATASETS = dict(d1=1, d2=2, d3=1)
GEOMETRY_SELECTION_POLICY = "ten-pairs-with-one-geometry-refusal-when-present-v2"


def select_pilot(tasks, families, max_captures=5, per_family=2, item_keys=None):
    families = tuple(families)
    if (not tasks or not families or len(set(families)) != len(families)
            or type(max_captures) is not int or max_captures < 1
            or type(per_family) is not int or per_family < 1):
        raise ValueError("Invalid pilot cohort limits")
    if len({t["key"] for t in tasks}) != len(tasks):
        raise ValueError("Duplicate pilot candidate key")
    if item_keys is not None:
        if not isinstance(item_keys, list) or len(item_keys) != 10 or len(set(item_keys)) != 10:
            raise ValueError("The registered pilot requires ten distinct item keys")
        selected = [task for task in tasks if task["key"] in set(item_keys)]
        counts = Counter(task["family"] for task in selected)
        captures = sorted({task["native"] for task in selected})
        distance_datasets = Counter(task["native"].split("/")[0] for task in selected
                                    if task["family"] == "object_abs_distance")
        if distance_datasets != Counter(DISTANCE_DATASETS):
            raise ValueError("The distance pilot must cover all three datasets with the two d2 anchor items")
        if ([task["key"] for task in selected] != item_keys or item_keys[0] != tasks[0]["key"]
                or counts != Counter(PILOT_COUNTS) or set(families) != set(PILOT_COUNTS)
                or len(captures) > max_captures):
            raise ValueError("The registered pilot lost its ordered coverage or capture bound")
        return dict(item_keys=item_keys, captures=captures, first_key=item_keys[0], families=dict(counts),
                    distance_datasets=dict(distance_datasets))
    by_capture = {}
    for task in tasks:
        if task["family"] not in families:
            raise ValueError("Pilot candidate is outside the registered families")
        by_capture.setdefault(task["native"], Counter())[task["family"]] += 1
    chosen = [tasks[0]["native"]]
    counts = by_capture[chosen[0]].copy()
    while any(counts[f] < per_family for f in families):
        if len(chosen) >= max_captures:
            raise ValueError("Pilot family coverage exceeds the capture allowance")
        candidates = sorted(set(by_capture)-set(chosen))
        gain = lambda c: sum(min(per_family, counts[f]+by_capture[c][f])
                             - min(per_family, counts[f]) for f in families)
        if not candidates or max(map(gain, candidates)) == 0:
            raise ValueError("Pilot lacks a registered family")
        selected = max(candidates, key=gain)
        chosen.append(selected)
        counts.update(by_capture[selected])
    selected = []
    counts = Counter()
    for task in tasks:
        if task["native"] in chosen and counts[task["family"]] < per_family:
            selected.append(task)
            counts[task["family"]] += 1
    if selected[0]["key"] != tasks[0]["key"] or any(counts[f] != per_family for f in families):
        raise ValueError("Pilot selection lost its first capture or family coverage")
    return dict(item_keys=[t["key"] for t in selected],
                captures=sorted({t["native"] for t in selected}),
                first_key=tasks[0]["key"], families=dict(counts))


def select_geometry_pilot(tasks, registered, geometry):
    names = [row["native"] for row in geometry]
    if (len(tasks) != 636 or len({row["key"] for row in tasks}) != 636
            or len(names) != 84 or len(set(names)) != 84
            or set(names) != {row["native"] for row in tasks}
            or any(row.get("status") not in ("PASS", "REFUSED") for row in geometry)):
        raise ValueError("The pilot geometry dispositions differ from the full cohort")
    passed = {row["native"] for row in geometry if row["status"] == "PASS"}
    eligible = [row for row in tasks if row["native"] in passed]
    preferred = registered.get("item_keys")
    if (not isinstance(preferred, list) or len(preferred) != 10
            or len(set(preferred)) != 10 or not set(preferred) <= {row["key"] for row in tasks}):
        raise ValueError("The preferred pilot keys differ from the registered cohort")
    priority = lambda row:(row["key"] not in preferred,
        preferred.index(row["key"]) if row["key"] in preferred else 0)
    ordered = sorted(eligible, key=priority)
    any_refused = len(passed) != 84
    distance = dict(d1=1, d2=1, d3=1) if any_refused else dict(d1=1, d2=2, d3=1)
    selected = []
    missing = []
    if any_refused:
        refused = sorted((row for row in tasks if row["native"] not in passed
                          and row["family"] == "object_abs_distance"), key=priority)
        if refused:
            selected.append(refused[0])
        else:
            missing.append(dict(family="object_abs_distance", geometry="REFUSED", needed=1, available=0))
    for dataset, count in distance.items():
        group = [row for row in ordered if row["family"] == "object_abs_distance"
                 and row["native"].startswith(dataset+"/")]
        selected.extend(group[:count])
        if len(group) < count:
            missing.append(dict(family="object_abs_distance", dataset=dataset, needed=count, available=len(group)))
    for family, count in PILOT_COUNTS.items():
        if family == "object_abs_distance":
            continue
        group = [row for row in ordered if row["family"] == family]
        selected.extend(group[:count])
        if len(group) < count:
            missing.append(dict(family=family, needed=count, available=len(group)))
    if missing:
        return dict(policy=GEOMETRY_SELECTION_POLICY, status="INSUFFICIENT_PASSING_COVERAGE",
                    item_keys=[], captures=[], missing=missing, required_distance_datasets=distance)
    keys = {row["key"] for row in selected}
    selected = [row for row in tasks if row["key"] in keys]
    if len(selected) != 10 or Counter(row["family"] for row in selected) != Counter(PILOT_COUNTS):
        raise ValueError("The passing pilot lost its ten-pair family coverage")
    return dict(policy=GEOMETRY_SELECTION_POLICY, status="READY", item_keys=[row["key"] for row in selected],
                captures=sorted({row["native"] for row in selected}), first_key=selected[0]["key"],
                families=dict(Counter(row["family"] for row in selected)),
                distance_datasets=dict(Counter(row["native"].split("/")[0] for row in selected
                                               if row["family"] == "object_abs_distance")),
                passed_distance_datasets=distance,
                passed_item_keys=[row["key"] for row in selected if row["native"] in passed],
                refused_item_keys=[row["key"] for row in selected if row["native"] not in passed])


def named_function(source, name):
    matches = [n for n in ast.parse(source).body
               if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(matches) != 1 or matches[0].decorator_list:
        raise ValueError("Unrecognized native source function")
    return matches[0]


def assigned(node):
    if not isinstance(node, ast.Assign):
        return set()
    return {n.id for target in node.targets for n in ast.walk(target)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}


def restoration_index(body):
    matches = [i for i, n in enumerate(body) if assigned(n) == {"model", "processor", "info"}]
    if len(matches) != 1:
        raise ValueError("Unrecognized native restoration boundary")
    return matches[0]


def derived(original, name, body, extra=()):
    result = deepcopy(original)
    result.name = name
    result.body = deepcopy(body)
    result.args.args.extend(ast.arg(arg=name) for name in extra)
    return ast.fix_missing_locations(result)


def partition(nomdg_source, geometry_source):
    run = named_function(nomdg_source, "run")
    restore_at = restoration_index(run.body)
    counts = [i for i, n in enumerate(run.body)
              if assigned(n) == {"count"} and isinstance(n.value, ast.Constant) and n.value.value == 0]
    if len(counts) != 1 or counts[0] <= restore_at or counts[0]+1 >= len(run.body):
        raise ValueError("Unrecognized native item-loop boundary")
    count_at = counts[0]
    loop = run.body[count_at+1]
    if (not isinstance(loop, ast.For) or ast.unparse(loop.target) != "key"
            or ast.unparse(loop.iter) != "request['keys']"):
        raise ValueError("Unrecognized native item loop")
    prefix = run.body[restore_at+1:count_at]
    if not any(isinstance(n, ast.Constant) and n.value == "GPU_PARITY.json"
               for statement in prefix for n in ast.walk(statement)):
        raise ValueError("Native parity boundary is missing")
    parity = [n for n in prefix if assigned(n) not in ({"g"}, {"masks"})]
    result = {
        "restore": derived(run, "native_restore", run.body[:restore_at+1]+[
            ast.Return(value=ast.Call(func=ast.Name(id="locals", ctx=ast.Load()), args=[], keywords=[]))]),
        "parity": derived(run, "native_parity", parity+[
            ast.Return(value=ast.Call(func=ast.Name(id="locals", ctx=ast.Load()), args=[], keywords=[]))]),
        "pair": derived(run, "native_pair", [run.body[count_at]]+loop.body+[
            ast.Return(value=ast.Name(id="pair", ctx=ast.Load()))], ("key",)),
    }
    prepare = named_function(geometry_source, "prepare")
    restore_at = restoration_index(prepare.body)
    result["geometry_restore"] = derived(
        prepare, "native_geometry_restore", prepare.body[:restore_at+1]+[
            ast.Return(value=ast.Call(func=ast.Name(id="locals", ctx=ast.Load()), args=[], keywords=[]))])
    body = deepcopy(prepare.body[:restore_at]+prepare.body[restore_at+1:])
    captures = [n for n in body if isinstance(n, ast.For) and ast.unparse(n.iter) == "captures()"]
    if len(captures) != 1:
        raise ValueError("Unrecognized checkpoint-geometry capture loop")
    captures[0].iter = ast.Name(id="selected_captures", ctx=ast.Load())
    result["geometry"] = derived(prepare, "native_geometry", body,
                                 ("model", "processor", "info", "selected_captures"))
    return result


def load_parts(paths, pins):
    if set(paths) != {"nomdg", "geometry"} or set(pins) != set(paths):
        raise ValueError("Incomplete native source pins")
    sources = {}
    for name, path in paths.items():
        path = Path(path)
        if not path.is_absolute() or path.is_symlink():
            raise ValueError("Native source must be an absolute regular file")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != pins[name]:
            raise ValueError("Native source pin differs")
        sources[name] = data.decode()
    return partition(sources["nomdg"], sources["geometry"])


def function(node, namespace):
    module = ast.fix_missing_locations(ast.Module(body=[deepcopy(node)], type_ignores=[]))
    local = dict(namespace)
    exec(compile(module, "<pinned native kernel>", "exec"), local)
    return local[node.name]
