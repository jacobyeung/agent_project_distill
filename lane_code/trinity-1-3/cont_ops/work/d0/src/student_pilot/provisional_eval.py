from pathlib import Path

from .common import binding, digest_json, load_json
from .provisional import adapter_directory, require_mode


GEOMETRY_DIRECTORY = "geometry"
FULL_WEIGHTS_DIRECTORY = "full_weights"  # full_ft.EXPORT_DIRECTORY, without importing torch on the LoRA path
AUXILIARY_HEADS = "auxiliary_heads.pt"
AUXILIARY_MANIFEST = "auxiliary_heads.json"


def full_ft_receipt(receipt):
    """True for the receipt of a full fine-tuning publication (full weights or the frozen-VLM stage)."""
    adapter = receipt.get("adapter")
    return isinstance(adapter, dict) and ("full_weights_manifest_sha256" in adapter or adapter.get("frozen_vlm") is True)


def validate_publication(receipt, receipt_path, adapter, model, config, label, geometry_store=None, full_ft=False):
    """Admit a labeled publication. Returns what an evaluator needs beyond the LoRA files:
    {"weights": "lora" | "full_weights" | "frozen_vlm", "geometry": normalized block or None,
     "export": the verified full-weights export manifest or None, "full_ft": the result's full_ft record or None,
     "auxiliary_heads": the census entry of auxiliary_heads.pt or None, "camera": the camera settings or None}.

    A geometry-input publication is admitted only with an explicit eval feature store (`geometry_store`), and a
    full fine-tuning publication only for a caller that loads full weights (`full_ft=True`); only the orchard
    evaluator passes either, so every other caller refuses both."""
    from .benchmark_eval.contracts import MODEL_PINS, SHA_RE
    from .orchard_paths import enabled
    if enabled():
        from .orchard_eval.contracts import MODEL_PINS
    from .students import training_parameters

    rgb = {"frame_count": 32, "do_sample_frames": False, "size": config["rgb"]["size"],
           "timing": "original_source_indices_and_fps_native_processor", "question_options": "verbatim; null options mean no options"}

    require_mode(receipt, label)
    expected = MODEL_PINS[model]
    full = full_ft_receipt(receipt)
    if full and not full_ft:
        raise ValueError("Full fine-tuning publications are evaluated only by the orchard evaluator")
    if (receipt.get("schema") != "student-publication-v1" or receipt.get("status") != "TRAINED"
            or receipt.get("student") != model
            or receipt.get("base") != {key: expected[key] for key in ("repo_id", "revision")}
            or receipt.get("base_restart") != "fresh_load_of_original_snapshot_no_smoke_adapter"
            or receipt.get("preprocessing") != rgb
            or any(rgb[key] != config["rgb"][key] for key in ("frame_count", "do_sample_frames", "size"))
            or (set(receipt.get("trained_module_families", [])) != {"vision", "merger", "language"} if not full
                else not isinstance(receipt.get("trained_module_families"), list))
            or receipt.get("provenance", {}).get("dirty") is not False):
        raise ValueError("Provisional publication/base/preprocessing lineage is missing or incompatible")
    for name in ("training_data_sha256", "PROVISIONAL_DIVISION_SHA"):
        if not isinstance(receipt.get(name), str) or not SHA_RE.fullmatch(receipt[name]):
            raise ValueError(f"Missing provisional lineage binding: {name}")
    root = Path(receipt_path).resolve().parent
    directory = adapter_directory(label)
    if (Path(receipt.get("published_path", "")).resolve() != root
            or receipt.get("adapter_directory") != directory or Path(adapter).resolve() != root / directory):
        raise ValueError("Adapter and receipt must belong to the labeled publication directory")
    manifest_pin = receipt["sha256_manifest"]
    if Path(manifest_pin["path"]).resolve() != root / "SHA256_MANIFEST.json":
        raise ValueError("Provisional publication manifest escapes its directory")
    binding(manifest_pin["path"], manifest_pin["sha256"])
    manifest = require_mode(load_json(manifest_pin["path"]), label)
    if (manifest.get("schema") != "student-publication-sha256-v1" or manifest.get("PROVISIONAL_DIVISION_SHA") != receipt["PROVISIONAL_DIVISION_SHA"]
            or manifest.get("provenance") != receipt["provenance"] or receipt.get("file_count") != len(manifest["files"])):
        raise ValueError("Provisional publication census, provenance, or division changed")
    for name in manifest["files"]:
        path = (root / name).resolve()
        if not path.is_relative_to(root) or path == root or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Provisional publication file escapes its directory")
    result_pin = receipt["training_result"]
    if Path(result_pin["path"]).resolve() != root / "training_result.json":
        raise ValueError("Training result must be the portable published copy")
    binding(result_pin["path"], result_pin["sha256"])
    result = require_mode(load_json(result_pin["path"]), label)
    if (result.get("schema") != "completed-provisional-diagnostic-training-v1" or result.get("status") != "TRAINED"
            or result.get("student") != model or result.get("base", {}).get("revision") != expected["revision"]
            or result.get("base_restart") != receipt["base_restart"]
            or result.get("PROVISIONAL_DIVISION_SHA") != receipt["PROVISIONAL_DIVISION_SHA"]
            or result.get("training_manifest", {}).get("sha256") != receipt["training_data_sha256"]
            or result.get("protocol_version") is None and result.get("adapter_parameters") != training_parameters(model)
            or result.get("provenance", {}).get("dirty") is not False
            or bool(result.get("synthetic")) != bool(receipt.get("synthetic"))
            or type(result.get("realized", {}).get("optimizer_steps")) is not int or result["realized"]["optimizer_steps"] < 1):
        raise ValueError("Published provisional training result is incomplete or inconsistent")
    expected_files = {"training_result.json": result_pin["sha256"]}
    for name in ("protocol", "division"):
        pin = receipt[name]
        if Path(pin["path"]).resolve() != root / f"{name}.json":
            raise ValueError("Provisional protocol/division must use portable published copies")
        binding(pin["path"], pin["sha256"])
        expected_files[f"{name}.json"] = pin["sha256"]
    protocol = require_mode(load_json(receipt["protocol"]["path"]), label)
    division = require_mode(load_json(receipt["division"]["path"]), label)
    if (protocol.get("schema") != "provisional-student-diagnostic-protocol-v1"
            or protocol.get("student") != model or protocol.get("division") != division
            or protocol.get("PROVISIONAL_DIVISION_SHA") != receipt["PROVISIONAL_DIVISION_SHA"]
            or digest_json(division) != receipt["PROVISIONAL_DIVISION_SHA"]
            or receipt["protocol"]["sha256"] != result.get("protocol", {}).get("sha256")):
        raise ValueError("Published provisional protocol/division lineage changed")
    settings = camera = None
    if any(value.get("protocol_version") is not None for value in (protocol, result, receipt)):
        from .ddp_config import validate_camera_protocol, validate_training_result
        settings = validate_training_result(result, protocol, label)
        if receipt.get("protocol_version") != settings["version"]:
            raise ValueError("Publication changed the training protocol version")
        camera = validate_camera_protocol(protocol)
    census = manifest["files"]
    block = settings.get("full_ft") if settings is not None else None
    if full != (block is not None):
        raise ValueError("Publication receipt and training result disagree on full fine-tuning")
    export_prefix = f"{directory}/{FULL_WEIGHTS_DIRECTORY}/"
    weights = "lora"
    if full:
        from .full_ft import EXPORT_MANIFEST, frozen_vlm
        weights = "frozen_vlm" if frozen_vlm(block) else "full_weights"
        geometry_keys = {"geometry_weights_sha256"} if result.get("geometry") is not None else set()
        if (receipt.get("trained_module_families") != [group for group, on in block["train"].items() if on]
                or not isinstance(result.get("full_ft"), dict) or result["full_ft"].get("train") != block["train"]
                or "auxiliary_heads" not in result):
            raise ValueError("Full fine-tuning publication families or settings differ from its training result")
        if weights == "full_weights":
            pin = result["adapter"]["full_weights"]
            if (set(result["adapter"]) != {"full_weights", "full_weights_bytes", "full_weights_tensors"}
                    or set(receipt["adapter"]) != {"full_weights_manifest_sha256", *geometry_keys}
                    or not isinstance(pin, dict) or receipt["adapter"]["full_weights_manifest_sha256"] != pin.get("sha256")):
                raise ValueError("Full-weights publication adapter differs from its training result")
            expected_files[export_prefix + EXPORT_MANIFEST] = pin["sha256"]
        elif result["adapter"] != {"frozen_vlm": True} or set(receipt["adapter"]) != {"frozen_vlm", *geometry_keys}:
            raise ValueError("Frozen-VLM publication adapter differs from its training result")
        allowed = {f"{directory}/provenance.json"}
        if any(name.startswith(f"{directory}/") and name not in allowed and not name.startswith(export_prefix) for name in census):
            raise ValueError("A full fine-tuning publication mixes in LoRA or other adapter files")
        if weights == "frozen_vlm" and any(name.startswith(export_prefix) for name in census):
            raise ValueError("A frozen-VLM publication cannot publish full weights")
    else:
        if any(name.startswith(export_prefix) for name in census) or "full_ft" in result:
            raise ValueError("A LoRA publication cannot publish full weights")
        adapter_items = [("config", "adapter_config.json"), ("weights", "adapter_model.safetensors")]
        if "vision_blocks" in result.get("adapter", {}) or "vision_blocks_sha256" in receipt.get("adapter", {}):
            adapter_items.append(("vision_blocks", "vision_blocks.safetensors"))
        for kind, filename in adapter_items:
            expected_files[f"{directory}/{filename}"] = result["adapter"][kind]["sha256"]
            if result["adapter"][kind]["sha256"] != receipt["adapter"][f"{kind}_sha256"]:
                raise ValueError("Publication adapter hashes disagree with the training result")
    provenance_name = f"{directory}/provenance.json"
    if provenance_name not in manifest["files"]:
        raise ValueError("The adapter directory lacks its provisional provenance")
    expected_files[provenance_name] = manifest["files"][provenance_name]["sha256"]
    for name, digest in expected_files.items():
        if manifest["files"].get(name, {}).get("sha256") != digest:
            raise ValueError("Required training/adapter bytes are absent from the publication census")
        path = root / name
        binding(path, digest)
        if path.stat().st_size != manifest["files"][name]["bytes"]:
            raise ValueError("Provisional publication file size changed")
    require_mode(load_json(root / provenance_name), label)
    export = export_census(root, directory, census, result, protocol, model) if weights == "full_weights" else None
    heads = auxiliary_census(root, census, result, full)
    if camera is not None and (heads is None or not isinstance(heads["manifest"], dict)
                               or not isinstance(heads["manifest"].get("camera"), dict)
                               or heads["manifest"]["camera"].get("settings") != camera):
        raise ValueError("A camera-head publication must publish its auxiliary heads with the protocol's camera settings")
    return {"weights": weights, "geometry": publication_geometry(root, census, settings, result, receipt, geometry_store),
            "export": export, "full_ft": result.get("full_ft") if full else None, "auxiliary_heads": heads, "camera": camera,
            "headcall": settings.get("headcall") if settings is not None else None}


