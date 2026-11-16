import ast
import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT.parent)]
import native_common as C
import native_stage as S
import kernels as K

LANE = Path("/scratch/jjyeung/orch_cd/evalx")
WORK = LANE / "work/milestone"
SCHEMA = "evalx-native-complete-pin-graph-v1"
DISPOSITIONS = {"executed locally", "statically proved",
                "covered by a named earlier pilot", "live only"}
AUTHORITY_ROWS = {7, 8, 28, 36}
MASK_PATH = str(C.LOGICAL_ROOT / "orchard_native/MASK_CACHE_P6_BOUND.json")
P5_FAMILY = dict(path=str(WORK / "native_package_s23_02/seal/FAMILY.json"),
                 sha256="62a94599cc05478e56986c39edea4c8f82139392a1966d5145b175f09be05bfe")
P5_AUTH = dict(path=str(WORK / "native_package_s23_02/pilot5_failure/AUTHENTICATED_FAILURE.json"),
               sha256="652e88fc31f12fe1522f1ee5314dc87613ac7a38144dd7c5924694bd448fb638")
P3_FAMILY = dict(path=str(ROOT / "submissions/e47eeb632/FAMILY.json"),
                 sha256="74e351b57f4a035b6dc385c2d89861d3bd6a7d31a8a63c8eaee0f30d51c2515a")
P3_REPORT = dict(path=str(WORK / "native_probe_s23_01/pilot3_failure/FAILURE_REPORT.json"),
                 sha256="a429b1639a99883c8061e41d0bf9003396d4415430e06d7d568be6e306cdc802")
AUDIT = dict(path="/scratch/jjyeung/orch_cd/leg_s1_review/NATIVE_PIN_GRAPH_AUDIT.md",
             sha256="32b64f304776abc96e0fb91df19f4f29d7ca3625ba3d5a88fa85fc76fbec49fe")
SOURCE_MANIFEST = WORK / "native_package_s24_03/CONTROLLER_SOURCE_PINS.json"
CHANGED_SOURCES = (
    "native/out2/nomdg.py", "native/out2/perception.py", "native/out2/reader_policy.py",
    "native/out2/geometry.py", "native/out2/geometry_refusals.py",
    "native/out2/r1.py", "native/out2/camera_report.py", "orchard_native/native_job.py",
    "orchard_native/kernels.py", "orchard_native/native_metrics.py", "orchard_native/native_worker.py",
    "orchard_native/native_cpu_replica.py", "orchard_native/native_local_check.py",
    "orchard_native/native_pin_graph.py", "orchard_native/MASK_CACHE_P6_BOUND.json",
    "orchard_native/native_common.py", "orchard_native/native_launcher.py")
CONTROLLER_SOURCES = (
    "package_candidate.py", "reuse_guard.py", "reuse_submit_gate.py",
    "test_reader_policy.py", "test_native_candidate.py", "test_admission_candidate.py",
    "replay_candidate.py", "cpu_pilot_replay.py",
    "candidate_fixtures.py", "test_candidate_runtime.py", "test_geometry_refusals.py", "test_review_fixes.py",
    "test_geometry_numeric.py")
