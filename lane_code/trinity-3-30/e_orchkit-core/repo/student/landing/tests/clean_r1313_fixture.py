import copy
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import av
import numpy as np
from PIL import Image

from student_pilot import clean_conversion as conversion
from student_pilot import clean_source as source
from student_pilot.common import canonical_bytes

EXPLANATION = ("The archived observation places the marker to the left of the reference object in the stated viewing direction. "
               "The recorded comparison uses that same reference direction and identifies the left-side choice without introducing another observation.")


class Fixture:
    def __init__(self, qids=None, frame_scene="toy_scene", wrong_pixels=False, wrong_dimensions=False,
                 source_patch=None, trace_patch=None, acceptance_patch=None, terminal_patch=None,
                 budget=16384, topup_patch=None, initial_patch=None, config_patch=None, scene_patch=None,
                 recovered_provider_error=False):
        self.recovered_provider_error = recovered_provider_error
        self.workspace = Path(os.environ["CLEAN_VSI590K_WORKSPACE"])
        self.root = source.local_path(self.workspace, Path(os.environ["CLEAN_VSI590K_TEST_ROOT"]) / uuid4().hex)
        self.root.mkdir(parents=True)
        self.clean = self.root / source.POOL
        self.run_root = self.root / "inputs/collector"
        self.census = self.root / "inputs/census"
        self.qids = qids or ["vsi590k_000001"]
        self.rows = [{"dataset": "scannetppv2", "id": qid, "option_letters": ["A", "B"], "options": ["left", "right"],
                      "question": "Which listed choice matches the archived observation?", "question_type": "object_rel_direction_medium",
                      "question_video_sha256": "1" * 64, "scene_name": "toy_scene", "source_question_type": "relative_direction_object",
                      "source_row_1based": index + 1, "video": "scannetppv2/toy_scene.mkv"}
                     for index, qid in enumerate(self.qids)]
        if source_patch:
            source_patch(self.rows)
        self.membership = self.root / "inputs/membership.jsonl"
        self.write_bytes(self.membership, b"".join(json.dumps(row, sort_keys=True).encode() + b"\n" for row in self.rows))
        scene = self.make_media(frame_scene, wrong_pixels, wrong_dimensions)
        if scene_patch:
            scene_patch(scene)
        self.scene_pin = self.save(self.root / "inputs/scene_receipt.json", scene)
        registry = self.save(self.root / "inputs/registry.json", {"schema": "r1313-assets-registry-v1", "receipts": [self.scene_pin]})
        contract = self.save(self.root / "inputs/contract.json", {"schema": "r1313-vsi590k-gt-collector-v1", "round": 1313,
                             "arm": "teacher_training_GT", "model": {"requested_id": source.MODEL},
                             "membership": self.pin(self.membership)})
        identity = {"schema": "r1313-run-identity-v1", "agent_id": "offline-source-fixture",
                    "work_id": "offline_source_fixture", "membership_sha256": self.pin(self.membership)["sha256"],
                    "source_contract_sha256": contract["sha256"]}
        self.save(self.run_root / "RUN_IDENTITY.json", identity)
        config = self.save(self.root / "inputs/collection_config.json", {"schema": "r1313-collection-config-v1", "mode": "production",
                           "run_root": str(self.run_root), "budget": 16384, "agent_id": identity["agent_id"],
                           "work_id": identity["work_id"], "source_contract": contract["path"],
                           "source_contract_sha256": contract["sha256"], "assets_registry": registry["path"],
                           "assets_registry_sha256": registry["sha256"]})
        accepted = []
        self.raw_paths, self.topup_paths, self.initial_paths = {}, {}, {}
        for row in self.rows:
            qid = row["id"]
            self.save(self.run_root / "episode_inputs" / (qid + ".json"), row)
            directory = self.run_root / "attempts" / qid / "b16384"
            runtime_row = {**row, "scene_name": row["dataset"] + "__" + row["scene_name"], "source_scene_name": row["scene_name"]}
            receipt = {"schema": "r1313-training-episode-v1", "round": 1313, "fixture_only": False,
                       "input_rows": [runtime_row], "membership_sha256": identity["membership_sha256"],
                       "source_contract": contract, "collection_config": config, "scene_receipt": self.scene_pin,
                       "selected_frames_sha256": self.scene_pin["sha256"], "planner_output_budget_tokens": 16384,
                       "experiment_dir": str(directory), "student_inputs": {"modality": "question_and_RGB_only", "frames": scene["frames"]}}
            thought = self.ai([{ "type": "thinking", "thinking": EXPLANATION}], [{"id": "tool-1", "name": "execute_python_code",
                              "args": {"execution_summary": EXPLANATION}}], "first")
            final = self.ai([{"type": "text", "text": "<ANSWER>A</ANSWER>"}], [], "final")
            raw = {"question_id": qid, "scene_name": runtime_row["scene_name"], "question_type": row["question_type"],
                   "question": row["question"], "run_receipt": receipt, "budget_terminal": False, "error": None,
                   "orphan_tool_drop": False, "pred": "IGNORED_PREDICTION", "trace": [thought,
                   {"role": "tool", "tool_call_id": "tool-1", "content": "The marker is 2 meters from the center and left of the reference."}, final]}
            clean = copy.deepcopy(raw)
            attempt = {"schema": "req73-question-attempt-v4", "status": "completed", "arm": "teacher_training_GT",
                       "requested_model": source.MODEL, "question_id": qid, "planner_output_budget_tokens": 16384,
                       "planner_calls": 2, "provider_attempts": 3 if recovered_provider_error else 2}
            if budget == 32768:
                initial_raw, initial_clean, initial_attempt = copy.deepcopy((raw, clean, attempt))
                for entry in (initial_raw, initial_clean):
                    entry["budget_terminal"] = True
                    message = entry["trace"][-1]
                    for native in (message, message["raw_response"]):
                        native["content"][0]["text"] = "Incomplete capped explanation"
                        native["response_metadata"]["finish_reason"] = "MAX_TOKENS"
                        native["usage_metadata"].update(output_tokens=16384, total_tokens=16394)
                if initial_patch:
                    initial_patch(initial_raw, initial_clean, initial_attempt)
                initial_root = directory / "finalized" / qid
                initial_pin = self.save(initial_root / f"trace_{qid}.json", initial_raw)
                self.initial_paths[qid] = Path(initial_pin["path"])
                self.save(initial_root / f"trace_{qid}_clean.json", initial_clean)
                self.save(initial_root / "attempt.json", initial_attempt)
                self.make_archive(directory, row, initial_raw, scene)
                self.save(self.run_root / "terminals" / (qid + "__b16384.json"),
                          {"question_id": qid, "episode_id": qid + "__b16384", "budget": 16384,
                           "return_code": 0, "output": str(directory), "finished_unix": 1})
                authorization = [{"row": row, "output_budget_tokens": 32768,
                                  "original_trace_path": initial_pin["path"], "original_trace_sha256": initial_pin["sha256"]}]
                if topup_patch:
                    topup_patch(authorization)
                topups = self.save(self.root / "inputs" / (qid + "_TOPUPS.json"), authorization)
                self.topup_paths[qid] = Path(topups["path"])
                config_value = {**source.read_json(self.workspace, config["path"]), "budget": 32768,
                                "topups": topups["path"], "topups_sha256": topups["sha256"]}
                if config_patch:
                    config_patch(config_value)
                selected_config = self.save(self.root / "inputs" / (qid + "_config32k.json"), config_value)
                directory = self.run_root / "attempts" / qid / "b32768"
                for entry in (raw, clean):
                    entry["run_receipt"].update(planner_output_budget_tokens=32768, experiment_dir=str(directory),
                                                collection_config=selected_config)
                attempt["planner_output_budget_tokens"] = 32768
            if trace_patch:
                trace_patch(raw, clean, attempt)
            final_root = directory / "finalized" / qid
            raw_pin = self.save(final_root / f"trace_{qid}.json", raw)
            self.raw_paths[qid] = Path(raw_pin["path"])
            self.save(final_root / f"trace_{qid}_clean.json", clean)
            self.save(final_root / "attempt.json", attempt)
            self.make_archive(directory, row, raw, scene)
            terminal = {"question_id": qid, "episode_id": qid + f"__b{budget}", "budget": budget,
                        "return_code": 0, "output": str(directory), "finished_unix": 1}
            if terminal_patch:
                terminal_patch(terminal)
            self.save(self.run_root / "terminals" / (qid + f"__b{budget}.json"), terminal)
            decision = {"id": qid, "accepted": True, "answer_correct": True, "mechanically_complete": True,
                        "has_perceptual_evidence": True, "perceptual_evidence": [{"tool_call_id": "tool-1", "tool": "execute_python_code"}],
                        "needs_topup": False, "final_cap_failure": False, "chosen_budget": budget,
                        "trace_path": raw_pin["path"], "trace_sha256": raw_pin["sha256"]}
            accepted.append(decision)
        decisions = copy.deepcopy(accepted)
        if acceptance_patch:
            acceptance_patch(accepted, decisions)
        self.save(self.census / "ACCEPTED.json", accepted)
        self.save(self.census / "DECISIONS.json", decisions)
        self.save(self.census / "SUMMARY.json", {"schema": "r1313-collection-census-v1", "candidate_questions": len(self.qids),
                  "distinct_accepted": len(accepted), "distinct_finalized": len(decisions)})
        self.save(self.census / "TOPUPS.json", [])
        self.save(self.census / "PARTIAL_ATTEMPTS.json", [])
        self.telemetry = self.root / "inputs/native_telemetry_fixture.py"
        self.write_bytes(self.telemetry, b"FIXTURE_ONLY = True\n")

    def write_bytes(self, path, value):
        source.local_path(self.workspace, path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(value)
        return self.pin(path)

    def save(self, path, value):
        return self.write_bytes(path, canonical_bytes(value))

    def pin(self, path):
        return source.pin(self.workspace, path)

    def make_media(self, frame_scene, wrong_pixels, wrong_dimensions):
        video_path = self.root / "inputs/media/scannetppv2/toy_scene.mkv"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        generator = np.random.default_rng(17)
        pixels = [generator.integers(0, 256, (12, 16, 3), dtype=np.uint8) for _ in range(32)]
        with av.open(str(video_path), mode="w") as container:
            stream = container.add_stream("ffv1", rate=8)
            stream.width, stream.height, stream.pix_fmt = 16, 12, "bgr0"
            for image in pixels:
                for packet in stream.encode(av.VideoFrame.from_ndarray(image, format="rgb24")):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
        video = {**self.pin(video_path), "decoded_frame_count": 32, "fps": 8.0, "timestamp_basis": "ordinal/fps"}
        frames, alignment = [], []
        for index, image in enumerate(pixels):
            path = self.root / "inputs/scene_assets" / ("scannetppv2__" + frame_scene) / "frames" / f"frame_{index:06d}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            selected = image.copy()
            if wrong_pixels and index == 0:
                selected[0, 0, 0] ^= 1
            Image.fromarray(selected).save(path)
            frame = {**self.pin(path), "ordinal": index, "stem": path.stem, "timestamp_sec": index / 8}
            frames.append(frame)
            dimensions = [17, 12] if wrong_dimensions else [16, 12]
            alignment.append({"slot_1based": index + 1, "ordinal": index, "stem": path.stem, "timestamp_sec": index / 8,
                              "selected_rgb_sha256": frame["sha256"], "selected_png_matches_vsi_decode": True,
                              "vsi_canvas_wh": dimensions, "target_canvas_wh": dimensions, "raw_source_canvas_wh": [16, 12]})
        align_pin = self.save(self.root / "inputs/alignment.json", {"schema": "r1313-official-alignment-v1", "validated_slots": 32,
                              "pose_field": "aligned_pose", "estimated_geometry_used": False, "frames": alignment})
        stems = [frame["stem"] for frame in frames]
        frame_pin = self.save(self.root / "inputs/source_frames.json", {"frames": frames, "video": video, "selected_frames": stems})
        provenance = self.save(self.root / "inputs/source_provenance.json", {"schema": "r1313-source-provenance-v1", "dataset": "scannetppv2",
                               "source_scene_id": "toy_scene", "source_frames_receipt": frame_pin, "raw_sources": {"iphone/rgb.mkv": video}})
        return {"schema": "r1313-scene-assets-v1", "round": 1313, "dataset": "scannetppv2", "scene_name": "toy_scene",
                "runtime_scene_id": "scannetppv2__toy_scene", "frames": frames, "image_count": 32, "selected_frames": stems,
                "video": video, "alignment": align_pin, "source_provenance": provenance}

    @staticmethod
    def ai(content, calls, identity):
        raw = {"content": content, "tool_calls": calls, "invalid_tool_calls": [],
               "response_metadata": {"finish_reason": "STOP", "model_name": source.MODEL},
               "usage_metadata": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}}
        return {"role": "ai", "id": identity, "provenance": "provider", "content": copy.deepcopy(content),
                "tool_calls": copy.deepcopy(calls), "response_metadata": copy.deepcopy(raw["response_metadata"]),
                "usage_metadata": copy.deepcopy(raw["usage_metadata"]), "raw_response": raw}

    def make_archive(self, directory, row, raw, scene):
        root = directory / "archive"
        self.save(root / "identity.json", {"question_id": row["id"], "budget": raw["run_receipt"]["planner_output_budget_tokens"],
                                          "source_question": row, "scene_receipt_path": self.scene_pin["path"]})
        events = [("scene_input", scene)]
        if self.recovered_provider_error:
            events.extend([
                ("provider_request", {"call_id": "failed-call", "method": "generate_content", "kwargs": {"model": source.MODEL}}),
                ("provider_terminal", {"call_id": "failed-call", "status": "error", "type": "ServerError", "message": "503 unavailable"}),
                ("planner_attempt", {"status": "error", "type": "ServerError"}),
            ])
        for index, message in enumerate(m for m in raw["trace"] if m["role"] == "ai"):
            call_id = f"source-call-{index}"
            parts = [{"text": part.get("text", part.get("thinking", "")), "thought": part["type"] == "thinking"}
                     for part in message["content"]]
            sdk = {"model_version": source.MODEL, "usage_metadata": {"prompt_token_count": 10, "candidates_token_count": 20, "total_token_count": 30},
                   "candidates": [{"finish_reason": message["response_metadata"]["finish_reason"], "content": {"parts": parts}}]}
            events.extend([("provider_request", {"call_id": call_id, "method": "generate_content", "kwargs": {"model": source.MODEL}}),
                           ("provider_response", {"call_id": call_id, "response": sdk}),
                           ("provider_terminal", {"call_id": call_id, "status": "ok"}),
                           ("planner_attempt", {"raw_response": message["raw_response"]})])
            if index == 0:
                auxiliary = "auxiliary-stream"
                events.extend([("provider_request", {"call_id": auxiliary, "method": "generate_content_stream", "kwargs": {"model": source.MODEL}}),
                               ("provider_chunk", {"call_id": auxiliary, "response": copy.deepcopy(sdk)}),
                               ("provider_terminal", {"call_id": auxiliary, "status": "ok"})])
        journal = []
        for index, (kind, payload) in enumerate(events, 1):
            relative = f"events/{index:08d}_{kind}.json"
            self.save(root / relative, {"id": index, "kind": kind, "payload": payload, "time_ns": index})
            journal.append({"id": index, "kind": kind, "path": relative})
        self.write_bytes(root / "journal.jsonl", b"".join(json.dumps(row).encode() + b"\n" for row in journal))
        self.write_bytes(root / "artifact_refs.jsonl", b"")

    def freeze(self, allow_missing=False, membership=True):
        return source.freeze(self.workspace, self.run_root, self.census, self.clean / "snapshot",
                             self.membership if membership else None, allow_missing=allow_missing)

    def prepare(self, count=None, dry_run=False):
        snapshot = self.freeze()
        return conversion.prepare(self.workspace, snapshot["path"], self.clean / "job", count,
                                  dry_run=dry_run, telemetry_path=self.telemetry)

    def lease(self, job):
        now = datetime.now(timezone.utc)
        status = self.save(self.clean / "leases/supervisor.json", {"offline_fixture": True, "workers": 1})
        lease = {"schema": conversion.LEASE_SCHEMA, "source_pool": source.POOL, "job": job,
                 "coordination_lease_passed": True, "collector_handshake_passed": True, "no_other_paid_calls": True,
                 "annotation_workers": 1, "concurrency_cap": 1, "max_calls": len(source.read_json(self.workspace, job["path"])["selected_qids"]),
                 "model": source.MODEL, "work_id": "clean_vsi590k__offline_fixture", "owner": "fixture-annotator",
                 "coordination_lease_evidence": "synthetic offline fixture; no real lease or calls",
                 "collector_handshake_evidence": "synthetic offline fixture", "supervisor_status": status,
                 "admitted_at": now.isoformat(), "expires_at": (now + timedelta(hours=1)).isoformat()}
        return self.save(self.clean / "leases/api.json", lease)

    def review(self, run_directory, qids=None, supported=True, independent=True):
        bundle = source.read_json(self.workspace, run_directory / "review_bundle.json")
        review = bundle["review_template"]
        review.update(reviewer="independent-offline-fixture", independent_of_converter=independent)
        if qids is not None:
            review["decisions"] = [r for r in review["decisions"] if r["qid"] in qids]
        for row in review["decisions"]:
            row["verdict"] = "accept"
            row["checks"] = {key: True for key in conversion.conversion.REVIEW_CHECKS}
            row["claim_verdicts"] = [{**claim, "supported": supported} for claim in row["claim_verdicts"]]
        return self.save(self.clean / "reviews" / (uuid4().hex + ".json"), review)


