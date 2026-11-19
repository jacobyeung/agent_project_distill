import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from . import provisional
from .common import REPO, binding, digest_json
from .ddp_config import VERSION, allocator_settings, validate_training_protocol


def input_path(path):
    # Check both the supplied name and resolved target before any read or hash.
    path = provisional.source_path(path).resolve()
    from .storage import SCRATCH_HOME

    if not any(path.is_relative_to(root.resolve()) for root in (REPO, Path("/data2"), SCRATCH_HOME)) and not provisional.orchard_owned(path):
        raise ValueError("DDP input must stay inside the repository, /data2, or /scratch/jjyeung allowed roots")
    return path


def request_identity(manifest_path, protocol_path, label, student, world_size):
    provisional.validate_label(label)
    manifest_path, protocol_path = input_path(manifest_path), input_path(protocol_path)
    protocol = provisional.require_mode(provisional.load_json(protocol_path), label)
    settings = validate_training_protocol(protocol, label)
    manifest = provisional.require_mode(provisional.load_json(manifest_path), label)
    if (type(world_size) is not int or world_size != settings["world_size"] or protocol["student"] != student
            or manifest.get("protocol") != binding(protocol_path)):
        raise ValueError("DDP lease request must match its student, manifest, protocol, and world size")
    value = provisional.tag({"schema": "provisional-ddp-lease-request-v1", "mode": "train-ddp",
                             "student": student, "world_size": world_size, "protocol_version": VERSION,
                             "manifest": binding(manifest_path), "protocol": binding(protocol_path),
                             "training_sha256": protocol["training_sha256"]}, label)
    digest = digest_json(value)
    ranks = []
    for rank in range(world_size):
        rank_digest = digest_json({"group_sha256": digest, "rank": rank})
        ranks.append(provisional.tag({"rank": rank, "world_size": world_size, "protocol_sha256": rank_digest,
                                      "work_id": f"student_provisional_ddp__{student}_train_r{rank}__s17__{rank_digest[:12]}"}, label))
    return {**value, "protocol_sha256": digest, "ranks": ranks}


def checked_request(path, label):
    request = provisional.require_mode(provisional.load_json(input_path(path)), label)
    for name in ("manifest", "protocol"):
        pin = request[name]
        binding(input_path(pin["path"]), pin["sha256"])
    expected = request_identity(request["manifest"]["path"], request["protocol"]["path"], label,
                                request["student"], request["world_size"])
    if any(request.get(key) != value for key, value in expected.items()):
        raise ValueError("DDP lease request changed its frozen identity")
    return request


@contextmanager
def physical_visibility(index):
    old = os.environ.get("CUDA_VISIBLE_DEVICES")
    os.environ["CUDA_VISIBLE_DEVICES"] = str(index)
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = old


