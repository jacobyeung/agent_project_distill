from copy import deepcopy
import json
from pathlib import Path
import re
import sqlite3

from .carrier_c1_routing import ALIAS, alias_names
from .p3_provenance import file_pin, load, pinned, write
from .s1_scene_census import Census, SceneCoverageError, compare, fingerprint


def dev_names(pin):
    value = load(pinned(pin))
    if value.get("schema") != "dev_s1_withhold_v1":
        raise ValueError("Dev-S1 exclusion schema differs")
    fields = ("natives", "rooms", "physical_groups")
    if (any(not isinstance(value.get(key), list) for key in fields) or
            any(not isinstance(value.get(key), dict) for key in ("canonical", "aliases"))):
        raise ValueError("Dev-S1 exclusion membership is incomplete")
    names = [name for key in fields for name in value[key]]
    for key in ("canonical", "aliases"):
        for native, aliases in value[key].items():
            if not isinstance(aliases, list):
                raise ValueError("Dev-S1 exclusion aliases must be lists")
            names.extend([native, *aliases])
    return names


def benchmark_names(pin):
    value = load(pinned(pin))
    if value.get("schema") != "benchmark_scene_exclusions_v1":
        raise ValueError("Benchmark exclusion schema differs")
    names = alias_names(value)
    for corpus, identifiers in value.get("other_corpora", {}).items():
        if not isinstance(identifiers, list) or any(not isinstance(item, str) for item in identifiers):
            raise ValueError("Benchmark corpus exclusion identifiers differ")
        names.extend(f"{corpus}/{identifier}" for identifier in identifiers)
    return names


class Exclusions:
    def __init__(self, pin, benchmark_pin=None):
        self.files = dict(dev=pin, benchmark=benchmark_pin)
        self.sources = {}
        self.datasets = {}
        self.expected = {}
        self.names = {}
        self.corpora = {name.casefold() for name in load(pinned(benchmark_pin)).get("other_corpora", {})} if benchmark_pin else set()
        self.aliases = {**ALIAS, "d1": "d1", "d2": "d2", "d3": "d3", "scannet++": "d2"}
        for key, reader in (("dev", dev_names), ("benchmark", benchmark_names)):
            names = reader(self.files[key]) if self.files[key] else []
            if (self.files[key] and not names) or any(
                    not isinstance(name, str) or "/" not in name or not all(name.split("/")) for name in names):
                raise ValueError("Scene exclusion names must be dataset-qualified")
            self.names[key] = {self.key(name) for name in names}
        self.census = Census(self.files)

    def dataset(self, value):
        if not isinstance(value, str):
            raise SceneCoverageError("Unknown scene dataset prefix")
        name = value.casefold()
        if name in self.aliases:
            return self.aliases[name]
        if name in self.corpora:
            return name
        raise SceneCoverageError("Unknown scene dataset prefix: " + value)

    def key(self, value):
        if not isinstance(value, str) or "/" not in value or not all(value.split("/")):
            raise SceneCoverageError("Scene exclusion names must be dataset-qualified")
        dataset, scene = value.split("/", 1)
        return self.dataset(dataset)+"/"+scene

    def identifiers(self, row):
        keys = []
        dataset, scene = row.get("dataset"), row.get("scene")
        if dataset is not None:
            dataset = self.dataset(dataset)
        if isinstance(scene, str):
            if "/" in scene:
                keys.append(scene)
            elif dataset:
                keys.append(f"{dataset}/{scene}")
            elif re.fullmatch(r"scene\d+_\d+", scene):
                keys.append("d1/"+scene)
        for source in (row, row.get("routing") or {}, row.get("provenance") or {}):
            if not isinstance(source, dict):
                continue
            for field in ("canonical", "physical_group", "room", "alias"):
                value = source.get(field)
                if isinstance(value, str) and "/" in value:
                    keys.append(value)
        if not keys:
            raise SceneCoverageError("Scene exclusion row lacks a dataset-qualified scene")
        return {self.key(key) for key in keys}

    def matched(self, keys):
        rooms = {match[1] for key in keys if (match := re.fullmatch(r"(d1/scene\d+)_\d+", key))}
        return {key: bool((keys | rooms) & names) for key, names in self.names.items()}

    def matches(self, row):
        return self.matched(self.identifiers(row))

    def excluded(self, row):
        return any(self.matches(row).values())

    def counts(self, source):
        self.datasets.setdefault(source, set())
        return self.sources.setdefault(source, dict(seen=0, removed=0, retained=0,
                                                    dev_matches=0, benchmark_matches=0, overlap_matches=0))

    def expect(self, source, rows, population=None):
        self.counts(source)
        self.expected[source] = self.census.count(rows, population)

    def keep(self, row, source):
        value = self.counts(source)
        keys = self.identifiers(row)
        self.datasets[source].update(key.split("/", 1)[0] for key in keys)
        matches = self.matched(keys)
        rejected = any(matches.values())
        value["seen"] += 1
        value["removed"] += int(rejected)
        value["retained"] += int(not rejected)
        value["dev_matches"] += int(matches["dev"])
        value["benchmark_matches"] += int(matches["benchmark"])
        value["overlap_matches"] += int(all(matches.values()))
        return not rejected

    def report(self, validate=True):
        comparisons = {}
        if validate:
            for source, counts in self.sources.items():
                comparisons[source] = compare(self.expected.get(source), counts, self.files, source)
        return dict(schema="s1-scene-filter-v1", files=self.files, sources=self.sources,
                    expected=self.expected, comparisons=comparisons,
                    datasets={name: sorted(values) for name, values in self.datasets.items()})