ROWS = [
    (1, "BATCH.sh:7-12", "assigned job and private root", "Slurm environment; exclusive mkdir", "token", "live"),
    (2, "BATCH.sh:8-10", "literal payload digest", "decoded payload bytes", "PACKET/BATCH", "batch"),
    (3, "BATCH.sh:13-25", "32 MiB, unique relative regular members", "payload tar headers and contents", "bootstrap/code/member", "batch"),
    (4, "native_job.py:257;native_common.py:114-122", "config schema, mode, partition, step, token, GPU count", "CONFIG.json", "CONFIG/authorization", "config"),
    (5, "native_job.py:67-75", "partition, root, user and allocation", "environment and private root", "Slurm/config", "live"),
    (6, "native_job.py:83-86", "family, review and order pins", "embedded control bytes", "family hash x4", "control_pins"),
    (7, "native_common.py:73-111", "family assets, limits, contract and ACCEPT", "config and review", "FAMILY/CONFIG", "authority"),
    (8, "native_common.py:68-70,89-103", "authorization, plan and one order line", "config and ORDER.md", "token/artifact/family/plan", "authority"),
    (9, "native_job.py:89-91", "bootstrap pin map", "embedded and staged bootstrap files", "code_pins/member", "pins"),
    (10, "native_job.py:175-178;orchard_stage.py:120", "job-private local storage", "mount and storage proof", "initial/launch storage", "live"),
    (11, "native_job.py:179,194;native_job.py:38-64", "empty exclusive H100", "live card and process state", "allocation/card", "live"),
    (12, "native_stage.py:400-402", "five objects under one billion bytes", "small_objects and local archives", "object identities", "objects"),
    (13, "native_stage.py:34-41,143-148", "prefix, name, generation, size and digest", "bound object descriptors and upload receipt", "object name/hash", "objects"),
    (14, "orchard_stage.py:142-149", "per-part size, SHA256, optional MD5; whole SHA256", "exact local object bytes", "upload/object/member", "objects"),
    (15, "native_stage.py:409-410", "member maps and expanded limits", "fresh staged file inventory", "all code/adapter/input pins", "inventory"),
    (16, "native_stage.py:411-441", "runtime, numpy, closure and trainer identities", "authenticated P5 staged archives", "runtime ARCHIVE/tree", "p5"),
    (17, "native_stage.py:95-106,425-431", "safe interpreter links and unique interpreter", "authenticated P5 runtime inventory", "runtime/spec.python", "p5"),
    (18, "native_stage.py:435-438", "tree_sources and source-map digest", "trainer inventory and RUNTIME_TREE.json", "tree digest x4", "static"),
    (19, "native_stage.py:444", "bwrap size and digest", "authenticated P5 executable", "assets/staging", "p5"),
    (20, "native_stage.py:445-455", "FLA manifest, bytes and members", "staged manifest and authenticated P5 FLA inventory", "manifest/member", "static_p5"),
    (21, "native_stage.py:160-175", "entrypoint and sitecustomize asset pins", "generated static runtime-spec fields", "assets/spec/code/member", "static"),
    (22, "native_stage.py:460-466", "model-manifest pin", "exact model-object member", "manifest/member", "static"),
    (23, "native_stage.py:460-471", "base archive and model-file inventory", "authenticated P5 base staging", "base/model manifest", "p5"),
    (24, "native_stage.py:472-473", "three depth-file identities", "authenticated P5 staged files", "depth/raw G3T", "p5"),
    (25, "native_stage.py:480-499", "export parts, size, hash, headers and artifact", "authenticated P5 transport and local artifact metadata", "artifact hash x4", "p5"),
    (26, "native_stage.py:197-204", "frame_puller pin", "exact code member", "asset/member", "static"),
    (27, "native_stage.py:205-212", "frame inventory", "authenticated P5 frame staging and CPU item references", "frames/inputs", "static_p5"),
    (28, "native_job.py:182-183;native_common.py:123-133", "real controls, code pins and checkpoint step", "namespace-mapped staged files", "family/bootstrap/code", "authority"),
    (29, "native_job.py:184", "fresh output directory", "exclusive mkdir in assigned private root", "token/run path", "live"),
    (30, "native_job.py:195", "vnice pin and executable guard scripts", "code members and staged modes", "asset/member/ORCHARD_ASSETS", "static"),
    (31, "native_bootstrap.py:32-36", "isolated flags, schema, ARCHIVE and SOURCE", "batch command, static spec and P5 bootstrap", "runtime hash/tree digest", "static_p5"),
    (32, "native_bootstrap.py:37-45", "interpreter and overlay identities", "authenticated P5 runtime and module origins", "runtime/spec", "p5"),
    (33, "native_bootstrap.py:47-53", "sitecustomize pin and alias path", "exact staged sitecustomize bytes", "asset/member/spec", "static"),
    (34, "native_bootstrap.py:56-68", "seven import pins, origins and required versions", "authenticated P5 verified imports", "spec/overlays", "p5"),
    (35, "native_bootstrap.py:86-87", "entrypoint pin and command target", "exact staged native_worker.py", "assets/FAMILY/CONFIG/spec/code/member", "static"),
    (36, "native_worker.py:248-254", "complete config admission and allocation", "namespace config; preserved live allocation predicate", "controller/worker config", "authority"),
    (37, "native_worker.py:16-23", "adapter pin map", "exact staged adapter files", "code/member", "static"),
    (38, "native_worker.py:26-41;camera_cohort.py:42-71", "input pins, cohort, 152/636/84, counts, keys and selection", "path-mapped CPU replica on staged inputs", "cohort/input/member", "replica"),
    (39, "native_worker.py:127;kernels.py:117-129", "nomdg and geometry kernel-source pins", "staged sources and real partition function", "kernel/adapter/code/member", "replica"),
    (40, "runtime_tree.py:10-36;nomdg.py:306", "runtime tree and restore source identities", "static tree proof and identical P3 restore kernel", "tree digest x4", "p3"),
    (41, "read_runtime.py:12-92", "config, artifact, receipt, preparation, source seals and init-spec", "authenticated P3 restore on identical checked inputs", "artifact/config/tree", "p3"),
    (42, "native_worker.py:179;perception.py:70", "mask-cache producer equals sealed nomdg", "new staged receipt and CPU replica", "reader pin x6", "replica"),
    (43, "perception.py:64-89", "mask headers, frozen kit, SAM, provenance, operands and cache pins", "path-mapped CPU replica", "mask/kit/input/member", "replica"),
    (44, "geometry.py:104-117;routed.py:28", "raw G3T constants and pins, capture rows and frame hashes", "staged files, pinned tower source and CPU replica", "G3T/frame/tree", "replica"),
    (45, "native_job.terminal;native_metrics.project", "all 84 capture dispositions, ten-pair refusal coverage or explicit insufficient coverage", "CPU-tested controller, worker and metrics; real head outcomes remain live", "report/parity/terminal receipt", "terminal"),
    (46, "orchard_results.py:44-88", "fresh pool/token directory; pool at most one GiB", "live publisher checks and bounded pool snapshot", "pool/token/return limits", "live"),
]
ROWS = [(*row[:-1], "live" if row[0] in (25, 40, 41, 45) else row[-1]) for row in ROWS]
ROWS.extend((47+i, name, "sealed family code pin", "fresh staged member hash",
             "source/adapter/bootstrap/member", "candidate_sources") for i, name in enumerate(CHANGED_SOURCES))