def export_census(root, directory, census, result, protocol, model):
    """The full-weights export manifest of a publication whose census holds exactly the export's files.

    The census must name the manifest, the index and every shard with the manifest's sha256 and sizes, the export
    must describe this result's tensors and base, and full_ft.read_export then hashes every shard against it."""
    from .full_ft import EXPORT_DIRECTORY, EXPORT_MANIFEST, read_export

    if EXPORT_DIRECTORY != FULL_WEIGHTS_DIRECTORY:
        raise ValueError("Full-weights export directory changed")
    prefix = f"{directory}/{EXPORT_DIRECTORY}/"
    folder = root / directory / EXPORT_DIRECTORY
    if folder.is_symlink() or (root / directory).is_symlink() or not folder.resolve().is_relative_to(root):
        raise ValueError("Full-weights export escapes its publication")
    export = load_json(folder / EXPORT_MANIFEST)
    files, index = export.get("files"), export.get("index")
    if (not isinstance(files, list) or not files or not isinstance(index, dict)
            or any(not isinstance(item, dict) or not isinstance(item.get("name"), str) or Path(item["name"]).name != item["name"]
                   for item in [index, *files])):
        raise ValueError("Malformed full-weights export manifest")
    names = {name for name in census if name.startswith(prefix)}
    if names != {prefix + EXPORT_MANIFEST, prefix + index["name"], *(prefix + item["name"] for item in files)} or len(names) != len(files) + 2:
        raise ValueError("Full-weights census differs from its export manifest")
    if census[prefix + index["name"]]["sha256"] != index.get("sha256"):
        raise ValueError("Full-weights index differs from the publication census")
    for item in files:
        if census[prefix + item["name"]] != {"sha256": item.get("sha256"), "bytes": item.get("bytes")}:
            raise ValueError(f"Full-weights shard differs from the publication census: {item['name']}")
    if (export.get("tensor_count") != result["adapter"]["full_weights_tensors"]
            or export.get("bytes") != result["adapter"]["full_weights_bytes"]
            or export.get("base") != {"student": model, "base": protocol.get("base"), "base_sha256": protocol.get("base_sha256")}
            or not isinstance(export.get("training"), dict)
            or export["training"].get("mode") != result["full_ft"].get("mode")
            or export["training"].get("train") != result["full_ft"]["train"]):
        raise ValueError("Full-weights export describes another training result or base")
    read_export(folder)
    return export


