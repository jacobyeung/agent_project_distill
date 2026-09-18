import argparse
import hashlib
import json
import statistics
from pathlib import Path

from torch.utils.data import Dataset

from .common import MODEL, canonical_bytes, digest_json
from .dataset_builder import (INPUT_FIELDS, SCHEMA, DatasetBuildError, canonical_scene, parse_json,
                              require, scene_partition, scoped_path, split_proof, text_sha256, validate_prompt)


class StudentDataset(Dataset):
    def __init__(self, manifest, workspace_root, split="train", allow_fixtures=False):
        require(split in ("train", "validation", "all"), "Split must be train, validation, or all")
        self.workspace_root = Path(workspace_root).absolute()
        self.manifest_path = scoped_path(manifest, self.workspace_root, Path.cwd())
        self.directory = self.manifest_path.parent
        raw_manifest = self.manifest_path.read_bytes()
        self.manifest_sha256 = hashlib.sha256(raw_manifest).hexdigest()
        self.manifest = parse_json(raw_manifest)
        require(isinstance(self.manifest, dict) and self.manifest.get("schema") == SCHEMA, "Unexpected training manifest schema")
        require(allow_fixtures or self.manifest.get("fixture_only") is False, "Synthetic fixture datasets require explicit allow_fixtures=True")
        require(self.manifest.get("training_eligible") is True or allow_fixtures and self.manifest.get("fixture_only") is True,
                "Manifest is not eligible for training")
        examples = self.manifest.get("examples")
        require(isinstance(examples, list) and len(examples) == self.manifest.get("example_count"), "Manifest example census mismatch")
        require(len({row["qid"] for row in examples}) == len(examples), "Manifest has duplicate question IDs")
        for row in examples:
            require(canonical_scene(row["dataset"], row["scene"]) == row["physical_scene_id"], "Manifest physical scene identity drift")
            require(row["split"] == scene_partition(row["physical_scene_id"], self.manifest["split_seed"], self.manifest["validation_fraction"]),
                    "Manifest scene partition drift")
            require(len(row["frames"]) == 32 and len(row["frame_order"]) == 32
                    and row["frame_order_sha256"] == digest_json(row["frame_order"]), "Manifest frame order drift")
        proof = self._bound_json(self.manifest["split_proof"])
        require(proof == split_proof(examples, self.manifest["split_seed"], self.manifest["validation_fraction"]),
                "Written split proof differs from the manifest census")
        expected = {(row["shard"], row["record_index"]): row for row in examples}
        require(len(expected) == len(examples), "Manifest record locations are not unique")
        self.locations, self.rows = [], []
        seen, shard_names = set(), set()
        for shard in self.manifest["shards"]:
            require(shard["path"] not in shard_names, "Duplicate shard path")
            shard_names.add(shard["path"])
            path = self._dataset_path(shard["path"])
            digest, count = hashlib.sha256(), 0
            with path.open("rb") as stream:
                while True:
                    offset = stream.tell()
                    line = stream.readline()
                    if not line:
                        break
                    digest.update(line)
                    identity = (shard["path"], count)
                    require(identity in expected, "Shard contains a record absent from the manifest")
                    row = expected[identity]
                    require(hashlib.sha256(line).hexdigest() == row["record_sha256"] and row["split"] == shard["split"],
                            "Shard record hash or partition mismatch")
                    seen.add(identity)
                    if split in ("all", row["split"]):
                        self.locations.append((path, offset, len(line)))
                        self.rows.append(row)
                    count += 1
            require(count == shard["rows"] and digest.hexdigest() == shard["sha256"], "Shard file hash or record count mismatch")
        require(seen == set(expected), "Some manifest examples have no shard record")
        self.split = split

    def _dataset_path(self, path):
        require(isinstance(path, str) and not Path(path).is_absolute(), "Dataset members must have relative paths")
        resolved = scoped_path(path, self.workspace_root, self.directory)
        require(resolved.is_relative_to(self.directory), "Dataset member escapes its package")
        return resolved

    def _bound_json(self, pin):
        path = self._dataset_path(pin["path"])
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == pin["sha256"], "Dataset member hash mismatch")
        return parse_json(data)

    def __len__(self):
        return len(self.locations)

    def __getitem__(self, index):
        path, offset, length = self.locations[index]
        expected = self.rows[index]
        with path.open("rb") as stream:
            stream.seek(offset)
            data = stream.read(length)
        require(hashlib.sha256(data).hexdigest() == expected["record_sha256"], "Shard record changed after Dataset initialization")
        record = parse_json(data)
        require(isinstance(record, dict) and set(record) == {"qid", "physical_scene_id", "split", "student_input", "messages"},
                "Training record fields differ from the RGB-only schema")
        require(all(record[key] == expected[key] for key in ("qid", "physical_scene_id", "split")), "Record identity differs from the manifest")
        inputs = record["student_input"]
        require(isinstance(inputs, dict) and set(inputs) == INPUT_FIELDS, "Student input contains unexpected fields")
        prompt = validate_prompt(inputs["question"], inputs["options"])
        require(text_sha256(inputs["question"]) == expected["question_sha256"] and digest_json(inputs["options"]) == expected["options_sha256"],
                "Record question/options hash mismatch")
        require(inputs["frames"] == expected["frames"] and len(inputs["frame_indices"]) == len(inputs["timestamps"]) == 32,
                "Record frames or timing counts differ from the manifest")
        order = [{"position": position, "original_frame_index": inputs["frame_indices"][position],
                  "timestamp": inputs["timestamps"][position], "sha256": frame["sha256"]} for position, frame in enumerate(inputs["frames"])]
        require(order == expected["frame_order"], "Record frame order differs from the manifest")
        messages = record["messages"]
        require(isinstance(messages, list) and len(messages) == 2 and isinstance(messages[1], dict), "Expected exactly user and assistant turns")
        target = messages[1].get("content")
        require(isinstance(target, str) and text_sha256(target) == expected["rendered_target_sha256"], "Rendered assistant target hash mismatch")
        require(messages == [{"role": "user", "content": [{"type": "image", "image": frame["path"]} for frame in inputs["frames"]]
                             + [{"type": "text", "text": prompt}]}, {"role": "assistant", "content": target}],
                "Chat record differs from its allowlisted student-input projection")
        frames = [{"path": str(self._dataset_path(frame["path"])), "sha256": frame["sha256"]} for frame in inputs["frames"]]
        return {"qid": record["qid"], "student_input": {**inputs, "options": inputs["options"] or [], "frames": frames}, "target": target}