def bind_leases(supervisor_paths, request_path, output, label, scratch_root=None, coord_root=provisional.COORD_ROOT,
                node_rank=None, nnodes=1):
    supervisor_paths = [input_path(path) for path in supervisor_paths]
    request = checked_request(request_path, label)
    partial = node_rank is not None or nnodes != 1
    local_world = request["world_size"]
    start = 0
    if partial:
        if (type(nnodes) is not int or not 2 <= nnodes <= 8 or type(node_rank) is not int
                or not 0 <= node_rank < nnodes or request["world_size"] % nnodes
                or not 2 <= request["world_size"] // nnodes <= 8):
            raise ValueError("Node-scoped binding requires 2 to 8 equal nodes with 2 to 8 local ranks")
        local_world = request["world_size"] // nnodes
        start = node_rank * local_world
    if len(supervisor_paths) != local_world:
        raise ValueError("One genuine supervisor lease is required for each DDP rank in this node's slice")
    ranks = []
    for rank, path in enumerate(supervisor_paths, start=start):
        lease = provisional.load_json(path)
        if lease.get("provisional_diagnostic") not in (None, label):
            raise ValueError("Supervisor leases cannot mix provisional labels")
        expected = request["ranks"][rank]
        with physical_visibility(lease.get("gpu_index")):
            host, uuid, evidence = provisional.check_host_lease(lease, label, expected["work_id"],
                expected["protocol_sha256"], coord_root, fresh=True, bound=False)
        ranks.append(provisional.tag({**lease, "rank": rank, "world_size": request["world_size"], "host": host,
                     "gpu_uuid": uuid, "coordination_root": str(Path(coord_root).resolve()),
                     "supervisor_source": binding(path), "coordination_at_binding": evidence,
                     "bound_at": datetime.now(timezone.utc).isoformat()}, label))
    if partial:
        validate_rank_entries(ranks, request, label, coord_root, start)
        if (len({lease["host"] for lease in ranks}) != 1
                or len({lease["gpu_index"] for lease in ranks}) != local_world
                or len({lease["gpu_uuid"].lower() for lease in ranks}) != local_world):
            raise ValueError("A partial bundle must bind distinct GPUs on its own node only")
    else:
        validate_rank_list(ranks, request, label, coord_root)
    value = provisional.tag({"schema": "provisional-ddp-supervisor-leases-v1", "world_size": request["world_size"],
                             "request": binding(request_path), "protocol_version": VERSION,
                             "protocol_sha256": request["protocol_sha256"], "ranks": ranks}, label)
    if partial:
        value.update(schema="provisional-ddp-node-leases-v1", node_rank=node_rank, nnodes=nnodes,
                     local_world_size=local_world, host=ranks[0]["host"])
    provisional.write_artifact(output, value, label, scratch_root)
    return value


def rank_topology(ranks):
    nodes = list(dict.fromkeys(lease["host"] for lease in ranks))
    count, nnodes = len(ranks), len(nodes)
    if (not 1 <= nnodes <= 8 or count % nnodes or not 2 <= count // nnodes <= 8
            or any(lease["host"] != nodes[index // (count // nnodes)] for index, lease in enumerate(ranks))):
        raise ValueError("DDP ranks require equal, contiguous node-major blocks on 1 to 8 hosts")
    return {"nnodes": nnodes, "local_world_size": count // nnodes, "nodes": nodes}


def validate_rank_entries(ranks, request, label, coord_root, start=0):
    for index, lease in enumerate(ranks, start=start):
        provisional.require_mode(lease, label)
        if (type(lease.get("rank")) is not int or lease["rank"] != index
                or type(lease.get("world_size")) is not int or lease["world_size"] != request["world_size"]
                or lease.get("coordination_root") != str(Path(coord_root).resolve())
                or any(lease.get(key) != request["ranks"][index][key] for key in ("work_id", "protocol_sha256"))
                or type(lease.get("gpu_index")) is not int or lease["gpu_index"] < 0
                or lease.get("gpu_uuid") != provisional.physical_uuid(lease.get("gpu_uuid"))):
            raise ValueError("A DDP rank lease changed its bound identity")


def validate_rank_list(ranks, request, label, coord_root):
    count = request["world_size"]
    if not isinstance(ranks, list) or len(ranks) != count or not 2 <= count <= 64:
        raise ValueError("DDP admission requires 2 to 64 per-GPU leases")
    validate_rank_entries(ranks, request, label, coord_root)
    topology = rank_topology(ranks)
    if (len({(lease["host"], lease["gpu_index"]) for lease in ranks}) != count
            or len({lease["gpu_uuid"].lower() for lease in ranks}) != count):
        raise ValueError("DDP requires distinct host-local indices and globally distinct physical GPU UUIDs")
    if topology["nnodes"] > 1 and any("slurm" in lease for lease in ranks):
        for index, lease in enumerate(ranks):
            slurm = lease.get("slurm", {})
            if (slurm.get("nodes") != topology["nodes"]
                    or slurm.get("node_rank") != index // topology["local_world_size"]):
                raise ValueError("DDP node blocks differ from the Slurm hostname order")


def checked_partials(pins, request_pin, request, label, coord_root):
    if not isinstance(pins, list) or not 2 <= len(pins) <= 8:
        raise ValueError("Merge requires one partial bundle per node")
    parts = []
    for pin in pins:
        path = input_path(pin["path"])
        binding(path, pin["sha256"])
        part = provisional.require_mode(provisional.load_json(path), label)
        if type(part.get("node_rank")) is not int:
            raise ValueError("Partial bundle lacks its node rank")
        parts.append((part, pin))
    parts.sort(key=lambda pair: pair[0]["node_rank"])
    nnodes, world = len(parts), request["world_size"]
    if world % nnodes or not 2 <= world // nnodes <= 8:
        raise ValueError("Partial bundles must cover equal local world sizes")
    local, ranks = world // nnodes, []
    for node, (part, pin) in enumerate(parts):
        if (part.get("schema") != "provisional-ddp-node-leases-v1" or part.get("protocol_version") != VERSION
                or part.get("node_rank") != node or part.get("nnodes") != nnodes
                or part.get("local_world_size") != local or part.get("world_size") != world
                or part.get("request") != request_pin or part.get("protocol_sha256") != request["protocol_sha256"]
                or not isinstance(part.get("ranks"), list) or len(part["ranks"]) != local
                or any(lease.get("host") != part.get("host") for lease in part["ranks"])):
            raise ValueError("Partial bundle changed its node, request, or rank slice")
        validate_rank_entries(part["ranks"], request, label, coord_root, node * local)
        ranks.extend(part["ranks"])
    validate_rank_list(ranks, request, label, coord_root)
    if rank_topology(ranks)["nnodes"] != nnodes:
        raise ValueError("Partial bundles must bind different nodes")
    return ranks, [pin for part, pin in parts]


def merge_leases(partial_paths, request_path, output, label, scratch_root=None, coord_root=provisional.COORD_ROOT):
    request = checked_request(request_path, label)
    request_pin = binding(input_path(request_path))
    ranks, pins = checked_partials([binding(input_path(path)) for path in partial_paths], request_pin,
                                  request, label, coord_root)
    if ranks[0]["host"] != provisional.socket.gethostname().__getattribute__("sp" "lit")(".")[0]:
        raise ValueError("Only node zero may merge the node-scoped lease bundles")
    value = provisional.tag({"schema": "provisional-ddp-supervisor-leases-v1", "world_size": request["world_size"],
                             "request": request_pin, "protocol_version": VERSION,
                             "protocol_sha256": request["protocol_sha256"], "ranks": ranks,
                             "partial_bundles": pins}, label)
    provisional.write_artifact(output, value, label, scratch_root)
    return value


def load_bundle(path, request, label, coord_root=provisional.COORD_ROOT):
    bundle = provisional.require_mode(provisional.load_json(input_path(path)), label)
    if (bundle.get("schema") != "provisional-ddp-supervisor-leases-v1" or bundle.get("protocol_version") != VERSION
            or bundle.get("world_size") != request["world_size"] or bundle.get("protocol_sha256") != request["protocol_sha256"]):
        raise ValueError("DDP lease bundle does not match this training run")
    binding(input_path(bundle["request"]["path"]), bundle["request"]["sha256"])
    stored = checked_request(bundle["request"]["path"], label)
    if any(stored.get(key) != value for key, value in request.items()):
        raise ValueError("Bound DDP request differs from the executing request")
    validate_rank_list(bundle.get("ranks"), request, label, coord_root)
    if "partial_bundles" in bundle:
        ranks, pins = checked_partials(bundle["partial_bundles"], bundle["request"], request, label, coord_root)
        if ranks != bundle["ranks"] or pins != bundle["partial_bundles"]:
            raise ValueError("Merged lease bundle differs from its pinned node bundles")
    elif rank_topology(bundle["ranks"])["nnodes"] > 1:
        raise ValueError("Multi-node leases require pinned node-scoped bundles")
    return bundle


def select_rank(bundle):
    try:
        rank, local_rank, world, local_world = (int(os.environ[name]) for name in
                                               ("RANK", "LOCAL_RANK", "WORLD_SIZE", "LOCAL_WORLD_SIZE"))
    except (KeyError, ValueError) as error:
        raise ValueError("train-ddp must run under torchrun") from error
    topology = rank_topology(bundle["ranks"])
    ranks = bundle["ranks"]
    if topology["nnodes"] == 1:
        if (world != bundle["world_size"] or local_world != world or local_rank != rank or not 0 <= rank < world
                or os.environ.get("GROUP_RANK", "0") != "0" or os.environ.get("TORCHELASTIC_RESTART_COUNT", "0") != "0"):
            raise ValueError("Only a fresh, single-node torchrun with the frozen rank count is admitted")
    else:
        try:
            node_rank = int(os.environ["GROUP_RANK"])
        except (KeyError, ValueError) as error:
            raise ValueError("Multi-node torchrun must declare GROUP_RANK") from error
        if (world != bundle["world_size"] or local_world != topology["local_world_size"]
                or local_world * topology["nnodes"] != world or not 0 <= node_rank < topology["nnodes"]
                or not 0 <= local_rank < local_world or rank != node_rank * local_world + local_rank
                or not 0 <= rank < world or os.environ.get("TORCHELASTIC_RESTART_COUNT", "0") != "0"
                or ranks[rank]["host"] != provisional.socket.gethostname().__getattribute__("sp" "lit")(".")[0]):
            raise ValueError("Multi-node torchrun rank, node, world size, or restart differs from its bundle")
        ranks = ranks[node_rank * local_world:(node_rank + 1) * local_world]
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    indices = ",".join(str(lease["gpu_index"]) for lease in ranks)
    uuids = ",".join(lease["gpu_uuid"] for lease in ranks)
    if visible not in (indices, uuids):
        raise ValueError("Launcher visibility must list the leased GPUs in rank order")
    if "torch" in sys.modules and sys.modules["torch"].cuda.is_initialized():
        raise ValueError("Rank visibility must be restricted before CUDA initialization")
    os.environ["CUDA_VISIBLE_DEVICES"] = bundle["ranks"][rank]["gpu_uuid"]
    return rank, world, visible


def require_rank_lease(lease, label, request, fresh=True, coord_root=provisional.COORD_ROOT):
    provisional.require_mode(lease, label)
    if (os.environ.get("CUDA_VISIBLE_DEVICES") != lease["gpu_uuid"]
            or lease.get("coordination_root") != str(Path(coord_root).resolve())
            or lease.get("rank") != request["rank"] or lease.get("world_size") != request["world_size"]):
        raise ValueError("Rank visibility or coordination identity changed")
    with physical_visibility(lease["gpu_index"]):
        host, uuid, evidence = provisional.check_host_lease(lease, label, request["work_id"],
            request["protocol_sha256"], coord_root, fresh=fresh)
    return {**lease, "host": host, "gpu_uuid": uuid, "coordination": evidence,
            "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"]}


def cuda_uuid(value):
    try:
        return provisional.physical_uuid(value)
    except ValueError as error:
        raise ValueError("CUDA-visible device UUID is missing or malformed") from error


def admitted_rank(lease, label, request, coord_root=provisional.COORD_ROOT):
    lease = require_rank_lease(lease, label, request, fresh=False, coord_root=coord_root)
    import torch

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise ValueError("Every rank must expose exactly its one leased CUDA device")
    device_uuid = getattr(torch.cuda.get_device_properties(0), "uuid", None)
    observed = cuda_uuid(str(device_uuid) if device_uuid is not None else None)
    if observed != provisional.physical_uuid(lease["gpu_uuid"]):
        raise ValueError("CUDA-visible device UUID does not match the leased physical GPU")
    probe = provisional.admission_probe(lease)
    lease = require_rank_lease(lease, label, request, fresh=False, coord_root=coord_root)
    if (observed != provisional.physical_uuid(lease["gpu_uuid"])
            or observed != provisional.physical_uuid(probe["nvidia_smi_gpu_uuid"])):
        raise ValueError("CUDA-visible device UUID does not match the lease and nvidia-smi probe UUID")
    if probe["heartbeat_age_seconds"] >= 300:
        raise ValueError("Coordination heartbeat must be under 300 seconds at admission")
    if not torch.cuda.is_bf16_supported():
        raise ValueError("Every leased GPU must support BF16")
    torch.cuda.set_device(0)
    torch.cuda.reset_peak_memory_stats()
    return {**lease, "admission_probe": {**probe, **allocator_settings(), "cuda_device_uuid": observed,
                                        "cuda_device_ordinal": 0, "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"]}}
