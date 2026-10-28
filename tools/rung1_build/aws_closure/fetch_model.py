"""Fetch one pinned model snapshot from the public model hub into the code-aws model root (host side, stdlib only).

usage: fetch_model.py SPEC_JSON   spec: {"repo_hex": hex of "ORG/NAME", "revision": 40-hex commit,
                                         "config_sha256": expected sha256 of config.json, "model_root": directory}
Files land in MODEL_ROOT/models--ORG--NAME/snapshots/REVISION/ (the hub cache layout the trainer reads), each written to a
.part file and renamed; an existing file of the listed size is kept. config.json must hash to config_sha256. The
processor files are compared with every other snapshot under MODEL_ROOT and their hashes printed.
"""
import hashlib
import json
import os
import subprocess
import sys
import urllib.request


def sha_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def main(spec_path):
    spec = json.load(open(spec_path))
    repo = bytes.fromhex(spec["repo_hex"]).decode()
    revision, root = spec["revision"], spec["model_root"]
    assert len(revision) == 40 and all(c in "0123456789abcdef" for c in revision)
    org, _, name = repo.partition("/")
    assert org and name and "/" not in name
    target = os.path.join(root, "models--%s--%s" % (org, name), "snapshots", revision)
    os.makedirs(target, exist_ok=True)
    with urllib.request.urlopen("https://huggingface.co/api/models/%s/revision/%s?blobs=true" % (repo, revision),
                                timeout=60) as reply:
        info = json.load(reply)
    files = [(s["rfilename"], s.get("size")) for s in info["siblings"]]
    print("FILES", len(files), "BYTES", sum(size or 0 for _, size in files), flush=True)
    for relative, size in files:
        path = os.path.join(target, relative)
        if os.path.exists(path) and (size is None or os.path.getsize(path) == size):
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        url = "https://huggingface.co/%s/resolve/%s/%s" % (repo, revision, relative)
        subprocess.check_call(["curl", "-sS", "-L", "--fail", "--retry", "3", "-o", path + ".part", url])
        if size is not None and os.path.getsize(path + ".part") != size:
            raise SystemExit("SIZE_MISMATCH " + relative)
        os.replace(path + ".part", path)
        print("GOT", relative, size, flush=True)
    config = sha_file(os.path.join(target, "config.json"))
    if config != spec["config_sha256"]:
        raise SystemExit("CONFIG_SHA_MISMATCH " + config)
    print("CONFIG_OK", config)
    processor = ("preprocessor_config.json", "video_preprocessor_config.json", "tokenizer.json", "tokenizer_config.json",
                 "chat_template.jinja", "chat_template.json", "vocab.json", "merges.txt")
    for other in sorted(os.listdir(root)):
        snapshots = os.path.join(root, other, "snapshots")
        if not os.path.isdir(snapshots):
            continue
        for snap in sorted(os.listdir(snapshots)):
            for name_ in processor:
                path = os.path.join(snapshots, snap, name_)
                if os.path.exists(path):
                    print("PROCESSOR", other[-12:], snap[:8], name_, sha_file(path)[:16])
    print("FETCH_DONE", target)


if __name__ == "__main__":
    main(sys.argv[1])