class SmokeCollator:
    def __init__(self, processor):
        self.processor = processor
        self.last_audit = None

    def __call__(self, rows):
        from .batches import encode_row

        require(len(rows) == 1, "The existing smoke encoder requires microbatch size one")
        batch, self.last_audit = encode_row(self.processor, rows[0])
        return batch


class MockByteTokenizer:
    eos_token = "<eos>"
    eos_token_id = 257
    pad_token_id = 0

    def encode(self, text, add_special_tokens=False):
        parts = text.split(self.eos_token)
        ids = []
        for index, part in enumerate(parts):
            if index:
                ids.append(self.eos_token_id)
            ids.extend(byte + 1 for byte in part.encode("utf-8"))
        return ids

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False, **kwargs):
        text = ""
        for message in messages:
            content = message["content"]
            if isinstance(content, list):
                content = "".join("<image>" if item["type"] == "image" else item["text"] for item in content)
            text += "<" + message["role"] + ">" + content + self.eos_token
        if add_generation_prompt:
            text += "<assistant>"
        return self.encode(text) if tokenize else text


def model_specs():
    path = Path(__file__).resolve().parents[1] / "configs/student_benchmark_eval_v1.json"
    specs = parse_json(path.read_bytes())["models"]
    require(set(specs) == {"onethinker", "qwen35"}, "Both pinned student model configurations are required")
    return specs


def load_offline_tokenizer(model, path, workspace_root):
    metadata = {"mocked": False, "reason": None, "requested_path": str(path), "local_files_only": True, "trust_remote_code": False}
    try:
        local = scoped_path(path, workspace_root, Path.cwd())
    except DatasetBuildError:
        return MockByteTokenizer(), {**metadata, "mocked": True, "reason": "Tokenizer path is outside the allowed workspace; no lookup was attempted"}
    if not local.is_dir():
        return MockByteTokenizer(), {**metadata, "mocked": True, "reason": "Tokenizer directory is unavailable inside the allowed workspace"}
    names = ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "added_tokens.json", "vocab.json", "merges.txt", "chat_template.jinja", "chat_template.json", "config.json")
    files = {name: scoped_path(local / name, workspace_root) for name in names}
    required = ("config.json", "chat_template.jinja", "tokenizer.json", "tokenizer_config.json")
    if any(not files[name].is_file() for name in required):
        return MockByteTokenizer(), {**metadata, "mocked": True, "reason": "Offline tokenizer or pinned model/template files are missing inside the workspace"}
    pins = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items() if path.is_file()}
    spec = model_specs()[model]
    require(pins["config.json"] == spec["config_sha256"], "Offline tokenizer model config does not match the selected student")
    require(pins["chat_template.jinja"] == spec["template_sha256"], "Offline tokenizer chat template does not match the selected student")
    metadata.update(model_config_and_template_verified=True, tokenizer_file_sha256=pins)
    try:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(local, local_files_only=True, trust_remote_code=False)
    except (OSError, ValueError, ImportError) as error:
        return MockByteTokenizer(), {**metadata, "mocked": True, "reason": f"Tokenizer could not load offline ({type(error).__name__}): {error}"}
    require(isinstance(tokenizer.eos_token, str) and bool(tokenizer.eos_token), "Loaded tokenizer must define an end-of-turn token")
    return tokenizer, metadata


