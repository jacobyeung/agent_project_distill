from .students import same_student
import hashlib
import json
import os
from pathlib import Path
import re

from .common import binding, digest_json
from .orchard_paths import resolve_read
from .provisional import load_json, require_mode, source_path, write_artifact


SCHEMA = "sft-init-adapter-v1"
SHA256 = re.compile(r"[0-9a-f]{64}")
IDENTITY_KEYS = ("init_adapter_identity", "init_adapter_sha256")


def init_adapter_identity(path, student):
    from .orchard_eval.contracts import MODEL_PINS

    directory = resolve_read(path).resolve()
    receipt_path = directory / 'PUBLISHED.json' if (directory / 'PUBLISHED.json').is_file() else directory.parent / 'PUBLISHED.json'
    receipt = json.loads(receipt_path.read_text()) if receipt_path.is_file() else None
    if receipt is None:
        raise ValueError('Initial SFT adapter requires a publication receipt')
    expected = {key: MODEL_PINS[student][key] for key in ('repo_id', 'revision')}
    if (receipt.get('schema') != 'student-publication-v1' or receipt.get('status') != 'TRAINED'
            or not same_student(receipt.get('student'), student) or receipt.get('base') != expected
            or receipt.get('provenance', {}).get('dirty') is not False):
        raise ValueError('Initial SFT publication must name the selected student and pinned base')
    name = receipt.get('adapter_directory', '')
    if not name or Path(name).name != name or name in ('.', '..'):
        raise ValueError('Initial adapter must be inside its publication')
    published_adapter = receipt_path.parent / name
    if directory == receipt_path.parent:
        directory = published_adapter
    if directory.resolve() != published_adapter.resolve() or not directory.resolve().is_relative_to(receipt_path.parent):
        raise ValueError('Initial adapter directory differs from its publication')
    pins = {key: binding(directory / filename, receipt['adapter'][f'{key}_sha256'])
            for key, filename in (('config', 'adapter_config.json'), ('weights', 'adapter_model.safetensors'))}
    config = json.loads((directory / 'adapter_config.json').read_text())
    base = str(config.get('base_model_name_or_path', ''))
    if (base != expected['repo_id'] and Path(base).name != expected['revision']
            or config.get('revision') not in (None, expected['revision'])):
        raise ValueError('Initial adapter config names a different base checkpoint')
    if (config.get('peft_type') != 'LORA' or not config.get('target_modules')
            or config.get('bias', 'none') != 'none' or config.get('modules_to_save')):
        raise ValueError('SFT initialization requires LoRA-only adapter weights')
    return {'directory': str(directory), 'base': expected, **pins, 'training_receipt': binding(receipt_path),
            'sha256': digest_json({key: value['sha256'] for key, value in pins.items()})}