def auxiliary_census(root, census, result, full):
    """The published auxiliary_heads.pt (census entry plus its JSON manifest), or None.

    A full fine-tuning result records the heads' binding or None, and the census must agree; a LoRA publication
    carries the file only in its census."""
    entry = census.get(AUXILIARY_HEADS)
    if full:
        recorded = result.get("auxiliary_heads")
        if (recorded is None) != (entry is None) or recorded is not None and (
                not isinstance(recorded, dict) or recorded.get("sha256") != entry["sha256"]):
            raise ValueError("Published auxiliary heads differ from the training result")
    if entry is None:
        return None
    path = root / AUXILIARY_HEADS
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError("Auxiliary heads escape their publication")
    binding(path, entry["sha256"])
    if path.stat().st_size != entry["bytes"]:
        raise ValueError("Auxiliary heads size changed")
    heads_manifest = None
    if AUXILIARY_MANIFEST in census:
        binding(root / AUXILIARY_MANIFEST, census[AUXILIARY_MANIFEST]["sha256"])
        heads_manifest = load_json(root / AUXILIARY_MANIFEST)
        if not isinstance(heads_manifest, dict) or heads_manifest.get("weights", {}).get("sha256") != entry["sha256"]:
            raise ValueError("Auxiliary heads manifest names other weights")
    return {"name": AUXILIARY_HEADS, "sha256": entry["sha256"], "bytes": entry["bytes"], "manifest": heads_manifest}


