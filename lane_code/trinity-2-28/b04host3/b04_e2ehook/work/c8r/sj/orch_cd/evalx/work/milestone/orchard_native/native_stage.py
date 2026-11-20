import json
import os
from pathlib import Path
import re
import sys
import tarfile
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import orchard_job as J
import orchard_stage as S
import chain_save as A
import native_bootstrap as B

PROJECT = Path("/project/community/jjyeung")
RUNTIME = "rwtrain_torch211_cu129"
RUNTIME_LINKS = {
    prefix+"/"+name: ("/usr/bin/python3", "/usr/bin/python3.12")
    for prefix in (RUNTIME+"/bin", "venvs/"+RUNTIME+"/bin")
    for name in ("python", "python3", "python3.12")}


def physical(root, path):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Require a canonical registered native path")
    if path.is_relative_to(PROJECT):
        return Path(root)/"project"/path.relative_to(PROJECT)
    return J.physical(root, path)


def cloud_uri(record):
    name = record.get("name", "")
    if (not re.fullmatch(r"[a-z0-9_-]+/[A-Za-z0-9_./-]+", name)
            or ".." in Path(name).parts or not str(record.get("generation", "")).isdigit()
            or not re.fullmatch("[0-9a-f]{64}", record.get("sha256", ""))
            or type(record.get("bytes")) is not int or record["bytes"] <= 0):
        raise ValueError("Cloud object needs a canonical name, generation, size and hash")
    return "gs://cmu-gpucloud-jjyeung/"+name+"#"+str(record["generation"])