def normalize_request(value):
    if (not isinstance(value, dict) or set(value) != {"weights_sha256", "published_sha256", "parent_run"}
            or any(not isinstance(value.get(key), str) or SHA256.fullmatch(value[key]) is None
                   for key in ("weights_sha256", "published_sha256"))
            or not isinstance(value.get("parent_run"), str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,200}", value["parent_run"]) is None):
        raise ValueError("Initial adapter requires content-only weights_sha256, published_sha256, and parent_run pins")
    return dict(value)


def request_for(identity):
    return {"weights_sha256": identity["weights"]["sha256"],
            "published_sha256": identity["training_receipt"]["sha256"], "parent_run": identity["parent_run"]}


def validate_request(request, identity):
    if normalize_request(request) != request_for(identity):
        raise ValueError("Initial adapter request differs from the frozen parent")


def base_content(base):
    result = {"revision": base.get("revision")}
    for field in ("files", "weight_shards"):
        pins = base.get(field)
        if not isinstance(pins, list) or not pins:
            raise ValueError("Parent base/tokenizer/processor identity requires complete file and weight pins")
        content = {}
        for pin in pins:
            if (not isinstance(pin, dict) or not isinstance(pin.get("path"), str)
                    or not isinstance(pin.get("sha256"), str) or SHA256.fullmatch(pin["sha256"]) is None):
                raise ValueError("Malformed base/tokenizer/processor content pin")
            name = Path(pin["path"]).name
            if not name or name in content:
                raise ValueError("Duplicate or missing base/tokenizer/processor filename")
            content[name] = pin["sha256"]
        result[field] = content
    if not {"config.json", "model.safetensors.index.json", "tokenizer.json", "tokenizer_config.json"} <= result["files"].keys():
        raise ValueError("Parent base/tokenizer/processor identity is incomplete")
    return result


def target_modules(base, student):
    from accelerate import init_empty_weights
    from .adapters import discover_targets
    from .students import model_class

    pin = next(pin for pin in base["files"] if Path(pin["path"]).name == "config.json")
    binding(pin["path"], pin["sha256"])
    cls = model_class(student)
    config = cls.config_class.from_dict(load_json(pin["path"]))
    with init_empty_weights(include_buffers=True):
        model = cls(config)
    return {"expected": sorted(name for names in discover_targets(model).values() for name in names),
            "modules": [name for name, _ in model.named_modules()]}


def lora_identity(config, training, layout):
    from peft import LoraConfig, TaskType
    from peft.tuners.tuners_utils import check_target_module_exists

    targets = config.get("target_modules")
    if (not isinstance(targets, (list, str)) or not targets
            or isinstance(targets, list) and (any(not isinstance(name, str) or not name for name in targets)
                                             or len(set(targets)) != len(targets))):
        raise ValueError("Invalid or duplicate LoRA target modules")
    for key, field in (("r", "lora_rank"), ("lora_alpha", "lora_alpha"), ("lora_dropout", "lora_dropout")):
        if type(config.get(key)) not in (int, float) or config[key] != training[field]:
            raise ValueError(f"Initial LoRA setting differs: {key}")
    expected = LoraConfig(task_type=TaskType.CAUSAL_LM, r=training["lora_rank"], lora_alpha=training["lora_alpha"],
                          lora_dropout=training["lora_dropout"], bias="none", target_modules=layout["expected"])
    try:
        actual = LoraConfig(**config)
        selected = sorted(name for name in layout["modules"] if check_target_module_exists(actual, name))
    except (TypeError, ValueError, re.error) as error:
        raise ValueError(f"Invalid initial LoRA adapter config: {error}") from error
    if selected != layout["expected"]:
        raise ValueError("Initial LoRA target modules differ from the exact model allowlist")
    excluded = {"base_model_name_or_path", "revision", "inference_mode", "peft_version", "target_modules"}
    actual, expected = actual.to_dict(), expected.to_dict()
    differences = [key for key in actual.keys() | expected.keys()
                   if key not in excluded and actual.get(key) != expected.get(key)]
    if differences:
        raise ValueError(f"Initial LoRA adapter options differ: {sorted(differences)}")
    return {"rank": training["lora_rank"], "alpha": training["lora_alpha"], "dropout": training["lora_dropout"],
            "target_modules_sha256": digest_json(selected)}


def prepare_identity(path, student, training, base, label, request, layout=None, with_source=False):
    from .ddp_config import TARGET_OPTIONS, VERSION

    request = normalize_request(request)
    directory = source_path(path).resolve()
    receipt_path = directory / "PUBLISHED.json" if (directory / "PUBLISHED.json").is_file() else directory.parent / "PUBLISHED.json"
    binding(receipt_path, request["published_sha256"])
    source = init_adapter_identity(directory, student)
    validate_request(request, {**source, "parent_run": request["parent_run"]})
    root = receipt_path.parent
    receipt = require_mode(load_json(receipt_path), label)
    recorded = Path(receipt.get("published_path", ""))
    parent_run = recorded.parent.name if recorded.name == "publication" else recorded.name
    if parent_run != request["parent_run"]:
        raise ValueError("Initial publication names a different parent run")
    protocol_path = root / "protocol.json"
    for name in (source["config"]["path"], source["weights"]["path"], str(protocol_path)):
        artifact = Path(name)
        if artifact.is_symlink() or not artifact.resolve().is_relative_to(root):
            raise ValueError("Initial adapter artifact escapes its publication")
    pin = binding(protocol_path, receipt.get("protocol", {}).get("sha256"))
    if not isinstance(receipt.get("protocol", {}).get("sha256"), str):
        raise ValueError("Initial publication must bind its parent protocol")
    parent = require_mode(load_json(protocol_path), label)
    if (parent.get("schema") != "provisional-student-diagnostic-protocol-v1" or not same_student(parent.get("student"), student)
            or parent.get("protocol_version") != VERSION or parent.get("selection_frozen_before_evaluation") is not True
            or parent.get("base_sha256") != digest_json(parent.get("base"))
            or base_content(parent["base"]) != base_content(base) or base.get("revision") != source["base"]["revision"]):
        raise ValueError("Initial parent base/tokenizer/processor identity differs from the new run")
    # Every targets option attaches the same LoRA allowlist; lora_identity verifies the parent's modules.
    parent_targets = parent.get("training", {}).get("targets")
    if (parent.get("training", {}).get("max_steps") is not None
            or any(parent.get("training", {}).get(key) != training[key]
                   for key in ("lora_rank", "lora_alpha", "lora_dropout"))
            or not isinstance(parent_targets, str) or parent_targets not in TARGET_OPTIONS):
        raise ValueError("Initial parent LoRA training settings differ from the new run")
    config = load_json(source["config"]["path"])
    lora = lora_identity(config, training, layout if layout is not None else target_modules(base, student))
    identity = {"schema": SCHEMA, "base": source["base"], "sha256": source["sha256"], "parent_run": parent_run,
                "config": {"sha256": source["config"]["sha256"]}, "weights": {"sha256": source["weights"]["sha256"]},
                "training_receipt": {"sha256": source["training_receipt"]["sha256"]},
                "parent_protocol_sha256": pin["sha256"], "base_content_sha256": digest_json(base_content(base)), "lora": lora}
    for item in (source["config"], source["training_receipt"], pin):
        binding(item["path"], item["sha256"])
    return (identity, source) if with_source else identity


def validate_identity(protocol):
    if not any(key in protocol for key in IDENTITY_KEYS):
        return None
    from .orchard_eval.contracts import MODEL_PINS

    identity = protocol.get("init_adapter_identity")
    fields = {"schema", "base", "sha256", "parent_run", "config", "weights", "training_receipt",
              "parent_protocol_sha256", "base_content_sha256", "lora"}
    if (not isinstance(identity, dict) or set(identity) != fields or identity.get("schema") != SCHEMA
            or protocol.get("init_adapter_sha256") != digest_json(identity)):
        raise ValueError("Frozen initial adapter identity or hash changed")
    for key in ("config", "weights", "training_receipt"):
        pin = identity[key]
        if (not isinstance(pin, dict) or set(pin) != {"sha256"} or not isinstance(pin["sha256"], str)
                or SHA256.fullmatch(pin["sha256"]) is None):
            raise ValueError("Initial adapter identity must contain content hashes, never paths")
    normalize_request(request_for(identity))
    for key in ("sha256", "parent_protocol_sha256", "base_content_sha256"):
        if not isinstance(identity[key], str) or SHA256.fullmatch(identity[key]) is None:
            raise ValueError("Invalid initial adapter identity hash")
    expected_base = {key: MODEL_PINS[protocol["student"]][key] for key in ("repo_id", "revision")}
    lora, training = identity["lora"], protocol["training"]
    if (identity["base"] != expected_base or identity["base_content_sha256"] != digest_json(base_content(protocol["base"]))
            or identity["sha256"] != digest_json({key: identity[key]["sha256"] for key in ("config", "weights")})
            or not isinstance(lora, dict) or set(lora) != {"rank", "alpha", "dropout", "target_modules_sha256"}
            or any(lora[key] != training[field] for key, field in (("rank", "lora_rank"), ("alpha", "lora_alpha"), ("dropout", "lora_dropout")))
            or not isinstance(lora["target_modules_sha256"], str) or SHA256.fullmatch(lora["target_modules_sha256"]) is None):
        raise ValueError("Frozen initial adapter base or LoRA identity differs from the protocol")
    return identity


def validate_result(result, protocol):
    validate_identity(protocol)
    if any(result.get(key) != protocol.get(key) for key in IDENTITY_KEYS):
        raise ValueError("Training result differs from its frozen initial adapter")


def runtime_bindings():
    return [binding(path) for path in (Path(__file__), Path(__file__).parent / "orchard_eval/contracts.py")]


def configured_source(config_path, student):
    path = Path(config_path).with_suffix(".init_adapter.json")
    if not resolve_read(path).is_file() and os.environ.get("ORCH_DEPLOY"):
        path = Path(os.environ["ORCH_DEPLOY"]) / "scripts/orchard/configs" / f"{student}.init_adapter.json"
    source = load_json(source_path(path))
    if not isinstance(source.get("publication"), str) or not source["publication"]:
        raise ValueError("Initial adapter source sidecar requires a publication location")
    return source["publication"]


def freeze_initialization(protocol, output, label, scratch_root, config_path, configured, path,
                          weights_sha256, published_sha256, parent_run):
    from .ddp_config import VERSION

    if protocol.get("protocol_version") != VERSION:
        raise ValueError("SFT warm-start requires an explicit DDP/FSDP training config")
    request = normalize_request(configured) if configured is not None else None
    if any(value is not None for value in (weights_sha256, published_sha256, parent_run)):
        explicit = normalize_request({"weights_sha256": weights_sha256, "published_sha256": published_sha256,
                                      "parent_run": parent_run})
        if request is not None and explicit != request:
            raise ValueError("Initial adapter CLI pins differ from the training config")
        request = explicit
    if request is None:
        raise ValueError("Initial adapter requires expected weights, publication hash, and parent run")
    path = path if path is not None else configured_source(config_path, protocol["student"])
    identity = prepare_identity(path, protocol["student"], protocol["training"], protocol["base"], label, request)
    protocol.update(init_adapter_identity=identity, init_adapter_sha256=digest_json(identity))
    protocol["runtime"] += runtime_bindings()
    source = {"schema": "sft-init-adapter-location-v1", "publication": str(source_path(path).resolve()),
              "init_adapter_sha256": protocol["init_adapter_sha256"]}
    write_artifact(Path(output).with_suffix(".init_adapter.json"), source, label, scratch_root)


def initialize_adapters(model, report, protocol, protocol_path, resume_from=None, init_adapter=None):
    identity = validate_identity(protocol)
    if identity is None:
        if init_adapter is not None:
            raise ValueError("An initial adapter must be frozen at prepare time")
        return report
    result = {**report, "initialization": identity, "initialization_applied": False}
    # A resume restores trainable groups from its checkpoint; frozen groups exist only in the parent.
    if resume_from is not None and not report.get("frozen_group_parameters"):
        return result
    import torch
    from peft import get_peft_model_state_dict, set_peft_model_state_dict
    from safetensors.torch import load

    if init_adapter is None:
        location = load_json(source_path(Path(protocol_path).with_suffix(".init_adapter.json")))
        if location.get("init_adapter_sha256") != protocol["init_adapter_sha256"]:
            raise ValueError("Initial adapter source sidecar belongs to a different parent")
        init_adapter = location["publication"]
    layout = {"expected": sorted(name for names in report["targets"].values() for name in names),
              "modules": [name for name, _ in model.get_base_model().named_modules()]}
    live_config = model.peft_config["default"].to_dict()
    if isinstance(live_config["target_modules"], set):
        live_config["target_modules"] = sorted(live_config["target_modules"])
    if lora_identity(live_config, protocol["training"], layout) != identity["lora"]:
        raise ValueError("Live LoRA adapter differs from the frozen parent")
    actual, source = prepare_identity(init_adapter, protocol["student"], protocol["training"], protocol["base"],
                                      protocol["provisional_diagnostic"], request_for(identity), layout=layout, with_source=True)
    if actual != identity:
        raise ValueError("Initial adapter differs from the frozen parent identity")
    payload = Path(source["weights"]["path"]).read_bytes()
    if hashlib.sha256(payload).hexdigest() != source["weights"]["sha256"]:
        raise ValueError("Initial adapter tensor bytes changed while loading")
    saved = load(payload)
    restored = get_peft_model_state_dict(model, save_embedding_layers=False)
    if (set(saved) != set(restored) or any(saved[name].shape != value.shape or saved[name].dtype != value.dtype
                                         or saved[name].dtype != torch.float32 or not bool(torch.isfinite(saved[name]).all())
                                         for name, value in restored.items())):
        raise ValueError("Initial adapter tensor names, shapes, dtypes, or finite values differ")
    set_peft_model_state_dict(model, saved)
    restored = get_peft_model_state_dict(model, save_embedding_layers=False)
    if any(not torch.equal(value.detach().cpu(), saved[name]) for name, value in restored.items()):
        raise ValueError("Reloaded SFT adapter tensors differ from the publication")
    trainable = [(name, value) for name, value in model.named_parameters() if value.requires_grad]
    vision_lookup = set()
    if report.get("unfreeze_vision_blocks"):
        from .adapters import discover_vision_block_parameters
        vision_lookup = {name for name, _ in discover_vision_block_parameters(model)}
    if not trainable or any((name not in vision_lookup) and (".lora_" not in name or value.dtype != torch.float32)
                            for name, value in trainable):
        raise ValueError("Only FP32 LoRA tensors (and unfrozen vision blocks when enabled) may be trainable")
    if resume_from is not None:
        return {**result, "frozen_groups_reloaded_from_parent": sorted(report["frozen_group_parameters"]),
                "exact_tensor_equality": True, "initialization_source": source}
    return {**result, "initialization_applied": True, "exact_tensor_equality": True, "initialization_source": source}
