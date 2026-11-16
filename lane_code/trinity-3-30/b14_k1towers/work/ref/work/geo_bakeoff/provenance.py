import json
from pathlib import Path

from .io import sha256


PRICING_FILES = ("config.json", "rows.jsonl", "scores.json", "scores_fallback.json",
                 "errors.json", "errors_by_type.json", "parity.json", "raw.jsonl", "raw_summary.json")


def verify_arm_epoch(exports, digest):
    request = json.loads((Path(exports).parent / "request.json").read_text())
    if request["kit_seal_sha256"] != digest:
        raise ValueError("Parent geometry belongs to another sealed epoch")
    return request


def verify_export_receipt(exports, scene, complete=True):
    exports = Path(exports)
    if complete:
        summary = json.loads((exports / "summary.json").read_text())
        rows = summary["receipts"]
        by_scene = {row["scene"]: row for row in rows}
        if summary["status"] != "complete" or len(rows) != len(by_scene) or summary["scenes"] != len(rows):
            raise ValueError("The parent summary is incomplete or contains duplicate scenes")
        if summary.get("configuration_sha256") != sha256(exports / "config.json"):
            raise ValueError("The parent configuration differs from its receipt")
        if scene not in by_scene:
            raise ValueError(f"The parent did not finish scene {scene}")
        receipt = by_scene[scene]
    else:
        receipt = json.loads((exports / "receipts" / f"{scene}.json").read_text())
    if receipt["scene"] != scene:
        raise ValueError("Foreign scene receipt")
    filename = f"scannet__{scene}.npz"
    digest = receipt.get("export_sha256", receipt.get("output_sha256"))
    if not digest or sha256(exports / filename) != digest:
        raise ValueError(f"Parent export digest differs: {scene}")
    for key, relative in (
        ("dense_sha256", Path("dense") / filename),
        ("native_metrics_sha256", Path("native_metrics") / f"{scene}.json"),
        ("consensus_sha256", Path("consensus") / f"{scene}.json"),
        ("native_recipe_sha256", Path("native_recipes") / f"{scene}.json"),
    ):
        if key in receipt and sha256(exports / relative) != receipt[key]:
            raise ValueError(f"Parent artifact digest differs: {scene}/{key}")
    return receipt


def verify_pricing_cell(directory):
    from .pricing_policy import validate_pricing
    directory = Path(directory)
    receipt = json.loads((directory / "COMPLETE.json").read_text())
    if set(receipt["files"]) != set(PRICING_FILES):
        raise ValueError("Incomplete pricing receipt")
    for name, digest in receipt["files"].items():
        if sha256(directory / name) != digest:
            raise ValueError(f"Pricing receipt differs: {directory}/{name}")
    config = json.loads((directory / "config.json").read_text())
    rows = [json.loads(line) for line in (directory / "rows.jsonl").read_text().splitlines()]
    parity = json.loads((directory / "parity.json").read_text())["mismatches"]
    validate_pricing(rows, config, parity)
    return rows, config
