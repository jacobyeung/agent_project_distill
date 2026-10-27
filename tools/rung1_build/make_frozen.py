"""Frozen inputs of the rung-1 arms (trinity-3-3, Python 3.6): candidate index, inherited division and training config
per arm, packed as frozen/<ARM>/... for the code-aws preparation job.

  RG1_A1_S17  export G (GT-template traces), LoRA on text, vision and mergers (the SELF_V4 default)
  RG1_A2_S17  export G, vision frozen: targets exact_text_attention_mlp_mergers_vision_frozen (trainer branch
              vision-freeze, commit e343b549; the vision LoRA keeps its r1835 values)
  RG1_A3_S17  export P (GT perception-target traces), same config as A1
  RG1_C_S17   export X answer-only control, a fixed 1-in-10 subset of the rows (yardstick only)

Config: the SELF_V4 S17 config at world_size 32 (4 nodes x 8 GPUs), checkpoint_every_steps 500 and the neutral r1835
parent pins on code-aws (weights 02bccd99..., neutral publication 70c634a8...). Env R1_RECIPE picks the batch, identical
for every arm (no gradient accumulation across nodes, so the batch is world x microbatch):
  b256 (default; trainer 6e7786b5): batch 256, 8 per GPU, LR 1e-4 x sqrt(8) = 2.83e-4; arm names RG1_<arm>_S17
  b128 (trainer 6e7786b5): batch 128, 4 per GPU, LR 2e-4; arm names RG1_<arm>_B128_S17
  b32  (fallback, trainer b4b2979 or later): batch 32, 1 per GPU, LR 1e-4; arm names RG1_<arm>_B32_S17
usage: make_frozen.py SRC_ROOT OUT_ROOT
"""
import hashlib
import io
import json
import os
import sys
import tarfile

TEMPLATE = ("/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/selfv_20261025/orchard/"
            "native_mirror/SELF_V4_S17/config.json")
NEUTRAL_PARENT = {"parent_run": "q9_l250cp_u2_camrows_ev3_w4_e1_trinity_r1835",
                  "published_sha256": "70c634a83c0835e679f736de0129d8124d94016b788fea62f5ada5303b0afd04",
                  "weights_sha256": "02bccd997be4eb55cc56ad013fa8f10e56f3f02ca9fbcbe10b64d0123e5450d6"}
VISION_FROZEN = "exact_text_attention_mlp_mergers_vision_frozen"
ARMS = {"RG1_A1_S17": ("G", {}),
        "RG1_A2_S17": ("G", {"targets": VISION_FROZEN}),
        "RG1_A3_S17": ("P", {}),
        "RG1_C_S17": ("X", {"subset": "1in10"})}
RECIPES = {"b256": ("", {"effective_batch_size": 256, "max_microbatch_size": 8, "learning_rate": 0.000283}),
           "b128": ("_B128", {"effective_batch_size": 128, "max_microbatch_size": 4, "learning_rate": 0.0002}),
           "b32": ("_B32", {})}


def main():
    src, out = sys.argv[1:3]
    suffix, recipe = RECIPES[os.environ.get("R1_RECIPE", "b256")]
    arms = {name.replace("_S17", suffix + "_S17"): (export, dict(recipe, **change)) for name, (export, change) in ARMS.items()}
    if os.environ.get("R1_ARMS"):
        arms = json.loads(os.environ["R1_ARMS"])  # test runs name their own arms and settings
    template = json.load(open(src + TEMPLATE))
    assert template["init_adapter"]["weights_sha256"] == NEUTRAL_PARENT["weights_sha256"]
    assert template["targets"] == "exact_text_attention_mlp_vision_attention_mlp_mergers"
    members, summary = [], {}
    for arm, (export, change) in sorted(arms.items()):
        change = dict(change)
        subset = change.pop("subset", None)
        config = dict(template)
        config.update(world_size=32, seed=17, checkpoint_every_steps=500, init_adapter=dict(NEUTRAL_PARENT))
        config.update(change)
        if change.get("targets") == VISION_FROZEN:
            groups = dict(config["group_parameters"])
            config["frozen_group_parameters"] = {"vision": groups.pop("vision")}
            config["group_parameters"] = groups
            config["trainable_parameters"] = sum(groups.values())
        index = open(os.path.join(out, "export_" + export, "candidate_index.jsonl"), "rb").read()
        division = json.loads(open(os.path.join(out, "export_" + export, "inherited_division.json")).read())
        if subset == "1in10":
            held = set(division["heldout_qids"])
            lines = [line for line in index.split(b"\n") if line]
            keep = [line for line in lines if json.loads(line.decode())["qid"] in held
                    or int(hashlib.sha256(json.loads(line.decode())["qid"].encode()).hexdigest(), 16) % 10 == 0]
            index = b"".join(line + b"\n" for line in keep)
        files = {
            "config.json": (json.dumps(config, indent=2, sort_keys=True) + "\n").encode(),
            "candidate_index.jsonl": index,
            "inherited_division.json": open(os.path.join(out, "export_" + export, "inherited_division.json"), "rb").read(),
        }
        for name, data in sorted(files.items()):
            members.append(("frozen/%s/%s" % (arm, name), data))
        summary[arm] = {name: {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}
                        for name, data in files.items()}
        summary[arm]["export"] = export
        summary[arm]["rows_including_heldout_support"] = index.count(b"\n")
        summary[arm]["config_changes_from_self_v4_s17"] = sorted(["world_size", "checkpoint_every_steps",
                                                                   "init_adapter.published_sha256"] + list(change))
    path = os.path.join(out, "frozen_inputs.tar.gz")
    with tarfile.open(path + ".part", "w:gz", format=tarfile.USTAR_FORMAT) as stream:
        for name, data in members:
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode = len(data), 1793059200, 0o444
            stream.addfile(info, io.BytesIO(data))
    os.rename(path + ".part", path)
    data = open(path, "rb").read()
    summary["archive"] = {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}
    with open(os.path.join(out, "FROZEN_INPUTS.json"), "w") as stream:
        json.dump(summary, stream, indent=1, sort_keys=True)
    print(json.dumps(summary["archive"]))


if __name__ == "__main__":
    main()
