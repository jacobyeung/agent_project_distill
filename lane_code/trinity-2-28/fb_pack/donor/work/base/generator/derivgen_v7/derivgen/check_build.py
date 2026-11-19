"""Read-only replay of an emitted build, including private evidence shards."""
import itertools
from collections import Counter, OrderedDict
from pathlib import Path

from .common import ProvenanceError, pinned, read_json, rows, sha256
from .geometry import GTScene
from .provenance import Admission, adapters, l1_api, rung1_alias, validate_build
from .replay import audit


def check_build(path):
    manifest = read_json(Path(path)/"MANIFEST.json")
    for output in manifest["outputs"]: pinned(output)
    config = read_json(pinned(manifest["config"]))
    closure = manifest.get("code_closure", [])
    if config.get("trace_form") == "canonical_v38" and not closure:
        raise ProvenanceError("canonical saved build lacks code closure")
    if closure:
        actual = {str(p.resolve()) for p in Path(__file__).parent.glob("*.py")}
        if {p["path"] for p in closure} != actual:
            raise ProvenanceError("saved build code closure census mismatch")
        for pin in closure: pinned(pin)
    infrastructure = manifest["status"] == "infrastructure_only"
    validate_build(config, manifest["config"]["path"], infrastructure, manifest.get("parent_record"))
    admission = Admission(config, infrastructure)
    programs, T = adapters(config)
    l1 = l1_api(config)
    cache, count, census = OrderedDict(), 0, Counter()
    accepted = [p["path"] for p in manifest["outputs"] if Path(p["path"]).name.startswith("accepted-")]
    evidence = [p["path"] for p in manifest["outputs"] if Path(p["path"]).name.startswith("evidence-")]
    public_rows = itertools.chain.from_iterable((r for _, r in rows(p)) for p in accepted)
    private_rows = itertools.chain.from_iterable((r for _, r in rows(p)) for p in evidence)
    plans = {}
    # SQLite is opened immutable/read-only; replay never mutates the generation index.
    import sqlite3
    db = sqlite3.connect('file:'+str((Path(path)/'INDEX.sqlite').resolve())+'?mode=ro&immutable=1', uri=True)
    try:
        for record, private in itertools.zip_longest(public_rows, private_rows):
            if record is None or private is None or record["qid"] != private["qid"]:
                raise ProvenanceError("accepted/evidence stream alignment mismatch")
            provenance = record["provenance"]
            source_alias = provenance.get("source_alias", provenance["alias"])
            if "source_alias" in provenance and provenance["alias"] != rung1_alias(provenance["canonical"], source_alias):
                raise ProvenanceError("saved row rung-1 alias mismatch")
            source = {"qid": record["qid"], "scene": source_alias, "question_type": record["question_type"],
                      "answer": private.get("gt_label", private["source_answer"]), "infrastructure_only": infrastructure,
                      "student_input": {"question": record["question"], "options": record["options"], "frame_indices": provenance["frame_indices"]}}
            # Replay the exact source; the spelling map cannot recover correct occurrences.
            fixes = record.get("label_typo_fixed", {})
            if fixes:
                original = record.get("label_typo_original")
                if (not isinstance(original, dict) or not isinstance(original.get("question"), str)
                        or not isinstance(original.get("options"), list)
                        or not all(isinstance(option, str) for option in original["options"])):
                    raise ProvenanceError("saved typo-corrected row lacks original source text")
                source["student_input"].update(question=original["question"], options=list(original["options"]))
            alias, entry = admission.entry(source)
            if alias not in cache:
                cache[alias] = GTScene(entry, programs)
                cache[alias].l1 = l1
                if len(cache) > config.get("scene_cache_size", 1): cache.popitem(last=False)
            cache.move_to_end(alias)
            rec = db.execute('SELECT payload FROM plans WHERE qid=?', (record['qid'],)).fetchone()
            from .common import loads
            plan = loads(rec[0]) if rec else None
            census.update(audit({**record, "private": private}, cache[alias], T, config, source, plan))
            count += 1
    finally:
        db.close()
    counts = read_json(Path(path)/"COUNTS.json")
    if count != counts['counts'].get('accepted', 0): raise ProvenanceError("accepted replay count mismatch")
    dispositions = Counter()
    for p in manifest["outputs"]:
        if Path(p["path"]).name.startswith("dispositions-"):
            for _, row in rows(p["path"]): dispositions[row["disposition"]] += 1
    if sum(dispositions.values()) != counts['counts']['seen'] or any(dispositions[k] != counts['counts'].get(k, 0) for k in ('accepted','rejected','deferred')):
        raise ProvenanceError("disposition replay count mismatch")
    if dict(census) != read_json(Path(path)/'UNIT_CENSUS.json')['events_by_declared_unit']:
        raise ProvenanceError("unit census replay mismatch")
    return {"rows_replayed": count, "infrastructure_only": infrastructure, "units": dict(census), "manifest_sha256": sha256(Path(path)/"MANIFEST.json")}
