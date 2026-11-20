"""Exercise the selected shipped copier with local sessions and a local writer."""
from pathlib import Path
import argparse, ast, base64, hashlib, importlib.util, json, os, re, signal, stat, sys, time

sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths_k4 import L,D,R

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

def read(path):
    value = json.loads(Path(path).read_text())
    if isinstance(value, dict) and "payload" in value:
        raw = base64.b64decode(value["payload"], validate=True)
        assert hashlib.sha256(raw).hexdigest() == value["sha256"]
        return json.loads(raw)
    return value

def put(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

def module_path(kit):
    job = (kit / "job.sh").read_text()
    envelope = json.loads((kit / "k/j.json").read_text())
    decoded = base64.b64decode(envelope["payload"], validate=True)
    assert hashlib.sha256(decoded).hexdigest() == envelope["sha256"]
    texts = {"job.sh": job, "k/j.json(decoded)": decoded.decode()}
    # Follow the literal shell include used by the batch job.
    for text in list(texts.values()):
        for relative in re.findall(r"(?:\$ROOT|\$Q_KIT|\$HX)/([\w/.-]+\.sh)", text):
            if (kit / relative).is_file(): texts[relative] = (kit / relative).read_text()
    candidates = set()
    for text in texts.values():
        for line in text.splitlines():
            if "python" not in line or not any(flag in line for flag in ("--loop", "--final")): continue
            for relative in re.findall(r"(?:\$ROOT|\$Q_KIT|\$HX)/([\w/.-]+\.py)", line):
                if (kit / relative).is_file() and "class Copier:" in (kit / relative).read_text():
                    candidates.add(relative)
    if len(candidates) != 1: raise ValueError("Cannot identify one shipped live Copier: " + repr(candidates))
    relative = candidates.pop()
    return kit / relative, {name: hashlib.sha256(text.encode()).hexdigest() for name, text in texts.items()}

def writer_source():
    tree = ast.parse((L / "work/build24f/live_tests.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "WRITER" for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("Missing live_tests.WRITER")

def make_copier(kit, root):
    kit, root = Path(kit).resolve(), Path(root).resolve()
    if not root.is_relative_to(R): raise ValueError("Copier writes must stay under rehearsal_k2")
    path, launch = module_path(kit)
    spec = importlib.util.spec_from_file_location("rehearsal_k2_shipped_copier", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    target = root / "target"; home = target / "n_s"
    home.mkdir(parents=True, exist_ok=True, mode=0o700); home.chmod(0o700)
    names = read(kit / "k/y.json")["objects"]
    milestone = "m2" if "m2" in names else "m100"
    if milestone not in names: raise ValueError("Kit does not name the rehearsal milestone")
    sessions = {key + f".part{i:02d}-of-04": "https://rehearsal.invalid/local-only/" + str(i)
                for key in names.values() for i in range(4)}
    session = home / "sess.json"
    fd = os.open(session, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        os.fchmod(stream.fileno(), 0o600); json.dump(sessions, stream, sort_keys=True)
    writer = root / "writer.py"
    # Check coverage before invoking the unchanged local split writer.
    validation = """import json,sys
from pathlib import Path
sessions=json.loads(Path(sys.argv[2]).read_text())
assert all(sys.argv[3]+f".part{i:02d}-of-04" in sessions for i in range(4))
"""
    writer.write_text(validation + writer_source())
    native_read = module.read
    def fixture_read(p):
        value = native_read(p)
        if Path(p).resolve() == kit / "k/p.json":
            value = dict(value, n_root=str(target))
        return value
    module.read = fixture_read
    c = module.Copier(kit, root, "rehearsal", target=target, train=root / "p2/q/r", home=home, writer=writer)
    c.names["objects"]["m2"] = names[milestone]
    assert stat.S_IMODE(home.stat().st_mode) == 0o700
    assert stat.S_IMODE(session.stat().st_mode) == 0o600
    evidence = dict(kit=str(kit), kit_seal=sha(kit / "SHA256SUMS.txt"), module=str(path), module_sha256=sha(path),
                    launcher_sources=launch, step2_object=names[milestone], session_names=sorted(sessions),
                    directory_mode="0700", file_mode="0600", target=str(target),
                    boundaries=["k/p.json n_root substituted in memory only", "m2 uses " + milestone,
                                "local live_tests.WRITER; no network or GCS"], writer_sha256=sha(writer))
    put(root / "COPIER_SOURCE.json", evidence)
    return c, evidence

def main():
    p = argparse.ArgumentParser(); p.add_argument("kit", type=Path)
    p.add_argument("--root", type=Path, default=R); p.add_argument("--once", action="store_true")
    a = p.parse_args(); c, evidence = make_copier(a.kit, a.root)
    if a.once: c.pass_once(); return
    stop = [False]
    for sig in (signal.SIGTERM, signal.SIGINT): signal.signal(sig, lambda *_: stop.__setitem__(0, True))
    while not stop[0]: c.pass_once(); time.sleep(1)
    c.pass_once()

if __name__ == "__main__": main()
