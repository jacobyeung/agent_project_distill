"""After the full build lands on trinity-0-13 (/scratch/jjyeung/rung1_push/out_full): write the frame plan and the
specs for the code-aws preparation jobs, and queue upload actions in poll-sized batches (python3.12).

usage: stage_full.py plan            frame plan (fails if a needed frame has no code-aws source)
       stage_full.py uploads N       queue upload batch N (0, 1, ...) of the row archives, frozen inputs and plan
       stage_full.py jobs CLOSURE    queue the specs and one CPU prep job per chain (A1, A3, control)
       stage_full.py sjob CLOSURE A1_JOB   queue the job that follows A1: A2 (A1's encode records), the self-trace
                                     shard S from the verified samples on code-aws, and the A1+S mix
Every arm uses trainer 6e7786b5 (batch options) and the frozen recipe that make_frozen.py wrote (default b256).
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
TRAINER = {"trainer_commit": "6e7786b5adccf393b70c83c03149c950a32fbcf4",
           "runtime_record": "/opt/aws_incoming/534b2d61208ecdccf246c4a890c1a1e6402bdb537f317f5f3c6099dc4bd6cea1.json"}
SELF_SOURCE = "/lustre/fsw/portfolios/av/users/jyeung/ap/c4f1a9e2/v/out/c3r1"
SELF_MANIFEST = "6dcefc617325ccee0c4ad98508dd9702a9015d11bf908eed2f74da16a0126654"
SELF_SHARDS = 16


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
    elif argv[0] in ("jobs", "sjob"):
        closure = argv[1]
        inc = lambda path, digest: "/opt/aws_incoming/%s%s" % (digest, "".join(path.suffixes[-2:]))
        rows = {export: [inc(OUT / f"export_{export}" / a["file"], a["sha256"])
                         for a in json.loads((OUT / f"export_{export}/ARCHIVES.json").read_text())]
                for export in ("X", "G", "P")}
        frozen = json.loads((OUT / "FROZEN_INPUTS.json").read_text())["archive"]
        plan_sha = subprocess.check_output(["sha256sum", str(OUT / "FRAME_PLAN_FULL.json")], text=True).split()[0]
        plan = {"path": f"{X}/{plan_sha}.json", "sha256": plan_sha}
        frozen_pin = {"path": inc(OUT / "frozen_inputs.tar.gz", frozen["sha256"]), "sha256": frozen["sha256"]}
        if argv[0] == "sjob":
            commit = (TOOLS.parent / "work/COMMIT.txt").read_text().strip()
            spec = dict(TRAINER, phase="prep", purpose="rung-1 A2 (A1 records), self shard S and the A1+S mix",
                        frame_plans=[], row_archives=[], frozen_archives=[frozen_pin], self_source=SELF_SOURCE,
                        selfshard={"manifest_sha256": SELF_MANIFEST, "base_arm": "RG1_A1_S17", "s_arm": "RG1_S_S17",
                                   "mix_arm": "RG1_A1S_S17", "per_question": 2, "commit": commit},
                        chains=[{"frozen": "RG1_A2_S17", "shards": 56, "records_from": "RG1_A1_S17"},
                                {"frozen": "RG1_S_S17", "shards": SELF_SHARDS, "records_from": None},
                                {"frozen": "RG1_A1S_S17", "shards": 1,
                                 "records_from": f"RG1_A1_S17:56,RG1_S_S17:{SELF_SHARDS}"}], parallel=SELF_SHARDS)
            path = OUT / "SPEC_RG1_A2_S_A1S.json"
            path.write_text(json.dumps(spec, indent=1, sort_keys=True) + "\n")
            sha = subprocess.check_output([PY, "-B", str(TOOLS / "r1actions.py"), "spec", str(path)], text=True).strip()
            print("A2+S+A1S", sha, subprocess.check_output([PY, "-B", str(TOOLS / "r1actions.py"), "sbatch", closure, sha,
                                                          "24", "160G", "10:00:00", "afterok:" + argv[2]], text=True).strip())
            return
        for chain, export, shards in (("RG1_A1_S17", "G", 56), ("RG1_A3_S17", "P", 56), ("RG1_C_S17", "X", 16)):
            spec = dict(TRAINER, phase="prep", purpose=f"rung-1 preparation of {chain}", frame_plans=[plan],
                        row_archives=rows[export], frozen_archives=[frozen_pin],
                        chains=[{"frozen": chain, "shards": shards, "records_from": None}], parallel=shards)
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
