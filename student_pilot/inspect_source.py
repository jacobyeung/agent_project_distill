import argparse
import json
import re
from pathlib import Path

from .common import CONTRACT, CONTRACT_SHA, DONOR, MEMBERSHIP, MEMBERSHIP_SHA, REGISTRY, REGISTRY_SHA, binding, load_json


def schema(value, depth=3):
    if isinstance(value, dict):
        if depth == 0:
            return {"type": "dict", "keys": list(value)[:40], "length": len(value)}
        return {key: schema(item, depth - 1) for key, item in list(value.items())[:40]}
    if isinstance(value, list):
        return {"type": "list", "length": len(value), "item": schema(value[0], depth - 1) if value and depth else None}
    return type(value).__name__


def inspect_authorities():
    contract = load_json(CONTRACT)
    fields = ("membership", "inference_dataset", "model", "visual_input", "scorer", "categories", "category_counts", "scoring_transform", "carrier", "channels", "experiment_tag", "asset_manifest")
    registry = load_json(REGISTRY)
    first = next(iter(registry.values()))
    report = {
        "contract": {**binding(CONTRACT, CONTRACT_SHA), **{key: contract[key] for key in fields}},
        "membership": {**binding(MEMBERSHIP, MEMBERSHIP_SHA), "schema": schema(load_json(MEMBERSHIP))},
        "registry": {**binding(REGISTRY, REGISTRY_SHA), "scene_count": len(registry), "item_schema": schema(first), "sample_indices": first["indices"][:3], "sample_frame_names": first["frame_names"][:3]},
    }
    print(json.dumps(report, indent=2))


def inspect_example(path):
    path = Path(path)
    if not path.is_relative_to(DONOR / "run") or path.parent.parent.name != "finalized":
        raise ValueError("Only a named finalized donor example may be inspected")
    qid = path.parent.name
    report = {}
    for filename in (f"trace_{qid}_clean.json", f"trace_{qid}.json", f"attempt_{qid}.json"):
        data = load_json(path.parent / filename)
        report[filename] = {"top_level_keys": list(data)}
        trace = data.get("trace", {})
        messages = trace.get("messages", []) if isinstance(trace, dict) else trace
        finals = [message for message in messages if message.get("role") == "ai" and not message.get("tool_calls")]
        final = finals[-1] if finals else {}
        content = final.get("content", "")
        text = content if isinstance(content, str) else "\n".join(part.get("text", "") for part in content if part.get("type") == "text")
        report[filename].update({
            "message_count": len(messages), "final_schema": schema(final, 2),
            "final_text_characters": len(text), "prefix_characters": len(re.split(r"<ANSWER>", text, flags=re.I)[0]),
            "tags": sorted(set(re.findall(r"</?([A-Za-z_][A-Za-z_0-9]*)[ >]", text))),
            "final_metadata": final.get("response_metadata"),
            "final_provenance": final.get("provenance"),
            "attempt_status": data.get("status"), "error": bool(data.get("error")),
            "budget_terminal": data.get("budget_terminal"), "episode_terminal": data.get("episode_terminal"),
        })
        if "run_receipt" in data:
            report[filename]["external_data"] = data["run_receipt"].get("external_data")
            report[filename]["effective_contract_sha256"] = data["run_receipt"].get("effective_contract_sha256")
        if "native_google_provider_calls" in data:
            report[filename]["provider_call_schema"] = schema(data["native_google_provider_calls"][-1], 3)
        report[filename]["answer_tool_schemas"] = [
            {"message_index": index, "name": call.get("name"), "argument_schema": schema(call.get("args"), 2)}
            for index, message in enumerate(messages) for call in (message.get("tool_calls") or [])
            if any(word in str(call.get("name", "")).lower() for word in ("answer", "verif", "final"))
        ]
        report[filename]["final_candidates"] = []
        for message in finals:
            parts = message["content"] if isinstance(message["content"], list) else [{"type": "text", "text": message["content"]}]
            report[filename]["final_candidates"].append([
                {"type": part.get("type"), "characters": len(part.get("text", part.get("thinking", ""))), "has_detailed_explanation_heading": bool(re.search(r"detailed[ _]explanation", part.get("text", ""), re.I)), "tags": sorted(set(re.findall(r"</?([A-Za-z_][A-Za-z_0-9]*)[ >]", part.get("text", ""))))}
                for part in parts
            ])
    print(json.dumps(report, indent=2))


def inspect_manifests():
    contract = load_json(CONTRACT)
    paths = {
        "subset": Path(contract["membership"]["sealed_subset_path"]),
        "inference": Path(contract["inference_dataset"]["path"]),
        "assets": DONOR / "package" / contract["asset_manifest"]["path"],
    }
    report = {name: {"path": str(path), "schema": schema(load_json(path), 2)} for name, path in paths.items()}
    subset = load_json(paths["subset"])
    report["subset"]["source_pointers"] = {key: subset[key] for key in ("materialization", "source_join", "alignment_eligibility")}
    report["first_cell_evaluation"] = contract["first_cell_evaluation"]
    report["label_asset_candidates"] = [asset for asset in load_json(paths["assets"])["files"] if re.search(r"(dataset|answerable|vsibench.*json|ground_truth)", asset["path"], re.I)][:8]
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--example")
    parser.add_argument("--manifests", action="store_true")
    parser.add_argument("--audit-pointers", action="store_true")
    args = parser.parse_args()
    if args.example:
        inspect_example(args.example)
    elif args.manifests:
        inspect_manifests()
    elif args.audit_pointers:
        receipt = load_json(load_json(CONTRACT)["first_cell_evaluation"]["path"])
        def pointers(value, prefix=""):
            result = {}
            if isinstance(value, dict):
                for key, item in value.items():
                    result.update(pointers(item, f"{prefix}/{key}"))
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    result.update(pointers(item, f"{prefix}/{index}"))
            elif isinstance(value, str) and value.startswith(("/data2/", "/home/")):
                result[prefix] = value
            return result
        print(json.dumps(pointers(receipt), indent=2))
    else:
        inspect_authorities()