ROWS.extend((47+len(CHANGED_SOURCES)+i, name, "review-event controller source manifest",
             "current controller source hash", "review/CPU evidence/receipt", "controller_sources")
            for i, name in enumerate(CONTROLLER_SOURCES))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def constants(path, names):
    values = {}
    for node in ast.parse(Path(path).read_text()).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    values[target.id] = ast.literal_eval(node.value)
    require(set(values) == set(names), "A static source constant is unavailable")
    return values


def inventory(root, family):
    root = Path(root)
    members = {}
    for part in family["assets"]["small_objects"]:
        target = S.physical(root, part["destination"]) if part.get("destination") else root
        for name, expected in part["members"].items():
            S.S.relative(name)
            path = target / name
            require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
                    "A staged member escapes its exact-object tree")
            require(path.stat().st_size == expected["bytes"] and C.sha(path) == expected["sha256"],
                    "A staged member differs: " + name)
            require(str(path) not in members, "Two objects overlap in the staged tree")
            members[str(path)] = dict(expected, role=part["role"], mode=path.stat().st_mode & 0o777)
    return members


def static_checks(root, family, members):
    root = Path(root)
    assets, worker = family["assets"], family["worker_contract"]
    resolve = lambda path: S.physical(root, path)
    named = {name: assets[name] for name in
             ("worker_entrypoint", "vnice", "frame_puller", "sitecustomize", "model_manifest")}
    named["fla.manifest"] = assets["fla"]["manifest"]
    checked = {}
    for name, record in named.items():
        path = C.checked(record, resolve)
        member = members.get(str(path))
        require(member is not None and member["sha256"] == record["sha256"],
                "An asset pin is not its exact object member: " + name)
        checked[name] = dict(pin=record, actual_sha256=member["sha256"], role=member["role"])
    entry = assets["worker_entrypoint"]
    require(family["code_pins"].get(entry["path"]) == entry["sha256"],
            "The runtime entrypoint and code pin disagree")
    spec = dict(schema=S.B.SCHEMA, runtime_archive_sha256=assets["runtime"]["sha256"],
                source_map_sha256=S.B.SOURCE, entrypoints={"native_worker.py": entry},
                sitecustomize=assets["sitecustomize"])
    for record in (spec["entrypoints"]["native_worker.py"], spec["sitecustomize"]):
        S.B.checked(dict(path=str(resolve(record["path"])), sha256=record["sha256"]))
    require(Path(entry["path"]).name == "native_worker.py", "The command target differs from its spec")
    for name in ("vnice.sh", "terminator.sh"):
        path = resolve(str(Path(assets["vnice"]["path"]).with_name(name)))
        require(members.get(str(path), {}).get("mode") == 0o755, "A priority guard is not executable: " + name)
        member = path.relative_to(root).as_posix()
        with tarfile.open(root / "archives/code.tar", "r:") as archive:
            require(archive.getmember(member).mode & 0o777 == 0o755, "A code-object guard mode differs")
    tree_manifest = C.load(resolve(str(C.LOGICAL_ROOT / "native/out2/RUNTIME_TREE.json")))
    tree_code = resolve(str(C.LOGICAL_ROOT / "native/out2/runtime_tree.py"))
    expected = constants(tree_code, {"EXPECTED_SOURCES_SHA"})["EXPECTED_SOURCES_SHA"]
    tree_digest = C.canonical(assets["tree_sources"])
    require(S.B.ARCHIVE == assets["runtime"]["sha256"], "The bootstrap runtime archive identity differs")
    require(tree_digest == S.B.SOURCE == expected == tree_manifest["sources_sha256"]
            and tree_manifest["sources"] == assets["tree_sources"]
            and tree_manifest["files"] == len(assets["tree_sources"]), "The duplicated source-map identities differ")
    for path, digest in worker["adapter_pins"].items():
        require(family["code_pins"].get(path) == digest, "An adapter and code pin disagree")
        C.checked(dict(path=path, sha256=digest), resolve)
    for name, digest in worker["kernel_source_pins"].items():
        path = str(C.LOGICAL_ROOT / "native/out2" / (name + ".py"))
        require(worker["adapter_pins"].get(path) == family["code_pins"].get(path) == digest,
                "A kernel-source pin disagrees with its adapter or code pin")
        C.checked(dict(path=path, sha256=digest), resolve)
    for record in worker["inputs"].values():
        C.checked(record, resolve)
    mask = C.load(C.checked(worker["mask_cache"], resolve))
    old_family = C.load(C.checked(P5_FAMILY))
    old_mask = C.load(C.checked(old_family["worker_contract"]["mask_cache"], resolve))
    require(mask["producer_sha256"] == worker["kernel_source_pins"]["nomdg"],
            "The mask-cache producer is not the sealed reader")
    require({key: value for key, value in mask.items() if key != "producer_sha256"} ==
            {key: value for key, value in old_mask.items() if key != "producer_sha256"},
            "The mask receipt changed outside its producer hash")
    require(worker["mask_cache"]["path"] == MASK_PATH and
            family["code_pins"].get(MASK_PATH) == worker["mask_cache"]["sha256"],
            "The replacement mask receipt is not its own code member")
    tower = Path(assets["tree_root"]) / "student_pilot/tower_read.py"
    require(C.sha(tower) == assets["tree_sources"]["student_pilot/tower_read.py"],
            "The local tower source is not the staged trainer source")
    tower_constants = constants(tower, {"WEIGHTS_SHA256", "CONFIG_SHA256", "REVISION"})
    raw = C.load(C.checked(worker["raw_tower"], resolve))
    require((raw.get("schema"), raw.get("weights_sha256"), raw.get("config_sha256"), raw.get("revision")) ==
            ("legs1-raw-g3t-cache-v1", tower_constants["WEIGHTS_SHA256"],
             tower_constants["CONFIG_SHA256"], tower_constants["REVISION"]), "The raw G3T identities differ")
    for name in worker["geometry_captures"]:
        record = raw["captures"][name]
        actual = members.get(str(resolve(record["path"])))
        require(actual is not None and actual["sha256"] == record["sha256"],
                "A full-cohort raw-tower pin differs")
    return dict(assets=checked, static_spec=spec, tree_digest=tree_digest, tree_files=len(assets["tree_sources"]),
                raw_tower_constants=tower_constants, raw_captures_checked=len(worker["geometry_captures"]),
                mask_cache=worker["mask_cache"], mask_producer=mask["producer_sha256"],
                old_mask_cache=old_family["worker_contract"]["mask_cache"],
                mask_only_producer_changed=True, guard_modes=dict(vnice=0o755, terminator=0o755))


