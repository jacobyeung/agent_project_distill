import copy
from pathlib import Path

from .p3_provenance import file_pin, load, pinned, write
from .s1_pool import Pool


def relocate(selection_pin, catalog, directory, *, tokenizer=None):
    output = Path(directory)
    output.mkdir()
    original = load(pinned(selection_pin))
    moves = []

    def locate(pin):
        selected = catalog.get(pin["sha256"])
        if selected is None and tokenizer is not None and tokenizer["sha256"] == pin["sha256"]:
            selected = tokenizer["path"]
        result = dict(path=selected or pin["path"], sha256=pin["sha256"])
        pinned(result)
        if result != pin:
            moves.append(dict(source=pin, destination=result))
        return result

    manifest_pin = locate(original["manifest"])
    manifest = load(pinned(manifest_pin))
    for entry in manifest["sets"]:
        if original["sources"][entry["name"]]["status"] != "ELIGIBLE":
            continue
        kind = "packed" if "packed" in entry["files"] else "rows"
        value = entry["files"][kind]
        value.update(locate({key: value[key] for key in ("path", "sha256")}))
    for name, value in manifest["exclusions"].items():
        for field in ("list", "withhold", "v2"):
            if field in value and field+"_sha256" in value:
                value[field] = locate(dict(path=value[field], sha256=value[field+"_sha256"]))["path"]
    write(output / "manifest.json", manifest)
    value = copy.deepcopy(original)
    value["manifest"] = file_pin(output / "manifest.json")
    pool = Pool(value["manifest"], value["room_sets"])
    value["exclusions"] = pool.files
    value["scene_exclusions"] = pool.scenes.files
    value["remove_files"] = [{**pin, **locate({key: pin[key] for key in ("path", "sha256")})}
                             for pin in value["remove_files"]]
    if value["tokenizer"]:
        value["tokenizer"] = locate(value["tokenizer"])
    for entry in value["sources"].values():
        if entry["status"] != "ELIGIBLE":
            continue
        for key in ("source", "selection"):
            if key in entry:
                entry[key] = locate(entry[key])
    value["source_scene_exclusions"]["files"] = value["scene_exclusions"]
    for name, expected in value["source_scene_exclusions"]["expected"].items():
        expected["files"] = value["scene_exclusions"]
        expected["membership_files"] = value["exclusions"]
        if value["sources"][name]["status"] == "ELIGIBLE":
            expected["source"] = value["sources"][name]["source"]
    write(output / "receipt.json", value)
    report = dict(schema="s1-pool-relocation-v1", original=selection_pin,
                  relocated=file_pin(output / "receipt.json"), manifest_before=manifest_pin,
                  manifest_after=value["manifest"], same_byte_inputs=moves,
                  row_payloads_changed=False, selection_indices_changed=False, production_authorized=False)
    write(output / "relocation.json", report)
    return report
