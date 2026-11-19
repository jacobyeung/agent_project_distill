from collections import Counter
import hashlib
import json

from .p3_provenance import load, pinned


class SceneCoverageError(ValueError):
    pass


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def file_ids(files):
    return {name: value["sha256"] if value else None for name, value in files.items()}


class Census:
    def __init__(self, files):
        self.files = files
        values = {name: load(pinned(pin)) if pin else {} for name, pin in files.items()}
        self.prefixes = dict(d1="d1", scannet="d1", d2="d2", scannetpp="d2", scannetppv2="d2",
                             d3="d3", arkitscenes="d3", **{"scannet++": "d2"})
        for corpus in values["benchmark"].get("other_corpora", {}):
            self.prefixes.setdefault(corpus.casefold(), corpus.casefold())
        dev = values["dev"]
        dev_names = [item for field in ("natives", "rooms", "physical_groups") for item in dev.get(field, [])]
        for field in ("canonical", "aliases"):
            for name, aliases in dev.get(field, {}).items():
                dev_names.extend((name, *aliases))
        benchmark = values["benchmark"]
        benchmark_names = list(benchmark.get("scenes", []))+list(benchmark.get("physical_groups", []))
        benchmark_names.extend("/".join(parts) for parts in benchmark.get("rung1_tokens", []))
        benchmark_names.extend(corpus+"/"+scene for corpus, scenes in benchmark.get("other_corpora", {}).items()
                               for scene in scenes)
        self.names = {name: {self.identity(value) for value in names}
                      for name, names in (("dev", dev_names), ("benchmark", benchmark_names))}

    def prefix(self, value):
        if not isinstance(value, str) or value.casefold() not in self.prefixes:
            raise SceneCoverageError("Unknown scene dataset prefix in independent census: "+str(value))
        return self.prefixes[value.casefold()]

    def identity(self, value):
        if not isinstance(value, str):
            raise SceneCoverageError("Independent scene census needs string identifiers")
        prefix, separator, scene = value.partition("/")
        if not separator or not scene or any(not item for item in scene.split("/")):
            raise SceneCoverageError("Independent scene census needs dataset-qualified identifiers")
        return self.prefix(prefix)+"/"+scene

    def identities(self, row):
        identifiers = []
        dataset, scene = row.get("dataset"), row.get("scene")
        dataset = self.prefix(dataset) if dataset is not None else None
        if isinstance(scene, str):
            if "/" in scene:
                identifiers.append(scene)
            elif dataset:
                identifiers.append(dataset+"/"+scene)
            else:
                base, separator, scan = scene.rpartition("_")
                if separator and base.startswith("scene") and base[5:].isdigit() and scan.isdigit():
                    identifiers.append("d1/"+scene)
        for value in (row, row.get("routing"), row.get("provenance")):
            if isinstance(value, dict):
                identifiers.extend(value[key] for key in ("canonical", "physical_group", "room")
                                   if isinstance(value.get(key), str) and "/" in value[key])
        if not identifiers:
            raise SceneCoverageError("Independent scene census cannot identify a source scene")
        identities = {self.identity(value) for value in identifiers}
        for value in tuple(identities):
            dataset, scene = value.split("/", 1)
            base, separator, scan = scene.rpartition("_")
            if dataset == "d1" and separator and base.startswith("scene") and base[5:].isdigit() and scan.isdigit():
                identities.add(dataset+"/"+base)
        return tuple(sorted(identities))

    def count(self, rows, population=None):
        histogram = Counter(self.identities(row) for row in rows)
        unique = set().union(*(set(identifiers) for identifiers in histogram))
        matches = {name: unique.intersection(names) for name, names in self.names.items()}
        counts = dict(dev_matches=0, benchmark_matches=0, overlap_matches=0)
        for identifiers, number in histogram.items():
            identifiers = set(identifiers)
            dev, benchmark = (bool(identifiers.intersection(matches[name])) for name in ("dev", "benchmark"))
            counts["dev_matches"] += number*int(dev)
            counts["benchmark_matches"] += number*int(benchmark)
            counts["overlap_matches"] += number*int(dev and benchmark)
        return dict(schema="s1-scene-census-v1", method="pre-filter-distinct-scene-intersection",
                    files=self.files, rows=sum(histogram.values()), distinct_scene_ids=len(unique),
                    scene_ids_sha256=fingerprint(sorted(histogram.items())), population=population, counts=counts)


def compare(expected, observed, files, source):
    methods = ("pre-filter-distinct-scene-intersection", "pinned-pool-qid-membership",
               "subset-of-independently-checked-pool-selection")
    if (not isinstance(expected, dict) or expected.get("schema") != "s1-scene-census-v1"
            or expected.get("method") not in methods or file_ids(expected.get("files", {})) != file_ids(files)):
        raise SceneCoverageError("Missing or foreign independent scene census: "+source)
    for key in ("dev_matches", "benchmark_matches", "overlap_matches"):
        value = expected.get("counts", {}).get(key)
        if type(value) is not int or value < 0 or observed.get(key) != value:
            raise SceneCoverageError("Filter differs from independent scene census: "+source+"/"+key)
    rows = expected.get("rows")
    if rows is not None and (type(rows) is not int or rows < 0 or rows != observed.get("seen")):
        raise SceneCoverageError("Row population differs from independent scene census: "+source)
    return "PASS"