def p5_evidence(family, config):
    baseline = C.load(C.checked(P5_FAMILY))
    auth = C.load(C.checked(P5_AUTH))
    require(auth["verdict"] == "AUTHENTICATED_FAILED_RETURN" and auth["job"] == 169589,
            "The prior staging evidence is not authenticated")
    C.checked(auth["archive"])
    staged = C.load(C.checked(auth["staging"]))
    runtime = C.load(C.checked(auth["runtime"]))
    old_config = C.load(WORK / "native_package_s23_02/authorized_advanced_v2/CONFIG.json")
    for name, value in baseline["assets"].items():
        if name not in ("small_objects", "worker_entrypoint"):
            require(family["assets"][name] == value, "A P5-covered asset changed: " + name)
    for name in ("runtime", "numpy", "closure", "trainer", "bwrap", "base"):
        expected = family["assets"][name]
        require(staged[name]["sha256"] == expected["sha256"] and staged[name]["bytes"] == expected["bytes"],
                "A covered staging receipt differs: " + name)
    for index, expected in enumerate(family["assets"]["depth"]):
        actual = staged["depth_" + str(index)]
        require(actual["sha256"] == expected["sha256"] and actual["bytes"] == expected["bytes"],
                "A covered depth receipt differs")
    imports = None
    for line in Path(C.checked(auth["worker_log"])).read_text().splitlines():
        if '"native_imports_verified"' in line:
            imports = json.loads(line)["imports"]
    require(imports is not None and set(imports) == set(S.B.IMPORTS), "The P5 import evidence is incomplete")
    for name, value in imports.items():
        require(value["sha256"] == runtime["imports"][name]["sha256"] and
                value["path"] == runtime["imports"][name]["path"], "An authenticated import pin differs")
        if name in S.B.REQUIRED_VERSIONS:
            require(value["version"] == S.B.REQUIRED_VERSIONS[name], "A required import version differs")
    return dict(job=169589, family=P5_FAMILY, authentication=P5_AUTH, archive=auth["archive"],
                staging=auth["staging"], runtime=auth["runtime"], worker_log=auth["worker_log"],
                object_identity_fields_verified="Unchanged runtime, base, trainer, depth and import identities; the stop export requires fresh live verification",
                verified_imports=imports, covered_assets=[name for name in staged if name != "export"],
                export_covered=False,
                staged_receipt_digests={name: C.canonical(value) for name, value in staged.items()})


