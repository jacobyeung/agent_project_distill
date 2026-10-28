# Rung-1 arms for 10-28 night with a checkpoint every 200 steps: each new frozen dir hard-links its source's candidate
# index and division (no new data inodes) and gets the source config with checkpoint_every_steps 200 and the listed
# changes. Write-once: an existing dir must already hold exactly these bytes.
F=/lustre/fsw/portfolios/av/users/jyeung/ap/59845bf9/d/orch/runs/aws128p_20261025/frozen
timeout 120 python3 - $F <<'PY'
import hashlib, json, os, sys
F = sys.argv[1]
ARMS = [("R27_A1_S17_K200", "R27_A1_S17", {}),
        ("R27_X_S17_K200", "R27_X_S17", {}),
        ("RG1_X_S17_K200", "RG1_X_S17", {}),
        ("RG1_X_W64_S17_K200", "RG1_X_S17", {"world_size": 64, "max_microbatch_size": 4}),
        ("RG1_X_W64_S18_K200", "RG1_X_S17", {"seed": 18, "world_size": 64, "max_microbatch_size": 4}),
        ("RG1_A1_W64_S18_K200", "RG1_A1_W64_S18", {}),
        ("RG1_A1_S18_K200", "RG1_A1_S17", {"seed": 18}),
        ("RG1_A3_W64_S17_K200", "RG1_A3_W64_S17", {}),
        ("RG1_A1S_W64_S17_K200", "RG1_A1S_W64_S17", {})]
for new, src, change in ARMS:
    config = json.load(open(f"{F}/{src}/config.json"))
    config.update(change, checkpoint_every_steps=200)
    data = (json.dumps(config, indent=2, sort_keys=True) + "\n").encode()
    d = f"{F}/{new}"
    if os.path.isdir(d):
        same = open(f"{d}/config.json", "rb").read() == data and all(
            os.path.samefile(f"{d}/{n}", f"{F}/{src}/{n}") for n in ("candidate_index.jsonl", "inherited_division.json"))
        print("K200", new, "present", "same" if same else "DIFFERENT"); continue
    os.mkdir(d + ".part")
    for n in ("candidate_index.jsonl", "inherited_division.json"):
        os.link(f"{F}/{src}/{n}", f"{d}.part/{n}")
    with open(f"{d}.part/config.json", "xb") as stream:
        stream.write(data)
    os.rename(d + ".part", d)
    print("K200", new, "from", src, "config", hashlib.sha256(data).hexdigest()[:12], "world", config["world_size"],
          "seed", config["seed"], "micro", config["max_microbatch_size"], "ckpt", config["checkpoint_every_steps"])
PY