def document(payload):
    evidence = next(e for e in payload["evidence"] if e["kind"] == "provider_thought_summary")
    sentences = EXPLANATION.split(". ")
    paragraphs = []
    for index, purpose in enumerate(("setup", "observations", "derivation", "conclusion")):
        text = sentences[index % len(sentences)]
        if not text.endswith("."):
            text += "."
        paragraphs.append({"purpose": purpose, "claims": [{"text": text,
            "citations": [{"evidence_id": evidence["id"], "quote": text}]}]})
    return {"status": "converted", "explanation": paragraphs,
            "answer": conversion.conversion.answer_body(payload["native_final_provenance"])}


def response_for(request):
    payload = json.loads(request["contents"][0]["parts"][0]["text"])
    content = json.dumps(document(payload))
    thoughts = "This is synthetic retained annotation telemetry."
    usage = {"prompt_token_count": 20, "candidates_token_count": 50, "total_token_count": 70}
    native = {"model_version": source.MODEL, "usage_metadata": usage, "candidates": [{"finish_reason": "STOP", "content": {
              "parts": [{"text": thoughts, "thought": True}, {"text": content}]}}]}
    identity = {"call_id": "synthetic-" + uuid4().hex, "where": "student_grounded_conversion", "model": source.MODEL, "output_budget_tokens": request["config"]["max_output_tokens"]}
    row = {**identity, "event": "native_google_call_terminal_v1", "model_role": "annotation", "provider": "google",
           "content": content, "thoughts": thoughts, "finish_reason": "STOP", "usage": usage,
           "provider_served_model": source.MODEL, "raw_response": [native], "native_candidates": native["candidates"],
           "status": "ok", "tool_budget_terminal": False}
    return {**row, "events": [{**identity, "event": "native_google_call_start_v1"}, copy.deepcopy(row)], "sdk_version": "offline-fixture"}
