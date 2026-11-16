import hashlib
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PILOT = REPO.parent
ARTIFACTS = REPO / "artifacts"
DONOR = Path("/data2/jjyeung/agent_project_data/r1298_req229_common_gt/v14/cells/gt_gt_high")
CONTRACT = DONOR / "package/contract.json"
CONTRACT_SHA = "0027aa304dd8255eb9ead6d6e7fb473fbba45fd12b667febf6a70634806972a1"
MEMBERSHIP = Path("/data2/jjyeung/agent_project_data/answerable500_membership_20260824/MEMBERSHIP_ANSWERABLE_500.json")
MEMBERSHIP_SHA = "2de71c248b9b9817d515510b48dd4d9a5a3800583f5ea64ea2be855b16220fbf"
REGISTRY = Path("/home/jjyeung/agent_project_astra_self_improve/right_now/selected_frames_full.json")
REGISTRY_SHA = "85f88a727b68b94be82e38b977415328c241fd3fe6bd3e7dd70a5ea7e386acbc"
SCORER_MAIN = Path("/home/jjyeung/agent_project/agent/agentic_information_5.0/evaluate_benchmark_v4.py")
SCORER_LIB = SCORER_MAIN.parent.parent / "evaluation/scoring.py"
MODEL = Path("/data2/jjyeung/cache/huggingface/hub/models--OneThink--OneThinker-8B/snapshots/2b7032f4179d8c032d2eac67b3692263f85be0fc")
MODEL_REVISION = MODEL.name


def configure_environment():
    paths = {
        "TMPDIR": REPO / ".tmp",
        "HF_HOME": REPO / ".cache/huggingface",
        "XDG_CACHE_HOME": REPO / ".cache",
        "TORCH_HOME": REPO / ".cache/torch",
        "TRITON_CACHE_DIR": REPO / ".cache/triton",
        "PIP_CACHE_DIR": REPO / ".cache/pip",
    }
    for key, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["WANDB_DISABLED"] = "true"
    os.environ.setdefault("OMP_NUM_THREADS", "4")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    with Path(path).open() as stream:
        return json.load(stream)


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def digest_json(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def write_once(path, value):
    path = Path(path)
    if not path.resolve().is_relative_to(Path("/data2")):
        raise ValueError("Artifacts must remain under /data2")
    payload = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"Refusing to change immutable artifact: {path}")
        return path
    with path.open("xb") as stream:
        stream.write(payload)
    return path


def binding(path, expected=None):
    result = {"path": str(path), "sha256": sha256(path)}
    if expected is not None and result["sha256"] != expected:
        raise ValueError(f"Hash mismatch for {path}")
    return result