def _statistics(values):
    ordered = sorted(values)
    return {"count": len(values), "min": ordered[0], "median": statistics.median(ordered),
            "p95": ordered[max(0, (95 * len(ordered) + 99) // 100 - 1)], "max": ordered[-1], "mean": statistics.mean(ordered)}


def dry_run(dataset, num_examples=8, tokenizer_paths=None):
    require(type(num_examples) is int and num_examples > 0 and len(dataset) > 0, "Dry-run requires a positive number of available examples")
    specs = model_specs()
    supplied = tokenizer_paths or {}
    require(set(supplied) <= set(specs), "Unknown tokenizer model name")
    defaults = {name: MODEL.parents[2] / f'models--{spec["repo_id"].replace("/", "--")}/snapshots/{spec["revision"]}' for name, spec in specs.items()}
    rows = [dataset[index] for index in range(min(num_examples, len(dataset)))]
    models = {}
    for name, spec in specs.items():
        tokenizer, metadata = load_offline_tokenizer(name, supplied.get(name, defaults[name]), dataset.workspace_root)
        lengths = []
        for row in rows:
            inputs = row["student_input"]
            content = [{"type": "image", "image": frame["path"]} for frame in inputs["frames"]]
            content.append({"type": "text", "text": validate_prompt(inputs["question"], inputs["options"])})
            user = [{"role": "user", "content": content}]
            template_kwargs = {} if spec.get("enable_thinking") is None else {"enable_thinking": spec["enable_thinking"]}
            prompt = tokenizer.apply_chat_template(user, tokenize=False, add_generation_prompt=True, **template_kwargs)
            full = tokenizer.apply_chat_template(user + [{"role": "assistant", "content": row["target"]}], tokenize=False,
                                                 add_generation_prompt=False, **template_kwargs)
            lengths.append({"qid": row["qid"], "prompt_text_tokens": len(tokenizer.encode(prompt, add_special_tokens=False)),
                            "assistant_text_tokens_including_eos": len(tokenizer.encode(row["target"] + tokenizer.eos_token, add_special_tokens=False)),
                            "sequence_text_tokens": len(tokenizer.encode(full, add_special_tokens=False)), "template_prefix_matches": full.startswith(prompt)})
        models[name] = {**metadata, "repo_id": spec["repo_id"], "revision": spec["revision"],
                        "tokenizer_kind": "mock_utf8_bytes_not_model_tokens" if metadata["mocked"] else "offline_model_tokenizer",
                        "model_token_lengths_verified": not metadata["mocked"], "visual_expansion_measured": False,
                        "measurement_scope": "Chat text and unexpanded image placeholders only; not the smoke video's expanded multimodal sequence length",
                        "template_prefix_matches_all": all(row["template_prefix_matches"] for row in lengths), "per_example": lengths,
                        **{key: _statistics([row[key] for row in lengths]) for key in ("prompt_text_tokens", "assistant_text_tokens_including_eos", "sequence_text_tokens")}}
    return {"schema": "student-dataset-tokenizer-dry-run-v1", "manifest_sha256": dataset.manifest_sha256, "examples": len(rows),
            "selection": "First N examples in deterministic shard order", "models": models, "truncation": False,
            "provider_calls": 0, "gpu_runs": 0, "training_readiness_verified": False,
            "required_before_training": "Run the real model processor through SmokeCollator; verify full visual expansion, masks, and context fit"}


def tokenizer_arguments(values):
    result = {}
    for value in values:
        name, separator, path = value.partition("=")
        require(separator and name in ("onethinker", "qwen35") and name not in result and bool(path),
                "Use each --tokenizer as onethinker=LOCAL_PATH or qwen35=LOCAL_PATH exactly once")
        result[name] = path
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline RGB32 shard loader and per-student tokenizer length report")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--split", choices=("train", "validation", "all"), default="all")
    parser.add_argument("--allow-fixtures", action="store_true")
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--num-examples", type=int, default=8)
    parser.add_argument("--tokenizer", action="append", default=[], metavar="MODEL=LOCAL_PATH")
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    dataset = StudentDataset(args.manifest, args.workspace_root, args.split, args.allow_fixtures)
    report = dry_run(dataset, args.num_examples, tokenizer_arguments(args.tokenizer))
    if args.report:
        path = scoped_path(args.report, dataset.workspace_root, Path.cwd())
        with path.open("xb") as stream:
            stream.write(canonical_bytes(report))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
