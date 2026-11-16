from pathlib import Path

from .p3_provenance import file_pin, load, pinned


def clip_sources(value):
    path = pinned(value)
    if path.suffix != ".json":
        return None
    manifest = load(path)
    if manifest.get("schema") != "s1-mdg-clips-v1":
        raise ValueError("Unknown MDG clip manifest")
    sources = manifest.get("clips")
    if not isinstance(sources, list) or not sources:
        raise ValueError("MDG clip manifest needs pinned sources")
    paths = [pinned(source).resolve() for source in sources]
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate MDG clip source")
    return sources


def directory(value):
    if isinstance(value, str):
        return str(Path(value).resolve()), None
    if not isinstance(value, dict) or set(value) != {"root", "manifest"}:
        raise ValueError("MDG directory requires its root and pinned manifest")
    root = Path(value["root"])
    if not root.is_absolute() or ".." in root.parts:
        raise ValueError("MDG directory root must be absolute")
    pinned(value["manifest"])
    return str(root.resolve()), value["manifest"]


def artifact(value):
    if isinstance(value, str):
        root = Path(value)
        result = {name: file_pin(root / name) for name in ("mdg.json", "mdg.pt")}
        if load(root / "mdg.json").get("lora_config"):
            result["lora.pt"] = file_pin(root / "lora.pt")
        return result
    if (not isinstance(value, dict) or not {"mdg.json", "mdg.pt"} <= set(value)
            or set(value) - {"mdg.json", "mdg.pt", "lora.pt"}):
        raise ValueError("MDG initialization needs exact metadata and weight pins")
    paths = {name: pinned(pin).resolve() for name, pin in value.items()}
    if len({path.parent for path in paths.values()}) != 1 or any(path.name != name for name, path in paths.items()):
        raise ValueError("MDG initialization files must share one canonical directory")
    if bool(load(paths["mdg.json"]).get("lora_config")) != ("lora.pt" in paths):
        raise ValueError("MDG initialization LoRA pins differ")
    return value


def raster_manifest(source):
    if not source.get("raster_manifest"):
        return None
    manifest = load(pinned(source["raster_manifest"]))
    if manifest.get("schema") != "s1-mdg-raster-inputs-v1":
        raise ValueError("Unknown MDG raster manifest")
    root = Path(source["rasters"]).resolve()
    result = {}
    for item in manifest.get("files", []):
        relative = Path(item["destination"])
        path = (root / relative).resolve()
        if relative.is_absolute() or ".." in relative.parts or not path.is_relative_to(root) or path in result:
            raise ValueError("Invalid or duplicate MDG raster member")
        if type(item["bytes"]) is not int or item["bytes"] < 1:
            raise ValueError("MDG raster member lacks its size")
        result[path] = dict(path=str(path), sha256=item["sha256"], bytes=item["bytes"])
    if len(result) != manifest.get("count") or not result:
        raise ValueError("MDG raster manifest membership differs")
    return result


def frame_hashes(source):
    if not source.get("frame_manifest"):
        return None
    value = load(pinned(source["frame_manifest"]))
    if value.get("complete") is not True or value.get("errors") or value.get("checked") != len(value.get("frames", {})):
        raise ValueError("Resized MDG frame manifest is incomplete")
    result = set()
    for item in value["frames"].values():
        sha = item["sha256"]
        if item["name"] != f"k8pd/{sha[:2]}/{sha}.png":
            raise ValueError("Resized MDG frame name differs from its hash")
        result.add(sha)
    return result


def explicit_frames(clip, root):
    if clip.get("student_input"):
        return clip
    from .grounding_train import clip_row
    row = clip_row(clip)
    row["student_input"]["frames"] = [
        dict(path=str(Path(root) / "k8pd" / sha[:2] / (sha+".png")), sha256=sha)
        for sha in clip["frame_sha256"]]
    return {**clip, "student_input": row["student_input"]}
