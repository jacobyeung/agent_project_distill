import os
from pathlib import Path

from .common import MODEL, binding

STUDENTS = {
    "onethinker": {
        "snapshot": MODEL,
        "architecture": "Qwen3VLForConditionalGeneration",
        "processor": "Qwen3VLProcessor",
        "model_type": "qwen3_vl",
        "config_sha256": "cc76a13b9e08a9548e177717d4e0b929142edcaf674d26dff5b2c586a8e28a35",
        "group_parameters": {"text": 43_646_976, "vision": 3_849_984, "mergers": 573_440},
        "target_counts": {"text": 252, "vision": 108, "mergers": 8},
    },
    "qwen35": {
        "snapshot": Path("/data2/jjyeung/cache/huggingface/hub/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a"),
        "architecture": "Qwen3_5ForConditionalGeneration",
        "processor": "Qwen3VLProcessor",
        "model_type": "qwen3_5",
        "text_config": {"num_hidden_layers": 32, "hidden_size": 4096},
        "config_sha256": "d0883072e01861ed0b2d47be3c16c36a8e81c224c7ffaa310c6558fb3f932b05",
        "group_parameters": {"text": 43_278_336, "vision": 3_849_984, "mergers": 143_360},
        "target_counts": {"text": 248, "vision": 108, "mergers": 2},
    },
    "qwen36_27b": {
        "snapshot": Path(os.environ.get("QWEN36_27B_SNAPSHOT", "/data2/jjyeung/cache/huggingface/hub/models--Qwen--Qwen3.6-27B/snapshots/6a9e13bd6fc8f0983b9b99948120bc37f49c13e9")),
        "revision": "6a9e13bd6fc8f0983b9b99948120bc37f49c13e9",
        "architecture": "Qwen3_5ForConditionalGeneration",
        "processor": "Qwen3VLProcessor",
        "model_type": "qwen3_5",
        "text_config": {"num_hidden_layers": 64, "hidden_size": 5120},
        "config_sha256": "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c",
        "group_parameters": {"text": 116_727_808, "vision": 3_849_984, "mergers": 151_552},
        "target_counts": {"text": 496, "vision": 108, "mergers": 2},
    },
}


# Deployment aliases retain all content and architecture pins of their canonical student.
ALIASES = {"m8a9e": "qwen35"}
STUDENTS["m8a9e"] = {**STUDENTS["qwen35"], "snapshot_dir": "a32330d0"}


def canonical_student(student):
    return ALIASES.get(student, student)


def same_student(left, right):
    return isinstance(left, str) and isinstance(right, str) and canonical_student(left) == canonical_student(right)


def runtime_student():
    value = os.environ.get(("Q_E5" if "Q_E5" in os.environ else "R1_STUDENT_HEX"))
    student = bytes.fromhex(value).decode() if value else "qwen35"
    if student not in STUDENTS:
        raise ValueError("Unknown runtime student")
    return student


def get_student(student="onethinker"):
    if student not in STUDENTS:
        raise ValueError(f"Unknown student: {student}; choose one of {tuple(STUDENTS)}")
    spec = STUDENTS[student]
    from .orchard_paths import enabled, snapshot
    if enabled():
        spec = {**spec, "snapshot": snapshot(spec)}
    if "revision" in spec and spec["snapshot"].name != spec["revision"]:
        raise ValueError(f"Student snapshot directory must retain revision {spec['revision']}")
    return spec


def model_class(student="onethinker"):
    import transformers

    return getattr(transformers, get_student(student)["architecture"])


def student_for_model(model):
    matches = [name for name, spec in STUDENTS.items() if name not in ALIASES and spec["model_type"] == model.config.model_type]
    if len(matches) > 1:
        text = getattr(model.config, "text_config", None)
        matches = [name for name in matches if all(getattr(text, key, None) == value
                   for key, value in STUDENTS[name]["text_config"].items())]
    if len(matches) != 1:
        raise ValueError(f"Unsupported student architecture: {model.config.model_type}")
    selected = runtime_student()
    return selected if selected in ALIASES and canonical_student(selected) == matches[0] else matches[0]


def validate_snapshot(student="onethinker"):
    spec = get_student(student)
    binding(spec["snapshot"] / "config.json", spec["config_sha256"])
    return spec["snapshot"]


def training_parameters(student="onethinker"):
    return sum(get_student(student)["group_parameters"].values())


if __name__ == "__main__":
    print(runtime_student())
