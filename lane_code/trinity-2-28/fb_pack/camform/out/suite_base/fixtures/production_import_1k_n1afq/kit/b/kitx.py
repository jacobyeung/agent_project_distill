#!/usr/bin/env python3
"""Extract one kit tar into DEST while hashing it (one read pass; stdlib only).

usage: kitx.py TAR SHA256 DEST
Extracts into DEST.part.<pid>, then renames it to DEST only when the tar's SHA-256 equals SHA256 and tar exits 0.
DEST must not exist (callers keep a stamp per sha). Prints KITX_OK <name> <seconds>.
"""
import hashlib, os, subprocess, sys, time


def main(tar, expected, dest):
    started = time.time()
    if os.path.exists(dest):
        sys.exit(f"kitx: {dest} exists")
    part = f"{dest}.part.{os.getpid()}"
    os.makedirs(part)
    proc = subprocess.Popen(["tar", "-x", "-f", "-", "-C", part], stdin=subprocess.PIPE)
    digest = hashlib.sha256()
    with open(tar, "rb") as stream:
        for block in iter(lambda: stream.read(16 << 20), b""):
            digest.update(block)
            proc.stdin.write(block)
    proc.stdin.close()
    rc = proc.wait()
    if rc != 0 or digest.hexdigest() != expected:
        os.rename(part, f"{dest}.bad.{os.getpid()}")
        sys.exit(f"kitx: {tar} rc={rc} sha={digest.hexdigest()} expected {expected}")
    os.rename(part, dest)
    print(f"KITX_OK {os.path.basename(tar)} {time.time() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:4])