def publication_geometry(root, census, settings, result, receipt, geometry_store):
    """The geometry block of a publication whose census, bytes and training result hold exactly its projector, or None.

    Refuses a block without its two files, geometry files or a recorded projector without a block, projector hashes
    that differ from the training result or the receipt, published settings that differ from the training config, a
    geometry publication without an eval store, and a store without one."""
    block = settings.get("geometry") if settings is not None else None
    names = sorted(name for name in census if Path(name).parts[:1] == (GEOMETRY_DIRECTORY,))
    if block is None:
        if (names or (root / GEOMETRY_DIRECTORY).exists() or (root / GEOMETRY_DIRECTORY).is_symlink()
                or result.get("geometry") is not None or "geometry_weights_sha256" in receipt.get("adapter", {})):
            raise ValueError("Geometry projector files are published without a geometry training block")
        if geometry_store is not None:
            raise ValueError("A geometry eval store applies only to a geometry-input publication")
        return None
    from . import geometry_input
    if geometry_store is None:
        raise ValueError("A geometry-input publication is evaluated only with an explicit geometry eval store")
    expected = {key: f"{GEOMETRY_DIRECTORY}/{name}"
                for key, name in (("manifest", geometry_input.MANIFEST_NAME), ("weights", geometry_input.WEIGHTS_NAME))}
    if names != sorted(expected.values()):
        raise ValueError("A geometry-input publication must hold exactly its projector manifest and weights")
    digests = {}
    for key, name in expected.items():
        path = root / name
        if path.is_symlink() or path.parent.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("Geometry publication file escapes its directory")
        digests[key] = binding(path, census[name]["sha256"])["sha256"]
        if path.stat().st_size != census[name]["bytes"]:
            raise ValueError("Geometry publication file size changed")
    recorded = result.get("geometry")
    if (not isinstance(recorded, dict) or any(not isinstance(recorded.get(key), dict) or recorded[key].get("sha256") != digest
                                              for key, digest in digests.items())
            or receipt.get("adapter", {}).get("geometry_weights_sha256") != digests["weights"]):
        raise ValueError("Published geometry projector hashes differ from the training result")
    published = load_json(root / expected["manifest"])
    if (not isinstance(published, dict) or published.get("schema") != geometry_input.SCHEMA
            or geometry_input.normalize(published.get("settings")) != block
            or published.get("weights") != {"path": geometry_input.WEIGHTS_NAME, "sha256": digests["weights"]}):
        raise ValueError("Published geometry settings or projector hash differ from the training config")
    return block