def p3_evidence(root, family, config):
    baseline = C.load(C.checked(P3_FAMILY))
    report = C.load(C.checked(P3_REPORT))
    auth = C.load(C.checked(report["authentication"]))
    require(report["authenticated"] is True and report["job"] == 169521 and auth["authenticated"] is True,
            "The P3 restore evidence is not authenticated")
    require(C.sha(report["archive"]["path"]) == auth["archive_sha256"], "The P3 return changed")
    parity = C.load(WORK / "native_probe_s23_01/pilot3_failure/GPU_PARITY.json")
    require(parity["P2"]["pass"] is True and parity["P3"]["pass"] is True,
            "The authenticated P3 parity does not establish a completed restore")
    old_config = C.load(ROOT / "submissions/e47eeb632/CONFIG.json")
    for name in ("runtime", "numpy", "fla", "closure", "trainer", "tree_sources", "base", "depth", "sitecustomize"):
        require(family["assets"][name] == baseline["assets"][name], "A P3 restore input changed: " + name)
    for name in ("config", "data_receipt", "artifact"):
        require(config["worker"][name] == old_config["worker"][name], "A checked P3 restore identity changed")
    require(config["transport"] == old_config["transport"], "The P3 export transport changed")
    old_object = next(part for part in baseline["assets"]["small_objects"] if part["role"] == "code")
    archive_path = WORK / "native_probe_s23_01/packages/code.tar"
    require(C.sha(archive_path) == old_object["sha256"], "The P3 source object changed")
    old_sources, current = {}, {}
    with tarfile.open(archive_path, "r:") as archive:
        for name in ("nomdg", "geometry"):
            logical = str(C.LOGICAL_ROOT / "native/out2" / (name + ".py"))
            member = "sj/" + str(Path(logical).relative_to("/scratch/jjyeung"))
            old_sources[name] = archive.extractfile(member).read().decode()
            current[name] = Path(S.physical(root, logical)).read_text()
    before, after = K.partition(**{name + "_source": value for name, value in old_sources.items()}), K.partition(
        **{name + "_source": value for name, value in current.items()})
    restore_hashes = {}
    for name in ("restore", "geometry_restore"):
        old = ast.dump(before[name], include_attributes=False)
        new = ast.dump(after[name], include_attributes=False)
        require(old == new, "A P3-covered restore kernel changed")
        restore_hashes[name] = hashlib.sha256(new.encode()).hexdigest()
    for path, digest in baseline["worker_contract"]["adapter_pins"].items():
        if Path(path).name != "nomdg.py":
            require(family["worker_contract"]["adapter_pins"].get(path) == digest,
                    "A restore dependency changed outside the admitted parity-only reader change")
    return dict(job=169521, family=P3_FAMILY, failure_report=P3_REPORT,
                authentication=report["authentication"], archive=report["archive"],
                source_object=dict(path=str(archive_path), sha256=old_object["sha256"]),
                restore_ast_sha256=restore_hashes, model_restore_established_by="Authenticated successful P2 and P3")


