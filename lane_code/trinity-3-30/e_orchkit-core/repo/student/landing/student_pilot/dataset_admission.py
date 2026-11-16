from pathlib import Path

from .dataset_builder import bound_json, native_answer, prepare_bound_target, require


def prepare_clean_index(index, index_path, workspace_root, media, answer_tag):
    from .clean_conversion import POOL, load_admitted

    require(index.get("source_pool") == POOL and index.get("original_weights_required") is True,
            "The native admission index must select the clean VSI-590K pool and original student weights")
    manifest, manifest_pin = bound_json(index.get("manifest"), workspace_root, index_path.parent)
    verified = load_admitted(workspace_root, index_path)
    require(manifest == verified, "Native admission verifier returned a different manifest")
    snapshot, snapshot_pin = bound_json(manifest.get("snapshot"), workspace_root, Path(manifest_pin["path"]).parent)
    require(isinstance(snapshot.get("rows"), list), "Native source snapshot has no row census")
    sources = {row["qid"]: row for row in snapshot["rows"]}
    require(len(sources) == len(snapshot["rows"]), "Native source snapshot repeats question IDs")
    prepared = []
    for row in manifest["rows"]:
        require(row["qid"] in sources and row.get("source_pool") == POOL, "Admitted row is absent from the clean source snapshot")
        source = sources[row["qid"]]
        conversion = row["conversion"]
        require(conversion.get("semantic_grounding_verified") is True and source.get("status") == "ready"
                and source.get("media", {}).get("pixels_verified") is True, "Native source or independent grounding review is not admitted")
        target, target_pin = bound_json(conversion.get("candidate"), workspace_root, Path(manifest_pin["path"]).parent)
        require(target.get("target") == row["target"], "Admitted target text disagrees with its candidate")
        _, review_pin = bound_json(conversion.get("review"), workspace_root, Path(manifest_pin["path"]).parent)
        original = source["source_row"]
        require(row["dataset"] == original["dataset"] and row["scene"] == source["media"]["physical_scene"],
                "Native runtime scene disagrees with the physical source scene")
        binding = {"schema": "student-source-binding-v1", "source_pool": "nyu-visionx/VSI-590K",
                   **{key: row[key] for key in ("qid", "dataset", "category", "student_input")}, "scene": original["scene_name"],
                   "native_answer": native_answer(source["native_answer_archive"]["native_final"]),
                   "request": conversion["request"], "source_terminal": source["terminal"],
                   "fixture_only": source.get("fixture_only") is True or snapshot.get("fixture_only") is True}
        prepared.append(prepare_bound_target(target, target_pin, binding, snapshot_pin, review_pin,
                                             workspace_root, media, answer_tag))
    return prepared
