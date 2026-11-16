import json
import random
import re

from .common import ARTIFACTS, CONTRACT, CONTRACT_SHA, MEMBERSHIP, MEMBERSHIP_SHA, REGISTRY, REGISTRY_SHA, binding, load_json, write_once


def physical_group(dataset, scene):
    match = re.fullmatch(r"(scene\d{4})_\d{2}", scene) if dataset == "scannet" else None
    return f"{dataset}/{match.group(1) if match else scene}"


def identity(row):
    return {key: str(row[key]) for key in ("qid", "dataset", "scene", "category")}


def make_split(canonical, donor, seed=17):
    canonical = [identity(row) for row in canonical]
    donor = [identity(row) for row in donor]
    canonical_map = {row["qid"]: row for row in canonical}
    if len(canonical_map) != len(canonical) or len({row["qid"] for row in donor}) != len(donor):
        raise ValueError("Duplicate question identity")
    if any(canonical_map.get(row["qid"]) != row for row in donor):
        raise ValueError("Donor membership differs from canonical membership")
    groups = sorted({physical_group(row["dataset"], row["scene"]) for row in donor})
    if len(groups) < 2:
        raise ValueError("At least two physical scene groups are required")
    random.Random(seed).shuffle(groups)
    heldout_groups = set(groups[:max(1, round(len(groups) * 0.2))])
    heldout = [row for row in canonical if physical_group(row["dataset"], row["scene"]) in heldout_groups]
    train = [row for row in donor if physical_group(row["dataset"], row["scene"]) not in heldout_groups]
    return {
        "schema": "diagnostic-whole-scene-split-v1",
        "seed": seed,
        "heldout_fraction_of_groups": 0.2,
        "group_policy": "ScanNet sceneNNNN scan suffixes share a group; other datasets use the supplied scene identity because no repeat-scan mapping is supplied. Heldout includes the canonical closure of selected physical groups.",
        "selection_uses_correctness": False,
        "donor_group_count": len(groups),
        "donor_scene_count": len({(row["dataset"], row["scene"]) for row in donor}),
        "heldout_group_ids": sorted(heldout_groups),
        "train_group_ids": sorted(set(groups) - heldout_groups),
        "train_candidate_qids": sorted(row["qid"] for row in train),
        "heldout_qids": sorted(row["qid"] for row in heldout),
        "train_scenes": sorted({f'{row["dataset"]}/{row["scene"]}' for row in train}),
        "heldout_scenes": sorted({f'{row["dataset"]}/{row["scene"]}' for row in heldout}),
    }


def freeze_split():
    contract_binding = binding(CONTRACT, CONTRACT_SHA)
    membership_binding = binding(MEMBERSHIP, MEMBERSHIP_SHA)
    registry_binding = binding(REGISTRY, REGISTRY_SHA)
    contract = load_json(CONTRACT)
    subset_path = contract["membership"]["sealed_subset_path"]
    subset_binding = binding(subset_path, contract["membership"]["sealed_subset_sha256"])
    inference = contract["inference_dataset"]
    inference_binding = binding(inference["path"], inference["sha256"])
    canonical, donor = load_json(MEMBERSHIP), load_json(subset_path)["members"]
    if len(canonical) != 500 or len(donor) != 264:
        raise ValueError("Unexpected canonical or donor cohort size")
    split = make_split(canonical, donor)
    if split["donor_scene_count"] != 91:
        raise ValueError("Unexpected GT donor scene count")
    split["bindings"] = {
        "contract": contract_binding, "canonical_membership": membership_binding,
        "donor_subset": subset_binding, "inference_dataset": inference_binding,
        "selected_frame_registry": registry_binding,
    }
    write_once(ARTIFACTS / "data/split.json", split)
    return split


if __name__ == "__main__":
    split = freeze_split()
    print(json.dumps({key: len(split[key]) for key in ("train_candidate_qids", "heldout_qids", "train_scenes", "heldout_scenes", "train_group_ids", "heldout_group_ids")}, indent=2))