def _indices(values):
    if (not isinstance(values, list) or any(type(value) is not int or value < 0 for value in values)
            or len(set(values)) != len(values)):
        raise ValueError("Scene selection has invalid or duplicate source indices")
    return values


def _selected_rows(connection, wanted):
    """Read selected rows in native i order without materializing other payloads."""
    # SQLite INTEGER indices fit in int64. Out-of-range requests remain missing
    # and are rejected by the existing found != wanted check.
    ordered = sorted(index for index in wanted if index <= (1 << 63)-1)
    for start in range(0, len(ordered), 256):
        batch = ordered[start:start+256]
        placeholders = ','.join('?' for _ in batch)
        yield from connection.execute(
            'SELECT i,row FROM rows WHERE i IN ('+placeholders+') ORDER BY i', batch)


def _database(database, indices, rule, source):
    indices = _indices(indices)
    wanted, found, kept = set(indices), set(), set()
    rule.counts(source)
    path = pinned(database)
    with sqlite3.connect(path.as_uri()+"?mode=ro", uri=True) as connection:
        import os
        # Keep sequential scans for dense prefixes; keyed reads help sparse selections.
        fast = (os.environ.get('S1_PREP_SELECT_SQL') == '1' and bool(wanted)
                and len(wanted)*4 < max(wanted)+1)
        def rows():
            return (_selected_rows(connection, wanted) if fast else
                    connection.execute("SELECT i,row FROM rows ORDER BY i"))
        rule.expect(source, (json.loads(text) for index, text in rows()
                             if index in wanted), dict(database=database, indices_sha256=fingerprint(indices)))
        for index, text in rows():
            if index not in wanted:
                continue
            found.add(index)
            if rule.keep(json.loads(text), source):
                kept.add(index)
    if found != wanted:
        raise ValueError("Scene selection references absent database rows")
    return [index for index in indices if index in kept]


def _clips(value, indices, rule, source):
    from .c1_pose_mix import _clip_scenes
    scenes = _clip_scenes(value)
    wanted, found, kept = set(_indices(indices)), set(), set()
    rule.counts(source)
    with pinned(value["clips_plan"]).open() as handle:
        rule.expect(source, (dict(row, scene=scenes[row["recording_fingerprint"]])
                             for line in handle if (row := json.loads(line))["i"] in wanted),
                    dict(clips_plan=value["clips_plan"], indices_sha256=fingerprint(indices)))
    with pinned(value["clips_plan"]).open() as handle:
        for number, line in enumerate(handle):
            row = json.loads(line)
            if row["i"] != number:
                raise ValueError("Scene selection clip plan order differs")
            if number not in wanted:
                continue
            found.add(number)
            scene = scenes[row["recording_fingerprint"]]
            if rule.keep(dict(row, scene=scene), source):
                kept.add(number)
    if found != wanted:
        raise ValueError("Scene selection references absent clip rows")
    return [index for index in indices if index in kept]