def manifest_files(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        name = str(S.relative(name.lstrip("*")))
        if not re.fullmatch("[0-9a-f]{64}", digest) or name in result:
            raise ValueError("Invalid runtime member manifest")
        result[name] = digest
    if not result or len(result) > 20000:
        raise ValueError("Runtime inventory is empty or exceeds its bound")
    return result


def extract_named(path, root, wanted):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    inventory, total = {}, 0
    with tarfile.open(path, "r:") as archive:
        for count, entry in enumerate(archive):
            name = str(S.relative(entry.name))
            if count >= 200000:
                raise ValueError("Archive inventory exceeds its bound")
            if name not in wanted:
                continue
            record = wanted[name]
            total += entry.size
            if (name in inventory or not entry.isfile() or entry.size < 0
                    or total > Path(path).stat().st_size
                    or entry.size > record.get("max_bytes", 8*1024**3)
                    or ("bytes" in record and entry.size != record["bytes"])):
                raise ValueError("Selected archive member is duplicated or invalid")
            target = root/str(S.relative(record["destination"]))
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_symlink() or not target.parent.resolve().is_relative_to(root.resolve()):
                raise ValueError("Selected archive member escapes its destination")
            digest, copied = S.hashlib.sha256(), 0
            with archive.extractfile(entry) as source, target.open("xb") as output:
                for chunk in iter(lambda: source.read(S.CHUNK), b""):
                    digest.update(chunk)
                    copied += len(chunk)
                    if output.write(chunk) != len(chunk):
                        raise OSError("Short native staging write")
            if copied != entry.size or digest.hexdigest() != record["sha256"]:
                raise ValueError("Selected archive member differs from its pin")
            target.chmod(entry.mode & 0o755)
            inventory[name] = dict(bytes=copied, sha256=digest.hexdigest())
    if set(inventory) != set(wanted):
        raise ValueError("Required archive members are missing: "+repr(sorted(set(wanted)-set(inventory))[:5]))
    return inventory


def runtime_links(archive):
    result = {}
    with tarfile.open(archive, "r:") as stream:
        for count, entry in enumerate(stream):
            name = str(S.relative(entry.name))
            if count >= 200000:
                raise ValueError("Runtime header inventory exceeds its bound")
            if entry.issym() and Path(entry.linkname).is_absolute():
                if entry.linkname not in RUNTIME_LINKS.get(name, ()):
                    raise ValueError("Production runtime has an unregistered absolute link")
                result[name] = entry.linkname
    return result


def namespace(root, config):
    root = Path(root)
    argv = [str(root/"bwrap")]
    for name in ("usr", "bin", "sbin", "lib", "lib64", "etc", "opt", "run", "sys"):
        path = Path("/")/name
        if path.is_symlink():
            argv += ["--symlink", os.readlink(path), str(path)]
        elif path.exists():
            argv += ["--ro-bind", str(path), str(path)]
    argv += [
        "--dev-bind", "/dev", "/dev", "--proc", "/proc", "--bind", "/tmp", "/tmp",
        "--ro-bind", str(root), str(root),
        "--bind", str(root/"cache"), str(root/"cache"),
        "--bind", str(root/"temp"), str(root/"temp"),
        "--bind", str(root/"home"), str(root/"home"),
        "--dir", "/scratch", "--ro-bind", str(root/"sj"), str(J.SJ),
        "--ro-bind", str(root/"fsw"), str(J.FSW), "--dir", "/lustre",
        "--ro-bind", str(root/"m/ap"), str(J.AP), "--dir", "/project",
        "--dir", "/project/community", "--ro-bind", str(root/"project"), str(PROJECT),
        "--bind", str(physical(root, config["logical_run"])), str(physical(root, config["logical_run"])),
        "--bind", str(physical(root, config["logical_run"])), config["logical_run"],
        "--dir", "/home/jjyeung", "--die-with-parent", "--chdir", str(root)]
    return argv


def copied(item, destination):
    path = Path(item["path"])
    if not path.is_absolute() or ".." in path.parts or path.is_symlink():
        raise ValueError("Native staging requires an explicit regular source")
    S.room(Path(destination).parent, 2*item["bytes"])
    return S.copy_parts([item], destination, lambda part: Path(part["path"]).open("rb"),
                        expected_sha=item["sha256"])


def cloud(record, root, assets):
    if not record["name"].startswith(assets["cloud_prefix"]+"/"):
        raise ValueError("Cloud object is outside the sealed upload prefix")
    return S.process_stream(
        ["/usr/bin/gcloud", "storage", "cat", cloud_uri(record)],
        S.cloud_environment(assets["gcloud_config"]), Path(root)/"staging.log")


def verify_inventory(actual, expected):
    if actual != expected:
        missing = sorted(set(expected)-set(actual))
        extra = sorted(set(actual)-set(expected))
        changed = sorted(k for k in set(actual)&set(expected) if actual[k] != expected[k])
        raise ValueError("Staged inventory differs: "+repr(dict(
            missing=missing[:5], extra=extra[:5], changed=changed[:5])))


def runtime_spec(root, config, python):
    root = Path(root)
    assets = config["assets"]
    paths = dict(fla=str(root/"fla/p"), numpy=str(root/"numpy"),
                 kit=str(physical(root, assets["kit_import_root"])),
                 anyhost=str(root/"closure"),
                 aliases=str(physical(root, assets["aliases_root"])))
    site = Path(python).parent.parent/"lib/python3.12/site-packages"
    spec = dict(schema=B.SCHEMA, runtime_archive_sha256=assets["runtime"]["sha256"],
                source_map_sha256=B.SOURCE, python=dict(path=str(python), sha256=S.sha(python)),
                import_paths=paths, imports={},
                sitecustomize=assets["sitecustomize"],
                entrypoints={"native_worker.py": assets["worker_entrypoint"]})
    spec["sitecustomize"] = dict(
        path=str(physical(root, spec["sitecustomize"]["path"])),
        sha256=spec["sitecustomize"]["sha256"])
    for name in B.IMPORTS:
        required = B.REQUIRED_OVERLAYS.get(name)
        candidates = ([Path(paths[required])/name/"__init__.py"] if required else
                      [Path(value)/name/"__init__.py" for value in paths.values()]+
                      [site/name/"__init__.py"])
        found = next((path for path in candidates if path.is_file()), None)
        if required and (found is None or not found.resolve().is_relative_to(Path(paths[required]).resolve())):
            raise ValueError(name+" is absent from its required overlay")
        if found is None:
            raise ValueError("Production import is absent from the explicit closure: "+name)
        spec["imports"][name] = dict(path=str(found), sha256=S.sha(found))
    ptxas = root/"fla/p/triton/backends/nvidia/bin/ptxas"
    if (not ptxas.is_file() or not ptxas.resolve().is_relative_to((root/"fla/p").resolve())
            or not os.access(ptxas, os.X_OK)):
        raise ValueError("The staged ptxas compiler is not executable")
    spec["ptxas"] = dict(path=str(ptxas), sha256=S.sha(ptxas))
    return spec


def frames(root, config):
    assets, worker = config["assets"], config["worker"]
    puller = physical(root, assets["frame_puller"]["path"])
    if S.sha(puller) != assets["frame_puller"]["sha256"]:
        raise ValueError("The accepted frame puller differs")
    requests = Path(root)/"NEED_FRAMES.txt"
    with requests.open("x") as stream:
        stream.write(assets["frame_request"])
    target = physical(root, worker["frames_root"])
    target.mkdir(parents=True)
    argv = ["/usr/bin/python3", "-I", "-s", "-B", str(puller),
            str(requests), assets["frames_source"]]
    with S.process_stream(argv, dict(os.environ), Path(root)/"staging.log") as stream:
        inventory = S.extract_stream(stream, target, None, 20*1024**3)
        while stream.read(S.CHUNK):
            pass
    verify_inventory({name: row["sha256"] for name, row in inventory.items()},
                     assets["frames_inventory"])
    return dict(files=len(inventory), bytes=sum(row["bytes"] for row in inventory.values()))


def gcs_header_range(part, start, end, token):
    cloud_uri(part)
    generation = str(part["generation"])
    if not 0 <= start <= end < part["bytes"]:
        raise ValueError("The header range is outside its pinned part")
    url = ("https://storage.googleapis.com/cmu-gpucloud-jjyeung/"+
           quote(part["name"], safe="/")+"?generation="+generation)
    request = Request(url, headers={"Authorization": "Bearer "+token,
        "Accept-Encoding": "identity", "Range": f"bytes={start}-{end}",
        "x-goog-if-generation-match": generation})
    with urlopen(request, timeout=120) as response:
        if (response.status != 206 or response.headers.get("x-goog-generation") != generation
                or response.headers.get("Content-Encoding") not in (None, "identity")
                or response.headers.get("Content-Length") != str(end-start+1)
                or response.headers.get("Content-Range") != f"bytes {start}-{end}/{part['bytes']}"):
            raise ValueError("The GCS header generation, range or size differs from its pin")
        data = response.read(end-start+1)
    if len(data) != end-start+1:
        raise ValueError("The GCS header response is truncated; no retry")
    return data


def export_headers(transport, fetch, clock=time.monotonic, sleep=time.sleep):
    parts, requests, consumed, last = transport["parts"], [], 0, None
    total = sum(part["bytes"] for part in parts)
    if total != transport["archive_bytes"] or not parts:
        raise ValueError("Export parts do not cover the attested archive")
    for part in parts:
        cloud_uri(part)

    def read(offset, size):
        nonlocal consumed, last
        if size < 0 or offset < 0 or offset+size > total:
            raise ValueError("A tar header or member extends beyond the attested archive")
        if consumed+size > 2*1024**2:
            raise ValueError("The export header byte allowance is exhausted")
        data, base = bytearray(), 0
        for part in parts:
            boundary = base+part["bytes"]
            if offset < boundary and len(data) < size:
                start = offset-base
                count = min(size-len(data), boundary-offset)
                if len(requests) >= 300:
                    raise ValueError("The export header request allowance is exhausted")
                if last is not None:
                    sleep(max(0, 1-(clock()-last)))
                last = clock()
                chunk = fetch(part, start, start+count-1)
                if len(chunk) != count:
                    raise ValueError("The header range is truncated; no retry")
                requests.append(dict(name=part["name"], generation=str(part["generation"]),
                    start=start, end=start+count-1, sha256=S.hashlib.sha256(chunk).hexdigest()))
                consumed += len(chunk)
                data.extend(chunk)
                offset += count
            base = boundary
        if len(data) != size:
            raise ValueError("Pinned parts do not cover the header range")
        return bytes(data)

    def pax(data):
        result, offset = {}, 0
        while offset < len(data):
            space = data.index(b" ", offset)
            count = int(data[offset:space])
            end = offset+count
            if count <= space-offset+1 or end > len(data) or data[end-1:end] != b"\n":
                raise ValueError("Malformed PAX header record")
            key, value = data[space+1:end-1].decode("utf-8").split("=", 1)
            if key.startswith("GNU.sparse"):
                raise ValueError("Sparse exports are not admitted")
            result[key] = value
            offset = end
        return result

    offset, extended = 0, 0
    members, seen, global_pax, pending = [], set(), {}, {}
    while True:
        header_offset = offset
        raw = read(offset, 512)
        offset += 512
        if raw == b"\0"*512:
            if pending or read(offset, 512) != b"\0"*512:
                raise ValueError("The export has an incomplete terminal header")
            break
        try:
            member = tarfile.TarInfo.frombuf(raw, "utf-8", "strict")
        except tarfile.HeaderError as error:
            raise ValueError("Invalid export tar header: "+str(error)) from error
        if member.size < 0:
            raise ValueError("A tar member has a negative size")
        blocks = (member.size+511)//512
        if member.type in (tarfile.XHDTYPE, tarfile.XGLTYPE, tarfile.GNUTYPE_LONGNAME, tarfile.GNUTYPE_LONGLINK):
            data = read(offset, blocks*512)[:member.size]
            offset += blocks*512
            extended += blocks
            if member.type in (tarfile.XHDTYPE, tarfile.XGLTYPE):
                (global_pax if member.type == tarfile.XGLTYPE else pending).update(pax(data))
            else:
                pending["path" if member.type == tarfile.GNUTYPE_LONGNAME else "linkpath"] = (
                    data.rstrip(b"\0").decode("utf-8"))
            continue
        attributes = dict(global_pax, **pending)
        pending = {}
        size = int(attributes.get("size", member.size))
        name = str(S.relative(attributes.get("path", member.name)))
        if name in seen or size < 0 or offset+((size+511)//512)*512 > total:
            raise ValueError("A tar member is duplicated or extends beyond its archive")
        seen.add(name)
        members.append(dict(name=name, size=size, type=member.type.decode("ascii"),
                            mode=member.mode, header_offset=header_offset))
        offset += ((size+511)//512)*512
    return dict(schema="evalx-generation-pinned-export-headers-v1", parts=parts,
        archive_sha256=transport["archive_sha256"], archive_bytes=total,
        members=members, requests=requests, bytes_read=consumed, extended_blocks=extended,
        payload_bytes_read=False, request_limit=300, byte_limit=2*1024**2,
        minimum_request_interval_seconds=1)


def validate_export_headers(value, step):
    if not value["members"]:
        raise ValueError("The export has no members")
    for member in value["members"]:
        path = S.relative(member["name"])
        if path.parts[0] != "m"+str(step) or member["type"] not in ("0", "\0", "5"):
            raise ValueError("Foreign or nonregular export member: "+member["name"])


def export_destination(root, config):
    root = Path(root)
    target = physical(root, config["worker"]["artifact"]["path"]).parent.parent
    if target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Unsafe native export destination: "+str(target))
    expected = {}
    for part in config["assets"]["small_objects"]:
        destination = physical(root, part["destination"]) if part.get("destination") else root
        for name, record in part["members"].items():
            path = destination/S.relative(name)
            if path.is_relative_to(target):
                relative = str(path.relative_to(target))
                if relative in expected:
                    raise ValueError("Repeated staged export entry: "+relative)
                expected[relative] = record["sha256"]
    directories = {str(parent) for name in expected for parent in Path(name).parents}
    found, unexpected = set(), []
    if target.exists() and not target.is_dir():
        raise ValueError("Native export destination is not a directory: "+str(target))
    pending = [target] if target.exists() else []
    while pending:
        for path in sorted(pending.pop().iterdir()):
            name = str(path.relative_to(target))
            if path.is_symlink():
                unexpected.append(name)
            elif path.is_dir() and name in directories:
                pending.append(path)
            elif path.is_file() and name in expected and S.sha(path) == expected[name]:
                found.add(name)
            else:
                unexpected.append(name)
    missing = sorted(set(expected)-found)
    if unexpected or missing:
        raise ValueError("Native export destination "+str(target)+" has unexpected entries "+
                         repr(sorted(unexpected))+"; missing or changed staged entries "+repr(missing))
    target.mkdir(parents=True, exist_ok=True)
    return target


def stage(root, config):
    root = Path(root)
    assets, records = config["assets"], {}
    previous = time.monotonic()

    def phase(name, record):
        nonlocal previous
        now = time.monotonic()
        records[name] = dict(record, seconds=now-previous,
                             completed_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        previous = now
        A.atomic_json(root/"STAGING.json", records)

    archives = root/"archives"
    archives.mkdir()
    for name in ("sj", "fsw", "m/ap", "project"):
        (root/name).mkdir(parents=True, exist_ok=True)
    total = sum(part["bytes"] for part in assets["small_objects"])
    if total >= 1000000000 or len(assets["small_objects"]) != 5:
        raise ValueError("Native uploaded closure exceeds its five-object/under-1-GB allowance")
    for part in assets["small_objects"]:
        archive = archives/(part["role"]+".tar")
        receipt = S.copy_parts([part], archive, lambda p: cloud(p, root, assets),
                               expected_sha=part["sha256"])
        destination = physical(root, part["destination"]) if part.get("destination") else root
        with archive.open("rb") as stream:
            inventory = S.extract_stream(stream, destination, None, part["expanded_bytes"])
        verify_inventory(inventory, part["members"])
        phase("small_"+part["role"], receipt)
    for name in ("runtime", "numpy", "closure", "trainer"):
        item = assets[name]
        archive = archives/(name+".tar")
        receipt = copied(item, archive)
        target = (root/"project/c7d31ddd/venvs" if name == "runtime" else
                  physical(root, assets["tree_root"]) if name == "trainer" else root/name)
        target.mkdir(parents=True, exist_ok=True)
        if name == "runtime":
            saved = S.RUNTIME_ABSOLUTE_LINKS
            try:
                S.RUNTIME_ABSOLUTE_LINKS = runtime_links(archive)
                inventory = S.unpack(archive, target, links=True)
                receipt["absolute_interpreter_links"] = dict(S.RUNTIME_ABSOLUTE_LINKS)
            finally:
                S.RUNTIME_ABSOLUTE_LINKS = saved
            candidates = [target/RUNTIME/"bin/python", target/"venvs"/RUNTIME/"bin/python"]
            present = [path for path in candidates if path.is_file()]
            if len(present) != 1:
                raise ValueError("Production archive lacks a unique native interpreter")
            python = present[0]
            receipt["python"] = str(python)
        else:
            inventory = S.unpack(archive, target)
        if name == "trainer":
            verify_inventory(
                {key: value["sha256"] for key, value in inventory.items()},
                assets["tree_sources"])
            link = physical(root, assets["trainer_logical_archive"])
            link.parent.mkdir(parents=True, exist_ok=True)
            os.link(archive, link)
        phase(name, dict(receipt, files=len(inventory)))
    bwrap = root/"bwrap"
    phase("bwrap", copied(assets["bwrap"], bwrap))
    bwrap.chmod(0o700)
    manifest = physical(root, assets["fla"]["manifest"]["path"])
    if S.sha(manifest) != assets["fla"]["manifest"]["sha256"]:
        raise ValueError("FLA manifest differs")
    wanted = {"ebe69df8/p/"+name: dict(destination="p/"+name, sha256=digest)
              for name, digest in manifest_files(manifest).items()}
    source = Path(assets["fla"]["path"])
    if source.stat().st_size != assets["fla"]["bytes"]:
        raise ValueError("Production FLA archive byte count differs")
    S.room(root, source.stat().st_size)
    inventory = extract_named(source, root/"fla", wanted)
    phase("fla", dict(files=len(inventory), bytes=sum(v["bytes"] for v in inventory.values()),
                      inventory_sha256=assets["fla"]["manifest"]["sha256"]))
    records["runtime_spec"] = runtime_spec(root, config, python)
    A.atomic_json(root/"STAGING.json", records)
    model = json.loads(physical(root, assets["model_manifest"]["path"]).read_text())
    if S.sha(physical(root, assets["model_manifest"]["path"])) != assets["model_manifest"]["sha256"]:
        raise ValueError("Production model manifest differs")
    archive = archives/"base.tar"
    receipt = copied(assets["base"], archive)
    target = physical(root, model["root"])
    target.mkdir(parents=True)
    inventory = S.unpack(archive, target, strip=3)
    verify_inventory({name: row["sha256"] for name, row in inventory.items()}, model["files"])
    phase("base", dict(receipt, files=len(inventory)))
    for index, item in enumerate(assets["depth"]):
        target = physical(root, item["logical_path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        phase("depth_"+str(index), copied(item, target))
    transport = config["transport"]
    authentication = S.subprocess.run(["/usr/bin/gcloud", "auth", "print-access-token"],
        env=S.cloud_environment(assets["gcloud_config"]), capture_output=True, text=True, timeout=60)
    token = authentication.stdout.strip()
    if authentication.returncode or not token or "\n" in token or "\r" in token:
        raise RuntimeError("GCS authentication failed; stop for the operator")
    headers = export_headers(transport, lambda part, start, end: gcs_header_range(part, start, end, token))
    validate_export_headers(headers, config["step"])
    phase("export_headers", headers)
    target = export_destination(root, config)
    archive = archives/"export.tar"
    receipt = S.copy_parts(transport["parts"], archive,
                           lambda p: S.process_stream(
                               ["/usr/bin/gcloud", "storage", "cat", cloud_uri(p)],
                               S.cloud_environment(assets["gcloud_config"]), root/"staging.log"),
                           expected_sha=transport["archive_sha256"])
    if receipt["bytes"] != transport["archive_bytes"]:
        raise ValueError("Production export byte count differs")
    S.room(root, archive.stat().st_size)
    with archive.open("rb") as stream:
        inventory = S.extract_stream(stream, target, config["step"], archive.stat().st_size)
    if {name: row["bytes"] for name, row in inventory.items()} != {
            row["name"]: row["size"] for row in headers["members"] if row["type"] in ("0", "\0")}:
        raise ValueError("The extracted export differs from its generation-pinned header inventory")
    if S.sha(physical(root, config["worker"]["artifact"]["path"])) != config["worker"]["artifact"]["sha256"]:
        raise ValueError("Production export artifact differs")
    phase("export", receipt)
    phase("frames", frames(root, config))
    A.atomic_json(root/"STAGING.json", records)
    S.room(root)
    return records
