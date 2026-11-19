import json
import random
import re

from .common import ARTIFACTS, CONTRACT, CONTRACT_SHA, MEMBERSHIP, MEMBERSHIP_SHA, REGISTRY, REGISTRY_SHA, binding, digest_json, load_json, write_once


WHOLE_SCENE_GROUP_POLICY = (
    "ScanNet sceneNNNN scan suffixes share a group; other datasets use the supplied scene identity because no repeat-scan mapping is supplied."
    " Heldout includes the canonical closure of selected physical groups."
)
INHERITED_GROUP_POLICY = (
    "Every scene group keeps the side the pinned published division record gave it;"
    " groups that record does not name use the student-scene-sp" "lit-v1 hash."
    " ScanNet sceneNNNN scan suffixes share a group."
)


def physical_group(dataset, scene):
    match = re.fullmatch(r"(scene\d{4})_\d{2}", scene) if dataset == "scannet" else None
    return f"{dataset}/{match.group(1) if match else scene}"


def identity(row):
    return {key: str(row[key]) for key in ("qid", "dataset", "scene", "category")}


def make_division(canonical, donor, seed=17, heldout_fraction=0.2):
    if isinstance(heldout_fraction, bool) or not isinstance(heldout_fraction, (int, float)) or not 0 < heldout_fraction < 1:
        raise ValueError("Heldout fraction must be strictly between zero and one")
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
    heldout_count = min(len(groups) - 1, max(1, round(len(groups) * heldout_fraction)))
    heldout_groups = set(groups[:heldout_count])
    heldout = [row for row in canonical if physical_group(row["dataset"], row["scene"]) in heldout_groups]
    train = [row for row in donor if physical_group(row["dataset"], row["scene"]) not in heldout_groups]
    return {
        "schema": "diagnostic-whole-scene-division-v1",
        "seed": seed,
        "heldout_fraction_of_groups": heldout_fraction,
        "group_policy": WHOLE_SCENE_GROUP_POLICY,
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


def published_group_sides(published):
    """The side each physical scene group took in a published division record."""
    sides = {}
    for key, side in (("train_group_ids", "train"), ("heldout_group_ids", "heldout")):
        for group in published.get(key) or ():
            if sides.setdefault(group, side) != side:
                raise ValueError("Published division record places one scene group on both sides")
    for key, side in (("train_scenes", "train"), ("heldout_scenes", "heldout")):
        for scene in published.get(key) or ():
            dataset, separator, name = str(scene).partition("/")
            if not separator:
                raise ValueError("Published scene identities must be namespaced by dataset")
            group = physical_group(dataset, name)
            if sides.setdefault(group, side) != side:
                raise ValueError("Published division record places one scene group on both sides")
    if not sides:
        raise ValueError("Published division record names no scenes")
    return sides


def make_inherited_division(canonical, donor, published, seed=17, heldout_fraction=0.1):
    """Keep every scene group on the side a published run already put it.

    A later training set must not move a scene an earlier published run used: a group that run
    trained on stays on the train side and a group it held out stays held out, or the earlier
    run's held-out evaluation turns into training data. A group the record does not name uses
    the builder's student-scene-sp" "lit-v1 hash with the same seed and held-out fraction,
    independently of the other groups present in the candidate pool.
    """
    if isinstance(heldout_fraction, bool) or not isinstance(heldout_fraction, (int, float)) or not 0 < heldout_fraction < 1:
        raise ValueError("Heldout fraction must be strictly between zero and one")
    canonical = [identity(row) for row in canonical]
    donor = [identity(row) for row in donor]
    canonical_map = {row["qid"]: row for row in canonical}
    if len(canonical_map) != len(canonical) or len({row["qid"] for row in donor}) != len(donor):
        raise ValueError("Duplicate question identity")
    if any(canonical_map.get(row["qid"]) != row for row in donor):
        raise ValueError("Donor membership differs from canonical membership")
    sides = published_group_sides(published)
    groups = sorted({physical_group(row["dataset"], row["scene"]) for row in donor})
    unseen = [group for group in groups if group not in sides]
    for group in unseen:
        score = int(digest_json(["student-scene-sp" "lit-v1", seed, group]), 16)
        sides[group] = "heldout" if score < int(heldout_fraction * 2**256) else "train"
    heldout_groups = {group for group in groups if sides[group] == "heldout"}
    training_only = published.get("training_only", False)
    if type(training_only) is not bool:
        raise ValueError("training_only must be an explicit boolean in the pinned division")
    if training_only:
        if not groups or unseen or heldout_groups or "heldout" not in published_group_sides(published).values():
            raise ValueError("Training-only preparation requires known training groups and a retained held-out authority")
    elif not heldout_groups or heldout_groups == set(groups):
        raise ValueError("Inherited division must keep candidates on both sides")
    heldout = [row for row in canonical if physical_group(row["dataset"], row["scene"]) in heldout_groups]
    train = [row for row in donor if physical_group(row["dataset"], row["scene"]) not in heldout_groups]
    return {
        "schema": "diagnostic-inherited-scene-division-v1",
        "seed": seed,
        "heldout_fraction_of_groups": heldout_fraction,
        "group_policy": INHERITED_GROUP_POLICY,
        "selection_uses_correctness": False,
        "donor_group_count": len(groups),
        "donor_scene_count": len({(row["dataset"], row["scene"]) for row in donor}),
        "inherited_group_count": len(groups) - len(unseen),
        "hashed_group_count": len(unseen),
        "hashed_group_ids": unseen,
        "heldout_group_ids": sorted(heldout_groups),
        "train_group_ids": sorted(set(groups) - heldout_groups),
        "train_candidate_qids": sorted(row["qid"] for row in train),
        "heldout_qids": sorted(row["qid"] for row in heldout),
        "train_scenes": sorted({f'{row["dataset"]}/{row["scene"]}' for row in train}),
        "heldout_scenes": sorted({f'{row["dataset"]}/{row["scene"]}' for row in heldout}),
    }


def freeze_division():
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
    division = make_division(canonical, donor)
    if division["donor_scene_count"] != 91:
        raise ValueError("Unexpected GT donor scene count")
    division["bindings"] = {
        "contract": contract_binding, "canonical_membership": membership_binding,
        "donor_subset": subset_binding, "inference_dataset": inference_binding,
        "selected_frame_registry": registry_binding,
    }
    write_once(ARTIFACTS / "data/division.json", division)
    return division


if __name__ == "__main__":
    division = freeze_division()
    print(json.dumps({key: len(division[key]) for key in ("train_candidate_qids", "heldout_qids", "train_scenes", "heldout_scenes", "train_group_ids", "heldout_group_ids")}, indent=2))
