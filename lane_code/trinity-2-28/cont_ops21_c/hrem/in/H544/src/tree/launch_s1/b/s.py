import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile
import uuid


def sha256(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            value.update(block)
    return value.hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def inside(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("Unsafe staged member name")
    root = Path(root).resolve()
    result = root.joinpath(*relative.parts)
    if not result.resolve().is_relative_to(root) or any(
            parent.is_symlink() for parent in (result, *result.parents) if parent.is_relative_to(root)):
        raise ValueError("Staged member escapes its owned root")
    return result


class Reader:
    def __init__(self, stream):
        self.stream, self.digest, self.bytes = stream, hashlib.sha256(), 0

    def read(self, size=-1):
        block = self.stream.read(size)
        self.digest.update(block)
        self.bytes += len(block)
        return block


class Stage:
    def __init__(self, kit, node):
        self.kit, self.node = Path(kit).resolve(), Path(node).resolve()
        self.roots = dict(u=self.node / "aws/u/ap/8865619b/u",
                          data2root=self.node / "c7d31ddd/data2root")
        self.state, self.parts = self.node / ".imports", self.node / ".parts"
        self.state.mkdir(parents=True, exist_ok=True)
        self.parts.mkdir(parents=True, exist_ok=True)
        self.code = sha256(__file__)

    def destination(self, value):
        path = PurePosixPath(value)
        if not path.parts or path.parts[0] not in self.roots or len(path.parts) < 2:
            raise ValueError("Staged destination is outside the input roots")
        return inside(self.roots[path.parts[0]], str(PurePosixPath(*path.parts[1:])))

    def metadata(self, pin):
        path = inside(self.kit, pin["file"])
        if sha256(path) != pin["sha256"]:
            raise ValueError("Staging metadata changed")
        return json.loads(path.read_text())

    def publish(self, stream, destination, expected, size):
        if not re.fullmatch("[0-9a-f]{64}", expected) or type(size) is not int or size < 0:
            raise ValueError("Staged payload lacks an exact digest and byte count")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if destination.stat().st_size != size or sha256(destination) != expected:
                raise ValueError("An existing staged payload differs")
            return
        bucket = self.parts / expected[:2]
        bucket.mkdir(exist_ok=True)
        partial = bucket / (expected+"."+uuid.uuid4().hex)
        reader = Reader(stream)
        with partial.open("xb") as target:
            for block in iter(lambda: reader.read(8 << 20), b""):
                target.write(block)
        if reader.bytes != size or reader.digest.hexdigest() != expected:
            raise ValueError("Staged payload differs from its pin")
        os.chmod(partial, 0o400)
        os.link(partial, destination)

    def file(self, entry):
        destination = self.destination(entry["destination"])
        if destination.exists():
            self.publish(io.BytesIO(), destination, entry["sha256"], entry["bytes"])
            return
        source = Path(entry["source"])
        if source.stat().st_size != entry["bytes"]:
            raise ValueError("Staged source byte count differs")
        with source.open("rb") as stream:
            self.publish(stream, destination, entry["sha256"], entry["bytes"])

    def archive(self, entry):
        inventory = None
        if "inventory" in entry:
            inventory = {}
            for value in entry["inventory"]:
                if value["name"] in inventory and inventory[value["name"]] != value:
                    raise ValueError("Archive inventory repeats a conflicting member")
                inventory[value["name"]] = value
            if not inventory:
                raise ValueError("Archive inventory is empty")
        identity = hashlib.sha256(encoded(dict(entry=entry, implementation=self.code))).hexdigest()
        marker = self.state / (identity+".json")
        if marker.exists():
            record = json.loads(marker.read_text())
            if record.get("identity") != identity or record.get("entry") != entry or not record.get("files"):
                raise ValueError("Staged archive receipt differs")
            files = record["files"]
            for value in files:
                path = self.destination(value["destination"])
                if not path.is_file() or path.stat().st_size != value["bytes"]:
                    raise ValueError("A staged archive member disappeared or changed size")
            for value in sorted(files, key=lambda item: hashlib.sha256(
                    ("17|"+item["destination"]).encode()).hexdigest())[:64]:
                if sha256(self.destination(value["destination"])) != value["sha256"]:
                    raise ValueError("A staged archive hash sample changed")
            return dict(sha256=entry["sha256"], members=len(files), reused=True)
        files, seen = [], set()
        source = Path(entry["source"])
        if source.stat().st_size != entry["bytes"]:
            raise ValueError("Archive source byte count differs")
        with source.open("rb") as stream:
            reader = Reader(stream)
            with tarfile.open(fileobj=reader, mode="r|*") as archive:
                for member in archive:
                    relative = PurePosixPath(member.name)
                    if relative.is_absolute() or ".." in relative.parts or member.issym() or member.islnk():
                        raise ValueError("Unsafe archive member")
                    if member.isdir():
                        continue
                    if not member.isfile():
                        raise ValueError("Nonregular archive member")
                    prefix = entry.get("member_prefix")
                    if prefix and not relative.is_relative_to(prefix):
                        raise ValueError("Archive member has the wrong prefix")
                    if inventory is not None:
                        if str(relative) == "SHA256SUMS" and member.size <= 65536:
                            continue
                        value = inventory.get(str(relative))
                        if value is None or value["bytes"] != member.size:
                            raise ValueError("Archive member differs from its inventory")
                        expected = value["sha256"]
                    else:
                        expected = relative.stem
                        if (relative.suffix != ".png" or not re.fullmatch("[0-9a-f]{64}", expected)
                                or relative.parent.name != expected[:2]):
                            raise ValueError("Frame archive is not content-addressed")
                    if str(relative) in seen:
                        if inventory is not None:
                            continue
                        raise ValueError("Duplicate frame archive member")
                    seen.add(str(relative))
                    destination = str(PurePosixPath(entry["destination"]) / relative)
                    with archive.extractfile(member) as payload:
                        self.publish(payload, self.destination(destination), expected, member.size)
                    files.append(dict(destination=destination, sha256=expected, bytes=member.size))
            while reader.read(8 << 20):
                pass
            if reader.bytes != entry["bytes"] or reader.digest.hexdigest() != entry["sha256"]:
                raise ValueError("Frame archive digest differs")
        if (not files or entry.get("members", len(files)) != len(files)
                or inventory is not None and seen != set(inventory)):
            raise ValueError("Frame archive member count differs")
        data = encoded(dict(identity=identity, entry=entry, files=files))
        self.publish(io.BytesIO(data), marker, hashlib.sha256(data).hexdigest(), len(data))
        return dict(sha256=entry["sha256"], members=len(files), reused=False)

    def run(self, plan, *, frames=True):
        if plan.get("schema") != "s1-staged-inputs-v1":
            raise ValueError("Unknown staging contract")
        results = []
        for entry in plan.get("packages", []):
            results.append(self.archive(entry))
        for entry in plan["files"]:
            self.file(entry)
        for entry in plan["directories"]:
            manifest = self.metadata(entry["manifest"])
            if manifest.get("schema") != "s1-mdg-raster-inputs-v1" or manifest["count"] != len(manifest["files"]):
                raise ValueError("Raster manifest differs")
            if sum(value["bytes"] for value in manifest["files"]) != manifest["bytes"]:
                raise ValueError("Raster byte count differs")
            for value in manifest["files"]:
                self.file(dict(source=str(inside(entry["source_root"], value["destination"])),
                               destination=value["destination"], sha256=value["sha256"], bytes=value["bytes"]))
            results.append(dict(raster_files=manifest["count"], bytes=manifest["bytes"]))
        if frames:
            for entry in plan["archives"]:
                results.append(self.archive(entry))
        return dict(schema="s1-staging-result-v1", status="PASS", results=results,
                    frames_staged=frames, production_authorized=False)


def main():
    current, kit, node, mode = sys.argv[1:]
    value = json.loads(Path(current).read_text())
    if "staged_inputs" in value:
        result = Stage(kit, node).run(value["staged_inputs"], frames=mode == "full")
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
