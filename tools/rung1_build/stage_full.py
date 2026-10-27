"""After the full build lands on trinity-0-13 (/scratch/jjyeung/rung1_push/out_full): write the frame plan and the
specs for the code-aws preparation jobs, and queue upload actions in poll-sized batches (python3.12).

usage: stage_full.py plan            frame plan (fails if a needed frame has no code-aws source)
       stage_full.py uploads N       queue upload batch N (0, 1, ...) of the row archives, frozen inputs and plan
       stage_full.py jobs CLOSURE    queue the specs and one CPU prep job per chain (A1, A3, control)
"""
import json
from pathlib import Path
import subprocess
import sys

OUT = Path("/scratch/jjyeung/rung1_push/out_full")
PUSH = Path("/scratch/jjyeung/rung1_push")
TOOLS = Path(__file__).resolve().parent
CODE = TOOLS.parent / "work/code"
PY = "/home/jjyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12"
X = "/lustre/fsw/portfolios/av/users/jyeung/ap/59845bf9/x"
BATCH_BYTES = 350_000_000  # one poll streams at most ~350 MB (0.5 MB/s, 900 s timeout)


def files():
    """(path, sha256) of everything the prep jobs read, from the build's own manifests."""
    entries = []
    for export in ("X", "G", "P"):
        for archive in json.loads((OUT / f"export_{export}/ARCHIVES.json").read_text()):
            entries.append((OUT / f"export_{export}" / archive["file"], archive["sha256"], archive["size_bytes"]))
    frozen = json.loads((OUT / "FROZEN_INPUTS.json").read_text())["archive"]
    entries.append((OUT / "frozen_inputs.tar.gz", frozen["sha256"], frozen["size_bytes"]))
    plan = OUT / "FRAME_PLAN_FULL.json"
    entries.append((plan, None, plan.stat().st_size))
    return entries


def main(argv):
    if argv[0] == "plan":
        subprocess.check_call(["python3", str(CODE / "make_frame_plan.py"), str(OUT / "FRAMES_NEEDED.json"),
                               str(OUT / "AWS_FRAME_PLAN.json"), str(PUSH / "frames"), X,
                               str(OUT / "FRAME_PLAN_FULL.json")])
    elif argv[0] == "uploads":
        wanted, batch, size = int(argv[1]), 0, 0
        for path, digest, nbytes in files():
            if size and size + nbytes > BATCH_BYTES:
                batch, size = batch + 1, 0
            size += nbytes
            if batch == wanted:
                args = [PY, "-B", str(TOOLS / "r1actions.py"), "upload", str(path), path.name.split(".")[0][:12]]
                if digest:
                    args.append(digest)
                print(subprocess.check_output(args, text=True).strip())
    elif argv[0] == "jobs":
        closure = argv[1]
        inc = lambda path, digest: "/opt/aws_incoming/%s%s" % (digest, "".join(path.suffixes[-2:]))
        rows = {export: [inc(OUT / f"export_{export}" / a["file"], a["sha256"])
                         for a in json.loads((OUT / f"export_{export}/ARCHIVES.json").read_text())]
                for export in ("X", "G", "P")}
        frozen = json.loads((OUT / "FROZEN_INPUTS.json").read_text())["archive"]
        plan_sha = subprocess.check_output(["sha256sum", str(OUT / "FRAME_PLAN_FULL.json")], text=True).split()[0]
        plan = {"path": f"{X}/{plan_sha}.json", "sha256": plan_sha}
        frozen_pin = {"path": inc(OUT / "frozen_inputs.tar.gz", frozen["sha256"]), "sha256": frozen["sha256"]}
        for chain, export, shards in (("RG1_A1_S17", "G", 56), ("RG1_A3_S17", "P", 56), ("RG1_C_S17", "X", 16)):
            spec = {"phase": "prep", "purpose": f"rung-1 preparation of {chain}", "frame_plans": [plan],
                    "row_archives": rows[export], "frozen_archives": [frozen_pin],
                    "chains": [{"frozen": chain, "shards": shards, "records_from": None}], "parallel": shards}
            path = OUT / f"SPEC_{chain}.json"
            path.write_text(json.dumps(spec, indent=1, sort_keys=True) + "\n")
            sha = subprocess.check_output([PY, "-B", str(TOOLS / "r1actions.py"), "spec", str(path)], text=True).strip()
            cpus, mem = ("64", "320G") if shards > 16 else ("24", "160G")
            name = subprocess.check_output([PY, "-B", str(TOOLS / "r1actions.py"), "sbatch", closure, sha, cpus, mem,
                                            "10:00:00"], text=True).strip()
            print(chain, sha, name)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
