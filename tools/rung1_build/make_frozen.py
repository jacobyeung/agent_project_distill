"""Frozen inputs of the three rung-1 arms (trinity-3-3, Python 3.6): candidate index, inherited division and training
config per arm, packed as frozen/<ARM>/... for the code-aws preparation job.

  RG1_A1_S17  export X, LoRA on text, vision and mergers (the SELF_V4 default)
  RG1_A2_S17  export X, vision frozen: targets text + mergers (needs trainer support; b4b2979 fixes "targets")
  RG1_A3_S17  export P (GT perception targets), same config as A1

Config: the SELF_V4 S17 config with world_size 8 (one 8-GPU node, effective batch 32), checkpoint_every_steps 500 and the
neutral r1835 parent pins on code-aws (weights 02bccd99..., neutral publication 70c634a8...).
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
ARMS = {"RG1_A1_S17": ("X", {}),
        "RG1_A2_S17": ("X", {"targets": "exact_text_attention_mlp_mergers"}),
        "RG1_A3_S17": ("P", {})}


def main():
    src, out = sys.argv[1:3]
    arms = json.loads(os.environ["R1_ARMS"]) if os.environ.get("R1_ARMS") else ARMS  # test runs name their own arms
    template = json.load(open(src + TEMPLATE))
    assert template["init_adapter"]["weights_sha256"] == NEUTRAL_PARENT["weights_sha256"]
    assert template["targets"] == "exact_text_attention_mlp_vision_attention_mlp_mergers"
    members, summary = [], {}
    for arm, (export, change) in sorted(arms.items()):
        config = dict(template)
        config.update(world_size=8, seed=17, checkpoint_every_steps=500, init_adapter=dict(NEUTRAL_PARENT), **change)
        if "targets" in change:
            groups = dict(config["group_parameters"])
            groups.pop("vision")
            config["group_parameters"] = groups
            config["trainable_parameters"] = sum(groups.values())
        files = {
            "config.json": (json.dumps(config, indent=2, sort_keys=True) + "\n").encode(),
            "candidate_index.jsonl": open(os.path.join(out, "export_" + export, "candidate_index.jsonl"), "rb").read(),
            "inherited_division.json": open(os.path.join(out, "export_" + export, "inherited_division.json"), "rb").read(),
        }
        for name, data in sorted(files.items()):
            members.append(("frozen/%s/%s" % (arm, name), data))
        summary[arm] = {name: {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}
                        for name, data in files.items()}
        summary[arm]["export"] = export
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