def selection(name, value, rule):
    if value.get("kind") == "mdg":
        index = load(pinned(value["index"]))
        if not isinstance(index.get("train"), list) or len(index["train"]) != value["count"]:
            raise ValueError("Scene selection MDG source count differs")
        selected = deepcopy(index)
        for split in ("train", "holdout", "tau", "val"):
            if split in selected:
                rule.expect(name+"/"+split, selected[split], dict(index=value["index"], partition=split))
                selected[split] = [row for row in selected[split] if rule.keep(row, name+"/"+split)]
        return "index", selected, dict(count=len(selected["train"]))
    if value.get("kind") == "mix":
        order = load(pinned(value["order"]))
        if (not isinstance(order, list) or len(order) != value["count"] or
                any(not isinstance(item, list) or len(item) != 2 or
                    any(type(part) is not int or part < 0 for part in item) or
                    item[0] >= len(value["sources"]) for item in order) or
                len({tuple(item) for item in order}) != len(order)):
            raise ValueError("Scene selection pose mixture order differs")
        allowed = set()
        for number, part in enumerate(value["sources"]):
            indices = [index for source, index in order if source == number]
            if part["kind"] == "rows":
                kept = _database(part["database"], indices, rule, f"{name}/{number}")
            elif part["kind"] == "c1r_clips":
                kept = _clips(part, indices, rule, f"{name}/{number}")
            else:
                raise ValueError("Scene selection pose mixture contains an unknown source")
            allowed.update((number, index) for index in kept)
        selected = [item for item in order if tuple(item) in allowed]
        changes = dict(count=len(selected))
        if "teacher_rows" in value:
            changes["teacher_rows"] = sum(value["sources"][source]["kind"] == "c1r_clips" for source, _ in selected)
        return "order", selected, changes
    indices = load(pinned(value["indices"])) if value.get("indices") else list(range(value["count"]))
    if len(indices) != value["count"]:
        raise ValueError("Scene selection database source count differs")
    selected = _database(value["database"], indices, rule, name)
    return "indices", selected, dict(count=len(selected))


def totals(report, rule):
    fields = ("seen", "removed", "retained", "dev_matches", "benchmark_matches", "overlap_matches")
    result = dict.fromkeys(fields, 0)
    expected = {name: value["sha256"] if value else None for name, value in rule.files.items()}
    files = report.get("files", {})
    actual = {name: value.get("sha256") if value else None for name, value in files.items()}
    if (report.get("schema") != "s1-scene-filter-v1" or actual != expected
            or set(report.get("datasets", {})) != set(report.get("sources", {}))
            or set(report.get("expected", {})) != set(report.get("sources", {}))):
        raise ValueError("Upstream scene coverage has foreign lists or missing datasets")
    for source, counts in report["sources"].items():
        compare(report["expected"][source], counts, rule.files, source)
        if (any(type(counts.get(key)) is not int or counts[key] < 0 for key in fields)
                or counts["seen"] != counts["removed"]+counts["retained"]
                or counts["removed"] != counts["dev_matches"]+counts["benchmark_matches"]-counts["overlap_matches"]
                or any(rule.dataset(name) != name for name in report["datasets"][source])):
            raise ValueError("Upstream scene coverage counts or dataset identifiers differ")
        for key in fields:
            result[key] += counts[key]
    for nested in report.get("upstream", {}).values():
        for key, value in totals(nested, rule).items():
            result[key] += value
    return result


def upstream(streams, rule):
    result = {}
    for name, value in streams.items():
        parts = {f"{name}/{index}": part for index, part in enumerate(value["sources"])} if value.get("kind") == "mix" else {name: value}
        for source, part in parts.items():
            if part.get("receipt") and part.get("kind") != "mdg":
                report = load(pinned(part["receipt"])).get("source_scene_exclusions")
                if report is not None:
                    totals(report, rule)
                    result[source] = report
    return result


