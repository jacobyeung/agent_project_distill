"""Re-pin the rcj helpers' whole-tree constant (nd.py:243 TREE, ch.py:16 TREE) to a new tree seal.

Usage: python -I swap_rcj.py RCJ_IN OUT_DIR OLD_SEAL NEW_SEAL
Copies RCJ_IN to OUT_DIR, replaces exactly one TREE line in each of nd.py and ch.py, and leaves every
other helper byte-identical (f.json's descriptive tree_sha256 is not read by code; it and nd.py FIELDS stay).
"""
from pathlib import Path
import hashlib, json, shutil, sys


def main(src, out, old, new):
    src, out = Path(src), Path(out)
    shutil.copytree(src, out, copy_function=shutil.copy2)
    for name in ('nd.py', 'ch.py'):
        path = out / name
        text = path.read_text()
        line = "TREE = '%s'\n" % old
        if text.count(line) != 1 or text.count(old) != 1:
            raise ValueError('TREE pin not unique in ' + name)
        mode = path.stat().st_mode & 0o777
        path.write_text(text.replace(line, "TREE = '%s'\n" % new))
        path.chmod(mode)
    result = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()}
    print(json.dumps(result, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:])
