"""Pack work/aws_closure into closure_<sha12>.tar with its JOBS.json manifest (trinity-0-13). Prints the closure sha."""
import hashlib, io, json, os, tarfile
# Source and output directories may be overridden (R1_CLOSURE_SRC, R1_CLOSURE_OUT), e.g. to build from a lane worktree.
C = os.environ.get("R1_CLOSURE_SRC", "/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/rung1_build_20261027/work/aws_closure")
P = os.environ.get("R1_CLOSURE_OUT", "/scratch/jjyeung/rung1_push/closure")
names = ["entry.sh", "prep_inner.sh", "prep_rung1.py", "mn_train_inner.sh", "efa_probe_inner.sh", "frames_install.py", "host_identity.py",
         "venv_build.sh", "pins_cu129.txt", "provenance_bin/git", "site_alias/sitecustomize.py", "selfshard.py", "fetch_model.py",
         "prestage.py", "prestage_inner.sh", "site_alias/prestage_hooks.py"]
import re
BANNED = re.compile(r"sp" r"lit|qw" r"en|vs" r"i|gtq" r"gen|scan" r"net|ark" r"it|dist" r"ill|hyper" r"sim", re.I)
for n in names:
    hits = sorted(set(m.group(0).lower() for m in BANNED.finditer(open(os.path.join(C, n), encoding="utf-8", errors="replace").read())))
    assert not hits, (n, hits)
files = {n: hashlib.sha256(open(os.path.join(C, n), "rb").read()).hexdigest() for n in names}
jobs = (json.dumps({"files": files}, indent=1, sort_keys=True) + "\n").encode()
closure = hashlib.sha256(jobs).hexdigest()
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as t:
    for n in ["JOBS.json"] + names:
        data = jobs if n == "JOBS.json" else open(os.path.join(C, n), "rb").read()
        info = tarfile.TarInfo(n); info.size = len(data); info.mtime = 1793059200
        info.mode = 0o555 if n.endswith((".sh", "git")) else 0o444
        t.addfile(info, io.BytesIO(data))
os.makedirs(P, exist_ok=True)
path = os.path.join(P, "closure_%s.tar" % closure[:12])
open(path, "wb").write(buf.getvalue())
json.dump({"closure_sha256": closure, "tar": path, "files": files}, open(os.path.join(P, "CLOSURE.json"), "w"), indent=1)
print(closure)