def object_checks(root, family, upload):
    assets = family["assets"]
    require(len(assets["small_objects"]) == 5 and sum(p["bytes"] for p in assets["small_objects"]) < 1000000000,
            "The five-object byte allowance differs")
    receipt = C.load(C.checked(upload))
    result = {}
    for part in assets["small_objects"]:
        uri = S.cloud_uri(part)
        path = Path(root) / "archives" / (part["role"] + ".tar")
        require(path.stat().st_size == part["bytes"] and C.sha(path) == part["sha256"],
                "An exact local archive differs")
        md5 = None
        if part.get("md5"):
            with path.open("rb") as stream:
                md5 = base64.b64encode(hashlib.file_digest(stream, "md5").digest()).decode()
            require(md5 == part["md5"], "An object MD5 differs")
        if part["role"] == "code":
            require(receipt["status"] == "CONFIRMED" and all(receipt[key] == part[key]
                    for key in ("name", "sha256", "bytes", "generation")),
                    "The replacement code is not its confirmed uploaded generation")
            require(str(receipt["server_metadata"]["generation"]) == str(part["generation"]),
                    "The server-confirmed generation differs")
        result[part["role"]] = dict(uri=uri, bytes=part["bytes"], sha256=part["sha256"],
                                   generation=part["generation"], md5=md5,
                                   members=len(part["members"]), members_sha256=C.canonical(part["members"]))
    return dict(objects=result, upload=upload)


