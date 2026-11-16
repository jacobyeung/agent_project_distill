import hashlib
from pathlib import Path

import numpy as np
from safetensors import safe_open
from transformers import AutoTokenizer

from .p3_provenance import file_pin, load, pinned, sha256, write


def model_pin(cfg):
    pose = load(pinned(cfg["streams"]["pose"]))
    if pose.get("model"):
        return pose["model"]
    for source in pose.get("sources", []):
        if source.get("receipt"):
            receipt = load(pinned(source["receipt"]))
            if receipt.get("model"):
                return receipt["model"]
    raise ValueError("Parent grounding requires the pose source's pinned base-model manifest")


def bind(cfg, output):
    from . import carrier_c1_run as run, full_ft, mdg_inputs, rehearsal
    from .mask_grounding_head import load_artifact
    from .mdg_targets import build_confusers
    output = Path(output)
    spec = cfg.get("init_artifact")
    if not isinstance(spec, dict) or spec.get("lm") != "full":
        raise ValueError("Parent grounding requires an explicit full-LM warm start")
    base_pin = model_pin(cfg)
    base = load(pinned(base_pin))
    base_root = Path(base["root"])
    for name, digest in base["files"].items():
        if name.endswith((".safetensors", ".bin", ".pt")):
            continue
        if Path(name).name != name or sha256(base_root / name) != digest:
            raise ValueError("Parent tokenizer or architecture metadata differs")
    architecture = load(base_root / "config.json")
    local = run.init_mirror(spec["artifact"])
    parent_path = local / "artifact.json" if local else pinned(spec["artifact"])
    if sha256(parent_path) != spec["artifact"]["sha256"]:
        raise ValueError("Parent artifact differs")
    parent = load(parent_path)
    if (parent.get("schema") != "carrier-c1-artifact-v1" or parent.get("base_identity") != cfg["base_identity"]
            or parent.get("base_identity") != base["base_identity"]):
        raise ValueError("Parent grounding base identity differs")
    weights_path = local / "full_weights" / full_ft.EXPORT_MANIFEST if local else pinned(parent["full_weights"])
    if sha256(weights_path) != parent["full_weights"]["sha256"]:
        raise ValueError("Parent full-weight manifest differs")
    weights = load(weights_path)
    if weights.get("schema") != full_ft.EXPORT_SCHEMA:
        raise ValueError("Parent grounding requires the native full-weight export")
    index = load(pinned(dict(path=str(weights_path.parent / weights["index"]["name"]),
                             sha256=weights["index"]["sha256"])))
    names = [name for name in index["weight_map"] if name.endswith("embed_tokens.weight")]
    if len(names) != 1:
        raise ValueError("Parent input-embedding tensor is ambiguous")
    tensor_name = names[0]
    shard_name = index["weight_map"][tensor_name]
    if Path(shard_name).name != shard_name:
        raise ValueError("Parent embedding shard is outside its export")
    matches = [entry for entry in weights["files"] if entry["name"] == shard_name]
    if len(matches) != 1:
        raise ValueError("Parent embedding shard lacks an exact manifest entry")
    shard = pinned(dict(path=str(weights_path.parent / shard_name), sha256=matches[0]["sha256"]))
    if shard.stat().st_size != matches[0]["bytes"]:
        raise ValueError("Parent embedding shard size differs")
    vocab = load(pinned(cfg["mdg"]["vocab"]))
    tokenizer = AutoTokenizer.from_pretrained(base_root, local_files_only=True, trust_remote_code=False)
    ids = {label: tokenizer.encode(label, add_special_tokens=False) for label in vocab}
    if not ids or any(not value for value in ids.values()):
        raise ValueError("Every grounding label needs parent-tokenizer IDs")
    selected = sorted({value for values in ids.values() for value in values})
    with safe_open(shard, framework="pt", device="cpu") as handle:
        matrix = handle.get_slice(tensor_name)
        shape = matrix.get_shape()
        if (len(shape) != 2 or shape[1] != architecture["text_config"]["hidden_size"]
                or selected[0] < 0 or selected[-1] >= shape[0]):
            raise ValueError("Parent input-embedding dimensions differ")
        table = {index: matrix[index:index+1].float().numpy()[0] for index in selected}
    if any(not np.isfinite(row).all() for row in table.values()):
        raise ValueError("Parent grounding embeddings contain bad values")
    embeddings = {label: np.mean([table[index] for index in values], 0) for label, values in ids.items()}
    confusers = build_confusers(vocab, lambda label: embeddings[label], k=10)
    shipped = load(pinned(cfg["mdg"]["confusers"]))
    changed = sorted(label for label in vocab if confusers[label] != shipped.get(label))
    write(output / "confusers.json", confusers)
    initialization = mdg_inputs.artifact(cfg["mdg"]["init_artifact"])
    head, metadata = load_artifact(Path(initialization["mdg.json"]["path"]).parent)
    if (head.cfg.lm_dim != architecture["text_config"]["hidden_size"]
            or head.cfg.vit_dim != architecture["vision_config"]["hidden_size"] or head.cfg.geo_dim):
        raise ValueError("MDG initialization is incompatible with the parent architecture")
    state = head.state_dict()
    row_digest = hashlib.sha256()
    for index, row in sorted(table.items()):
        row_digest.update(str(index).encode()+b"\0"+row.tobytes())
    proof = dict(schema="s1-parent-grounding-v1", status="PASS", parent_artifact=spec["artifact"],
                 parent_base_identity=base["base_identity"], rehearsal=rehearsal.enabled(),
                 parent_full_weights=parent["full_weights"], tokenizer_model=base_pin,
                 embedding_shard=dict(path=str(shard), sha256=matches[0]["sha256"]),
                 embedding_tensor=tensor_name, embedding_shape=shape,
                 token_rows=len(selected), embedding_rows_sha256=row_digest.hexdigest(),
                 method="rebuild-from-parent-input-embedding-rows", confusers=file_pin(output / "confusers.json"),
                 original_confusers=cfg["mdg"]["confusers"], vocab=cfg["mdg"]["vocab"],
                 confuser_classes=len(vocab), changed_confuser_classes=len(changed), changed_labels=changed,
                 init_artifact=initialization, init_step=metadata["step"],
                 exact_key_shape_coverage=True, init_tensors=len(state),
                 init_shapes={key: list(value.shape) for key, value in state.items()},
                 production_authorized=False)
    write(output / "parent_grounding.json", proof)
    return proof