def coverage_report(rule, streams, policy=None):
    report = rule.report()
    previous = upstream(streams, rule)
    if previous:
        report["upstream"] = previous
    totals(report, rule)
    if policy is None:
        return report
    if (policy.get("schema") != "s1-scene-coverage-v1" or not isinstance(policy.get("source_map"), dict)
            or not policy["source_map"]):
        raise ValueError("Scene coverage needs a bound independent source census")
    reference = load(pinned(policy["reference"]))
    if (reference.get("schema") != "dev_s1_manifest_v1" or not rule.files["dev"]
            or reference.get("withhold_file", {}).get("sha256") != rule.files["dev"]["sha256"]):
        raise ValueError("Independent scene census uses a different withheld population")
    groups = {}
    for source, counts in rule.sources.items():
        matches = [name for name in policy["source_map"] if source == name or source.startswith(name+"/")]
        if len(matches) != 1:
            raise ValueError("Scene coverage source lacks an unambiguous independent census: "+source)
        groups.setdefault(matches[0], []).append(source)
    records = {}
    for name, sources in groups.items():
        bindings = policy["source_map"][name]
        if not isinstance(bindings, list) or not bindings:
            raise ValueError("Scene coverage source needs an independent reference")
        refs, dev, benchmark = [], 0, []
        for binding in bindings:
            value = reference["withheld_training_rows"][binding["source"]]
            count = value["rows_withheld"]
            other = value.get("benchmark_rows_withheld")
            if "index" in binding:
                count = count[binding["index"]]
                other = other[binding["index"]] if other is not None else None
            if type(count) is not int or count < 0 or (other is not None and (type(other) is not int or other < 0)):
                raise ValueError("Independent scene census has invalid row counts")
            dev += count
            benchmark.append(other)
            refs.append(dict(binding=binding, path=value["path"], dev_rows=count, benchmark_rows=other))
        fields = ("seen", "removed", "retained", "dev_matches", "benchmark_matches", "overlap_matches")
        current = {key: sum(rule.sources[source][key] for source in sources) for key in fields}
        earlier = dict.fromkeys(fields, 0)
        for source in sources:
            if source in previous:
                for key, count in totals(previous[source], rule).items():
                    earlier[key] += count
        observed_dev = current["dev_matches"]+earlier["dev_matches"]
        observed_benchmark = current["benchmark_matches"]+earlier["benchmark_matches"]
        benchmark_reference = sum(benchmark) if all(value is not None for value in benchmark) else None
        if reference.get('exact_rebuilt_population') and (observed_dev != dev or observed_benchmark != benchmark_reference):
            raise ValueError('Filter differs from independent scene census: '+name)
        records[name] = dict(parts=sources, native=current, upstream=earlier, references=refs,
                             reference_dev_rows=dev, reference_benchmark_rows=benchmark_reference,
                             reference_comparison="NOT_COMPARED",
                             observed_dev_matches=observed_dev, observed_benchmark_matches=observed_benchmark)
    comparisons = report["comparisons"]
    status = "PASS" if comparisons.keys() == rule.sources.keys() and all(
        value == "PASS" for value in comparisons.values()) else "FAIL"
    report["coverage"] = dict(schema="s1-scene-coverage-result-v1", status=status, policy=policy, sources=records,
                             scope="admitted-population-census", raw_reference_status="NOT_COMPARED",
                             comparison="exact native census counts per source and list; raw reference populations are not compared")
    return report


def apply(streams, pin, output, benchmark_pin=None, coverage=None):
    rule = Exclusions(pin, benchmark_pin)
    result = {}
    for name, value in streams.items():
        if "scene_source" in value or not re.fullmatch(r"[a-z_]+", name):
            raise ValueError("Scene exclusion source is already filtered or unnamed")
        key, selected, changes = selection(name, value, rule)
        path = Path(output) / f"{name}_scene_{key}.json"
        write(path, selected)
        result[name] = {**deepcopy(value), **changes, key: file_pin(path), "scene_source": deepcopy(value)}
    for source, counts in rule.sources.items():
        print(json.dumps(dict(scene_exclusion=dict(source=source, files=rule.files, **counts))), flush=True)
    return result, coverage_report(rule, streams, coverage)


def verify(receipt, cfg):
    if any('reader_source' in v for v in receipt['streams'].values()):
        from .r1_population import scene_receipt
        receipt = scene_receipt(receipt)
    pin = cfg.get("dev_scene_exclusions")
    benchmark_pin = cfg.get("benchmark_scene_exclusions")
    if (receipt.get("dev_scene_exclusions") != pin or
            receipt.get("benchmark_scene_exclusions") != benchmark_pin):
        raise ValueError("Scene exclusion binding differs")
    if pin is None and benchmark_pin is None:
        if "scene_filter_report" in receipt or any("scene_source" in value for value in receipt["streams"].values()):
            raise ValueError("Scene exclusion evidence lacks a bound list")
        return
    rule = Exclusions(pin, benchmark_pin)
    originals = {}
    for name, value in receipt["streams"].items():
        original = value.get("scene_source")
        if not isinstance(original, dict) or "scene_source" in original:
            raise ValueError("Scene exclusion lacks the original source selection")
        originals[name] = original
        key, selected, changes = selection(name, original, rule)
        if load(pinned(value[key])) != selected:
            raise ValueError("Scene selection differs or an excluded scene remains")
        expected = {**deepcopy(original), **changes, key: value[key], "scene_source": original}
        if value != expected:
            raise ValueError("Scene selection changes source metadata")
    if receipt.get("scene_filter_report") != coverage_report(rule, originals, cfg.get("scene_coverage")):
        raise ValueError("Scene exclusion accounting differs")
