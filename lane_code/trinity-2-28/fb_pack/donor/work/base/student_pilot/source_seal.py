import hashlib
import gzip
from contextlib import ExitStack
import io
import os
from pathlib import Path, PurePosixPath
import re
import tarfile

from .p3_provenance import digest, file_pin, pinned, sha256


SCHEMA = "c1-sealed-source-v1"


def inventory(root):
    root = Path(root)
    files = {}
    for directory, dirs, names in os.walk(root):
        dirs[:] = sorted(name for name in dirs if name not in (".git", "__pycache__", "artifacts"))
        if any((Path(directory) / name).is_symlink() for name in dirs + names):
            raise ValueError("Source contains a link")
        for name in sorted(names):
            path = Path(directory) / name
            if path.stat().st_size > 16_000_000:
                raise ValueError("Source contains a non-tiny asset")
            files[str(path.relative_to(root))] = sha256(path)
    return files


def archive(root, output, files, *, compress=False):
    root = Path(root)
    with ExitStack() as stack:
        if compress:
            raw_output = stack.enter_context(Path(output).open('xb'))
            compressed = stack.enter_context(gzip.GzipFile(filename='', mode='wb', fileobj=raw_output, mtime=0))
            target = stack.enter_context(tarfile.open(fileobj=compressed, mode='w'))
        else:
            target = stack.enter_context(tarfile.open(output, 'x'))
        for name in sorted(files):
            raw = (root / name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != files[name]:
                raise ValueError("Source changed during packaging")
            entry = tarfile.TarInfo(name)
            entry.size = len(raw)
            entry.mode = 0o755 if os.access(root / name, os.X_OK) else 0o644
            target.addfile(entry, io.BytesIO(raw))


def check_archive(pin, expected):
    files = {}
    with tarfile.open(pinned(pin), "r:*") as archive_file:
        for member in archive_file:
            name = PurePosixPath(member.name)
            if (not member.isfile() or name.is_absolute() or ".." in name.parts
                    or member.name in files or member.size > 16_000_000):
                raise ValueError("Archive contains an unadmitted member")
            with archive_file.extractfile(member) as handle:
                value = hashlib.sha256()
                for block in iter(lambda: handle.read(1 << 20), b""):
                    value.update(block)
            files[member.name] = value.hexdigest()
    if files != expected:
        raise ValueError("Archive does not contain the sealed source tree")


def create(root, archive_file, sources, operation_sources, *, archive_path=None):
    files = inventory(root)
    archive_pin = file_pin(archive_file)
    check_archive(archive_pin, files)
    if any(files.get(name) != value for name, value in {**sources, **operation_sources}.items()):
        raise ValueError("Source closure is outside the sealed tree")
    if archive_path is not None:
        archive_pin["path"] = str(archive_path)
    tree_sha = digest(files)
    return dict(schema=SCHEMA, commit="sha256:"+tree_sha, tree_sha256=tree_sha, files=files,
                sources=sources, operation_sources=operation_sources, archive=archive_pin)


def verify(seal, root, sources):
    files = inventory(root)
    if (seal.get("schema") != SCHEMA or seal.get("files") != files or seal.get("sources") != sources
            or seal.get("tree_sha256") != digest(files) or seal.get("commit") != "sha256:"+digest(files)):
        raise ValueError("Source differs from its sealed tree")
    check_archive(seal["archive"], files)
    return seal["commit"]


def binding(seal, config_sha):
    if seal.get("schema") != SCHEMA:
        return None
    if not isinstance(config_sha, str) or not re.fullmatch("[0-9a-f]{64}", config_sha):
        raise ValueError("Source binding needs a configuration SHA256")
    value = dict(schema="s1-run-seal-v1", tree_sha256=seal["tree_sha256"],
                 config_sha256=config_sha, archive=seal["archive"])
    return {**value, "sha256": digest(value)}


def check_binding(value, seal, config_sha):
    if value != binding(seal, config_sha):
        raise ValueError("Tree/configuration seal differs")


def check_export(receipt, artifact):
    training = receipt.get("source_seal")
    exported = artifact.get("source_seal")
    if training is None and exported is None:
        return
    if not isinstance(training, dict) or not isinstance(exported, dict):
        raise ValueError("Export lacks its source seal")
    for value in (training, exported):
        body = {key: part for key, part in value.items() if key != "sha256"}
        if (set(body) != {"schema", "tree_sha256", "config_sha256", "archive"}
                or body["schema"] != "s1-run-seal-v1" or value.get("sha256") != digest(body)):
            raise ValueError("Export source seal is malformed")
    if (training["tree_sha256"] != exported["tree_sha256"] or training["archive"] != exported["archive"]
            or exported["config_sha256"] != artifact["config_sha256"]
            or artifact.get("training_source_seal") != training):
        raise ValueError("Export source lineage differs from preparation")