def cpu_replica(root, config_path):
    tag = C.sha(config_path)[:16]
    output = Path(root) / ("CPU_REPLICA_" + tag + ".json")
    log = Path(root) / ("CPU_REPLICA_" + tag + ".log")
    helper = ROOT / "native_cpu_replica.py"
    if not output.exists():
        with log.open("xb") as stream:
            result = subprocess.run(
                [sys.executable, "-I", "-s", "-B", str(helper), "--root", str(root),
                 "--config", str(config_path), "--record", str(output)],
                stdout=stream, stderr=subprocess.STDOUT, timeout=180,
                env={**os.environ, "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "1",
                     "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
        require(result.returncode == 0, "The path-mapped CPU replica failed; inspect " + str(log))
    value = C.load(output)
    require(value["passed"] is True and value["cpu_only"] is True and
            value["config"]["sha256"] == C.sha(config_path) and value["helper"]["sha256"] == C.sha(helper),
            "The CPU replica proof differs")
    return dict(record=C.pin(output), log=C.pin(log), helper=C.pin(helper),
                checks=list(value["checks"]), mask_producer=value["details"]["masks"]["producer_actual"])


def validate(record, allow_pending=False):
    require(record.get("schema") == SCHEMA and len(record.get("rows", [])) == len(ROWS),
            "The complete extended comparison graph is required")
    require({row.get("id") for row in record["rows"]} == {row[0] for row in ROWS},
            "A comparison row is missing or duplicated")
    for row in record["rows"]:
        require(row.get("disposition") in DISPOSITIONS and row.get("location") and row.get("expected_from")
                and row.get("actual_from") and row.get("evidence"), "An audit row has no evaluated disposition")
        pending = allow_pending and row["id"] in AUTHORITY_ROWS and row.get("status") == "requires_real_controls"
        require(row.get("passed") is True or pending, "A comparison row failed or remains unevaluated: " + str(row["id"]))
        if row["disposition"] == "live only":
            require(row.get("predicate") and row.get("live_check_unchanged") is True, "A live-only row lacks its enforced predicate")
        if row["disposition"] == "covered by a named earlier pilot":
            require(row["evidence"].get("job") in (169589, 169521) and row["evidence"].get("authentication"),
                    "A covered row lacks authenticated pilot evidence")
    return record


def prove(root, family_path, packet, upload, pool, output):
    import native_launcher as L

    root, packet = Path(root), Path(packet)
    family = C.load(family_path)
    config = C.load(packet / "CONFIG.json")
    C.checked(AUDIT)
    require(C.sha(family_path) == config["family"]["sha256"], "The graph's family and packet differ")
    groups = {}

    def check(name, operation):
        try:
            groups[name] = dict(passed=True, evidence=operation())
        except Exception as error:
            groups[name] = dict(passed=False, evidence=dict(error_type=type(error).__name__, error=str(error)))

    def batch():
        L.validate_batch((packet / "BATCH.sh").read_text(), config,
                         dict(family, bytes=Path(family_path).read_bytes()),
                         (packet / "REVIEW.json").read_bytes(), (packet / "ORDER.md").read_bytes())
        return dict(batch=C.pin(packet / "BATCH.sh"), packet_config=C.pin(packet / "CONFIG.json"),
                    maximum_expanded_bytes=32 * 1024**2)

    def controls():
        for key, filename in (("family", "FAMILY.json"), ("review", "REVIEW.json")):
            require(C.sha(packet / filename) == config[key]["sha256"], "A packet control digest differs")
        require(C.sha(packet / "ORDER.md") == config["authorization"]["orch_order"]["sha256"], "The order digest differs")
        return dict(files={name: C.pin(packet / name) for name in ("FAMILY.json", "REVIEW.json", "ORDER.md")})

    def authority():
        C.admit(config, family, C.load(packet / "REVIEW.json"))
        C.validate_order((packet / "ORDER.md").read_text(), config)
        return dict(config=C.pin(packet / "CONFIG.json"), controls=groups["control_pins"]["evidence"])

    def pins():
        for path, digest in family["code_pins"].items():
            C.checked(dict(path=path, sha256=digest), lambda value: S.physical(root, value))
        for name, digest in family["bootstrap_pins"].items():
            require(family["code_pins"].get(str(C.LOGICAL_ROOT / name)) == digest, "A duplicate bootstrap pin differs")
        artifact = C.load(C.checked(config["worker"]["artifact"], lambda value: S.physical(root, value)))
        require(artifact["step"] == config["step"], "The staged checkpoint step differs")
        return dict(code_pins=len(family["code_pins"]), bootstrap_pins=len(family["bootstrap_pins"]),
                    artifact=config["worker"]["artifact"], step=artifact["step"])

    check("batch", batch)
    check("config", lambda: dict(validated=C.validate_config(config, launch=False)["token"],
                                 config=C.pin(packet / "CONFIG.json")))
    check("control_pins", controls)
    check("authority", authority)
    check("pins", pins)
    check("objects", lambda: object_checks(root, family, upload))
    members = {}

    def member_check():
        members.update(inventory(root, family))
        return dict(members=len(members), inventory_sha256=C.canonical(members))

    check("inventory", member_check)
    check("static", lambda: static_checks(root, family, members))
    check("p5", lambda: p5_evidence(family, config))
    check("replica", lambda: cpu_replica(root, packet / "CONFIG.json"))
    baseline = C.load(C.checked(P5_FAMILY))
    terminal = {}
    for name in ("native_job.py",):
        path = str(C.LOGICAL_ROOT / "orchard_native" / name)
        require(family["code_pins"][path] == baseline["code_pins"][path], "The audited return chain changed")
        terminal[name] = family["code_pins"][path]
    groups["terminal"] = dict(passed=True, evidence=dict(audit=AUDIT, unchanged_source_sha256=terminal))
    def candidate_sources():
        result = {}
        for name in CHANGED_SOURCES:
            logical = str(C.LOGICAL_ROOT / name)
            path = C.checked(dict(path=logical, sha256=family["code_pins"][logical]),
                             lambda value: S.physical(root, value))
            result[name] = dict(logical_path=logical, staged=C.pin(path))
        return result

    def controller_sources():
        manifest = C.load(SOURCE_MANIFEST)
        require(set(manifest["sources"]) == set(CONTROLLER_SOURCES),
                "The controller source-manifest membership differs")
        for name, record in manifest["sources"].items():
            require(record["path"] == str(SOURCE_MANIFEST.parent / name),
                    "A controller source left its candidate scope")
            C.checked(record)
        return dict(manifest=C.pin(SOURCE_MANIFEST), sources=manifest["sources"])

    check("candidate_sources", candidate_sources)
    check("controller_sources", controller_sources)
    pool_value = C.load(C.checked(pool))
    require(pool_value["pool"]["limit_bytes"] == 1024**3, "The result-pool allowance differs")
    groups["live"] = dict(passed=True, evidence=dict(
        unchanged_job_code=family["code_pins"][str(C.LOGICAL_ROOT / "orchard_native/native_job.py")],
        pool_snapshot=pool, pool_bytes=pool_value["pool"]["bytes"],
        pilot_and_full_upper_bounds_fit=pool_value["pool"]["pilot_and_full_upper_bounds_fit"]))
    groups["static_p5"] = dict(passed=groups["static"]["passed"] and groups["p5"]["passed"],
                               evidence=groups["p5"]["evidence"])
    rows = []
    for number, location, expected, actual, duplicate, group in ROWS:
        result = groups[group]
        pending = number in AUTHORITY_ROWS and config.get("build_only") is True
        disposition = ("live only" if group == "live" else
                       "covered by a named earlier pilot" if group in ("p5", "p3", "static_p5") else
                       "statically proved" if group in ("static", "terminal") else "executed locally")
        row = dict(id=number, location=location, expected_from=expected, actual_from=actual,
                   duplicate_owners=duplicate, disposition=disposition, group=group,
                   passed=result["passed"] and not pending, evidence=result["evidence"],
                   status="requires_real_controls" if pending else "passed" if result["passed"] else "failed")
        if group == "live":
            row.update(predicate=expected + "; enforced by " + location, live_check_unchanged=True)
        rows.append(row)
    value = dict(schema=SCHEMA, checked_utc=datetime.now(timezone.utc).isoformat(),
                 audit=AUDIT, helper=C.pin(__file__), family=C.pin(family_path),
                 packet_config=C.pin(packet / "CONFIG.json"), root=str(root), rows=rows,
                 groups=groups, upload=upload, pool_snapshot=pool,
                 source_manifest=C.pin(SOURCE_MANIFEST),
                 passed=all(row["passed"] for row in rows),
                 inputs_passed=all(row["passed"] or row["status"] == "requires_real_controls" for row in rows),
                 pending_real_control_rows=[row["id"] for row in rows if row["status"] == "requires_real_controls"],
                 first_cuda_api="native_worker.py:132 torch.cuda.reset_peak_memory_stats",
                 first_model_tensor_load="read_runtime.py:92 model.to(device)",
                 source_boundary_note="The audit's restore rows precede tensor loading, not the earlier CUDA statistics call.",
                 production_interpreter_executed=False, gpu_worker_executed=False, network_calls=0)
    if Path(output).exists():
        saved = C.load(output)
        value["checked_utc"] = saved["checked_utc"]
        require(saved == value, "A retained comparison graph names different inputs")
    else:
        C.dump(output, value)
    validate(value, allow_pending=config.get("build_only") is True)
    return value
