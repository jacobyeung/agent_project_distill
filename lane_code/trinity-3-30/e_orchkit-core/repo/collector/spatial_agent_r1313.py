"""r1313 native Gemini SPLIT training carrier with fixed authenticated GT perception."""

package_version = "r1313_vsi_distill_gt_training_v1"

import os
import json
import hashlib
import numpy as np
import re
import re as _re
import math
import sys
import io
import multiprocessing
import threading
import time
import contextlib
import contextvars
import uuid
import native_google_telemetry as native_google
from training_assets import custody_effect, custody_stream
import training_policy as reference_policy
from nondeleting_lifecycle import retire_path
from pathlib import Path
from typing import TypedDict, Annotated, Sequence
from PIL import Image

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

from training_assets import require_r2_store

# ─────────────────────────────────────────────────────────────────────────────
# NVIDIA/OpenAI-compatible planner setup.
#   Planner / verifier        -> NVIDIA Inference API, default Opus 4.8
#   Tool-internal VLM grounds -> Google-native Gemini flash, unchanged from r205
# ─────────────────────────────────────────────────────────────────────────────
from google import genai as _genai
from google.genai import types as _gtypes
from openai import OpenAI as _OAI

TOOL_VLM_MODEL = os.environ.get("TOOL_VLM_MODEL", "gemini-3.5-flash")
PLANNER_OUTPUT_BUDGET_LADDER = (16384, 32768)
PLANNER_MAX_OUTPUT_TOKENS = int(os.environ.get("REQ73_PLANNER_OUTPUT_BUDGET", "16384"))
if PLANNER_MAX_OUTPUT_TOKENS not in PLANNER_OUTPUT_BUDGET_LADDER:
    raise RuntimeError("r1313 planner output budget must be 16384 or the authorized 32768 top-up")
if os.environ.get("GP_NATIVE") != "1":
    raise RuntimeError("r1044 requires the reviewed Google-native planner transport")

_GP_NATIVE_MODEL = "gemini-3.1-pro-preview"


def _gp_native() -> bool:
    return os.environ.get("GP_NATIVE", "0") == "1"


def _planner_model() -> str:
    # The GP-native branch must not inspect NVIDIA-only configuration.
    if _gp_native():
        return _GP_NATIVE_MODEL
    return os.environ.get("NV_PLANNER_MODEL", "azure/anthropic/claude-opus-4-8")


def _verifier_model() -> str:
    if _gp_native():
        return _GP_NATIVE_MODEL
    return os.environ.get("NV_VERIFIER_MODEL", _planner_model())


def _nvidia_transport_config() -> tuple[str, str, bool]:
    return (
        os.environ.get("NV_INFERENCE_BASE_URL", "https://inference-api.nvidia.com"),
        os.environ.get("NV_INFERENCE_DATA_CLASSIFICATION", "sensitive"),
        os.environ.get("NV_CACHE_CONTROL", "0") == "1",
    )

_NV_CLIENT_SINGLETON = None


def _omit_temperature_for_model(model: str) -> bool:
    low = model.lower()
    return "gpt-5" in low or "/anthropic/claude-" in low


_PERMANENT_CLASSES = {"BadRequestError", "InvalidRequestError", "UnprocessableEntityError",
                      "NotFoundError", "PermissionDeniedError", "AuthenticationError",
                      "ConflictError", "JSONDecodeError", "OutputParserException",
                      "APIResponseValidationError", "ValidationError"}
_TRANSIENT_CLASSES = {"APIConnectionError", "APITimeoutError", "APIConnectionTimeoutError",
                      "ConnectionError", "ConnectTimeout", "ReadTimeout", "Timeout", "TimeoutError",
                      "RateLimitError", "InternalServerError", "ServiceUnavailableError",
                      "ConnectError", "TimeoutException", "PoolTimeout", "WriteTimeout",
                      "ReadError", "WriteError", "CloseError", "NetworkError",
                      "RemoteProtocolError"}
try:
    import httpx as _httpx
    _HTTPX_TRANSIENT = (_httpx.TimeoutException, _httpx.NetworkError, _httpx.RemoteProtocolError)
except Exception:
    _HTTPX_TRANSIENT = ()

_PERMANENT_SIGNATURES = (
    "bad request", "invalid request", "invalid_request",
    "context length", "context window", "maximum context", "context_length_exceeded",
    "tool call parser", "tool-call parser", "qwen3_xml",
    "parse error", "parse failed", "parser failure", "parser error", "json parse",
    "jsondecode", "unterminated string", "extra data", "expecting value",
    "expecting ',' delimiter", "malformed", "validation error", "validation failed",
    "unprocessable", "not found", "permission denied", "unauthorized", "authentication",
)


def _extract_http_status(exc: BaseException):
    for attr in ("status_code", "code", "http_status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    value = getattr(getattr(exc, "response", None), "status_code", None)
    return value if isinstance(value, int) else None


def _exc_class_names(exc: BaseException) -> set:
    return {cls.__name__ for cls in type(exc).__mro__}


def _error_text_bucket(text: str) -> str:
    """Classify an API error as permanent, transient, or unknown; permanent wins."""
    low = text.lower()
    if any(signature in low for signature in _PERMANENT_SIGNATURES):
        return "permanent"
    if (_re.search(r"error code[:\s]+4(?!29)\d\d\b", low)
            or _re.search(r"\bstatus[:\s]+4(?!29)\d\d\b", low)
            or _re.search(r"\bhttp[:\s]+4(?!29)\d\d\b", low)
            or _re.fullmatch(r"\s*4(?!29)\d\d\s*", low)):
        return "permanent"
    if (_re.search(r"\b429\b", text) or "rate limit" in low
            or "too many requests" in low or "resource_exhausted" in low
            or "resource exhausted" in low):
        return "transient"
    if any(signature in low for signature in (
            "connection error", "connection reset", "connection aborted",
            "connection refused", "all connection attempts failed", "server disconnected")):
        return "transient"
    if "timed out" in low or "overloaded" in low or _re.search(r"\b529\b", text):
        return "transient"
    if any(signature in low for signature in (
            "service unavailable", "internal server error", "bad gateway", "gateway timeout")):
        return "transient"
    if (_re.search(r"error code[:\s]+5\d\d\b", low)
            or _re.search(r"\bstatus[:\s]+5\d\d\b", low)
            or _re.search(r"\bhttp[:\s]+5\d\d\b", low)):
        return "transient"
    return "unknown"


def _is_transient_api_error(exc: BaseException) -> bool:
    """Strict transient allowlist; unknown and permanent failures do not retry."""
    names = _exc_class_names(exc)
    text = str(exc)
    if names & _PERMANENT_CLASSES:
        return False
    bucket = _error_text_bucket(text)
    if bucket == "permanent":
        return False
    status = _extract_http_status(exc)
    if status is not None:
        if status == 429 or 500 <= status <= 599:
            return True
        if 400 <= status <= 499:
            return False
    if names & _TRANSIENT_CLASSES:
        return True
    if _HTTPX_TRANSIENT and isinstance(exc, _HTTPX_TRANSIENT):
        return True
    return bucket == "transient"


def _is_rate_limit_429(exc: BaseException) -> bool:
    status = _extract_http_status(exc)
    if status is not None:
        return status == 429
    if "RateLimitError" in _exc_class_names(exc):
        return True
    low = str(exc).lower()
    return (bool(_re.search(r"\b429\b", str(exc))) or "rate limit" in low
            or "too many requests" in low or "resource_exhausted" in low
            or "resource exhausted" in low)


def _transient_max_attempts(exc: BaseException, base_max: int) -> int:
    return base_max


def _transient_api_backoff_seconds(exc: BaseException, attempt: int) -> float:
    import random
    if _is_rate_limit_429(exc):
        return min(5.0 * (2 ** attempt) + random.uniform(0.0, 5.0), 120.0)
    return min(2.0 * (2 ** attempt) + random.uniform(0.0, 2.0), 60.0)


def _require_nvidia_api_key() -> str:
    api_key = os.environ.get("NV_INFERENCE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "NV_INFERENCE_API_KEY is required only for the NVIDIA transport")
    return api_key


def _nvidia_client() -> _OAI:
    global _NV_CLIENT_SINGLETON
    if _NV_CLIENT_SINGLETON is None:
        base_url, data_classification, _ = _nvidia_transport_config()
        _NV_CLIENT_SINGLETON = _OAI(
            api_key=_require_nvidia_api_key(),
            base_url=base_url,
            default_headers={"dataClassification": data_classification},
        )
    return _NV_CLIENT_SINGLETON


def _google_client() -> "_genai.Client":
    return _genai.Client(
        api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
        http_options={"api_version": "v1alpha"},
    )


def _json_safe(value):
    """Return a lossless JSON-safe provider payload, including binary signatures."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        import base64
        return {"encoding": "base64", "data": base64.b64encode(value).decode("ascii")}
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        try:
            return _json_safe(model_dump(mode="json", exclude_none=False))
        except TypeError:
            return _json_safe(model_dump(exclude_none=False))
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, (str, int, float, bool)):
        return enum_value
    return str(value)


_GEMINI_SIGNATURE_FIELD = "__gemini_function_call_thought_signatures__"


def _langchain_raw_response(message) -> dict:
    """Serialize every LangChain response field that can carry provider output."""
    dumped = _json_safe(message)
    if not isinstance(dumped, dict):
        dumped = {"value": dumped}
    # ChatGoogleGenerativeAI stores function-call thought signatures in
    # additional_kwargs[_GEMINI_SIGNATURE_FIELD]. Keeping the complete AIMessage
    # both persists those bytes and passes them back unchanged in graph history.
    return dumped


def _google_multimodal(
    parts: list,
    model: str = TOOL_VLM_MODEL,
    temperature: float = 0.0,
    thinking_level: str | None = None,
    max_output_tokens: int = 4096,
    usage_sink: list | None = None,
) -> str:
    """
    Send a mixed text/image message to the Google GenAI API and return the text.

    `parts` is a list of (kind, payload) tuples:
        ("text",  str)   — text block
        ("image", bytes) — raw JPEG/PNG bytes

    r550: when `usage_sink` (the per-question llm_usage_list) is provided, appends one
    {"where","model","input_tokens","output_tokens","total_tokens","elapsed_ms"} entry
    per API call (best-effort; never raises).
    """
    # r208: any slash-containing model id routes through the NVIDIA
    # OpenAI-compatible endpoint (NVIDIA ids are always provider/vendor/name;
    # Google-native ids never contain '/'). Lets TOOL_VLM_MODEL sweep NVIDIA
    # VLMs (e.g. gcp/google/gemini-3.5-flash, openai/openai/gpt-5.5) without
    # touching the planner wiring.
    # GP_NATIVE (2026-06-10): planner on the GOOGLE key via the NATIVE genai/langchain
    # client. The Google OpenAI-compat endpoint 400s on multi-turn function calling
    # ("Function call is missing a thought_signature") because ChatOpenAI does not
    # round-trip Gemini-3 thought signatures; the native client handles them.
    if "/" in model or (not _gp_native() and model in {_planner_model(), _verifier_model()}):
        import base64

        _, _, use_nv_cache_control = _nvidia_transport_config()

        content = []
        for kind, payload in parts:
            if kind == "text":
                block = {"type": "text", "text": payload}
                if use_nv_cache_control:
                    block["cache_control"] = {"type": "ephemeral"}
                content.append(block)
            elif kind == "image":
                b64 = base64.b64encode(payload).decode("utf-8")
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                })

        kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max_output_tokens,
        }
        if not _omit_temperature_for_model(model):
            kwargs["temperature"] = temperature
        max_attempts = max(1, int(os.environ.get("NV_RETRY_ATTEMPTS", "3")))
        for attempt in range(max_attempts):
            try:
                _t0 = time.time()
                resp = _nvidia_client().chat.completions.create(**kwargs)
                _record_llm_usage(
                    usage_sink, "_google_multimodal", model,
                    getattr(resp, "usage", None), _t0,
                    model_version=getattr(resp, "model", None),
                )
                return (resp.choices[0].message.content or "") if resp.choices else ""
            except Exception as e:
                if _is_transient_api_error(e) and attempt + 1 < _transient_max_attempts(e, max_attempts):
                    time.sleep(_transient_api_backoff_seconds(e, attempt))
                    continue
                import sys as _sys
                print(f"[_google_multimodal/NVIDIA] EXCEPTION: {type(e).__name__}: {e}",
                      file=_sys.stderr, flush=True)
                raise

    gparts = []
    for kind, payload in parts:
        if kind == "text":
            gparts.append(_gtypes.Part.from_text(text=payload))
        elif kind == "image":
            gparts.append(_gtypes.Part.from_bytes(data=payload, mime_type="image/jpeg"))
    gen_config_kwargs = {"temperature": temperature, "max_output_tokens": max_output_tokens}
    if thinking_level is not None:
        # API-native camelCase spelling.
        gen_config_kwargs["thinking_config"] = _gtypes.ThinkingConfig(
            thinkingLevel=thinking_level,
            includeThoughts=True,
        )
    client = _google_client()
    max_attempts = max(1, int(os.environ.get("NV_RETRY_ATTEMPTS", "3")))
    for attempt in range(max_attempts):
        text = ""
        _t0 = time.time()
        _last_usage_meta = None
        _last_model_version = None
        _last_finish_reason = None
        _raw_responses = []
        try:
            for resp in custody_stream(native_google.generate_content_stream, client,
                sink=usage_sink, where="_google_multimodal",
                model_role="tool_vlm" if model == TOOL_VLM_MODEL else "verifier",
                model=model,
                contents=[_gtypes.Content(role="user", parts=gparts)],
                config=_gtypes.GenerateContentConfig(**gen_config_kwargs),
            ):
                _raw_responses.append(_json_safe(resp))
                _um = getattr(resp, "usage_metadata", None)
                if _um is not None:
                    _last_usage_meta = _um
                _mv = getattr(resp, "model_version", None)
                if _mv:
                    _last_model_version = _mv
                if not resp.candidates:
                    continue
                _last_finish_reason = getattr(resp.candidates[0], "finish_reason", None)
                for part in resp.candidates[0].content.parts:
                    if getattr(part, "thought", False):
                        continue
                    if part.text:
                        text += part.text
            _record_llm_usage(
                usage_sink, "_google_multimodal", model, _last_usage_meta, _t0,
                model_version=_last_model_version,
                finish_reason=_last_finish_reason,
                raw_response=_raw_responses,
            )
            return text
        except Exception as e:
            _record_llm_usage(usage_sink, "_google_multimodal", model, _last_usage_meta, _t0,
                model_version=_last_model_version, finish_reason=_last_finish_reason, raw_response=_raw_responses)
            if _is_transient_api_error(e) and attempt + 1 < _transient_max_attempts(e, max_attempts):
                time.sleep(_transient_api_backoff_seconds(e, attempt))
                continue
            raise


def _record_llm_usage(usage_sink, where, model, usage_meta, t0, model_version=None,
                      finish_reason=None, raw_response=None):
    """r550 COST TELEMETRY helper (r560: + served model_version): append one per-call usage
    entry to the per-question llm_usage_list. Best-effort — never raises, never alters
    planner-visible output."""
    try:
        if usage_sink is None:
            return
        entry = {"where": where, "model": str(model),
                 "elapsed_ms": int((time.time() - t0) * 1000)}
        entry["model_role"] = (
            "tool_vlm" if str(model) == str(TOOL_VLM_MODEL) else "verifier"
        )
        entry["provider_served_model"] = (
            str(model_version) if model_version else None
        )
        entry["finish_reason"] = _json_safe(finish_reason)
        entry["raw_response"] = _json_safe(raw_response)
        if usage_meta is not None:
            entry["input_tokens"]  = int(getattr(usage_meta, "prompt_token_count", 0) or 0)
            entry["output_tokens"] = int(getattr(usage_meta, "candidates_token_count", 0) or 0)
            entry["total_tokens"]  = int(getattr(usage_meta, "total_token_count", 0) or 0)
            _tt = getattr(usage_meta, "thoughts_token_count", 0)
            if _tt:
                entry["thoughts_tokens"] = int(_tt)
        usage_sink.append(entry)
    except Exception:
        pass


def _usage_sink_from_config(config) -> list | None:
    """r550: fetch the per-question llm_usage_list threaded through RunnableConfig."""
    try:
        return config.get("configurable", {}).get("llm_usage_list") if config is not None else None
    except Exception:
        return None

def _message_to_dict(message):
    if isinstance(message, dict): return message
    content = getattr(message, "content", None)
    if isinstance(content, list):
        pass
    elif content is None:
        content = ""
    out = {
        "role": getattr(message, "type", None) or getattr(message, "role", None),
        "content": content,
        "name": getattr(message, "name", None),
        "tool_calls": getattr(message, "tool_calls", None) if hasattr(message, "tool_calls") else None,
        "id": getattr(message, "id", None),
        "tool_call_id": getattr(message, "tool_call_id", None)
    }
    if isinstance(message, AIMessage):
        out["raw_response"] = _langchain_raw_response(message)
    try:
        artifact = getattr(message, "artifact", None)
        if artifact is not None:
            out["artifact"] = artifact
    except Exception:
        pass
    try:
        metadata = getattr(message, "response_metadata", None) or {}
        out["response_metadata"] = _json_safe(metadata)
        served = {
            key: metadata[key]
            for key in ("model_name", "model_version", "model")
            if metadata.get(key)
        }
        if served:
            out["served_model"] = served
    except Exception:
        pass
    try:
        usage = getattr(message, "usage_metadata", None)
        out["usage_metadata"] = _json_safe(usage)
        if isinstance(usage, dict):
            normalized = {
                key: int(usage.get(key, 0) or 0)
                for key in ("input_tokens", "output_tokens", "total_tokens")
            }
            if any(normalized.values()):
                out["llm_usage"] = normalized
    except Exception:
        pass
    return out

_RUN_OUTPUT_ROOT = os.environ.get("REQ73_RUN_OUTPUT_ROOT", "")
if (not os.path.isabs(_RUN_OUTPUT_ROOT)
        or not _RUN_OUTPUT_ROOT.startswith("/data2/jjyeung/agent_project_data/")):
    raise RuntimeError("REQ73_RUN_OUTPUT_ROOT must be the sealed arm-scoped /data2 directory")
BASE_DIR = os.path.join(_RUN_OUTPUT_ROOT, "runtime", "gt_cache")

# Raw MapAnything dense outputs (ex_31 showed raw > ransac on orientation/route
# tasks; we stick with raw here for most tools).
# r50: switched to mapanything_dense_373_32_outputs — 32-frame slice of a
# 373-frame full-video MapAnything pass. Sentinel
# `/home/jjyeung/agent_project/map-anything/mapanything_dense_373_32_outputs/
# done.txt` dropped 2026-05-01. Same .npz schema (pts3d_world, depth_z,
# intrinsics, conf, mask, camera_poses, indices), same 32 video frame indices
# per scene as the legacy 32_32 baseline. Pose accuracy improved: rotation
# 23.51° → 23.09°, translation 0.254 m → 0.210 m (-17 %). 512/512 scenes
# pre-staged.
DENSE_DIR = "/home/jjyeung/agent_project/map-anything/mapanything_dense_373_32_outputs"
# Gravity-aligned (RANSAC) dense outputs — exposed to the agent's
# execute_python_code sandbox via `load_ransac_dense(scene_id)` so the agent
# can write its own floor / vertical-axis logic. Raw outputs leave tilted
# floors that break floor-z slicing, so any code that filters by world-Z
# should prefer the RANSAC variant.
# r46: directory renamed to `_32_32` to make the legacy 32-frame provenance
# explicit. The new 373-frame ransac counterpart will land at
# `mapanything_ransac_dense_373_32_outputs/` once that extraction completes.
RANSAC_DIR = "/home/jjyeung/agent_project/map-anything/mapanything_ransac_dense_outputs"
POINT_CLOUD_DEFAULT_SOURCE = "g3t_scaled"
_LAB_BACKBONES = "/lab_data/tarrlab/jacoby/agent_project/dense_backbones"
G3T_UNIK3D_SCALED_DENSE_DIR = str(require_r2_store())
_POINT_CLOUD_SOURCES = {
    "mapanything": {
        "dense_dir": DENSE_DIR,
        "ransac_dir": RANSAC_DIR,
        "summary": ("stable multi-view alternative with the most-tested camera "
                    "trajectory and broad tool support, but weaker metric scale"),
    },
    "unik3d": {
        "dense_dir": "/home/jjyeung/agent_project/map-anything/unik3d_dense_outputs",
        "ransac_dir": None,
        "summary": ("metric depth-oriented cloud; useful when absolute scale/depth "
                    "is the main uncertainty, but less vetted for multi-view layout"),
    },
    "g3t_scaled": {
        "dense_dir": G3T_UNIK3D_SCALED_DENSE_DIR,
        "ransac_dir": None,
        "summary": ("default for every question; gravity/structure-oriented "
                    "metric cloud scaled by a per-scene UniK3D depth scalar, "
                    "useful for floor/layout and scale-sensitive measurements"),
    },
    # r311: extra backbones for the category-agnostic backbone study. These are
    # selected ONLY via FORCE_PC_SOURCE (the planner is never told about them and
    # cannot request them by name in normal operation). Each is a self-gravity-
    # aligned drop-in (dense_dir == ransac_dir).
    "gtpose": {
        "dense_dir": f"{_LAB_BACKBONES}/gtpose_dense_outputs",
        "ransac_dir": f"{_LAB_BACKBONES}/gtpose_dense_outputs",
        "summary": ("DIAGNOSTIC ONLY (GT camera poses + MapAnything depth); never a "
                    "deployed/headline backbone"),
    },
    "g3t_scaled_112": {
        "dense_dir": f"{_LAB_BACKBONES}/g3t_scaled_112_con_dense_outputs",
        "ransac_dir": f"{_LAB_BACKBONES}/g3t_scaled_112_con_dense_outputs",
        "summary": ("G3T structure (112-frame context) + per-scene metric scale; "
                    "high-frame coverage variant of g3t_scaled"),
    },
}

# r311: HARD-FORCED uniform point-cloud source for the category-agnostic backbone
# study + the clean headline. When FORCE_PC_SOURCE is set, EVERY point-cloud
# request (load_dense / load_ransac_dense / predict_2d_points / get_3d_points_*
# / etc.) is remapped to this one source, REGARDLESS of any planner-supplied
# `point_cloud_source` argument. This neutralizes the multi-source planner so a
# run measures exactly one backbone uniformly. The forced key is validated at
# import time. Selection is geometry/agnostic at the experiment level (one source
# per run), never keyed on the benchmark question category.
_FORCE_PC_SOURCE = (os.environ.get("FORCE_PC_SOURCE", "") or "").strip().lower() or None
_force_audit_logged = False


def _point_cloud_source_key(point_cloud_source: str | None = None) -> str:
    global _force_audit_logged
    aliases = {
        "default": POINT_CLOUD_DEFAULT_SOURCE,
        "ma": "mapanything",
        "map_anything": "mapanything",
        "unik": "unik3d",
        "uni_k3d": "unik3d",
        "g3t": "g3t_scaled",
    }
    # HARD FORCE: ignore the planner's choice entirely when FORCE_PC_SOURCE is set.
    if _FORCE_PC_SOURCE is not None:
        forced = aliases.get(_FORCE_PC_SOURCE, _FORCE_PC_SOURCE)
        if forced not in _POINT_CLOUD_SOURCES:
            valid = ", ".join(sorted(_POINT_CLOUD_SOURCES))
            raise ValueError(f"FORCE_PC_SOURCE={_FORCE_PC_SOURCE!r} invalid; valid: {valid}")
        if not _force_audit_logged:
            print(f"[r311 FORCE_PC_SOURCE] all point-cloud requests remapped to "
                  f"'{forced}' (planner requests ignored)", flush=True)
            _force_audit_logged = True
        return forced
    key = (point_cloud_source or POINT_CLOUD_DEFAULT_SOURCE).strip().lower()
    key = aliases.get(key, key)
    if key not in _POINT_CLOUD_SOURCES:
        valid = ", ".join(sorted(_POINT_CLOUD_SOURCES))
        raise ValueError(f"unknown point_cloud_source={point_cloud_source!r}; valid: {valid}")
    return key


def _point_cloud_source_text() -> str:
    return "; ".join(
        f"{name}: {spec['summary']}"
        for name, spec in _POINT_CLOUD_SOURCES.items()
    )
# r108: CuTR per-scene 3D-bbox catalogue (class-agnostic, score≥0.3, no NMS).
# See cutr.md for schema. Used by `query_3d_bbox_catalogue` (offline lookup) and
# `count_object_instances_via_masks_and_3d_iou` (paired with SAM 3 masks).
CUTR_DIR = "/home/jjyeung/agent_project/map-anything/cutr_dense_373_32_outputs"
# r108: subprocess pattern for SAM 3 (see sam3.md). The service runs in a
# dedicated env with Python 3.12 + torch 2.10; the agent's mapanything env
# cannot import sam3 directly.
SAM3_PYTHON  = "/user_data/jjyeung/miniforge3/envs/sam3/bin/python"
SAM3_SERVICE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sam3_service.py")
SAM3_DEFAULT_DEVICE = "cuda:1"   # GPU 1 currently has SAM3 cached weights
SAM3_TMP_ROOT = os.path.join(_RUN_OUTPUT_ROOT, "runtime", "sam3_masks")


def _path_is_within(path: str | Path, root: str | Path) -> bool:
    try:
        Path(path).resolve(strict=False).relative_to(Path(root).resolve(strict=False))
        return True
    except (OSError, ValueError):
        return False


def _sam3_mask_dir(scene_id: str, label: str, request_key: str) -> str:
    """Return a traversal-safe, request-local mask directory under this arm."""
    def component(value: str) -> str:
        raw = str(value)
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", raw).strip("_")[:48] or "value"
        return f"{safe}_{hashlib.sha256(raw.encode()).hexdigest()[:12]}"

    target = Path(SAM3_TMP_ROOT) / (
        f"{component(scene_id)}_{component(request_key)}_{component(label)}"
    )
    target.mkdir(parents=True, exist_ok=True)
    resolved = target.resolve(strict=False)
    if not _path_is_within(resolved, _RUN_OUTPUT_ROOT):
        raise RuntimeError(f"SAM3 mask directory escapes sealed arm root: {resolved}")
    return str(resolved)


def _require_arm_mask_dir(mask_dir: str) -> str:
    if not mask_dir:
        raise RuntimeError("SAM3 mask_dir is required")
    resolved = Path(mask_dir).resolve(strict=False)
    if not _path_is_within(resolved, SAM3_TMP_ROOT):
        raise RuntimeError(f"SAM3 mask_dir is outside the arm mask root: {resolved}")
    resolved.mkdir(parents=True, exist_ok=True)
    return str(resolved)


def _confine_sam3_mask_handle(mask_handle: str, mask_dir: str, field: str) -> str:
    """Keep in-arm handles; safely re-materialize any router/daemon cache escape."""
    source = Path(mask_handle).resolve(strict=False)
    if _path_is_within(source, _RUN_OUTPUT_ROOT):
        if not source.is_file():
            raise RuntimeError(f"SAM3 {field} is missing inside arm root: {source}")
        return str(source)
    if not source.is_file():
        raise RuntimeError(f"SAM3 rejected missing off-root {field}: {source}")
    mask = np.load(source, allow_pickle=False)
    if not isinstance(mask, np.ndarray) or mask.ndim != 2 or mask.dtype != np.bool_:
        raise RuntimeError(f"SAM3 rejected invalid off-root {field}: {source}")
    destination_dir = Path(_require_arm_mask_dir(mask_dir))
    stem = re.sub(r"[^A-Za-z0-9_-]", "_", source.stem)[:48] or "mask"
    digest = hashlib.sha256(str(source).encode()).hexdigest()[:12]
    destination = destination_dir / f"rehome_{field}_{stem}_{digest}.npy"
    temporary = destination_dir / f".{destination.name}.{uuid.uuid4().hex}.tmp.npy"
    try:
        np.save(temporary, mask, allow_pickle=False)
        if destination.exists():
            retire_path(destination)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            retire_path(temporary)
    if not _path_is_within(destination, _RUN_OUTPUT_ROOT):
        raise RuntimeError(f"SAM3 re-materialized {field} outside arm root")
    return str(destination.resolve(strict=False))


def _confine_sam3_instances(instances: list, mask_dir: str) -> list:
    for instance in instances:
        if not isinstance(instance, dict):
            continue
        for field in ("mask_handle", "mask_dense_handle"):
            handle = instance.get(field)
            if handle:
                instance[field] = _confine_sam3_mask_handle(handle, mask_dir, field)
    return instances


def _confine_sam3_payload(payload: dict, mask_dir: str, video: bool = False) -> dict:
    if not isinstance(payload, dict) or "error" in payload:
        return payload
    if video:
        for instances in (payload.get("frames", {}) or {}).values():
            _confine_sam3_instances(instances, mask_dir)
    else:
        _confine_sam3_instances(payload.get("instances", []) or [], mask_dir)
    return payload

CONFIG = {
    "use_gemini": True,
    "use_hints": True,
    "use_python_code": True,
}

_FRAMES_CACHE = None
_CACHE_LOCK = threading.Lock()

# r48: cache the all-prompt VLM response per (scene_id, object_label) so the
# internal "1"-branch all-prompt and any later "all" call see the same frame
# list.
_FRAMES_VLM_CACHE: dict = {}     # (scene_id, object_label) -> list[int]
_FRAMES_VLM_LOCK = threading.Lock()

# r54: deterministic cache for predict_2d_points. Cache key:
# (scene_id, frame_index, query). Value: parsed list returned by the tool.
# The same intra-process call reuses the parsed result.
_POINTS_VLM_CACHE: dict = {}     # (scene_id, frame_index, query) -> list[dict]
_POINTS_VLM_LOCK = threading.Lock()

_DENSE_CACHE: dict = {}  # (point_cloud_source, scene_id) -> loaded npz dict
_DENSE_LOCK = threading.Lock()

# r156: G3T-metric per-scene rescale (see _load_dense). r306 keeps legacy
# launcher-wide scale envs disabled by default because point-cloud selection is
# now an explicit tool argument; category/env pre-routing would violate the
# "same default backend for every question" policy. Set
# R306_ALLOW_LEGACY_SCALE_ENVS=1 only for a debug reproduction, not for fair eval.
_ALLOW_LEGACY_SCALE_ENVS = os.environ.get("R306_ALLOW_LEGACY_SCALE_ENVS", "0") == "1"
_G3T_METRIC = os.environ.get("G3T_METRIC") == "1"
_G3T_SCALE_CACHE: dict | None = None
_G3T_SCALE_MEDIAN: float | None = None

def _g3t_scale() -> dict:
    global _G3T_SCALE_CACHE, _G3T_SCALE_MEDIAN
    if _G3T_SCALE_CACHE is None:
        path = os.environ.get("G3T_SCALE_JSON",
                              os.path.join(os.path.dirname(os.path.abspath(__file__)), "g3t_metric_scale.json"))
        try:
            import json as _json
            _G3T_SCALE_CACHE = _json.load(open(path))
        except Exception:
            _G3T_SCALE_CACHE = {}
        vals = [v for v in _G3T_SCALE_CACHE.values() if isinstance(v, (int, float)) and v > 0]
        _G3T_SCALE_MEDIAN = float(np.median(vals)) if vals else 1.0
    return _G3T_SCALE_CACHE
def _g3t_scale_median() -> float:
    if _G3T_SCALE_MEDIAN is None:
        _g3t_scale()
    return _G3T_SCALE_MEDIAN or 1.0

# r218: honest per-scene scale correction (env SCALE_CORRECTION_JSON=<path>).
# Stage-0 screen winner ref_moge2 (2026-06-11): scalar = median(MoGe-2 depth) /
# median(backbone depth) per scene — predicted depth only, no GT, no VLM,
# question-agnostic. Set on abs/room launches only (size excluded: applying it
# there cancels against grounding under-measurement). Launches
_SCALE_CORR_CACHE: dict | None = None
def _scale_correction() -> dict:
    global _SCALE_CORR_CACHE
    if _SCALE_CORR_CACHE is None:
        path = os.environ.get("SCALE_CORRECTION_JSON", "")
        try:
            import json as _json
            _SCALE_CORR_CACHE = _json.load(open(path)).get("scales", {})
        except Exception:
            _SCALE_CORR_CACHE = {}
    return _SCALE_CORR_CACHE

_RANSAC_CACHE: dict = {}  # scene_key -> loaded RANSAC npz dict
_RANSAC_LOCK = threading.Lock()

# r108: CuTR per-scene catalogue cache. Each value is the dict from np.load on
# the per-scene .npz, with float16 -> float32 promotion applied to the small
# float-precision-sensitive arrays. See cutr.md for schema.
_CUTR_CACHE: dict = {}    # scene_id -> loaded CuTR npz dict
_CUTR_LOCK = threading.Lock()

# r108: SAM 3 result cache to avoid re-running the subprocess on identical
# (scene, frame, label) calls within a process. Keyed by the same triple as
# `predict_2d_points`'s memo.
_SAM3_CACHE: dict = {}    # (scene_id, frame_index, label) -> list[dict]
_SAM3_LOCK = threading.Lock()

def download_file(local_path: str) -> bool:
    # The sealed carrier's external assets are authenticated read-only inputs.
    # Runtime fallback downloads would mutate source paths outside the arm root.
    return os.path.isfile(local_path) and os.path.getsize(local_path) > 0

def _load_frames_cache():
    global _FRAMES_CACHE
    with _CACHE_LOCK:
        if _FRAMES_CACHE is not None: return _FRAMES_CACHE
    # FRAMES_CACHE_JSON env override (default = the shared VSIBench cache, unchanged) lets a
    # benchmark point at a corrected per-scene frame map without mutating the shared/frozen cache.
    # Used by VSTIBench (selected_frames_vstibench.json) to drop the legacy `centroids_prediction`
    # slot that desynced displayed-image vs lifted-geometry on 15 ScanNet scenes (dual-critique r1).
    cache_file = os.environ.get("FRAMES_CACHE_JSON", "/home/jjyeung/agent_project/right_now/selected_frames_full.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f: _FRAMES_CACHE = json.load(f)
    return _FRAMES_CACHE

AGENT_FRAMES_DIR = "/home/jjyeung/agent_project/agent/extracted_frames"   # pre-extracted PNGs (all 288 scenes × 32 frames)
FRAMES_CACHE_DIR = os.path.join(_RUN_OUTPUT_ROOT, "runtime", "frames_cache")
VIDEO_DIR        = "/home/jjyeung/agent_project/map-anything/vsibench_videos"
_R740_FRAME_REGISTRY_PATH = Path(
    "/home/jjyeung/agent_project/agent/rounds/manifests/r740/"
    "external_frames_registry_r740.json"
)
_R740_FRAME_REGISTRY_SHA256 = (
    "31f9385cfb7a995add9427e2f40fe5393856a05c5cf65807d9b8f1b4d13679d1"
)
_R740_FRAME_BINDINGS = None
_R740_FRAME_BINDINGS_LOCK = threading.Lock()

_R740_CONSUMPTION_SCHEMA = "r740-consumed-external-assets-v1"
_R740_CONSUMPTION_STATE = contextvars.ContextVar(
    "r740_consumption_episode", default=None
)
_R740_CONSUMPTION_REGISTRIES = None
_R740_CONSUMPTION_REGISTRY_LOCK = threading.Lock()
_R740_CONSUMPTION_DIGEST_CACHE = {}
_R740_CONSUMPTION_DIGEST_LOCK = threading.Lock()
_R740_CONSUMPTION_PROCESS_LOCK = threading.Lock()
_R740_CONSUMPTION_ORIGINAL_PROCESS = multiprocessing.Process


class R740FrameAccessRefused(RuntimeError):
    """An image path or byte stream is outside the sealed r740 registry."""


class R740AssetAccessRefused(RuntimeError):
    """A video or CuTR access cannot enter an r740 score-bearing episode."""


def _load_r740_consumption_registries() -> dict:
    global _R740_CONSUMPTION_REGISTRIES
    with _R740_CONSUMPTION_REGISTRY_LOCK:
        if _R740_CONSUMPTION_REGISTRIES is not None:
            return _R740_CONSUMPTION_REGISTRIES
        root = Path(__file__).resolve().parents[3] / "manifests" / "r740"
        specs = {
            "source_videos": (
                root / "external_videos_registry_r740.json",
                "r740-external-videos-registry-v2",
            ),
            "cutr_catalogues": (
                root / "cutr_catalogue_registry_r740.json",
                "r740-cutr-catalogue-registry-v1",
            ),
        }
        registries = {}
        for label, (path, schema) in specs.items():
            payload = json.loads(path.read_text())
            assets = payload.get("assets")
            if (
                payload.get("schema") != schema
                or payload.get("package_version") != package_version
                or payload.get("asset_count") != 288
                or payload.get("digest_count") != 288
                or not isinstance(assets, list)
                or len(assets) != 288
            ):
                raise R740AssetAccessRefused(
                    f"malformed authenticated r740 {label} registry"
                )
            by_scene = {}
            for row in assets:
                scene = row.get("scene") if isinstance(row, dict) else None
                if not isinstance(scene, str) or scene in by_scene:
                    raise R740AssetAccessRefused(
                        f"non-unique scene in authenticated r740 {label} registry"
                    )
                by_scene[scene] = dict(row)
            registries[label] = by_scene
        _R740_CONSUMPTION_REGISTRIES = registries
        return registries


def begin_r740_consumption_episode(question_id: str, event_root) -> None:
    if _R740_CONSUMPTION_STATE.get() is not None:
        raise R740AssetAccessRefused("nested r740 external-asset episode")
    qid = str(question_id)
    sidecar_dir = Path(event_root).expanduser().resolve() / ".r740_consumption"
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    qid_key = hashlib.sha256(qid.encode()).hexdigest()[:20]
    event_file = sidecar_dir / f"episode_{qid_key}_{uuid.uuid4().hex}.jsonl"
    with event_file.open("x", encoding="utf-8"):
        pass
    _R740_CONSUMPTION_STATE.set({
        "question_id": qid,
        "event_file": str(event_file),
    })


def _r740_consumption_context() -> tuple[str, str]:
    episode = _R740_CONSUMPTION_STATE.get()
    if episode is None:
        raise R740AssetAccessRefused("unattributed r740 external-asset access")
    return episode["question_id"], episode["event_file"]


def _append_r740_consumption_event(event: dict) -> None:
    question_id, event_file = _r740_consumption_context()
    row = {**event, "question_id": question_id, "pid": os.getpid()}
    payload = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
    flags = os.O_WRONLY | os.O_APPEND
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    descriptor = os.open(event_file, flags)
    try:
        if os.write(descriptor, payload) != len(payload):
            raise R740AssetAccessRefused("short r740 consumption-event append")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _r740_consumption_sha256(path: Path) -> str:
    stat = path.stat()
    key = (
        str(path), stat.st_dev, stat.st_ino, stat.st_size,
        stat.st_mtime_ns, stat.st_ctime_ns,
    )
    with _R740_CONSUMPTION_DIGEST_LOCK:
        digest = _R740_CONSUMPTION_DIGEST_CACHE.get(key)
    if digest is None:
        hasher = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1 << 20), b""):
                hasher.update(chunk)
        digest = hasher.hexdigest()
        with _R740_CONSUMPTION_DIGEST_LOCK:
            _R740_CONSUMPTION_DIGEST_CACHE[key] = digest
    return digest


def _r740_record_registered_access(registry: str, scene_id: str) -> dict:
    scene = str(scene_id)
    declared = _load_r740_consumption_registries().get(registry, {})
    row = declared.get(scene)
    if row is None:
        _append_r740_consumption_event({
            "access": "asset_access",
            "registry": registry,
            "scene": scene,
            "path": None,
            "size_bytes": None,
            "sha256": None,
            "status": "REFUSED",
            "reason": "out_of_registry",
        })
        raise R740AssetAccessRefused(
            f"r740 {registry} access REFUSED for out-of-registry scene {scene}"
        )
    path = Path(row["path"])
    try:
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError(path)
        size = path.stat().st_size
        digest = _r740_consumption_sha256(path)
        if size != row.get("size_bytes") or digest != row.get("sha256"):
            raise OSError("registered digest/size mismatch")
    except (OSError, ValueError) as exc:
        _append_r740_consumption_event({
            "access": "asset_access",
            "registry": registry,
            "scene": scene,
            "path": str(path),
            "size_bytes": row.get("size_bytes"),
            "sha256": row.get("sha256"),
            "status": "REFUSED",
            "reason": "digest_unavailable",
        })
        raise R740AssetAccessRefused(
            f"r740 {registry} digest_unavailable for scene {scene}: {exc}"
        ) from exc
    event = {
        "access": "asset_access",
        "registry": registry,
        "scene": scene,
        "path": str(path),
        "size_bytes": size,
        "sha256": digest,
        "status": "ADMITTED",
        "reason": None,
    }
    _append_r740_consumption_event(event)
    return event


def finish_r740_consumption_episode() -> dict:
    episode = _R740_CONSUMPTION_STATE.get()
    if episode is None:
        raise R740AssetAccessRefused("no active r740 external-asset episode")
    _R740_CONSUMPTION_STATE.set(None)
    event_file = Path(episode["event_file"])
    events = []
    for line_number, raw in enumerate(event_file.read_text().splitlines(), 1):
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise R740AssetAccessRefused(
                f"malformed r740 consumption sidecar line {line_number}"
            ) from exc
        if (
            not isinstance(row, dict)
            or row.get("question_id") != episode["question_id"]
            or not isinstance(row.get("pid"), int)
            or row["pid"] <= 0
        ):
            raise R740AssetAccessRefused(
                f"foreign r740 consumption sidecar event at line {line_number}"
            )
        events.append(row)
    unique = {
        (
            row["registry"], row["scene"], row["path"], row["size_bytes"],
            row["sha256"], row["status"], row["reason"],
        )
        for row in events
    }
    assets = [
        {
            "registry": registry,
            "scene": scene,
            "path": path,
            "size_bytes": size,
            "sha256": digest,
            "status": status,
            "reason": reason,
        }
        for registry, scene, path, size, digest, status, reason in sorted(
            unique, key=lambda value: tuple("" if item is None else str(item) for item in value)
        )
    ]
    return {
        "schema": _R740_CONSUMPTION_SCHEMA,
        "question_id": episode["question_id"],
        "event_count": len(events),
        "events": events,
        "consumed_assets": assets,
        "fatal_count": sum(row.get("status") != "ADMITTED" for row in events),
        "event_sidecar": {
            "path": str(event_file),
            "size_bytes": event_file.stat().st_size,
            "sha256": _r740_consumption_sha256(event_file),
            "event_count": len(events),
        },
    }


def _r740_child_target_with_episode(target, args, kwargs, episode) -> None:
    _R740_CONSUMPTION_STATE.set(dict(episode))
    try:
        target(*args, **kwargs)
    finally:
        _R740_CONSUMPTION_STATE.set(None)


class _R740EpisodeProcess(_R740_CONSUMPTION_ORIGINAL_PROCESS):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None,
                 *, daemon=None):
        kwargs = {} if kwargs is None else kwargs
        episode = _R740_CONSUMPTION_STATE.get()
        if episode is not None and target is not None:
            target, args, kwargs = (
                _r740_child_target_with_episode,
                (target, args, kwargs, dict(episode)),
                {},
            )
        super().__init__(
            group=group, target=target, name=name, args=args, kwargs=kwargs,
            daemon=daemon,
        )


def install_r740_consumption_capture() -> None:
    _load_r740_consumption_registries()
    with _R740_CONSUMPTION_PROCESS_LOCK:
        if multiprocessing.Process is _R740EpisodeProcess:
            return
        if multiprocessing.Process is not _R740_CONSUMPTION_ORIGINAL_PROCESS:
            raise R740AssetAccessRefused(
                "multiprocessing.Process already has a foreign consumption patch"
            )
        multiprocessing.Process = _R740EpisodeProcess


def _r740_sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_r740_frame_bindings():
    global _R740_FRAME_BINDINGS
    with _R740_FRAME_BINDINGS_LOCK:
        if _R740_FRAME_BINDINGS is not None:
            return _R740_FRAME_BINDINGS
        try:
            registry_bytes = _R740_FRAME_REGISTRY_PATH.read_bytes()
            registry = json.loads(registry_bytes)
        except Exception as exc:
            raise R740FrameAccessRefused(
                f"unreadable r740 frame registry: {_R740_FRAME_REGISTRY_PATH}"
            ) from exc
        if _r740_sha256_bytes(registry_bytes) != _R740_FRAME_REGISTRY_SHA256:
            raise R740FrameAccessRefused("r740 frame registry SHA-256 mismatch")
        assets = registry.get("assets")
        if (
            registry.get("schema") != "r740-external-frames-registry-v2"
            or registry.get("package_version") != package_version
            or registry.get("asset_count") != 9216
            or registry.get("digest_count") != 9216
            or not isinstance(assets, list)
            or len(assets) != 9216
        ):
            raise R740FrameAccessRefused("malformed r740 frame registry")
        by_key, by_path = {}, {}
        for row in assets:
            path = row.get("path")
            scene = row.get("scene")
            if not isinstance(path, str) or not os.path.isabs(path):
                raise R740FrameAccessRefused("r740 frame registry contains a relative path")
            key = (scene, Path(path).stem)
            if key in by_key or path in by_path or not isinstance(row.get("sha256"), str):
                raise R740FrameAccessRefused("r740 frame registry contains an invalid binding")
            by_key[key] = row
            by_path[path] = row
        _R740_FRAME_BINDINGS = (by_key, by_path)
        return _R740_FRAME_BINDINGS


def _read_r740_registered_frame(path: str) -> bytes:
    """Read once, authenticate, and return the exact registered image bytes."""
    _, by_path = _load_r740_frame_bindings()
    candidate = os.path.abspath(os.fspath(path))
    row = by_path.get(candidate)
    if row is None:
        raise R740FrameAccessRefused(f"unregistered r740 frame path: {candidate}")
    asset = Path(candidate)
    if asset.is_symlink() or not asset.is_file():
        raise R740FrameAccessRefused(f"missing regular registered r740 frame: {candidate}")
    payload = asset.read_bytes()
    if len(payload) != row.get("size_bytes"):
        raise R740FrameAccessRefused(f"registered r740 frame size mismatch: {candidate}")
    if _r740_sha256_bytes(payload) != row.get("sha256"):
        raise R740FrameAccessRefused(f"registered r740 frame SHA-256 mismatch: {candidate}")
    _append_r740_consumption_event({
        "access": "asset_access",
        "registry": "selected_frames",
        "scene": row["scene"],
        "path": candidate,
        "size_bytes": len(payload),
        "sha256": _r740_sha256_bytes(payload),
        "status": "ADMITTED",
        "reason": None,
    })
    return payload


def _get_local_image(scene_id: str, frame_name: str):
    """
    Return only the exact path registered for this scene/frame pair.
    """
    if not frame_name:
        return None
    by_key, _ = _load_r740_frame_bindings()
    row = by_key.get((scene_id, frame_name))
    if row is None:
        raise R740FrameAccessRefused(
            f"unregistered r740 scene/frame binding: {scene_id}/{frame_name}"
        )
    return row["path"]

def _get_resized_image_bytes(path: str) -> bytes:
    payload = _read_r740_registered_frame(path)
    try:
        img = Image.open(io.BytesIO(payload)).convert("RGB")
        img = img.resize((1024, 768), Image.Resampling.LANCZOS)  # r75: bumped from 640x480
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    except Exception:
        return payload

def _resolve_dataset(scene_id: str) -> str:
    """Infer dataset subdirectory from scene_id naming convention."""
    if scene_id.startswith("scene"):
        return "scannet"
    elif len(scene_id) == 8 and scene_id.isdigit():
        return "arkitscenes"
    return "scannetpp"

def _load_dense(scene_id: str, point_cloud_source: str | None = None) -> dict | None:
    """
    Load the per-scene dense .npz (depth, pts3d_world, intrinsics, mask, conf, camera_poses).
    Returns a dict of numpy arrays, or None if not found.
    Arrays shapes: pts3d_world (N,H,W,3), depth_z (N,H,W), intrinsics (N,3,3),
                   conf (N,H,W), mask (N,H,W), camera_poses (N,4,4), indices (N,).
    """
    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError:
        return None
    cache_key = (source_key, scene_id)
    with _DENSE_LOCK:
        if cache_key in _DENSE_CACHE:
            return _DENSE_CACHE[cache_key]

    dataset = _resolve_dataset(scene_id)
    npz_path = os.path.join(_POINT_CLOUD_SOURCES[source_key]["dense_dir"], dataset, f"{scene_id}.npz")
    if not os.path.exists(npz_path):
        return None

    data = dict(np.load(npz_path, allow_pickle=False))
    data["point_cloud_source"] = source_key
    data["point_cloud_summary"] = _POINT_CLOUD_SOURCES[source_key]["summary"]
    # Convert float16 arrays to float32 for computation accuracy
    for key in ("pts3d_world", "depth_z", "conf"):
        if key in data:
            data[key] = data[key].astype(np.float32)

    # r156: legacy G3T-metric mode. In r306 this can only affect the explicit
    # G3T source, and only behind the debug escape hatch above, so a stale
    # launcher env cannot rescale the default source cloud.
    if _ALLOW_LEGACY_SCALE_ENVS and _G3T_METRIC and source_key == "g3t_scaled":
        s = _g3t_scale().get(scene_id, _g3t_scale_median())
        if s and s > 0:
            data["pts3d_world"] = data["pts3d_world"] * np.float32(s)
            if "depth_z" in data:
                data["depth_z"] = data["depth_z"] * np.float32(s)
            if "camera_poses" in data:
                cp = data["camera_poses"].copy()
                cp[:, :3, 3] = cp[:, :3, 3] * s
                data["camera_poses"] = cp

    # r218: honest per-scene scale correction (see _scale_correction above).
    if (_ALLOW_LEGACY_SCALE_ENVS and source_key == POINT_CLOUD_DEFAULT_SOURCE
            and os.environ.get("SCALE_CORRECTION_JSON")):
        rec = _scale_correction().get(scene_id)
        s_corr = float(rec.get("scale", 0)) if isinstance(rec, dict) else 0.0
        if s_corr > 0 and s_corr != 1.0:
            data["pts3d_world"] = data["pts3d_world"] * np.float32(s_corr)
            if "depth_z" in data:
                data["depth_z"] = data["depth_z"] * np.float32(s_corr)
            if "camera_poses" in data:
                cp = data["camera_poses"].copy()
                cp[:, :3, 3] = cp[:, :3, 3] * s_corr
                data["camera_poses"] = cp
            import sys as _sys
            print(f"[scale_correction] {scene_id}: x{s_corr:.4f}",
                  file=_sys.stderr, flush=True)

    with _DENSE_LOCK:
        _DENSE_CACHE[cache_key] = data
    return data


def _dense_grid_hw(scene_id: str, point_cloud_source: str | None = None) -> tuple[int, int]:
    """MG-1 (r208): actual per-scene dense grid (H, W) read from the loaded npz.
    The legacy hardcoded (392, 518) landscape grid breaks on portrait npz grids
    (G3T/G3T-scaled serve e.g. 518x390) — 286 hard 'mask shape does not match
    pts3d_world' errors across 7 categories in r206. Falls back to (392, 518)
    when the dense outputs are unavailable."""
    try:
        dense = _load_dense(scene_id, point_cloud_source=point_cloud_source)
        if dense is not None and "pts3d_world" in dense:
            shp = dense["pts3d_world"].shape
            if len(shp) >= 3:
                return (int(shp[1]), int(shp[2]))
    except Exception:
        pass
    return (392, 518)


# NF-8 (r208, env FLOOR_REL_Z=1): per-scene floor-relative Z clip. The absolute
# Z >= -0.05 clip deletes most of the object in scenes whose floor sits below
# world Z=0. Env-gated so it is a
# separately attributable A/B arm.
_FLOOR_REL_Z = os.environ.get("FLOOR_REL_Z", "0") == "1"

# r209 lever gates — each lever is env-gated so one frozen file supports
# separate one-lever-per-A/B arms (launch with the gate on for the treatment).
_G1_GATE = os.environ.get("G1_GATE", "0") == "1"            # degenerate-mask gate + 2-sigma trim
_STR7_TOOL = os.environ.get("STR7_TOOL", "0") == "1"        # transform_to_observer_frame tool

# r210 lever gates (same pattern; specs: FABLE5_ERROR_ANALYSIS_2026-06-09.md §3).
_NF6_EARLIEST_VISIBLE = os.environ.get("NF6_EARLIEST_VISIBLE", "0") == "1"  # visibility-only find_frames scan + earliest-frame yes/no confirmation
_NF7_GROUNDING_UNION = os.environ.get("NF7_GROUNDING_UNION", "0") == "1"    # registers ground_object_all_frames (multi-frame grounding union)

# r213 lever gates (same pattern).
_MC_EXTENT = os.environ.get("MC_EXTENT", "0") == "1"        # registers get_object_instances_3d (MaskClustering view-consensus extents)
_STR3_ARBITER = os.environ.get("STR3_ARBITER", "0") == "1"  # co-visibility arbiter fields on predict_2d_segmentation_masks_video
_APPEAR_EVIDENCE = os.environ.get("APPEAR_EVIDENCE", "0") == "1"  # first-appearance telemetry fields on predict_2d_segmentation_masks_video

# r214 lever gates (same pattern; swarm-r213 HIGH-certainty fixes from the
# experiment_r212_frozen_s1 error-analysis swarm — CLOSED_LOOP_LEDGER.md rows 1-2).
_DG_GATE = os.environ.get("DG_GATE", "0") == "1"  # shared degenerate-grounding->3D gate (low_confidence flags + sliver drop + robust-agg drop + p5 closest-point)
_CI3D = os.environ.get("CI3D", "0") == "1"        # registers count_instances_3d (canonical tracked-ID merge+clamp instance count)

# r218 lever gates (same pattern).
_IDANCHOR = os.environ.get("IDANCHOR", "0") == "1"    # registers get_annotated_scene_overview (ID-badge frames + instance table)
_ROOM_POLY = os.environ.get("ROOM_POLY", "0") == "1"  # registers estimate_scene_footprint (raster polygon floor area)

# r219 lever gate (same pattern; counting-collapse EA fix from
# experiments_5.0/object_counting/experiment_r217_frozen_s1/errors.md — the
# CI3D-after-verifier-exhaustion bypass, qids 68/81/99/121/4416).
_CI3D_GUARD = os.environ.get("CI3D_GUARD", "0") == "1"  # block direct count_instances_3d calls after a pre-verifier rejection of a CI3D plan

# r220 lever gate (same pattern; counting-collapse EA EMISSION_MECHANICS fix,
# the planner may emit an EMPTY AI message (no text, no tool_calls) early in
# the episode and route_after_planner can send it to the forced-answer node.
# Stateless (history-scan) by design.)
_EMPTYAI_RETRY = os.environ.get("EMPTYAI_RETRY", "0") == "1"  # bounded planner retry on empty emission while evidence < 2

_EMPTYAI_NUDGE_MARK = "[SYSTEM NOTIFICATION]: Your last step was EMPTY"
_EMPTYAI_MAX_RETRIES = 2
_EMPTYAI_MIN_EVIDENCE = 2
_EMPTYAI_VERIFIER_TOOLS = ("verify_plan_pre_execution", "verify_plan_post_execution")


def _emptyai_content_empty(msg) -> bool:
    """True when an AIMessage carries no usable text (the frozen-emission shape)."""
    c = getattr(msg, "content", None)
    if c is None:
        return True
    if isinstance(c, str):
        return not c.strip()
    if isinstance(c, list):  # multimodal part list
        for part in c:
            if isinstance(part, str) and part.strip():
                return False
            if isinstance(part, dict) and str(part.get("text", "")).strip():
                return False
        return True
    return False


def _emptyai_should_retry(messages) -> bool:
    """Stateless check for the EMPTYAI_RETRY route: the trailing AI message is
    an empty emission, fewer than _EMPTYAI_MAX_RETRIES nudges were already
    injected, and the episode has gathered < _EMPTYAI_MIN_EVIDENCE successful
    non-verifier tool results (with evidence in hand, forced-answer is an
    acceptable outcome and we do not second-guess the route)."""
    if not messages or not _emptyai_content_empty(messages[-1]):
        return False
    nudges = 0
    evidence = 0
    for m in messages[:-1]:
        content = getattr(m, "content", "")
        if isinstance(content, str) and content.startswith(_EMPTYAI_NUDGE_MARK):
            nudges += 1
        if getattr(m, "name", None) and m.name not in _EMPTYAI_VERIFIER_TOOLS \
                and type(m).__name__ == "ToolMessage":
            if not _emptyai_is_error_result(content):
                evidence += 1
    return nudges < _EMPTYAI_MAX_RETRIES and evidence < _EMPTYAI_MIN_EVIDENCE


def _emptyai_is_error_result(content) -> bool:
    """Error-shaped tool results must not count as evidence. Tools emit errors
    in several shapes: '{"error": ...}' (dict→json), '[{"error": ...}]'
    (list-of-dict→json), '["Error: ..."]' (list-of-str→json), and the
    CI3D_GUARD refusal "{'error': 'ci3d_guarded', ...}" (str() of a dict,
    single-quote repr). Heuristic: a quoted error key/prefix in the head of
    the stringified payload. Undercounting evidence is the safe direction —
    it only means a (2-bounded) nudge fires where it maybe needn't."""
    head = str(content).lstrip()[:40].lower()
    return '"error"' in head or "'error'" in head or '"error:' in head or head.startswith("error")

# r218: startup warning — ROOM_POLY + SCALE_CORRECTION_JSON stacking is forbidden
# (coverage undercount cancels scale oversize; stacked => ~0.64x GT). r306 only
# honors the scale-correction env behind the explicit legacy debug gate above.
if _ALLOW_LEGACY_SCALE_ENVS and _ROOM_POLY and os.environ.get("SCALE_CORRECTION_JSON"):
    print(
        "[r218 WARN] ROOM_POLY + SCALE_CORRECTION stacking is forbidden "
        "(coverage-undercount cancels scale oversize; stacked => ~0.64x GT)",
        file=sys.stderr, flush=True,
    )


# DG-GATE (r214): one consolidated low-confidence verdict for every 3D lift.
# The individual signals mostly ALREADY exist scattered across tool outputs
# (bbox_quality_warning, mask_truncation_warning, edges_touched, area_norm) —
# the swarm found planners consuming flagged measurements anyway because no
# single field said "do not trust this". This consolidates them into
# `low_confidence` + `flags` + ONE actionable instruction.
_DG_INSTRUCTION = ("low-confidence grounding — re-ground this object on a "
                   "DIFFERENT frame (prefer one where it is fully visible, "
                   "away from the image edges) before trusting this measurement.")


def _dg_flags(*, area_norm: float | None = None, edges_touched: int | None = None,
              score: float | None = None, n_points: int | None = None,
              centroid=None, floor_z: float | None = None) -> list[str]:
    """DG-GATE (r214): consolidated degenerate-grounding flag list for a lifted
    region. Question-agnostic perception-quality signals only."""
    flags = []
    if area_norm is not None:
        if area_norm > 0.30:
            flags.append("area_norm_>0.30")
        elif area_norm < 0.01:
            flags.append("area_norm_<0.01")
    if edges_touched is not None and edges_touched >= 2:
        flags.append("edges_touched_>=2")
    if score is not None and score < 0.70:
        flags.append("mask_score_<0.70")
    if n_points is not None and n_points < 2000:
        flags.append("point_count_<2000")
    if centroid is not None:
        if floor_z is not None and float(centroid[2]) < floor_z - 0.15:
            flags.append("centroid_subfloor_z")
        if abs(float(centroid[0])) < 0.10 and abs(float(centroid[1])) < 0.10:
            flags.append("near_origin_centroid")
    return flags


def _dg_apply(result: dict, flags: list[str]) -> dict:
    """DG-GATE (r214): attach the consolidated verdict to a tool result dict."""
    result["low_confidence"] = bool(flags)
    if flags:
        result["flags"] = flags
        result["instruction"] = _DG_INSTRUCTION
    return result


def _dg_scene_floor_z(scene_id: str, dense: dict) -> float:
    """DG-GATE (r214): scene-level floor Z estimate (p2 of valid world-Z).
    Reuses _scene_floor_clip_z's cached p2-minus-5cm threshold and undoes the pad
    — unlike the per-region floor_z_estimate (p5 of the region itself, which a
    region median can never undercut), a sub-floor centroid CAN fall below this."""
    return _scene_floor_clip_z(scene_id, dense) + 0.05


def _dg_drop_degenerate_boxes(boxes: list) -> list:
    """DG-GATE (r214): drop self-flagging degenerate VLM boxes — tiny boxes
    (area < 0.6% of frame) and edge slivers / corner crops (width or height
    < 8% of frame while touching that axis's image edge). r212_frozen
    appearance swarm: 6/17 wrongs were a single such false-positive box pulling
    an object's first appearance earlier than truth; rel_distance/abs_distance
    saw the same boxes feeding depth-bleed 3D lifts. Returns [] when every box
    is degenerate (genuine "not visible")."""
    kept = []
    for box in boxes:
        xmin, ymin, xmax, ymax = box
        w, h = xmax - xmin, ymax - ymin
        if w * h < 0.006:
            continue
        if w < 0.08 and (xmin <= 0.02 or xmax >= 0.98):
            continue
        if h < 0.08 and (ymin <= 0.02 or ymax >= 0.98):
            continue
        kept.append(box)
    return kept


def _g1_trim_2sigma(pts: np.ndarray) -> np.ndarray:
    """G1 ARM-A (r209): per-axis >2-sigma outlier trim on the lifted cloud.
    Keeps the hard min()/extent semantics downstream — this only removes
    bleed points before statistics. No-op when it would leave <25 points or
    <30% of the cloud (collapse guard)."""
    if len(pts) < 50:
        return pts
    mu = pts.mean(axis=0)
    sd = pts.std(axis=0) + 1e-9
    keep = (np.abs(pts - mu) <= 2.0 * sd).all(axis=1)
    if keep.sum() >= max(25, int(0.30 * len(pts))):
        return pts[keep]
    return pts


def _g1_flags(*, area_norm: float | None, edges_touched: int | None,
              n_points: int, extent_p90, centroid_z: float | None,
              floor_z: float | None) -> tuple[bool, list[str]]:
    """G1 ARM-A (r209): structured degeneracy verdict for a lifted region.
    Question-agnostic perception-quality signals only."""
    reasons = []
    if area_norm is not None:
        if area_norm > 0.30:
            reasons.append("region_covers_>30%_of_frame")
        elif area_norm < 0.01:
            reasons.append("region_<1%_of_frame")
    if edges_touched is not None and edges_touched >= 2:
        reasons.append("clipped_at_>=2_image_edges")
    if n_points < 25:
        reasons.append("too_few_valid_3d_points")
    try:
        if extent_p90 is not None:
            horiz = float(max(extent_p90[0], extent_p90[1]))
            if horiz < 0.04:
                reasons.append("degenerate_horizontal_extent_<4cm")
    except Exception:
        pass
    if (centroid_z is not None and floor_z is not None
            and centroid_z < floor_z - 0.2):
        reasons.append("centroid_below_floor")
    return (len(reasons) > 0), reasons
_FLOOR_Z_CACHE: dict = {}
_FLOOR_Z_LOCK = threading.Lock()


def _scene_floor_clip_z(scene_id: str, dense: dict) -> float:
    """Floor-relative clip threshold: p2 of valid world-Z (subsampled) minus 5cm.
    Cached per scene. Only consulted when FLOOR_REL_Z=1."""
    source_key = dense.get("point_cloud_source", POINT_CLOUD_DEFAULT_SOURCE)
    cache_key = (source_key, scene_id)
    with _FLOOR_Z_LOCK:
        if cache_key in _FLOOR_Z_CACHE:
            return _FLOOR_Z_CACHE[cache_key]
    thr = -0.05
    try:
        pts = dense["pts3d_world"]
        msk = dense.get("mask")
        zs = pts[..., 2][msk] if msk is not None else pts[..., 2].ravel()
        zs = zs[np.isfinite(zs)]
        if zs.size > 200000:
            zs = zs[:: max(1, zs.size // 200000)]
        if zs.size > 100:
            thr = float(np.percentile(zs, 2)) - 0.05
    except Exception:
        thr = -0.05
    with _FLOOR_Z_LOCK:
        _FLOOR_Z_CACHE[cache_key] = thr
    return thr


def _load_ransac_dense(scene_id: str, point_cloud_source: str | None = None) -> dict | None:
    """
    Load the gravity-aligned (RANSAC) per-scene dense .npz. Same array layout as
    `_load_dense`, but the world frame is rotated so the floor lies in the XY plane
    (Z = up) — necessary for reliable floor-z slicing on tilted scenes.

    Falls back to `_load_dense(scene_id)` if the RANSAC file is missing for this
    scene, so callers always get the best-available dense data.
    """
    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError:
        return None
    cache_key = (source_key, scene_id)
    with _RANSAC_LOCK:
        if cache_key in _RANSAC_CACHE:
            return _RANSAC_CACHE[cache_key]

    dataset = _resolve_dataset(scene_id)
    ransac_dir = _POINT_CLOUD_SOURCES[source_key].get("ransac_dir")
    if not ransac_dir:
        return _load_dense(scene_id, point_cloud_source=source_key)
    npz_path = os.path.join(ransac_dir, dataset, f"{scene_id}.npz")
    if not os.path.exists(npz_path):
        return _load_dense(scene_id, point_cloud_source=source_key)

    data = dict(np.load(npz_path, allow_pickle=False))
    data["point_cloud_source"] = source_key
    data["point_cloud_summary"] = _POINT_CLOUD_SOURCES[source_key]["summary"]
    for key in ("pts3d_world", "depth_z", "conf"):
        if key in data:
            data[key] = data[key].astype(np.float32)

    # r156: keep the RANSAC/gravity path metric-consistent with _load_dense.
    if _ALLOW_LEGACY_SCALE_ENVS and _G3T_METRIC and source_key == "g3t_scaled":
        s = _g3t_scale().get(scene_id, _g3t_scale_median())
        if s and s > 0:
            data["pts3d_world"] = data["pts3d_world"] * np.float32(s)
            if "depth_z" in data:
                data["depth_z"] = data["depth_z"] * np.float32(s)
            if "camera_poses" in data:
                cp = data["camera_poses"].copy()
                cp[:, :3, 3] = cp[:, :3, 3] * s
                data["camera_poses"] = cp

    with _RANSAC_LOCK:
        _RANSAC_CACHE[cache_key] = data
    return data

def _load_cutr(scene_id: str) -> dict | None:
    """
    r108: Load the per-scene CuTR 3D-bbox catalogue. Returns a dict of numpy
    arrays per the schema in cutr.md, or None if the .npz is missing.

    Cached per process. float16 `object_desc` is left as float16 to save
    memory; numerical arrays are kept native dtype (already float32 / int).
    """
    # The access event is unconditional: a cache hit still consumes inference
    # derived from the registered catalogue and must fail if its backing digest
    # is no longer available.
    _r740_record_registered_access("cutr_catalogues", scene_id)
    with _CUTR_LOCK:
        if scene_id in _CUTR_CACHE:
            return _CUTR_CACHE[scene_id]

    dataset = _resolve_dataset(scene_id)
    npz_path = os.path.join(CUTR_DIR, dataset, f"{scene_id}.npz")
    if not os.path.exists(npz_path):
        return None
    data = dict(np.load(npz_path, allow_pickle=False))

    with _CUTR_LOCK:
        _CUTR_CACHE[scene_id] = data
    return data


def _frame_index_to_npz_idx(scene_id: str, frame_index: int, dense: dict) -> int | None:
    """
    Map a 1-based frame_index (from the agent) to the positional index in the dense arrays.
    frame_index is the 1-based index into selected_frames_cache[scene_id]["frame_names"].
    We find the matching video index from the frames cache and look it up in dense["indices"].
    """
    cache = _load_frames_cache()
    if not cache or scene_id not in cache:
        return None

    selected_indices = cache[scene_id].get("indices", [])
    if not (1 <= frame_index <= len(selected_indices)):
        return None

    # The video frame index (0-based into the original video)
    raw_video_idx = selected_indices[frame_index - 1]

    # Find where this video index sits in the dense npz's index list
    dense_indices = dense["indices"].tolist()
    if raw_video_idx in dense_indices:
        return dense_indices.index(raw_video_idx)

    # [addendum-131 F1] Fail closed: the canonical raw-video index for this frame
    # is absent from the dense npz's own `indices` array — the stale/mismatched-
    # store scenario the store audit flagged. The former positional fallback
    # (frame_index - 1) silently substituted a same-position slot with NO exact-vs-
    # fallback signal to the caller, masking store staleness and letting a slot with
    # different raw-frame provenance be read as if it matched. Return None (the
    # function's existing "cannot map" sentinel — every caller already guards it)
    # so the lookup miss surfaces as a clean error instead of a mis-provenanced slot.
    # Mirrors query_3d_bbox_catalogue's fail-closed discipline on the same lookup.
    return None


# ─────────────────────────────────────────────────────────────────────────────
# VLM tools
# ─────────────────────────────────────────────────────────────────────────────

# NF-6 (r210, env NF6_EARLIEST_VISIBLE=1): per-(scene,label) cache for the
# earliest-frame confirmation pass so repeat calls see identical fields.
_NF6_CONFIRM_CACHE: dict = {}
_NF6_CONFIRM_LOCK = threading.Lock()


def _nf6_confirm_earliest(scene_id: str, object_label: str, candidate_frames: list,
                          frame_paths: dict, config: RunnableConfig, k: int = 3) -> dict:
    """NF-6 (r210): generic earliest-visibility confirmation primitive. For the
    k earliest candidate frames, independently re-asks the tool VLM a yes/no
    visibility question on the full frame (no crop infra in this pipeline) and
    reports per-frame agreement counts. Purely informational — never alters the
    candidate list and renders no verdict; downstream logic decides what to do
    with the fields."""
    key = (scene_id, object_label.strip().lower())
    with _NF6_CONFIRM_LOCK:
        if key in _NF6_CONFIRM_CACHE:
            return _NF6_CONFIRM_CACHE[key]
    cand = sorted({int(f) for f in candidate_frames})
    checked = cand[:max(1, int(k))]
    per_frame: dict = {}
    for fi in checked:
        path = frame_paths.get(fi)
        ans = None
        if path:
            try:
                text = _google_multimodal(
                    [("image", _get_resized_image_bytes(path)),
                     ("text", f"Is any part of a '{object_label}' visible in this image, "
                              "even partially or at the frame edge? "
                              "Answer with exactly one word: YES or NO.")],
                    model=TOOL_VLM_MODEL, temperature=0.0, max_output_tokens=16,
                    usage_sink=_usage_sink_from_config(config))
                t = (text or "").strip().upper()
                if t.startswith("YES"):
                    ans = True
                elif t.startswith("NO"):
                    ans = False
            except Exception:
                ans = None
        per_frame[fi] = ans
    confirmed = [fi for fi in checked if per_frame[fi] is True]
    n_answered = sum(1 for v in per_frame.values() if v is not None)
    info = {
        "first_frame_all_candidates": min(cand) if cand else None,
        "first_frame_confirmed": min(confirmed) if confirmed else None,
        "earliest_frames_checked": checked,
        "visibility_recheck_per_frame": {str(fi): per_frame[fi] for fi in checked},
        "k_confirmed_of_n_checked": f"{len(confirmed)}/{n_answered}",
    }
    with _NF6_CONFIRM_LOCK:
        _NF6_CONFIRM_CACHE[key] = info
    return info


@tool
def find_frames_with_object(scene_id: str, object_label: str, config: RunnableConfig, num_frames: str = "5") -> list:
    """
    Scans all available frames (1–32) to find frames containing the object.

    Args:
        scene_id: VSIBench scene identifier.
        object_label: Natural-language label, e.g. "blue chair", "refrigerator".
        num_frames: How many frames to return.
                    "5" (default) — best frames for 3D localization, including first and last visible.
                    "1" — only the very first frame the object is visible in (use when only the earliest visible frame is needed).
                    "all" — every frame where the object is clearly visible.

    Returns:
        List of 1-based frame indices, e.g. [3, 12, 27]. Returns [] if object not found.
    """
    cache = _load_frames_cache()
    if not cache or scene_id not in cache: return [f"Error: Scene {scene_id} not found."]
    frame_names = cache[scene_id]["frame_names"]
    image_paths, valid_indices = [], []
    for i, fname in enumerate(frame_names):
        if not fname: continue
        path = _get_local_image(scene_id, fname)
        if path:
            image_paths.append(path)
            valid_indices.append(i + 1)
    if not image_paths: return [f"Error: No images loaded for scene {scene_id}."]

    # r47: when num_frames=="1" the legacy single-frame VLM prompt is a coin
    # flip — a non-deterministic single call asking "what is THE first frame?"
    # In r45/r46, ~5 / 8 wrong appearance-order traces had num_frames="1"
    # disagreeing with num_frames="all" output from the SAME scene. Replace
    # the single-frame prompt with the "all"-prompt and return [min(parsed)]
    # in deterministic post-processing — fixes the coin-flip without changing
    # the function's contract (still returns one frame index when num="1").
    # r48: cache the all-prompt VLM result per (scene_id, object_label) so a
    # later "all" call (or a later "1" call from another worker) sees the same
    # frame list as the first call.
    requested_one = str(num_frames) == "1"
    use_all_prompt = requested_one or str(num_frames).lower() == "all"
    if use_all_prompt:
        if _NF6_EARLIEST_VISIBLE:
            # NF-6 (r210): visibility-only criterion. The legacy wording below
            # ("clearly visible and its centroid can be accurately estimated")
            # adds a localization-quality requirement that systematically
            # reports first sightings LATE — partial / frame-edge sightings
            # are real sightings.
            prompt = (f"Identify ALL frames where ANY part of the '{object_label}' is visible — "
                      "even if it is only partially visible, small, far away, or cut off at the frame edge. "
                      "Do NOT require the object to be well-framed or easy to localize.\n"
                      "Return ONLY a JSON list of frame indices. Example: [4, 12, 24]\nIf not visible, return: []")
        else:
            prompt = (f"Identify ALL frames where the '{object_label}' is clearly visible and its centroid can be accurately estimated.\n"
                      "Return ONLY a JSON list of frame indices. Example: [4, 12, 24]\nIf not visible, return: []")
    else:
        prompt = (f"Identify the TOP {num_frames} BEST frames where the '{object_label}' is most clearly visible and its centroid can be accurately estimated. You MUST include the first and last frames the object is visible in.\n"
                  "Return ONLY a JSON list of frame indices. Example: [4, 12, 24]\nIf not visible, return: []")

    cache_key = (scene_id, object_label.strip().lower())
    if use_all_prompt:
        with _FRAMES_VLM_LOCK:
            cached = _FRAMES_VLM_CACHE.get(cache_key)
        if cached is not None:
            trace_list = config.get("configurable", {}).get("trace_list")
            if trace_list is not None:
                trace_list.append({"tool": "find_frames_with_object", "response": f"[cache hit] {cached}"})
            if not cached:
                return []
            out = [min(cached)] if requested_one else list(cached)
            if _NF6_EARLIEST_VISIBLE:
                # NF-6: appended info dict only — the frame-index list is unchanged.
                out = out + [_nf6_confirm_earliest(
                    scene_id, object_label, list(cached),
                    dict(zip(valid_indices, image_paths)), config
                )]
            return out

    try:
        parts = []
        for path, idx in zip(image_paths[:32], valid_indices[:32]):
            parts.append(("text",  f"Frame '{idx}':"))
            parts.append(("image", _get_resized_image_bytes(path)))
        parts.append(("text", prompt))
        text = _google_multimodal(
            parts, model=TOOL_VLM_MODEL, temperature=0.0, max_output_tokens=1536,
            usage_sink=_usage_sink_from_config(config),
        )
        trace_list = config.get("configurable", {}).get("trace_list")
        if trace_list is not None: trace_list.append({"tool": "find_frames_with_object", "response": text})
        match = re.search(r'\[([^\]]*)\]', text)
        if match:
            inner = match.group(1).strip()
            if not inner:
                if use_all_prompt:
                    with _FRAMES_VLM_LOCK:
                        _FRAMES_VLM_CACHE[cache_key] = []
                return []  # VLM explicitly reported no visible frames — genuine negative.
            parsed = [int(v.strip()) for v in inner.split(',') if v.strip().lstrip('-').isdigit()]
            in_range = [f for f in parsed if f in valid_indices]
            if in_range:
                if use_all_prompt:
                    with _FRAMES_VLM_LOCK:
                        _FRAMES_VLM_CACHE[cache_key] = list(in_range)
                nf6_info = None
                if _NF6_EARLIEST_VISIBLE and use_all_prompt:
                    # NF-6: confirmation pass on the K=3 earliest candidates.
                    # Appended as an extra info element; the frame-index list
                    # itself is never altered by the confirmation outcome.
                    nf6_info = _nf6_confirm_earliest(
                        scene_id, object_label, in_range,
                        dict(zip(valid_indices, image_paths)), config
                    )
                # r47: see top of function — if caller asked for "1", collapse
                # the "all"-prompt response to its earliest frame.
                if requested_one:
                    return [min(in_range)] + ([nf6_info] if nf6_info is not None else [])
                return in_range + ([nf6_info] if nf6_info is not None else [])
            snippet = text.strip().replace("\n", " ")[:160]
            return [f"Error: VLM returned a bracketed response that could not be parsed as frame indices. "
                    f"If you expect '{object_label}' to exist, retry ONCE with a different synonym; "
                    f"otherwise treat this object as absent and continue. Raw response: {snippet!r}"]
        snippet = text.strip().replace("\n", " ")[:160]
        return [f"Error: VLM response contained no JSON list of frame indices for '{object_label}'. "
                f"If you expect this object to exist, retry ONCE with a different synonym; "
                f"otherwise treat this object as absent and continue. Raw response: {snippet!r}"]
    except Exception as e: return [f"Error: {e}"]


if _NF6_EARLIEST_VISIBLE:
    # NF-6 (r210): surface the appended info element in the tool description so
    # the planner can read the fields. Gated so the control arm's tool schema
    # stays byte-identical to r209.
    find_frames_with_object.description += (
        "\n\nWhen num_frames is \"1\" or \"all\", the returned list additionally ends with one "
        "info dict from an independent earliest-visibility recheck of the K=3 earliest candidate "
        "frames: {first_frame_all_candidates, first_frame_confirmed, earliest_frames_checked, "
        "visibility_recheck_per_frame, k_confirmed_of_n_checked}. These are agreement counts, "
        "not a verdict; the frame-index list itself is unchanged.")


@tool
def get_frame_image(scene_id: str, frame_index: int) -> str:
    """
    Returns the local file path for a frame so you can visually inspect it.

    Args:
        scene_id: VSIBench scene identifier.
        frame_index: 1-based frame number (1–32).

    Returns:
        Absolute local path to the JPEG/PNG image, or an error string.
    """
    cache = _load_frames_cache()
    if not cache or scene_id not in cache: return f"Error: Scene {scene_id} not found."
    frame_names = cache[scene_id]["frame_names"]
    if not (1 <= frame_index <= len(frame_names)): return f"Error: Out of bounds."
    path = _get_local_image(scene_id, frame_names[frame_index - 1])
    _read_r740_registered_frame(path)
    return path


@tool
def predict_2d_bounding_box(scene_id: str, frame_index: int, object_label: str, config: RunnableConfig) -> list:
    """
    Uses a VLM to draw tight 2D bounding box(es) around ALL instances of an object in a frame.

    Use this when you need the 2D pixel footprint of an object (e.g. to measure its size
    or to identify which pixel to query with get_world_3d_point_from_2d).

    Args:
        scene_id: VSIBench scene identifier.
        frame_index: 1-based frame number (1–32).
        object_label: Natural-language label, e.g. "sofa", "second chair from the left".

    Returns:
        List of bounding boxes in normalized [0,1] coordinates: [[xmin, ymin, xmax, ymax], ...].
        Returns [] if object not visible. Returns [["Error: ..."]] on failure.

    Coordinate convention: (0,0) = top-left, (1,1) = bottom-right of the image.

    Implementation note (r42): queries Gemini using the canonical 2D-bbox schema
    `box_2d = [ymin, xmin, ymax, xmax]` normalized to 0–1000, with
    response_mime_type="application/json", then converts to the agent-facing
    [xmin, ymin, xmax, ymax] in [0, 1].
    """
    cache = _load_frames_cache()
    if not cache or scene_id not in cache: return [[f"Error: Scene {scene_id} not found."]]
    frame_names = cache[scene_id]["frame_names"]
    if not (1 <= frame_index <= len(frame_names)): return [[f"Error: Out of bounds."]]
    image_path = _get_local_image(scene_id, frame_names[frame_index - 1])

    prompt = (
        f"Detect every instance of '{object_label}' in this image and output a tight 2D bounding box for each.\n"
        "Return a JSON array. Each element MUST be an object with keys \"box_2d\" and \"label\". "
        "\"box_2d\" MUST be [ymin, xmin, ymax, xmax] normalized to 0-1000 (integers). "
        "\"label\" is a short text description for the specific instance "
        "(e.g. \"left chair\", \"chair near window\").\n"
        "If the object is not visible, return an empty JSON array: [].\n"
        "Output ONLY the JSON array — no prose, no markdown, no code fences."
    )

    try:
        image_bytes = _get_resized_image_bytes(image_path)
        if "/" in TOOL_VLM_MODEL:
            # r209 (2026-06-10): slash id -> NVIDIA endpoint (Google key being
            # sunset). Same prompt; JSON-array discipline enforced by prompt
            # text + the fence-tolerant parser below.
            raw_text = (_google_multimodal(
                [("image", image_bytes), ("text", prompt)],
                model=TOOL_VLM_MODEL, temperature=0.0,
                max_output_tokens=2048,
                usage_sink=_usage_sink_from_config(config)) or "").strip()
        else:
            client = _google_client()
            gparts = [
                _gtypes.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                _gtypes.Part.from_text(text=prompt),
            ]
            cfg = _gtypes.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=2048,
                response_mime_type="application/json",
            )
            _t0 = time.time()
            resp = custody_effect(native_google.generate_content, client,
                sink=_usage_sink_from_config(config), where="predict_2d_bounding_box", model_role="tool_vlm",
                model=TOOL_VLM_MODEL,
                contents=[_gtypes.Content(role="user", parts=gparts)],
                config=cfg,
            )
            _record_llm_usage(
                _usage_sink_from_config(config), "predict_2d_bounding_box",
                TOOL_VLM_MODEL, getattr(resp, "usage_metadata", None), _t0,
                model_version=getattr(resp, "model_version", None),
                finish_reason=getattr(resp.candidates[0], "finish_reason", None) if resp.candidates else None,
                raw_response=_json_safe(resp),
            )
            raw_text = (resp.text or "").strip()

        trace_list = config.get("configurable", {}).get("trace_list")
        if trace_list is not None:
            trace_list.append({"tool": "predict_2d_bounding_box", "response": raw_text})

        # Tolerate the occasional code fence even with response_mime_type=json
        cleaned = raw_text
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE).strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            m = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if not m: return []
            try: parsed = json.loads(m.group(0))
            except json.JSONDecodeError: return []

        if not isinstance(parsed, list): return []

        out = []
        for entry in parsed:
            box = entry.get("box_2d") if isinstance(entry, dict) else entry
            if not (isinstance(box, (list, tuple)) and len(box) == 4): continue
            try:
                ymin = float(box[0]) / 1000.0
                xmin = float(box[1]) / 1000.0
                ymax = float(box[2]) / 1000.0
                xmax = float(box[3]) / 1000.0
            except Exception:
                continue
            xmin = max(0.0, min(1.0, xmin))
            ymin = max(0.0, min(1.0, ymin))
            xmax = max(0.0, min(1.0, xmax))
            ymax = max(0.0, min(1.0, ymax))
            if xmin >= xmax or ymin >= ymax: continue
            out.append([round(xmin, 3), round(ymin, 3), round(xmax, 3), round(ymax, 3)])
        if _DG_GATE:
            out = _dg_drop_degenerate_boxes(out)
        return out
    except Exception as e:
        return [[f"Error: {e}"]]


@tool
def predict_2d_points(scene_id: str, frame_index: int, query: str, config: RunnableConfig,
                      point_cloud_source: str = POINT_CLOUD_DEFAULT_SOURCE) -> list:
    """
    VLM-based 2D-pixel-coordinate prediction with automatic 3D lift.

    Pass a natural-language query and get back a list of 2D pixel coordinates
    (one per matching item in the image), each accompanied by the 3D world
    point obtained by averaging `pts3d_world` from the selected point cloud
    source over a small patch around the pixel. Use this when a bounding box is too coarse — e.g. when you need
    the corner of a room, the centroid of an object, or a precise landmark
    like the tip of a lamp or the edge of a door.

    Compared to predict_2d_bounding_box, this returns POINTS (not boxes), and
    each point is already lifted to a world-space 3D coordinate, so the agent
    can skip the get_3d_points_in_bbox / get_world_3d_point_from_2d call.

    Args:
        scene_id: VSIBench scene identifier.
        frame_index: 1-based frame number (1–32).
        query: Natural-language description of which pixel(s) to return.
               Examples: "the four corners of the room floor",
               "the centroid of each chair", "the leftmost edge of the door",
               "the top of the lamp".
        point_cloud_source: Optional source for the 3D lift. Default is
            "g3t_scaled" for every question. Valid sources and tradeoffs:
            g3t_scaled = metric-scale and gravity-oriented default; mapanything =
            stable multi-view layout fallback; unik3d = metric depth-oriented
            alternative for scale/depth checks. Choose explicitly from the
            question/evidence; do not rely on launcher/category preselection.

    Returns:
        list[dict] — one entry per detected point:
          {"pixel_norm": [x, y]   # in [0, 1]; (0,0) = top-left, (1,1) = bottom-right
           "world":      [X, Y, Z] or None,  # Z-up world meters; None if dense lookup failed
           "label":      str       # short text from the VLM identifying this point
           "point_cloud_source": str
          }
        Returns [] if nothing matches the query.
        Returns [{"error": "..."}] on failure.

    Implementation: Gemini Flash returns coordinates as `[y, x]` integer pairs
    on a 0-1000 scale; the tool descales to [0, 1] and averages
    `pts3d_world` inside a small ~0.7%-of-image-side patch around each point.
    """
    cache = _load_frames_cache()
    if not cache or scene_id not in cache: return [{"error": f"Scene {scene_id} not found."}]
    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError as e:
        return [{"error": str(e)}]
    frame_names = cache[scene_id]["frame_names"]
    if not (1 <= frame_index <= len(frame_names)): return [{"error": "frame_index out of bounds."}]
    image_path = _get_local_image(scene_id, frame_names[frame_index - 1])
    if image_path is None: return [{"error": "Frame image not found."}]

    # r54: per-process memo on (scene_id, frame_index, query). Even with
    # greedy decoding, identical inputs occasionally drift by 1px between
    # repeated VLM calls (4/5 match in the sanity test). Returning the
    # cached parsed list on subsequent identical calls eliminates the
    # residual variance that single-linkage clustering downstream
    # amplifies into different counts.
    cache_key = (source_key, scene_id, frame_index, query)
    with _POINTS_VLM_LOCK:
        cached_results = _POINTS_VLM_CACHE.get(cache_key)
    if cached_results is not None:
        trace_list = config.get("configurable", {}).get("trace_list")
        if trace_list is not None:
            trace_list.append({"tool": "predict_2d_points", "response": "<cache_hit>"})
        return cached_results

    prompt = (
        f"Identify 2D pixel coordinates in the image matching this query:\n"
        f"  {query}\n"
        "Return a JSON array. Each element MUST be an object with keys "
        "\"point\" and \"label\". \"point\" MUST be [y, x] normalized to "
        "0-1000 (integers). \"label\" is a short text description for that "
        "specific point (e.g. \"northwest corner of room\", \"chair near sink\").\n"
        "If nothing in the image matches the query, return an empty JSON "
        "array: [].\n"
        "Output ONLY the JSON array — no prose, no markdown, no code fences."
    )

    try:
        image_bytes = _get_resized_image_bytes(image_path)
        if "/" in TOOL_VLM_MODEL:
            # r209 (2026-06-10): slash id -> NVIDIA endpoint (Google key being
            # sunset). r55 semantics preserved: temperature=0 + module cache.
            raw_text = (_google_multimodal(
                [("image", image_bytes), ("text", prompt)],
                model=TOOL_VLM_MODEL, temperature=0.0,
                max_output_tokens=2048,
                usage_sink=_usage_sink_from_config(config)) or "").strip()
        else:
            client = _google_client()
            gparts = [
                _gtypes.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                _gtypes.Part.from_text(text=prompt),
            ]
            # r55 (Fork 2 pivot): drop top_p=1.0/top_k=1/seed=42. The r54
            # counting subagent isolated the regression: greedy decoding
            # anchored the VLM on the SAME single instance per frame, and
            # r51/r53's stochasticity was actually providing the cluster
            # diversity that pushed counts ≥ 2. Variance was part of the
            # signal, not noise. r55 keeps temperature=0 and the
            # (scene_id, frame_index, query) module-level cache (the cache
            # was the load-bearing change behind r54's wins on
            # direction_easy/hard, per their respective subagents) but lets
            # tied-logit ties resolve via API-side default sampling. Same
            # input within a process still hits cache → deterministic; first
            # call per (scene, frame, query) triple gets the natural API
            # entropy that distinguishes co-visible same-label instances.
            cfg = _gtypes.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=2048,
                response_mime_type="application/json",
            )
            _t0 = time.time()
            resp = custody_effect(native_google.generate_content, client,
                sink=_usage_sink_from_config(config), where="predict_2d_points", model_role="tool_vlm",
                model=TOOL_VLM_MODEL,
                contents=[_gtypes.Content(role="user", parts=gparts)],
                config=cfg,
            )
            _record_llm_usage(
                _usage_sink_from_config(config), "predict_2d_points",
                TOOL_VLM_MODEL, getattr(resp, "usage_metadata", None), _t0,
                model_version=getattr(resp, "model_version", None),
                finish_reason=getattr(resp.candidates[0], "finish_reason", None) if resp.candidates else None,
                raw_response=_json_safe(resp),
            )
            raw_text = (resp.text or "").strip()

        trace_list = config.get("configurable", {}).get("trace_list")
        if trace_list is not None:
            trace_list.append({"tool": "predict_2d_points", "response": raw_text})

        cleaned = raw_text
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE).strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            m = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if not m: return []
            try: parsed = json.loads(m.group(0))
            except json.JSONDecodeError: return []
        if not isinstance(parsed, list): return []

        # Lift each point to 3D via small-patch averaging of pts3d_world.
        dense = _load_dense(scene_id, point_cloud_source=source_key)
        if dense is None:
            results = []
            for entry in parsed:
                point = entry.get("point") if isinstance(entry, dict) else None
                if not isinstance(point, list) or len(point) != 2: continue
                try:
                    y_scaled, x_scaled = float(point[0]), float(point[1])
                except Exception:
                    continue
                results.append({
                    "pixel_norm": [round(x_scaled / 1000.0, 4), round(y_scaled / 1000.0, 4)],
                    "world": None,
                    "label": entry.get("label", "") if isinstance(entry, dict) else "",
                    "point_cloud_source": source_key,
                })
            with _POINTS_VLM_LOCK:
                _POINTS_VLM_CACHE[cache_key] = results
            return results

        try:
            arr_idx = frame_index - 1
            pts3d = dense["pts3d_world"][arr_idx]   # (H, W, 3)
            mask  = dense["mask"][arr_idx]           # (H, W)
        except Exception as e:
            return [{"error": f"Dense lookup failed: {e}"}]

        H, W = pts3d.shape[:2]
        # Half-patch ≈ 0.7% of the image side — total ≈0.02% of pixels, ≈25 px on a 392×518 frame.
        half_patch_w = max(2, int(W * 0.03))
        half_patch_h = max(2, int(H * 0.03))

        results = []
        for entry in parsed:
            point = entry.get("point") if isinstance(entry, dict) else None
            if not isinstance(point, list) or len(point) != 2:
                continue
            try:
                y_scaled, x_scaled = float(point[0]), float(point[1])
            except Exception:
                continue
            x_norm = max(0.0, min(1.0, x_scaled / 1000.0))
            y_norm = max(0.0, min(1.0, y_scaled / 1000.0))
            px = int(round(x_norm * (W - 1)))
            py = int(round(y_norm * (H - 1)))
            x0 = max(0, px - half_patch_w);  x1 = min(W, px + half_patch_w + 1)
            y0 = max(0, py - half_patch_h);  y1 = min(H, py + half_patch_h + 1)
            patch_pts  = pts3d[y0:y1, x0:x1].reshape(-1, 3)
            patch_mask = mask[y0:y1, x0:x1].reshape(-1)
            valid = patch_pts[patch_mask]
            world = None
            if len(valid) >= 3:
                world = [round(float(v), 4) for v in valid.mean(axis=0)]
            results.append({
                "pixel_norm": [round(x_norm, 4), round(y_norm, 4)],
                "world":      world,
                "label":      entry.get("label", "") if isinstance(entry, dict) else "",
                "point_cloud_source": source_key,
            })
        if _DG_GATE:
            # DG-GATE (r214): flag implausible lifted points (sub-floor /
            # near-world-origin) so the planner re-grounds instead of consuming
            # a depth-bleed artifact. Deterministic — safe to cache below.
            _dg_floor = _dg_scene_floor_z(scene_id, dense)
            for _r in results:
                if _r.get("world") is None:
                    continue
                _fl = _dg_flags(centroid=_r["world"], floor_z=_dg_floor)
                if _fl:
                    _r["low_confidence"] = True
                    _r["flags"] = _fl
                    _r["instruction"] = _DG_INSTRUCTION
        with _POINTS_VLM_LOCK:
            _POINTS_VLM_CACHE[cache_key] = results
        return results
    except Exception as e:
        return [{"error": str(e)}]


# ─────────────────────────────────────────────────────────────────────────────
# Dense geometry tools (pure math — no VLM)
# ─────────────────────────────────────────────────────────────────────────────

@tool
def get_world_3d_point_from_2d(scene_id: str, frame_index: int, x_norm: float, y_norm: float,
                               config: RunnableConfig,
                               point_cloud_source: str = POINT_CLOUD_DEFAULT_SOURCE) -> list:
    """
    Directly looks up the world-frame 3D coordinates of a normalized 2D pixel using
    the selected dense pts3d_world output. This is a pure table-lookup — no VLM, no math.

    WORLD COORDINATE SYSTEM: floor = XY plane, Z = up (vertical height).

    Use this as the primary way to get 3D positions. It is more accurate than
    backprojecting depth and applying a pose transform because pts3d_world is the
    direct output of the 3D reconstruction model.

    Args:
        scene_id: VSIBench scene identifier.
        frame_index: 1-based frame number (1–32).
        x_norm: Normalized x pixel coordinate [0, 1], where 0 = left edge.
        y_norm: Normalized y pixel coordinate [0, 1], where 0 = top edge.
        point_cloud_source: Optional source. Default "g3t_scaled" is the same
            for every question. Valid sources/tradeoffs: g3t_scaled = metric-scale
            and gravity-oriented default; mapanything = stable layout fallback;
            unik3d = metric depth-oriented alternative. Choose explicitly
            inside the trace; do not depend on category/GT pre-routing.

    Returns:
        [X, Y, Z] in world coordinates (meters), or ["Error: ..."] on failure.
        Also returns {"valid": false} if the pixel falls on an occluded/edge region.
    """
    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError as e:
        return [f"Error: {e}"]
    dense = _load_dense(scene_id, point_cloud_source=source_key)
    if dense is None:
        return [f"Error: Dense outputs not found for scene {scene_id}. Run extract_mapanything_poses_vsibench.py first."]

    npz_idx = _frame_index_to_npz_idx(scene_id, frame_index, dense)
    if npz_idx is None:
        return [f"Error: Could not map frame_index={frame_index} for scene {scene_id}."]

    pts3d = dense["pts3d_world"][npz_idx]  # (H, W, 3)
    mask  = dense["mask"][npz_idx]          # (H, W) bool
    H, W, _ = pts3d.shape

    px = max(0, min(W - 1, int(x_norm * W)))
    py = max(0, min(H - 1, int(y_norm * H)))

    if not mask[py, px]:
        # Pixel is on an occluded or depth-edge region — try nearby valid pixel
        ys, xs = np.where(mask)
        if len(ys) == 0:
            return ["Error: No valid pixels in this frame."]
        dists = (ys - py) ** 2 + (xs - px) ** 2
        nearest = np.argmin(dists)
        py, px = int(ys[nearest]), int(xs[nearest])

    point = pts3d[py, px]
    result = [round(float(v), 4) for v in point]

    trace_list = config.get("configurable", {}).get("trace_list")
    if trace_list is not None:
        trace_list.append({"tool": "get_world_3d_point_from_2d",
                           "response": str({"point": result, "point_cloud_source": source_key})})
    return result


@tool
def get_3d_points_in_bbox(scene_id: str, frame_index: int, xmin: float, ymin: float, xmax: float, ymax: float,
                          config: RunnableConfig,
                          z_min: float | None = None, z_max: float | None = None,
                          point_cloud_source: str = POINT_CLOUD_DEFAULT_SOURCE) -> dict:
    """
    Extracts all dense world-frame 3D points from the selected point cloud source
    that fall within a 2D bounding box region.
    Filters to only valid (non-occluded) pixels using the confidence mask. Optional
    Z-range filter lets you slice horizontal slabs (e.g. the floor) without changing
    the 2D bbox.

    Use this tool for:
    - 3D extent of all points inside a 2D bbox (object footprint)
    - Floor / horizontal-slab analysis (call with bbox=(0,0,1,1) and z_min/z_max
      to restrict to a specific Z range, e.g. just the floor slab)
    - Any task where you need the spatial extent of a region, not just a centroid

    This is a pure lookup — no VLM, no estimation.

    Args:
        scene_id: VSIBench scene identifier.
        frame_index: 1-based frame number (1–32).
        xmin, ymin, xmax, ymax: Normalized [0,1] bounding box (output of predict_2d_bounding_box).
        z_min: Optional lower Z bound (meters, world-space). Points with Z < z_min are discarded.
        z_max: Optional upper Z bound (meters, world-space). Points with Z > z_max are discarded.
               Use this pair to restrict to horizontal slabs, e.g. the floor slab is
               typically Z ∈ [floor_z − 0.1, floor_z + 0.5]; use `floor_z_estimate` from
               the default return to set these bounds.
        point_cloud_source: Optional source. Default "g3t_scaled" is the same
               for every question. Valid sources/tradeoffs: g3t_scaled = metric-scale
               and gravity-oriented default; mapanything = stable layout fallback;
               unik3d = metric depth-oriented alternative. Choose explicitly
               inside the trace; do not depend on category/GT pre-routing.

    Returns:
        dict with keys:
            "centroid": [X, Y, Z] — median world position of all points in region (meters)
            "extent_xyz_p90":  [dx, dy, dz] — robust extent (p95−p5 per axis) in meters.
                                Raw (max−min) extent is not returned because it inflates from
                                wall/ceiling/floor depth bleeding into 2D bboxes.
            "min_xyz_p5":      [Xp5,  Yp5,  Zp5]  — 5th-percentile corner (robust lower bound)
            "max_xyz_p95":     [Xp95, Yp95, Zp95] — 95th-percentile corner (robust upper bound)
            "floor_z_estimate": float — 5th percentile of Z in the unfiltered region (meters).
                                Pass to z_min/z_max on a follow-up call to slice floor points.
            "num_valid_points": int — number of valid points used (after filters)
        Returns {"error": "..."} on failure.
    """

    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError as e:
        return {"error": str(e)}
    dense = _load_dense(scene_id, point_cloud_source=source_key)
    if dense is None:
        return {"error": f"Dense outputs not found for scene {scene_id}."}

    npz_idx = _frame_index_to_npz_idx(scene_id, frame_index, dense)
    if npz_idx is None:
        return {"error": f"Could not map frame_index={frame_index} for scene {scene_id}."}

    pts3d = dense["pts3d_world"][npz_idx]   # (H, W, 3)
    mask  = dense["mask"][npz_idx]           # (H, W) bool
    H, W, _ = pts3d.shape

    px_min = max(0, int(xmin * W))
    px_max = min(W - 1, int(xmax * W))
    py_min = max(0, int(ymin * H))
    py_max = min(H - 1, int(ymax * H))

    region_pts   = pts3d[py_min:py_max+1, px_min:px_max+1, :]  # (h, w, 3)
    region_mask  = mask[py_min:py_max+1, px_min:px_max+1]      # (h, w)

    valid_pts_unfiltered = region_pts[region_mask]  # (N, 3) — pre-Z-filter
    if len(valid_pts_unfiltered) == 0:
        return {"error": "No valid 3D points in the specified bbox region."}

    # floor_z_estimate is computed on the unfiltered set so it is stable regardless of the Z filter.
    floor_z_estimate = float(np.percentile(valid_pts_unfiltered[:, 2], 5))

    valid_pts = valid_pts_unfiltered
    _floor_clip = _scene_floor_clip_z(scene_id, dense) if _FLOOR_REL_Z else -0.05
    above_floor_abs = valid_pts[:, 2] >= _floor_clip
    valid_pts = valid_pts[above_floor_abs] if above_floor_abs.any() else valid_pts
    if z_min is not None:
        keep = valid_pts[:, 2] >= z_min
        if keep.any(): valid_pts = valid_pts[keep]
    if z_max is not None:
        keep = valid_pts[:, 2] <= z_max
        if keep.any(): valid_pts = valid_pts[keep]
    if len(valid_pts) == 0:
        return {"error": "No valid 3D points survived the Z filter.",
                "floor_z_estimate": round(floor_z_estimate, 4)}

    if _G1_GATE:
        valid_pts = _g1_trim_2sigma(valid_pts)

    centroid    = np.median(valid_pts, axis=0)
    p5_xyz      = np.percentile(valid_pts, 5,  axis=0)
    p95_xyz     = np.percentile(valid_pts, 95, axis=0)
    extent_p90  = p95_xyz - p5_xyz

    result = {
        "centroid":             [round(float(v), 4) for v in centroid],
        "extent_xyz_p90":       [round(float(v), 4) for v in extent_p90],
        "min_xyz_p5":           [round(float(v), 4) for v in p5_xyz],
        "max_xyz_p95":          [round(float(v), 4) for v in p95_xyz],
        "floor_z_estimate":     round(floor_z_estimate, 4),
        "num_valid_points":     int(len(valid_pts)),
        "point_cloud_source":   source_key,
    }
    if _G1_GATE:
        _bbox_area_norm = max(0.0, (xmax - xmin)) * max(0.0, (ymax - ymin))
        _edges = int(xmin <= 0.01) + int(xmax >= 0.99) + int(ymin <= 0.01) + int(ymax >= 0.99)
        _deg, _why = _g1_flags(area_norm=_bbox_area_norm, edges_touched=_edges,
                               n_points=int(len(valid_pts)), extent_p90=extent_p90,
                               centroid_z=float(centroid[2]),
                               floor_z=float(floor_z_estimate))
        result["degenerate"] = _deg
        if _deg:
            result["degenerate_reasons"] = _why
    if _DG_GATE:
        bbox_area = max(0.0, (xmax - xmin)) * max(0.0, (ymax - ymin))
        edges_touched = ((xmin <= 0.02) + (xmax >= 0.98)
                         + (ymin <= 0.02) + (ymax >= 0.98))
        # DG-GATE (r214): consolidated low-confidence verdict (reuses the
        # bbox_area / edges_touched already computed for bbox_quality_warning).
        _dg_apply(result, _dg_flags(
            area_norm=bbox_area, edges_touched=int(edges_touched),
            n_points=int(len(valid_pts)),
            centroid=[float(v) for v in centroid],
            floor_z=_dg_scene_floor_z(scene_id, dense)))
    trace_list = config.get("configurable", {}).get("trace_list")
    if trace_list is not None:
        trace_list.append({"tool": "get_3d_points_in_bbox", "response": str(result)})
    return result


@tool
def get_3d_points_in_mask(scene_id: str, frame_index: int, mask_dense_handle: str,
                          config: RunnableConfig,
                          z_min: float | None = None, z_max: float | None = None,
                          erode_iters: int = 0,
                          point_cloud_source: str = POINT_CLOUD_DEFAULT_SOURCE) -> dict:
    """
    r126: same return shape as `get_3d_points_in_bbox`, but the input region is
    a binary mask (the dense-resampled mask emitted by `predict_2d_segmentation_masks`'s
    `mask_dense_handle`) instead of a 2D bbox. This collapses the otherwise-required
    ~5 lines of `np.load(handle); pts = pts3d[mask]; ...` boilerplate inside
    `execute_python_code` into a single tool call, and gives the magnitude verifier
    a per-cluster physical extent to inspect.

    Use this whenever you have a SAM 3 instance mask and want the same 3D summary
    you'd otherwise get from `get_3d_points_in_bbox` — but tighter, because the
    mask follows the object silhouette rather than its bounding rectangle, so wall
    / ceiling / floor depth bleed is dramatically reduced.

    Args:
        scene_id: VSIBench scene identifier.
        frame_index: 1-based frame number (1-32). Must be the same frame the mask
            was generated from.
        mask_dense_handle: absolute path to the (392, 518) bool .npy emitted as
            `mask_dense_handle` by `predict_2d_segmentation_masks`. Must match the
            scene's `pts3d_world` shape.
        z_min, z_max: Optional Z filter (meters, world-space). Same semantics as
            `get_3d_points_in_bbox`.
        erode_iters: r133 — pixels to erode the mask boundary before lifting to
            3D. Boundary pixels suffer depth bleed (their `pts3d_world` value
            interpolates between object surface and background), which inflates
            the AABB outward (extent over-estimate) AND biases the centroid
            toward background by ~0.2-0.5 m. Recommended: 1-2 px when you need
            a faithful object perimeter/extent (light erosion preserves real
            surface); 2-3 px when you only need a clean centroid and not the
            perimeter. 0 keeps the un-eroded mask. Default 0 preserves
            r126-r132 semantics for backward compatibility, but most uses
            benefit from erode_iters >= 1. Falls back to un-eroded if erosion
            would leave fewer than 25 pixels.
        point_cloud_source: Optional source. Default "g3t_scaled" is the same
            for every question. Valid sources/tradeoffs: g3t_scaled = metric-scale
            and gravity-oriented default; mapanything = stable layout fallback;
            unik3d = metric depth-oriented alternative. Choose explicitly
            inside the trace; do not depend on category/GT pre-routing. If a
            SAM mask was dense-resampled for a different grid, this tool will
            re-resample the original image-space mask to the selected source
            when needed.

    Returns:
        dict — same keys as `get_3d_points_in_bbox`:
            "centroid", "extent_xyz_p90", "min_xyz_p5", "max_xyz_p95",
            "floor_z_estimate", "num_valid_points", "mask_quality_warning"
        `mask_quality_warning` is set when the mask covers < 100 pixels (tiny
        instance, likely a fragment) or when np.load fails to read the handle.
        Returns {"error": "..."} on failure.

    Pure perception/geometry primitive — no VLM, no estimation.
    """
    if not isinstance(mask_dense_handle, str) or not mask_dense_handle:
        return {"error": "mask_dense_handle must be a non-empty path string"}
    if not os.path.exists(mask_dense_handle):
        return {"error": f"mask_dense_handle file not found: {mask_dense_handle}"}

    try:
        mask = np.load(mask_dense_handle)
    except Exception as e:
        return {"error": f"failed to load mask: {type(e).__name__}: {e}"}
    if mask.dtype != bool:
        mask = mask.astype(bool)

    if erode_iters and erode_iters > 0:
        try:
            from scipy.ndimage import binary_erosion
            eroded = binary_erosion(mask, iterations=int(erode_iters))
            if eroded.sum() >= 25:
                mask = eroded
        except Exception:
            pass

    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError as e:
        return {"error": str(e)}
    dense = _load_dense(scene_id, point_cloud_source=source_key)
    if dense is None:
        return {"error": f"Dense outputs not found for scene {scene_id}."}

    npz_idx = _frame_index_to_npz_idx(scene_id, frame_index, dense)
    if npz_idx is None:
        return {"error": f"Could not map frame_index={frame_index} for scene {scene_id}."}

    pts3d = dense["pts3d_world"][npz_idx]   # (H, W, 3)
    valid = dense["mask"][npz_idx]           # (H, W) bool — confidence mask

    if mask.shape != pts3d.shape[:2]:
        # r192: SAM3 masks are occasionally off by a few px from the dense grid
        # (e.g. 392 vs 390) — center-crop/pad to the dense dims instead of discarding
        # the whole measurement (err-analysis size qids 180,489,3244,3527). Only
        # hard-error on a gross mismatch (>8 px), which signals the wrong handle.
        mh, mw = mask.shape; ph, pw = pts3d.shape[:2]
        if abs(mh - ph) <= 8 and abs(mw - pw) <= 8:
            _fixed = np.zeros((ph, pw), dtype=bool)
            _ch, _cw = min(mh, ph), min(mw, pw)
            _fixed[:_ch, :_cw] = mask[:_ch, :_cw]
            mask = _fixed
        else:
            # MG-1 (r208): a gross mismatch usually means the dense mask was
            # resampled to the legacy hardcoded grid while this scene's npz is
            # portrait (G3T 518x390 etc.). Recover by re-resampling the ORIGINAL
            # image-space mask to the actual npz grid (NEAREST) — never transpose
            # (risks silent 90-degree content rotation). Hard-error only if the
            # original mask is gone.
            recovered = None
            if mask_dense_handle.endswith("_dense.npy"):
                _orig = mask_dense_handle[:-len("_dense.npy")] + ".npy"
                if os.path.exists(_orig):
                    try:
                        from PIL import Image
                        _om = np.load(_orig)
                        _im = Image.fromarray((_om.astype(np.uint8) * 255))
                        _im = _im.resize((pw, ph), resample=Image.NEAREST)
                        recovered = np.asarray(_im) > 127
                        if erode_iters and erode_iters > 0:
                            try:
                                from scipy.ndimage import binary_erosion
                                _er = binary_erosion(recovered, iterations=int(erode_iters))
                                if _er.sum() >= 25:
                                    recovered = _er
                            except Exception:
                                pass
                    except Exception:
                        recovered = None
            if recovered is None:
                return {"error": (f"mask shape {mask.shape} does not match pts3d_world "
                                  f"{pts3d.shape[:2]} — pass `mask_dense_handle`, not "
                                  f"`mask_handle`, to this tool")}
            mask = recovered

    region_mask = mask & valid
    n_pixels = int(mask.sum())
    mask_quality_warning = None
    if n_pixels < 100:
        mask_quality_warning = (f"mask covers only {n_pixels} pixels — likely a "
                                f"fragment, treat extents as low-confidence")

    valid_pts_unfiltered = pts3d[region_mask]
    if len(valid_pts_unfiltered) == 0:
        return {"error": "No valid 3D points under the mask (mask + confidence "
                         "intersection is empty)."}

    floor_z_estimate = float(np.percentile(valid_pts_unfiltered[:, 2], 5))

    valid_pts = valid_pts_unfiltered
    _floor_clip = _scene_floor_clip_z(scene_id, dense) if _FLOOR_REL_Z else -0.05
    above_floor_abs = valid_pts[:, 2] >= _floor_clip
    valid_pts = valid_pts[above_floor_abs] if above_floor_abs.any() else valid_pts
    if z_min is not None:
        keep = valid_pts[:, 2] >= z_min
        if keep.any(): valid_pts = valid_pts[keep]
    if z_max is not None:
        keep = valid_pts[:, 2] <= z_max
        if keep.any(): valid_pts = valid_pts[keep]
    if len(valid_pts) == 0:
        return {"error": "No valid 3D points survived the Z filter.",
                "floor_z_estimate": round(floor_z_estimate, 4)}

    if _G1_GATE:
        valid_pts = _g1_trim_2sigma(valid_pts)

    centroid    = np.median(valid_pts, axis=0)
    p5_xyz      = np.percentile(valid_pts, 5,  axis=0)
    p95_xyz     = np.percentile(valid_pts, 95, axis=0)
    extent_p90  = p95_xyz - p5_xyz

    result = {
        "centroid":             [round(float(v), 4) for v in centroid],
        "extent_xyz_p90":       [round(float(v), 4) for v in extent_p90],
        "min_xyz_p5":           [round(float(v), 4) for v in p5_xyz],
        "max_xyz_p95":          [round(float(v), 4) for v in p95_xyz],
        "floor_z_estimate":     round(floor_z_estimate, 4),
        "num_valid_points":     int(len(valid_pts)),
        "mask_quality_warning": mask_quality_warning,
        "point_cloud_source":   source_key,
    }
    if _G1_GATE:
        _mh, _mw = mask.shape
        _area_norm = float(mask.sum()) / float(max(1, _mh * _mw))
        _edges = (int(mask[0, :].any()) + int(mask[-1, :].any())
                  + int(mask[:, 0].any()) + int(mask[:, -1].any()))
        _deg, _why = _g1_flags(area_norm=_area_norm, edges_touched=_edges,
                               n_points=int(len(valid_pts)), extent_p90=extent_p90,
                               centroid_z=float(centroid[2]),
                               floor_z=float(floor_z_estimate))
        result["degenerate"] = _deg
        if _deg:
            result["degenerate_reasons"] = _why
    if _DG_GATE:
        # DG-GATE (r214): consolidated low-confidence verdict. The mask score
        # is not visible at this site (only the handle is passed), so the
        # score<0.70 signal lives on the segmentation tools' instance outputs.
        _dg_mh, _dg_mw = mask.shape
        _dg_apply(result, _dg_flags(
            area_norm=float(mask.sum()) / float(max(1, _dg_mh * _dg_mw)),
            edges_touched=(int(mask[0, :].any()) + int(mask[-1, :].any())
                           + int(mask[:, 0].any()) + int(mask[:, -1].any())),
            n_points=int(len(valid_pts)),
            centroid=[float(v) for v in centroid],
            floor_z=_dg_scene_floor_z(scene_id, dense)))
    trace_list = config.get("configurable", {}).get("trace_list")
    if trace_list is not None:
        trace_list.append({"tool": "get_3d_points_in_mask", "response": str(result)})
    return result


# ─────────────────────────────────────────────────────────────────────────────
# r108: CuTR 3D-bbox catalogue + SAM 3 segmentation
# ─────────────────────────────────────────────────────────────────────────────

def _cutr_world_centers(cutr: dict, dense: dict, det_indices: np.ndarray | None = None
                        ) -> np.ndarray:
    """
    r108: world-frame 3D centers for CuTR detections. CuTR boxes_3d_center is in
    camera frame; the per-detection frame position indexes into MapAnything's
    camera_poses so we can apply the cam2world transform.

    Returns (M, 3) float32, where M = len(det_indices) if provided, else total
    detections in this scene.
    """
    fpos = cutr["boxes_3d_frame_idx"].astype(np.int64)            # (M_total,)
    centers_cam = cutr["boxes_3d_center"].astype(np.float32)      # (M_total, 3)
    poses = dense["camera_poses"].astype(np.float32)              # (N, 4, 4)
    if det_indices is None:
        idx = np.arange(centers_cam.shape[0])
    else:
        idx = np.asarray(det_indices, dtype=np.int64)
    fp = fpos[idx]
    c = centers_cam[idx]
    homo = np.concatenate([c, np.ones((c.shape[0], 1), dtype=np.float32)], axis=1)  # (M, 4)
    Ts = poses[fp]                                                  # (M, 4, 4)
    world = np.einsum("mij,mj->mi", Ts, homo)[:, :3]                # (M, 3)
    return world.astype(np.float32)


@tool
def query_3d_bbox_catalogue(scene_id: str, frame_index: int | None = None,
                            score_min: float = 0.3,
                            config: RunnableConfig = None) -> dict:
    """
    r108: pure offline lookup into the per-scene CuTR 3D-bbox catalogue. No
    inference, no GPU. Returns class-agnostic 3D bbox proposals already
    transformed to world Z-up via MapAnything camera poses.

    CuTR is class-agnostic — there is NO label filtering inside this tool.
    Filter by label downstream (e.g. via the SAM3 IoU match in
    `count_object_instances_via_masks_and_3d_iou`) or by score.

    Args:
        scene_id: VSIBench scene identifier.
        frame_index: Optional 1-based agent frame index (1..32). When set,
                     restrict to detections in that frame; otherwise return
                     all detections across all frames in the scene.
        score_min: Drop detections below this CuTR confidence (default 0.3,
                   the threshold the catalogue was filtered at).

    Returns:
        dict with:
          "n_dets":                  int — number of detections returned
          "scores":                  list[float]
          "boxes_2d":                list[[x0,y0,x1,y1]] — image pixels
          "boxes_3d_center_world":   list[[X,Y,Z]] — world Z-up
          "boxes_3d_size":           list[[L,H,W]] — extent in metres
          "frame_indices":           list[int] — original video frame index per det
          "object_desc":             list[list[float]] — 256-dim float embeddings
        Returns {"error": "..."} on failure.
    """
    cutr = _load_cutr(scene_id)
    if cutr is None:
        return {"error": f"CuTR catalogue missing for scene {scene_id}"}
    dense = _load_dense(scene_id)
    if dense is None:
        return {"error": f"MapAnything dense outputs missing for scene {scene_id}; cannot world-align CuTR centers"}

    fpos_all = cutr["boxes_3d_frame_idx"].astype(np.int64)
    scores_all = cutr["scores"].astype(np.float32)

    if frame_index is None:
        keep = scores_all >= float(score_min)
    else:
        # Map agent's 1-based frame_index → original video frame index.
        cache = _load_frames_cache()
        if not cache or scene_id not in cache:
            return {"error": f"Selected-frames cache missing scene {scene_id}"}
        sel = cache[scene_id]["indices"]
        if not (1 <= frame_index <= len(sel)):
            return {"error": f"frame_index {frame_index} out of range (1..{len(sel)})"}
        video_frame_idx = int(sel[frame_index - 1])
        # Find CuTR's positional index of this video frame
        cutr_frame_idx = np.where(cutr["frame_indices"] == video_frame_idx)[0]
        if len(cutr_frame_idx) == 0:
            return {"n_dets": 0, "scores": [], "boxes_2d": [],
                    "boxes_3d_center_world": [], "boxes_3d_size": [],
                    "frame_indices": [], "object_desc": []}
        fp_target = int(cutr_frame_idx[0])
        keep = (fpos_all == fp_target) & (scores_all >= float(score_min))

    keep_idx = np.where(keep)[0]
    if len(keep_idx) == 0:
        result = {"n_dets": 0, "scores": [], "boxes_2d": [],
                  "boxes_3d_center_world": [], "boxes_3d_size": [],
                  "frame_indices": []}
    else:
        # Cap to top-K by score to prevent context overflow. Scene-wide
        # queries can return 600-1000+ detections; with the (now-removed)
        # object_desc field that was 1.3-2.6 MB JSON, blowing the 1M-token
        # context limit and causing fatal pred=null. Top-K-by-score keeps
        # the highest-confidence detections, which is what downstream
        # label-matching code wants anyway.
        SCENE_TOP_K = 50
        FRAME_TOP_K = 25
        top_k = FRAME_TOP_K if frame_index is not None else SCENE_TOP_K
        if len(keep_idx) > top_k:
            top_order = np.argsort(scores_all[keep_idx])[::-1][:top_k]
            keep_idx = keep_idx[top_order]
        centers_world = _cutr_world_centers(cutr, dense, keep_idx)
        sizes = cutr["boxes_3d_size"][keep_idx].astype(np.float32)
        boxes2d = cutr["boxes_2d"][keep_idx].astype(np.float32)
        # Map back to original video frame indices for clarity
        det_fpos = fpos_all[keep_idx]
        orig_frames = cutr["frame_indices"][det_fpos].astype(np.int64)
        # NOTE r115: object_desc dropped from default return. Three subagents
        # flagged the 256-dim float arrays as the dominant cause of context
        # overflow on counting/size questions. Downstream label-matching uses
        # boxes_2d for SAM3 IoU, not embeddings.
        result = {
            "n_dets": int(len(keep_idx)),
            "scores": [round(float(s), 4) for s in scores_all[keep_idx].tolist()],
            "boxes_2d": [[round(float(v), 2) for v in row] for row in boxes2d.tolist()],
            "boxes_3d_center_world": [[round(float(v), 4) for v in row] for row in centers_world.tolist()],
            "boxes_3d_size": [[round(float(v), 4) for v in row] for row in sizes.tolist()],
            "frame_indices": [int(v) for v in orig_frames.tolist()],
        }

    if config is not None:
        trace_list = config.get("configurable", {}).get("trace_list")
        if trace_list is not None:
            trace_list.append({"tool": "query_3d_bbox_catalogue",
                               "response": f"n_dets={result.get('n_dets', 0)}"})
    return result


SAM3_ROUTER_URL = "http://127.0.0.1:8772/segment"


def _run_sam3_request(scene_id: str, frame_index: int, label: str,
                      mask_dir: str, score_thresh: float = 0.3) -> dict:
    """
    r123: replaces the per-call subprocess pattern (`_run_sam3_subprocess`,
    kept below for historical reference) with a POST to the persistent
    SAM3 router on localhost:8769. The router fan-outs across 10 daemons
    pre-loaded with SAM3 weights (~50 s cold start at sidecar bringup,
    p50 1.16s per call thereafter — vs ~50s subprocess cold-load).

    Sidecar must be running before this is invoked. The launcher
    `agent/sam3_launcher.sh` brings it up; `agent/sam3_teardown.sh`
    tears it down. Worker scripts assume the sidecar is already up;
    the orchestrator script handles bringup/teardown via launcher
    BEFORE the parallel-worker for-loop and teardown AFTER `wait`.

    The caller supplies an arm-root-confined `mask_dir`. Returned handles are
    checked because the pinned router/daemon caches do not key on mask_dir;
    an off-root cache hit is re-materialized under the current arm root.
    """
    # The daemon opens the source video in another process.  Bind that
    # consumption before sending the request, so arbitrary scene IDs never
    # reach the unrestricted daemon resolver.
    _r740_record_registered_access("source_videos", scene_id)
    import urllib.request, urllib.error
    confined_mask_dir = _require_arm_mask_dir(mask_dir)
    body = {
        "scene": scene_id, "frame_index": int(frame_index),
        "label": str(label), "score_thresh": float(score_thresh),
        "mask_dir": confined_mask_dir,
    }
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        SAM3_ROUTER_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with custody_effect(urllib.request.urlopen, req, timeout=30) as resp:
            return _confine_sam3_payload(
                json.loads(resp.read().decode()), confined_mask_dir,
            )
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read().decode())
        except Exception: return {"error": f"router HTTP {e.code}"}
    except Exception as e:
        return {"error": f"router request failed ({type(e).__name__}: {e})"}


def _run_sam3_subprocess(scene_id: str, frame_index: int, label: str,
                        score_thresh: float = 0.3,
                        device: str = SAM3_DEFAULT_DEVICE) -> dict:
    """
    Spawn the SAM3 service in its own env, capture the JSON payload, return it.
    Mask binary blobs are saved as .npy files under SAM3_TMP_ROOT and only
    referenced by path in the returned dict.
    """
    import subprocess
    import tempfile

    safe_label = re.sub(r"[^A-Za-z0-9_-]", "_", label.strip())[:64] or "label"
    out_dir = os.path.join(SAM3_TMP_ROOT, f"{scene_id}_f{frame_index}_{safe_label}")
    os.makedirs(out_dir, exist_ok=True)
    out_json = os.path.join(out_dir, "out.json")
    mask_dir = os.path.join(out_dir, "masks")

    cmd = [
        SAM3_PYTHON, SAM3_SERVICE,
        "--scene", scene_id,
        "--frame_index", str(int(frame_index)),
        "--label", str(label),
        "--out", out_json,
        "--mask_dir", mask_dir,
        "--score_thresh", str(float(score_thresh)),
        "--device", device,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired as e:
        return {"error": f"sam3 subprocess timeout: {e}"}
    except Exception as e:
        return {"error": f"sam3 subprocess launch failed: {e}"}
    if proc.returncode != 0:
        return {
            "error": f"sam3 subprocess exit {proc.returncode}",
            "stderr": (proc.stderr or "")[-1000:],
        }
    if not os.path.exists(out_json):
        return {"error": "sam3 subprocess produced no output JSON",
                "stderr": (proc.stderr or "")[-1000:]}
    try:
        with open(out_json) as f:
            payload = json.load(f)
    except Exception as e:
        return {"error": f"sam3 output JSON parse failed: {e}"}
    return payload


@tool
def predict_2d_segmentation_masks(scene_id: str, frame_index: int, object_label: str,
                                  config: RunnableConfig = None) -> list:
    """
    r108: SAM 3 text-prompted instance segmentation for a single frame. Returns
    one entry per detected instance with a tight 2D bbox, normalized area, and
    a path handle to the binary mask (saved to disk to keep mask blobs out of
    the LLM context).

    Use this whenever you need a per-instance pixel-accurate footprint of an
    object label — strictly more informative than a single bbox per object
    when same-label instances co-occur in the frame. SAM 3's text matching is
    fuzzy on synonyms, so try both the literal label and a close synonym if
    the first call returns empty (e.g. "trash bin" then "garbage can").

    Args:
        scene_id: VSIBench scene identifier.
        frame_index: 1-based frame number (1..32).
        object_label: Natural-language label, e.g. "bookshelf", "chair".

    Returns:
        list[dict] — one entry per kept instance:
          {"instance_id":        int,
           "score":               float,
           "bbox_pixels":         [x0, y0, x1, y1],
           "bbox_norm":           [x0, y0, x1, y1],   # / (W, H)
           "area_norm":           float,               # mask_area / (W*H)
           "mask_handle":         "<absolute .npy path>",  # bool (H_img,W_img)
           "mask_dense_handle":   "<absolute .npy path>",  # bool (392, 518)
                                                          # — same orientation
                                                          # as pts3d_world,
                                                          # safe to index
                                                          # `pts3d_world[i][mask]`
           "mask_dense_shape":    [392, 518],
          }
        Use `mask_dense_handle` when indexing the dense outputs from
        `load_dense` / `load_ransac_dense` (392×518). Use `mask_handle`
        only when overlaying on the raw image frame from `get_frame_image`.
        Returns [] if SAM 3 finds no instances.
        Returns [{"error": "..."}] on failure.

    Notes:
        - SAM 3 runs in a separate env via subprocess. First call per process
          incurs ~10–15 s of model load; subsequent calls are ~0.7 s + frame
          extraction. The mask binary lives on disk; only the path is echoed
          back to the agent. Use `np.load(mask_handle)` if downstream Python
          needs the mask.
        - Process-level cache keyed on (scene, frame_index, label) — repeat
          calls return cached results.
    """
    cache_key = (scene_id, int(frame_index), object_label.strip().lower())
    mask_dir = _sam3_mask_dir(
        scene_id, object_label, f"single_f{int(frame_index)}"
    )
    with _SAM3_LOCK:
        cached = _SAM3_CACHE.get(cache_key)
    if cached is not None:
        _r740_record_registered_access("source_videos", scene_id)
        try:
            cached = _confine_sam3_instances(cached, mask_dir)
        except Exception as exc:
            return [{"error": f"SAM3 cached mask confinement failed: {exc}"}]
        if config is not None:
            trace_list = config.get("configurable", {}).get("trace_list")
            if trace_list is not None:
                trace_list.append({"tool": "predict_2d_segmentation_masks",
                                   "response": f"<cache_hit n={len(cached)}>"})
        return cached

    payload = _run_sam3_request(
        scene_id, int(frame_index), object_label, mask_dir=mask_dir,
    )
    if isinstance(payload, dict) and "error" in payload:
        if config is not None:
            trace_list = config.get("configurable", {}).get("trace_list")
            if trace_list is not None:
                trace_list.append({"tool": "predict_2d_segmentation_masks",
                                   "response": f"ERROR: {payload}"})
        return [{"error": payload.get("error", "sam3 unknown failure"),
                 "stderr": payload.get("stderr", "")}]

    instances = payload.get("instances", []) or []

    # r125: resample each mask from SAM3's image shape (e.g. 480×640) down to
    # the dense pts3d_world shape (392×518) so callers can do
    # `pts3d_world[i][mask_dense]` without broadcast errors. We keep the
    # original `mask_handle` (image-space mask) for callers that overlay on
    # raw frames, and add a `mask_dense_handle` (dense-space mask) for those
    # that need to index `pts3d_world` / `depth_z` / `mask`. Counting and
    # rel_distance subagents (r124) traced multiple failures to this exact
    # shape mismatch where the agent wrote `pts3d[mask]` and got a silent
    # broadcast error.
    _DENSE_HW = _dense_grid_hw(scene_id)  # MG-1 (r208): actual per-scene npz grid, not hardcoded (392, 518)
    for inst in instances:
        if not isinstance(inst, dict):
            continue
        mh = inst.get("mask_handle")
        if not mh or not os.path.exists(mh):
            continue
        try:
            mask_img = np.load(mh)
        except Exception:
            continue

        # r128: image-edge truncation gate. When the binary mask touches the top
        # row or bottom row of the image, the object's vertical extent has been
        # clipped by the camera's field of view — extents derived from such a
        # mask systematically under-estimate (mask covers only what's visible)
        # OR over-estimate (depth-bleed onto wall/ceiling pixels included in
        # the clipped region). Surface a boolean flag so the agent / aggregator
        # can drop these frames.
        try:
            mh_top    = bool(mask_img.shape[0] > 0 and mask_img[0,    :].any())
            mh_bottom = bool(mask_img.shape[0] > 0 and mask_img[-1,   :].any())
            mh_left   = bool(mask_img.shape[1] > 0 and mask_img[:,    0].any())
            mh_right  = bool(mask_img.shape[1] > 0 and mask_img[:,   -1].any())
            edges_touched = int(mh_top) + int(mh_bottom) + int(mh_left) + int(mh_right)
            inst["mask_edges_touched"] = edges_touched
            if mh_top or mh_bottom:
                inst["mask_truncation_warning"] = (
                    f"mask touches image {'top' if mh_top else ''}"
                    f"{' and ' if (mh_top and mh_bottom) else ''}"
                    f"{'bottom' if mh_bottom else ''} edge — "
                    "vertical extent likely truncated; treat any Z-extent "
                    "derived from this frame as a lower bound and consider "
                    "dropping it. Horizontal/centroid-XY quantities are "
                    "unaffected."
                )
            else:
                inst["mask_truncation_warning"] = None
        except Exception:
            inst["mask_edges_touched"] = None
            inst["mask_truncation_warning"] = None

        try:
            from PIL import Image
            arr = (mask_img.astype(np.uint8) * 255)
            im = Image.fromarray(arr).resize((_DENSE_HW[1], _DENSE_HW[0]),
                                              resample=Image.NEAREST)
            mask_dense = (np.asarray(im) > 127).astype(bool)
            dense_path = mh[:-4] + "_dense.npy" if mh.endswith(".npy") else mh + "_dense.npy"
            np.save(dense_path, mask_dense)
            inst["mask_dense_handle"] = dense_path
            inst["mask_dense_shape"]  = list(_DENSE_HW)
        except Exception:
            # Resampling is a best-effort enrichment; do not fail the whole call.
            pass
    with _SAM3_LOCK:
        _SAM3_CACHE[cache_key] = instances

    if config is not None:
        trace_list = config.get("configurable", {}).get("trace_list")
        if trace_list is not None:
            trace_list.append({"tool": "predict_2d_segmentation_masks",
                               "response": f"n_kept={len(instances)} n_raw={payload.get('n_raw', '?')}"})
    return instances


# ---------- r134: SAM3 video tracking (cross-frame instance dedup) ----------

SAM3_VIDEO_ROUTER_URL = "http://127.0.0.1:8772/segment_video"


def _run_sam3_video_request(scene_id: str, frame_indices: list[int], label: str,
                            mask_dir: str, score_thresh: float = 0.3,
                            timeout: float = 240.0) -> dict:
    """r134: POST to /segment_video on the SAM3 router. Same retry/healthcheck
    contract as the per-frame route, but the daemon uses the SAM3 video model
    so instance_id is consistent across frames.
    """
    _r740_record_registered_access("source_videos", scene_id)
    import urllib.request, urllib.error
    confined_mask_dir = _require_arm_mask_dir(mask_dir)
    body = {
        "scene": scene_id,
        "frame_indices": [int(x) for x in frame_indices],
        "label": str(label),
        "score_thresh": float(score_thresh),
        "mask_dir": confined_mask_dir,
    }
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        SAM3_VIDEO_ROUTER_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with custody_effect(urllib.request.urlopen, req, timeout=timeout) as resp:
            return _confine_sam3_payload(
                json.loads(resp.read().decode()), confined_mask_dir, video=True,
            )
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read().decode())
        except Exception: return {"error": f"router HTTP {e.code}"}
    except Exception as e:
        return {"error": f"video router request failed ({type(e).__name__}: {e})"}


_SAM3_VIDEO_LOCK = threading.Lock()
_SAM3_VIDEO_CACHE: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
# STR-3 (r213, env STR3_ARBITER=1): deterministic co-visibility counting
# arbiter. Question-agnostic post-processing of SAM3 video-tracking geometry
# — surfaced as extra evidence fields on the
# predict_2d_segmentation_masks_video response, never a forced answer.
# ─────────────────────────────────────────────────────────────────────────────

_STR3_RULE = {"gd_ratio": 2.0, "lb_k": 3, "p_min": 2,
              "score_min": 0.5, "area_min": 0.0005, "ov_thresh": 0.5}


def _str3_disjoint_count(insts, area_min=0.0005, ov_thresh=0.5, score_min=0.5):
    """Max simultaneously-visible DISJOINT instances in one frame.

    Greedy by score; a detection is a new object only if its bbox overlap
    (intersection / min-area) with every kept detection is <= ov_thresh —
    catches nested/interpenetrating duplicate masks that plain IoU misses.
    Verbatim port of str3_offline_screen.disjoint_count."""
    cand = [i for i in insts if (i.get("area_norm") or 0) >= area_min
            and (i.get("score") or 0) >= score_min and i.get("bbox_pixels")]
    cand.sort(key=lambda i: -(i.get("score") or 0))
    kept = []
    for inst in cand:
        x0, y0, x1, y1 = inst["bbox_pixels"]
        a = max(0, x1 - x0) * max(0, y1 - y0)
        ok = True
        for kx0, ky0, kx1, ky1 in kept:
            ix = max(0, min(x1, kx1) - max(x0, kx0))
            iy = max(0, min(y1, ky1) - max(y0, ky0))
            ka = max(0, kx1 - kx0) * max(0, ky1 - ky0)
            mn = min(a, ka)
            if mn <= 0 or ix * iy / mn > ov_thresh:
                ok = False
                break
        if ok:
            kept.append((x0, y0, x1, y1))
    return len(kept)


def _str3_covis_arbitrate(baseline, frame_instance_lists, persistence_calls,
                          rule=_STR3_RULE):
    """Co-visibility arbiter (asymmetric robustness), port of
    str3_offline_screen.arbitrate with the winning rule.

    Args:
        baseline: the chosen aggregation count (int or None).
        frame_instance_lists: list of per-frame instance lists; each instance
            dict carries score / area_norm / bbox_pixels.
        persistence_calls: list of (persistence_dict, n_frames, union_count)
            — one entry per video-tracking call contributing evidence.

    Returns (arbitrated_count_or_None, inputs_dict):
        lb_gd = max single-frame disjoint count      (gate-down floor only —
                                                      raw max over-fires, so it
                                                      may never clamp UP)
        lb_up = lb_k-th highest frame disjoint count (clamp-up bound; needs the
                                                      co-visibility evidence in
                                                      >= lb_k frames)
        conf  = max(lb_gd, persistence-gated union)
        gate-down: baseline > gd_ratio * conf -> conf  (over-count arbitration)
        clamp-up:  final = max(final, lb_up)           (under-count arbitration)
    """
    counts = sorted((_str3_disjoint_count(insts, rule["area_min"],
                                          rule["ov_thresh"], rule["score_min"])
                     for insts in frame_instance_lists), reverse=True)
    lb_gd = counts[0] if counts else 0
    k = rule["lb_k"]
    lb_up = counts[k - 1] if len(counts) >= k else (counts[-1] if counts else 0)
    pu = 0
    for pers, n_frames, union in persistence_calls:
        if not pers:
            v = union or 0
        else:
            eff = rule["p_min"] if n_frames >= 2 * rule["p_min"] else 1
            v = sum(1 for x in pers.values() if x >= eff)
        pu = max(pu, v)
    conf = max(lb_gd, pu)
    inputs = {"baseline_count": baseline,
              "covis_lb_single_frame": lb_gd,
              "covis_lb_multiframe_k3": lb_up,
              "persistence_gated_union": pu}
    est = baseline if baseline is not None else (conf if conf > 0 else None)
    if est is None:
        return None, inputs
    if conf > 0 and est > rule["gd_ratio"] * conf:
        est = conf
    est = max(est, lb_up)
    return (est if est > 0 else None), inputs


# ─────────────────────────────────────────────────────────────────────────────
# APPEAR-EV (r213, env APPEAR_EVIDENCE=1): deterministic first-appearance
# telemetry per persistent tracked instance. It ships as planner-visible
# evidence fields on the predict_2d_segmentation_masks_video response and is
# computed over whatever frame_indices the call covered.
# ─────────────────────────────────────────────────────────────────────────────

def _appear_first_evidence(frames_out, score_min=0.4, area_min=0.0005,
                           min_persist=2):
    """Per-instance first qualifying frame + qualifying-frame count.

    Returns (rows, earliest): rows = [{instance_id, first_frame_index,
    n_frames_seen}] for instances with >= min_persist qualifying detections,
    sorted by first appearance; earliest = min first_frame_index (or None)."""
    items = []
    for f, insts in frames_out.items():
        try:
            items.append((int(f), insts))
        except Exception:
            continue
    persist: dict = {}
    first: dict = {}
    for f, insts in sorted(items):
        for det in insts:
            if ((det.get("score") or 0) >= score_min
                    and (det.get("area_norm") or 0) >= area_min):
                iid = det.get("instance_id")
                persist[iid] = persist.get(iid, 0) + 1
                if iid not in first:
                    first[iid] = f
    rows = sorted(({"instance_id": iid, "first_frame_index": first[iid],
                    "n_frames_seen": n}
                   for iid, n in persist.items() if n >= min_persist),
                  key=lambda r: (r["first_frame_index"], str(r["instance_id"])))
    earliest = rows[0]["first_frame_index"] if rows else None
    return rows, earliest


@tool
def predict_2d_segmentation_masks_video(scene_id: str, object_label: str,
                                        frame_indices: list[int],
                                        config: RunnableConfig = None) -> dict:
    """
    r134: SAM3 native video tracking across the listed frames. Returns
    per-frame instance masks where `instance_id` is CONSISTENT across frames —
    the same physical instance keeps the same id in every frame it appears.
    This solves the cross-frame instance-dedup problem without DBSCAN on 3D
    centroids (which suffers from multi-frame centroid scatter > inter-instance
    gap on tightly-packed scenes).

    Use this whenever you need cross-frame instance identity (e.g. to dedup the
    same physical object seen in many frames). For per-frame inspection
    (size/extent measurement), the per-frame `predict_2d_segmentation_masks` is
    still preferred.

    Args:
        scene_id: VSIBench scene identifier.
        object_label: Natural-language label, e.g. "chair", "backpack".
        frame_indices: list of 1-based frame numbers to track across (typically
            5-10 frames spanning the video; the tracker handles temporal
            coverage). Must be a non-empty list.

    Returns:
        dict — {
          "frames": {frame_index (int): [{
              "instance_id":        int,    # CONSISTENT across frames
              "score":              float,
              "bbox_pixels":        [x0, y0, x1, y1],
              "bbox_norm":          [x0, y0, x1, y1] / (W, H),
              "area_norm":          float,
              "mask_handle":        "<absolute .npy path>",   # bool (H_img, W_img)
              "mask_dense_handle":  "<absolute .npy path>",   # bool (392, 518)
              "mask_dense_shape":   [392, 518],
              "mask_pixel_count":   int,
              "mask_edges_touched": int (0..4),
              "mask_truncation_warning": str | None,
          }, ...]},
          "frame_size":           [W, H],
          "n_unique_instances":   int,            # union over all frames (OVER-counts under drift)
          "max_instances_in_any_frame": int,      # peak single-frame count (drift-immune)
          "instance_persistence": {inst_id: n_frames_seen},
          "score_thresh":         float,
        }

    Estimator properties (the two scene-level tallies bracket the truth from
    opposite sides):
        `max_instances_in_any_frame` is the PEAK number of distinct instances in a
        single frame — drift-immune and low-variance, but it UNDER-estimates when
        instances are spread out so no one frame shows them all at once.
        `n_unique_instances` is the cross-frame UNION of ids — it captures
        never-co-visible instances but OVER-estimates under tracker drift (drift
        mints a fresh id when it loses then re-acquires the same object).
        `instance_persistence` (frames-seen per id) lets
        you down-weight short-lived drift ids. Each instance's `mask_dense_handle`
        is already resampled to the `pts3d_world` (H,W) grid, so it can be indexed
        directly into the 3D points to place every detection in a common world frame.

    Cost: one call covers all listed frames at once (typically 10-30 s for 32
    frames), giving cross-frame instance identity directly.
    """
    if not isinstance(frame_indices, list) or not frame_indices:
        return {"error": "frame_indices must be a non-empty list of 1-based ints"}

    cache_key = (scene_id, object_label.strip().lower(),
                 tuple(int(x) for x in frame_indices))
    mask_dir = _sam3_mask_dir(
        scene_id, object_label,
        "video_" + hashlib.sha256(
            ",".join(str(int(x)) for x in frame_indices).encode()
        ).hexdigest()[:12],
    )
    with _SAM3_VIDEO_LOCK:
        cached = _SAM3_VIDEO_CACHE.get(cache_key)
    if cached is not None:
        _r740_record_registered_access("source_videos", scene_id)
        try:
            cached = _confine_sam3_payload(cached, mask_dir, video=True)
        except Exception as exc:
            return {"error": f"SAM3 cached mask confinement failed: {exc}"}
        if config is not None:
            trace_list = config.get("configurable", {}).get("trace_list")
            if trace_list is not None:
                trace_list.append({"tool": "predict_2d_segmentation_masks_video",
                                   "response": f"<cache_hit n_unique={cached.get('n_unique_instances', '?')}>"})
        return cached

    # Preserve SAM3 video behavior as shipped. Upstream applies its own
    # detector threshold internally; the daemon's returned scores are
    # probabilities, so 0.0 makes our downstream s<threshold test an
    # identity operation instead of a second confidence filter.
    payload = _run_sam3_video_request(
        scene_id, [int(x) for x in frame_indices], object_label,
        mask_dir=mask_dir,
        score_thresh=0.0,
    )
    if isinstance(payload, dict) and "error" in payload:
        if config is not None:
            trace_list = config.get("configurable", {}).get("trace_list")
            if trace_list is not None:
                trace_list.append({"tool": "predict_2d_segmentation_masks_video",
                                   "response": f"ERROR: {payload}"})
        return {"error": payload.get("error", "sam3 video unknown failure")}

    # Enrich each per-frame instance with mask_dense_handle + truncation flags,
    # mirroring the per-frame predict_2d_segmentation_masks tool so downstream
    # callers (get_3d_points_in_mask) work uniformly.
    _DENSE_HW = _dense_grid_hw(scene_id)  # MG-1 (r208): actual per-scene npz grid, not hardcoded (392, 518)
    frames_out = payload.get("frames", {}) or {}
    for fr_key, inst_list in list(frames_out.items()):
        # JSON dict keys come back as strings; normalize back to int.
        try:
            fr_int = int(fr_key)
        except Exception:
            continue
        if fr_key != fr_int:
            frames_out[fr_int] = inst_list
            del frames_out[fr_key]
        for inst in inst_list:
            mh = inst.get("mask_handle")
            if not mh or not os.path.exists(mh):
                continue
            try:
                mask_img = np.load(mh)
            except Exception:
                continue
            try:
                mh_top    = bool(mask_img.shape[0] > 0 and mask_img[0,    :].any())
                mh_bottom = bool(mask_img.shape[0] > 0 and mask_img[-1,   :].any())
                mh_left   = bool(mask_img.shape[1] > 0 and mask_img[:,    0].any())
                mh_right  = bool(mask_img.shape[1] > 0 and mask_img[:,   -1].any())
                edges_touched = int(mh_top) + int(mh_bottom) + int(mh_left) + int(mh_right)
                inst["mask_edges_touched"] = edges_touched
                inst["mask_truncation_warning"] = (
                    "vertical extent likely truncated (mask touches "
                    f"image {'top' if mh_top else 'bottom'} edge)"
                ) if (mh_top or mh_bottom) else None
            except Exception:
                inst["mask_edges_touched"] = None
                inst["mask_truncation_warning"] = None
            try:
                from PIL import Image
                arr = (mask_img.astype(np.uint8) * 255)
                im = Image.fromarray(arr).resize((_DENSE_HW[1], _DENSE_HW[0]),
                                                  resample=Image.NEAREST)
                mask_dense = (np.asarray(im) > 127).astype(bool)
                dense_path = mh[:-4] + "_dense.npy" if mh.endswith(".npy") else mh + "_dense.npy"
                np.save(dense_path, mask_dense)
                inst["mask_dense_handle"] = dense_path
                inst["mask_dense_shape"]  = list(_DENSE_HW)
            except Exception:
                pass
    payload["frames"] = frames_out

    # r180: per-frame peak count. The cross-frame union (n_unique_instances)
    # over-counts on repetitive/high-count objects because tracker drift mints
    # new instance_ids for the same physical object across frames. The peak
    # single-frame instance count is a deterministic returned tally.
    # Question-agnostic perception primitive; the planner chooses when to use it.
    try:
        payload["max_instances_in_any_frame"] = max(
            (len(v) for v in frames_out.values()), default=0)
    except Exception:
        payload["max_instances_in_any_frame"] = 0

    # r187 (counting analysis): tracker drift mints transient ids that are seen in
    # only 1-2 frames (instance_persistence < 3). n_significant_instances keeps
    # only instances persisting at least 3 frames. Question-agnostic.
    try:
        _pers = payload.get("instance_persistence", {}) or {}
        payload["n_significant_instances"] = int(sum(1 for v in _pers.values() if v >= 3))
    except Exception:
        payload["n_significant_instances"] = payload["max_instances_in_any_frame"]

    # STR-3 (r213, env STR3_ARBITER=1): deterministic co-visibility arbiter —
    # adds covis_arbitrated_count + the inputs that produced it as EXTRA
    # EVIDENCE alongside the existing tallies (never a forced answer). The
    # in-call baseline is this call's primary count (n_unique_instances),
    # matching the screen's per-video-call choice.
    if _STR3_ARBITER:
        try:
            _pers = payload.get("instance_persistence", {}) or {}
            est, arb_inputs = _str3_covis_arbitrate(
                payload.get("n_unique_instances"),
                list(frames_out.values()),
                [(_pers, len(frames_out), payload.get("n_unique_instances", 0))])
            payload["covis_arbitrated_count"] = est
            payload["covis_arbiter_inputs"] = arb_inputs
        except Exception:
            pass

    # APPEAR-EV (r213, env APPEAR_EVIDENCE=1): deterministic first-appearance
    # telemetry per persistent instance (screen thresholds score>=0.4,
    # area>=0.0005, persistence>=2) — EXTRA EVIDENCE the planner can weigh,
    # never an override (the standalone override broke 9/34 on the screen).
    if _APPEAR_EVIDENCE:
        try:
            rows, earliest = _appear_first_evidence(frames_out)
            payload["first_appearance_evidence"] = rows
            payload["earliest_confident_frame"] = earliest
        except Exception:
            pass

    with _SAM3_VIDEO_LOCK:
        _SAM3_VIDEO_CACHE[cache_key] = payload

    if config is not None:
        trace_list = config.get("configurable", {}).get("trace_list")
        if trace_list is not None:
            n_unique = payload.get("n_unique_instances", "?")
            n_maxfr = payload.get("max_instances_in_any_frame", "?")
            n_frames = len(payload.get("frames", {}))
            _covis = (f"covis_arbitrated_count={payload['covis_arbitrated_count']} "
                      if "covis_arbitrated_count" in payload else "")
            _appear = (f"earliest_confident_frame={payload['earliest_confident_frame']} "
                       if "earliest_confident_frame" in payload else "")
            trace_list.append({"tool": "predict_2d_segmentation_masks_video",
                               "response": (f"max_instances_in_any_frame={n_maxfr} "
                                            f"n_significant_instances={payload.get('n_significant_instances', '?')} "
                                            f"n_unique_instances={n_unique} "
                                            f"{_covis}"
                                            f"{_appear}"
                                            f"n_frames={n_frames} "
                                            f"persistence={payload.get('instance_persistence', {})}")})
    return payload


if _STR3_ARBITER:
    # Gated so the control arm's tool schema stays byte-identical to r210.
    predict_2d_segmentation_masks_video.description += (
        "\n\nWhen present, `covis_arbitrated_count` is a deterministic "
        "co-visibility-arbitrated instance-count estimate (computed from the "
        "per-frame disjoint-detection geometry and track persistence; "
        "`covis_arbiter_inputs` shows the bounds it was derived from). Treat "
        "it as additional evidence alongside the other tallies."
    )

if _APPEAR_EVIDENCE:
    # Gated so the control arm's tool schema stays byte-identical to r210.
    predict_2d_segmentation_masks_video.description += (
        "\n\nWhen present, `first_appearance_evidence` lists, for each "
        "persistent tracked instance, the first frame index (among the frames "
        "this call covered) where it was confidently detected, plus how many "
        "frames it was seen in; `earliest_confident_frame` is the minimum of "
        "those. Deterministic detection telemetry — treat it as additional "
        "evidence."
    )


# ─────────────────────────────────────────────────────────────────────────────
# MC-EXTENT (r213, env MC_EXTENT=1): MaskClustering view-consensus
# consolidated 3D instances + robust extents. Backing implementation =
# agent/maskclustering_extent.py (pointmap-native port of PKU-EPIC/
# MaskClustering, CVPR'24). SAM3 masks come via the local router inside the
# backing module.
# ─────────────────────────────────────────────────────────────────────────────

_MC_WINNING = {"voxel": 0.08, "tau": 0.9, "min_masks": 1, "split_eps": -1.0}
_MC_MODULE = None


def _mc_module():
    """Lazy import of agent/maskclustering_extent.py (agent dir = 3 levels up)."""
    global _MC_MODULE
    if _MC_MODULE is None:
        agent_dir = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        if agent_dir not in sys.path:
            sys.path.insert(0, agent_dir)
        import maskclustering_extent
        _MC_MODULE = maskclustering_extent
    return _MC_MODULE


@tool
def get_object_instances_3d(scene_id: str, object_label: str,
                            config: RunnableConfig = None) -> dict:
    """
    Consolidates multi-view SAM3 masks of one object label into 3D object
    instances with robust extents, via view-consensus mask-graph clustering.

    Question-agnostic perception primitive: runs SAM3 video tracking for
    `object_label` over all frames, lifts every per-frame mask onto the dense
    metric point cloud, clusters masks that consistently co-segment the same
    3D points across views, and unions each cluster's points into ONE
    consolidated instance. Because the union pools pixels from every view,
    the extents are robust to single-frame truncation/fragmentation, and the
    view-consensus grouping is robust to tracker-id drift.

    Args:
        scene_id: VSIBench scene identifier.
        object_label: natural-language label, e.g. "chair", "refrigerator".

    Returns:
        dict — {
          "instances": [{
              "instance_id": int,           # index within this result
              "n_views":     int,           # frames supporting the cluster
              "centroid":    [x, y, z],     # world Z-up, meters
              "extent_xyz":  [dx, dy, dz],  # p2-p98 span per world axis (m)
              "aabb_min":    [x, y, z],     # p2 corner of the union cloud
              "aabb_max":    [x, y, z],     # p98 corner of the union cloud
          }, ...],
          "n_instances": int,
        }
        or {"error": "..."} when the scene/label yields no usable masks.

    Cost: one SAM3 video pass over the scene (~10-30 s) + a few seconds of
    clustering. One call covers every instance of the label at once.
    """
    try:
        mc = _mc_module()
        dense = mc.load_scaled_dense(scene_id)
        if dense is None:
            return {"error": f"no dense npz for scene {scene_id}"}
        frame_indices = list(range(1, 33))
        payload = _run_sam3_video_request(
            scene_id, frame_indices, object_label,
            mask_dir=_sam3_mask_dir(scene_id, object_label, "mc_extent_video32"),
            score_thresh=0.5, timeout=360.0,
        )
        if "error" in payload:
            return {"error": f"SAM3: {payload['error']}"}
        graph = mc.build_mask_graph(scene_id, dense, payload,
                                    voxel=_MC_WINNING["voxel"])
        if graph is None:
            return {"error": f"no usable '{object_label}' masks in {scene_id}"}
        clusters = mc.cluster_graph(graph, tau=_MC_WINNING["tau"],
                                    min_masks=_MC_WINNING["min_masks"],
                                    split_eps=_MC_WINNING["split_eps"])
        instances = []
        for i, inst in enumerate(clusters):
            lo = np.percentile(inst["points"], 2, axis=0)
            hi = np.percentile(inst["points"], 98, axis=0)
            instances.append({
                "instance_id": i,
                "n_views": int(inst["n_views"]),
                "centroid": [round(float(v), 4) for v in inst["centroid_xyz"]],
                "extent_xyz": [round(float(v), 4) for v in (hi - lo)],
                "aabb_min": [round(float(v), 4) for v in lo],
                "aabb_max": [round(float(v), 4) for v in hi],
            })
        result = {"instances": instances, "n_instances": len(instances)}
        if config is not None:
            trace_list = config.get("configurable", {}).get("trace_list")
            if trace_list is not None:
                trace_list.append({"tool": "get_object_instances_3d",
                                   "response": str(result)})
        return result
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


# ─────────────────────────────────────────────────────────────────────────────
# r196: conditional high-count counting primitive.
# Voxel-merge logic copied verbatim from scratch/counting_dedup_probe.py.
# ─────────────────────────────────────────────────────────────────────────────

# Default frame set for count_object_instances_3d: ~20 evenly-spaced 1-based
# frames over the 32-frame selected set. This is the
# new tool's INTERNAL default; it does NOT change predict_2d_segmentation_masks_video's
# own default (that tool still takes explicit frame_indices).
def _count3d_default_frames(n_avail: int) -> list[int]:
    n_sample = min(20, n_avail) if n_avail >= 20 else n_avail
    if n_sample <= 0:
        return []
    return sorted(set(
        int(round(1 + i * (n_avail - 1) / (n_sample - 1))) if n_sample > 1 else 1
        for i in range(n_sample)))


def _count3d_detection_pts(mask_handle, scene_id, frame_index, dense,
                           miss_sink: list | None = None):
    """Robust per-detection 3D point set (N,3) or None.
    Copied from scratch/counting_dedup_probe.py:detection_pts (uses the agent's
    own _frame_index_to_npz_idx instead of the probe's frame_to_npz_idx)."""
    _MIN_PTS = 30
    if not mask_handle or not os.path.exists(mask_handle):
        return None
    npz_idx = _frame_index_to_npz_idx(scene_id, frame_index, dense)
    if npz_idx is None:
        if miss_sink is not None:
            miss_sink.append(int(frame_index))
        return None
    pts3d = dense["pts3d_world"][npz_idx]   # (H,W,3)
    valid = dense["mask"][npz_idx]          # (H,W) bool
    try:
        mask = np.load(mask_handle)
    except Exception:
        return None
    if mask.shape != pts3d.shape[:2]:
        from PIL import Image
        im = Image.fromarray((mask.astype(np.uint8) * 255))
        im = im.resize((pts3d.shape[1], pts3d.shape[0]), resample=Image.NEAREST)
        mask = np.asarray(im) > 127
    region = mask & valid
    if int(region.sum()) < _MIN_PTS:
        return None
    pts = pts3d[region]
    pts = pts[np.isfinite(pts).all(axis=1)]
    if pts.shape[0] < _MIN_PTS:
        return None
    lo = np.percentile(pts, 5, axis=0)
    hi = np.percentile(pts, 95, axis=0)
    keep = np.all((pts >= lo) & (pts <= hi), axis=1)
    return pts[keep] if keep.sum() >= 20 else pts


def _count3d_voxel_set(pts, voxel):
    if pts is None or len(pts) == 0:
        return frozenset()
    q = np.floor(pts / voxel).astype(np.int64)
    return frozenset(map(tuple, q))


def _count3d_voxel_iou(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a) + len(b) - inter
    return inter / union if union else 0.0


def _count3d_merge_voxel(tracklet_vsets, iou_thresh):
    """Union-find merge tracklets whose voxel-set IoU >= iou_thresh.
    Returns number of merged clusters. Copied from
    scratch/counting_dedup_probe.py:merge_voxel."""
    n = len(tracklet_vsets)
    if n == 0:
        return 0
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    for i in range(n):
        for j in range(i + 1, n):
            if _count3d_voxel_iou(tracklet_vsets[i], tracklet_vsets[j]) >= iou_thresh:
                union(i, j)
    return len({find(i) for i in range(n)})


@tool
def count_object_instances_3d(scene_id: str, object_label: str,
                              config: RunnableConfig = None,
                              point_cloud_source: str = POINT_CLOUD_DEFAULT_SOURCE) -> dict:
    """
    r196: deterministic distinct-instance-count primitive.

    Runs SAM 3 native video tracking (predict_2d_segmentation_masks_video) over
    the default ~20 evenly-spaced frames, then chooses a count estimator
    CONDITIONALLY based on the observed instance counts:
      - LOW-count branch (max_in_any_frame <= 5 AND n_unique <= 5):
        returns `max_in_any_frame`, the drift-immune peak single-frame instance
        count. The 3D merge is NOT run.
      - HIGH-count branch (max_in_any_frame > 5 OR n_unique > 5):
        lifts every tracklet's masks into the dense 3D cloud, voxelizes at 0.1 m,
        union-find merges tracklets with voxel-IoU >= 0.25 (dedups tracker-drift
        ids for the same physical object), and returns the merged cluster count
        `n_3d_merged`. Useful when instances are spread across frames so no
        single frame captures them all, but drift inflates the raw union count.

    Perception primitive composed in deterministic code (grounding = SAM3 video;
    dedup = voxel union-find; count = cluster length).

    Args:
        scene_id: VSIBench scene identifier.
        object_label: Natural-language label, e.g. "chair", "ceiling light".
        point_cloud_source: Optional source for lifting SAM masks. Default
            "g3t_scaled" is the same for every question; alternatives are
            "mapanything" and "unik3d". Choose explicitly inside the trace.

    Returns:
        dict — {
          "count":               int,    # the chosen estimate (use this)
          "branch":              "low" | "high",
          "max_in_any_frame":    int,
          "n_unique":            int,
          "n_3d_merged":         int,     # present only on the high-count branch
        }
        Returns {"error": "..."} on grounding/dense failure.
    """
    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError as e:
        return {"error": str(e)}
    dense = _load_dense(scene_id, point_cloud_source=source_key)
    if dense is None:
        return {"error": f"Dense outputs not found for scene {scene_id}."}
    n_avail = int(dense["pts3d_world"].shape[0])
    frame_indices = _count3d_default_frames(n_avail)
    if not frame_indices:
        return {"error": f"No frames available for scene {scene_id}."}

    # Reuse the registered video request without an effective local score filter.
    # DEFAULT frame setting —
    # do NOT expand here (r194's 20-frame seg_video default REGRESSED counting).
    payload = _run_sam3_video_request(
        scene_id, frame_indices, object_label,
        mask_dir=_sam3_mask_dir(scene_id, object_label, "count3d_video"),
        score_thresh=0.0)
    if isinstance(payload, dict) and "error" in payload:
        if config is not None:
            tl = config.get("configurable", {}).get("trace_list")
            if tl is not None:
                tl.append({"tool": "count_object_instances_3d",
                           "response": f"ERROR: {payload}"})
        return {"error": payload.get("error", "sam3 video unknown failure")}

    frames = payload.get("frames", {}) or {}
    max_in_any_frame = max((len(v) for v in frames.values()), default=0)
    persistence = payload.get("instance_persistence", {}) or {}
    n_unique = len(persistence) if persistence else int(payload.get("n_unique_instances", 0))

    high = (max_in_any_frame > 5) or (n_unique > 5)
    if not high:
        result = {"count": int(max_in_any_frame), "branch": "low",
                  "max_in_any_frame": int(max_in_any_frame), "n_unique": int(n_unique),
                  "point_cloud_source": source_key}
    else:
        # HIGH-count branch: lift each tracklet's masks to 3D, voxelize + merge.
        VOXEL, IOU_THRESH = 0.1, 0.25
        track_pts: dict = {}
        index_miss = []
        for fk, inst_list in frames.items():
            try:
                fi = int(fk)
            except Exception:
                continue
            for inst in inst_list:
                tid = inst.get("instance_id")
                pts = _count3d_detection_pts(
                    inst.get("mask_handle"), scene_id, fi, dense, miss_sink=index_miss)
                if pts is not None and len(pts):
                    track_pts.setdefault(tid, []).append(pts)
        if index_miss:
            result = {"error": "frame_index_unmappable",
                      "frames": sorted(set(index_miss)),
                      "scene_id": scene_id, "point_cloud_source": source_key,
                      "detail": "dense store index mismatch — count withheld (fail-closed)"}
            if config is not None:
                tl = config.get("configurable", {}).get("trace_list")
                if tl is not None:
                    tl.append({"tool": "count_object_instances_3d", "response": str(result)})
            return result
        tracklet_pts = {tid: np.vstack(lst) for tid, lst in track_pts.items() if lst}
        vsets = [_count3d_voxel_set(p, VOXEL) for p in tracklet_pts.values()]
        vsets = [v for v in vsets if v]
        n_3d_merged = _count3d_merge_voxel(vsets, IOU_THRESH)
        result = {"count": int(n_3d_merged), "branch": "high",
                  "max_in_any_frame": int(max_in_any_frame), "n_unique": int(n_unique),
                  "n_3d_merged": int(n_3d_merged), "point_cloud_source": source_key}

    if config is not None:
        tl = config.get("configurable", {}).get("trace_list")
        if tl is not None:
            tl.append({"tool": "count_object_instances_3d", "response": str(result)})
    return result


@tool
def count_instances_3d(scene_id: str, object_label: str,
                       config: RunnableConfig = None,
                       point_cloud_source: str = POINT_CLOUD_DEFAULT_SOURCE) -> dict:
    """
    CI3D (r214): deterministic 3D-consolidated instance tally for one object
    label, with ONE canonical `count` output.

    Runs SAM3 video tracking over ~20 evenly-spaced frames, lifts every tracked
    instance's masks onto the dense metric point cloud (frame -> dense-slot
    mapping via the scene's dense `indices` table — never positional f_idx-1
    arithmetic), computes one median 3D world centroid per tracked ID, merges
    IDs whose centroids lie within 0.6 m (tracker drift mints duplicate IDs for
    one physical object), and clamps the merged tally to the peak number of
    simultaneously-visible instances in any single frame (detections disjoint
    in the SAME frame are physically distinct, so the count can never fall
    below that floor).

    Perception primitive composed in deterministic geometry: grounding = SAM3
    video tracking; dedup = centroid-distance union-find; floor = single-frame
    co-occurrence; count = cluster-list length.

    Args:
        scene_id: VSIBench scene identifier.
        object_label: Natural-language label, e.g. "chair", "trash bin".
        point_cloud_source: Optional source for lifting SAM masks. Default
            "g3t_scaled" is the same for every question; alternatives are
            "mapanything" and "unik3d". Choose explicitly inside the trace.

    Returns:
        dict — {
          "count":    int,   # canonical consolidated instance count (use this)
          "evidence": {
              "n_raw_ids":        int,  # tracked IDs before merging
              "n_after_merge":    int,  # IDs left after the 0.6 m centroid merge
              "max_in_any_frame": int,  # peak single-frame count (clamp floor)
          },
        }
        Returns {"error": "..."} on grounding/dense failure.
    """
    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError as e:
        return {"error": str(e)}
    dense = _load_dense(scene_id, point_cloud_source=source_key)
    if dense is None:
        return {"error": f"Dense outputs not found for scene {scene_id}."}
    n_avail = int(dense["pts3d_world"].shape[0])
    frame_indices = _count3d_default_frames(n_avail)
    if not frame_indices:
        return {"error": f"No frames available for scene {scene_id}."}

    payload = _run_sam3_video_request(
        scene_id, frame_indices, object_label,
        mask_dir=_sam3_mask_dir(scene_id, object_label, "ci3d_video"),
        score_thresh=0.0)
    if isinstance(payload, dict) and "error" in payload:
        if config is not None:
            tl = config.get("configurable", {}).get("trace_list")
            if tl is not None:
                tl.append({"tool": "count_instances_3d",
                           "response": f"ERROR: {payload}"})
        return {"error": payload.get("error", "sam3 video unknown failure")}

    frames = payload.get("frames", {}) or {}
    max_in_any_frame = max((len(v) for v in frames.values()), default=0)

    # Per-tracked-ID 3D points. The frame->dense-slot lookup happens inside
    # _count3d_detection_pts via _frame_index_to_npz_idx (dense['indices']).
    raw_ids = set()
    track_pts: dict = {}
    index_miss = []
    for fk, inst_list in frames.items():
        try:
            fi = int(fk)
        except Exception:
            continue
        for inst in inst_list:
            tid = inst.get("instance_id")
            raw_ids.add(tid)
            pts = _count3d_detection_pts(
                inst.get("mask_handle"), scene_id, fi, dense, miss_sink=index_miss)
            if pts is not None and len(pts):
                track_pts.setdefault(tid, []).append(pts)

    if index_miss:
        result = {"error": "frame_index_unmappable",
                  "frames": sorted(set(index_miss)),
                  "scene_id": scene_id, "point_cloud_source": source_key,
                  "detail": "dense store index mismatch — count withheld (fail-closed)"}
        if config is not None:
            tl = config.get("configurable", {}).get("trace_list")
            if tl is not None:
                tl.append({"tool": "count_instances_3d", "response": str(result)})
        return result

    # Median 3D centroid per tracked ID, then union-find merge within 0.6 m.
    centroids = {tid: np.median(np.vstack(lst), axis=0)
                 for tid, lst in track_pts.items()}
    tids = sorted(centroids, key=str)
    n = len(tids)
    parent = list(range(n))
    def _find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i in range(n):
        for j in range(i + 1, n):
            if np.linalg.norm(centroids[tids[i]] - centroids[tids[j]]) <= 0.6:
                ri, rj = _find(i), _find(j)
                if ri != rj:
                    parent[rj] = ri
    n_merged = len({_find(i) for i in range(n)})
    # IDs that never lifted to 3D cannot be shown co-located — keep distinct.
    n_after_merge = n_merged + len(raw_ids - set(centroids))
    count = max(n_after_merge, max_in_any_frame)

    result = {"count": int(count),
              "evidence": {"n_raw_ids": int(len(raw_ids)),
                           "n_after_merge": int(n_after_merge),
                           "max_in_any_frame": int(max_in_any_frame)},
              "point_cloud_source": source_key}
    if config is not None:
        tl = config.get("configurable", {}).get("trace_list")
        if tl is not None:
            tl.append({"tool": "count_instances_3d", "response": str(result)})
    return result


@tool
def get_room_footprint_area(scene_id: str, config: RunnableConfig = None,
                            point_cloud_source: str = POINT_CLOUD_DEFAULT_SOURCE) -> dict:
    """
    Deterministic concave floor-footprint area (m^2) of a gravity-aligned scene.
    Extracts the floor-level horizontal point slab and estimates its 2D area via
    alpha-shape. Two alpha values are computed so a sparsely-sampled (fragmented)
    floor can be detected and a looser alpha used in that case.

    Pipeline (no VLM; gravity-aligned RANSAC dense):
      1. Histogram-mode floor_z (most-populated 0.1 m Z-bin in the lower half of
         the Z range — robust to a few sub-floor outliers vs a raw percentile).
      2. ALL mask-valid pixels kept (no conf gate). Low-conf pixels can be
         far-wall samples covering the room perimeter, not artifacts.
      3. Z-slab: floor_z+0.05 m .. floor_z + 1.0 m  → floor XY points.
      4. alpha-shape areas a06 = alpha_shape_area(xy, 0.6) and
         a20 = alpha_shape_area(xy, 2.0). If a06/a20 < 0.70 the floor
         reconstruction is fragmented (tight alpha under-covers) → use a20;
         otherwise a06.

    Args:
        scene_id: VSIBench scene identifier.
        point_cloud_source: Optional source. Default "g3t_scaled" is the same
          for every question; "mapanything" can be useful as a stable layout
          fallback; "unik3d" is available for metric depth checks. Choose
          explicitly inside the trace.

    Returns:
        dict with:
          "area_m2":          float — the chosen alpha-shape floor area
          "a06":              float — alpha=0.6 area
          "a20":              float — alpha=2.0 area
          "alpha_used":       float — alpha radius actually used
          "fragmented":       bool  — True when a06/a20 < 0.70
          "floor_z":          float — histogram-mode floor Z used (meters)
          "slab_n_points":    int   — floor-slab point count
        Returns {"error": "..."} on failure.
    """
    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError as e:
        return {"error": str(e)}
    dense = (_load_ransac_dense(scene_id, point_cloud_source=source_key)
             or _load_dense(scene_id, point_cloud_source=source_key))
    if dense is None:
        return {"error": f"Dense outputs unavailable for {scene_id}"}
    try:
        pts3d = dense["pts3d_world"].reshape(-1, 3)     # (N*H*W, 3)
        valid = dense["mask"].reshape(-1).astype(bool)
        conf  = dense["conf"].reshape(-1)
    except Exception as e:
        return {"error": f"Dense access failed: {e}"}

    # r202 G3T fix: keep ALL mask-valid pixels (drop the conf>0.5 gate).
    # For G3T_scaled, low-conf pixels are far-wall samples covering the room
    # PERIMETER — not MapAnything through-wall artifacts. Dropping them
    # under-covers the footprint.
    keep = valid
    pts = pts3d[keep]
    if pts.shape[0] < 1000:
        return {"error": "Not enough mask-valid points for floor estimate."}

    z = pts[:, 2]
    # Histogram-mode floor_z over the lower half of the Z range (0.1 m bins).
    z_lo, z_hi = float(np.percentile(z, 1)), float(np.percentile(z, 99))
    lower = z[z <= (z_lo + z_hi) / 2.0]
    if lower.size < 100:
        lower = z
    nbins = max(1, int(np.ceil((lower.max() - lower.min()) / 0.1)))
    counts, edges = np.histogram(lower, bins=nbins)
    floor_z = float((edges[counts.argmax()] + edges[counts.argmax() + 1]) / 2.0)

    # r202: slab 0.05m-1.0m above floor (was 0.0-0.5m). The extra headroom
    # captures more horizontal surface and pulls in far-wall base points.
    in_slab = (z >= floor_z + 0.05) & (z <= floor_z + 1.0)
    xy = pts[in_slab, :2]
    if xy.shape[0] < 100:
        return {"error": "Floor slab too sparse for alpha-shape area.",
                "floor_z": round(floor_z, 4), "slab_n_points": int(xy.shape[0])}

    # r202: XY p1-p99 clip removes XY outliers (wall-top projections, depth
    # bleed at slab boundary) that the 1m slab brings in.
    loq = np.percentile(xy, 1, axis=0)
    hiq = np.percentile(xy, 99, axis=0)
    m = ((xy[:, 0] >= loq[0]) & (xy[:, 0] <= hiq[0]) &
         (xy[:, 1] >= loq[1]) & (xy[:, 1] <= hiq[1]))
    xy = xy[m]
    if xy.shape[0] < 100:
        return {"error": "Floor slab too sparse after XY clip.",
                "floor_z": round(floor_z, 4), "slab_n_points": int(xy.shape[0])}

    a06 = _alpha_shape_area(xy, 0.6)
    a20 = _alpha_shape_area(xy, 2.0)
    # r192: raise fragmentation threshold 0.44 -> 0.70 and use the looser alpha=2.0
    # hull directly when fragmented. Per-question error analysis (deploy187) found a06
    # under-covers fragmented floors 30-50% on qids 531,541,565,622,657,673,2685,3828,
    # 635 while a20 (already computed) tracks GT. A/B vs deployFIX room before deploy.
    fragmented = (a20 > 1e-6) and (a06 / a20 < 0.70)
    if fragmented:
        area = a20
        alpha_used = 2.0
    else:
        area = a06
        alpha_used = 0.6
    return {
        "area_m2":       round(float(area), 4),
        "a06":           round(float(a06), 4),
        "a20":           round(float(a20), 4),
        "alpha_used":    alpha_used,
        "fragmented":    bool(fragmented),
        "floor_z":       round(floor_z, 4),
        "slab_n_points": int(xy.shape[0]),
        "point_cloud_source": source_key,
    }


@tool
def aggregate_aabbs_median(aabbs: list[dict], config: RunnableConfig = None) -> dict:
    """
    Reduce a list of per-frame 3D AABB observations of a single object across
    frames into one robust AABB by taking the per-axis median of corner
    coordinates. Use this whenever you have multiple `get_3d_points_in_bbox`
    results for the SAME physical object across different frames and need a
    single representative bounding box (e.g. for distance comparisons across
    different objects).

    The arithmetic mistake this primitive prevents: agents tend to write
    `min(min_xyz_p5)` and `max(max_xyz_p95)` across frames — a UNION — which
    silently grows the bbox by every per-frame outlier. The correct robust
    reduction is the median of each corner across frames; that is exactly
    what this tool returns. The verifier's "use the median, not the union"
    instruction is enforced mechanically here.

    Args:
        aabbs: list of dicts with keys `min_xyz_p5` and `max_xyz_p95` (e.g.
               the per-frame returns of `get_3d_points_in_bbox`). Entries
               missing those keys are dropped silently.

    Returns:
        dict with:
          "min_xyz_p5":     [x, y, z] median lower-corner across frames
          "max_xyz_p95":    [x, y, z] median upper-corner across frames
          "centroid":       midpoint of the median corners
          "extent_xyz":     max - min, per axis (m)
          "n_frames_used":  int — number of frame AABBs that contributed
        Returns {"error": "..."} on failure.

    """
    try:
        mins, maxs = [], []
        for a in aabbs or []:
            if not isinstance(a, dict): continue
            lo = a.get("min_xyz_p5"); hi = a.get("max_xyz_p95")
            if not (isinstance(lo, list) and isinstance(hi, list) and len(lo) == 3 and len(hi) == 3):
                continue
            try:
                lo_f = [float(v) for v in lo]; hi_f = [float(v) for v in hi]
            except Exception:
                continue
            mins.append(lo_f); maxs.append(hi_f)
        if not mins or not maxs:
            return {"error": "No usable AABBs in input."}
        mins_arr = np.array(mins); maxs_arr = np.array(maxs)
        med_min = np.median(mins_arr, axis=0)
        med_max = np.median(maxs_arr, axis=0)
        centroid = (med_min + med_max) / 2.0
        extent = med_max - med_min
        return {
            "min_xyz_p5":    [round(float(v), 4) for v in med_min],
            "max_xyz_p95":   [round(float(v), 4) for v in med_max],
            "centroid":      [round(float(v), 4) for v in centroid],
            "extent_xyz":    [round(float(v), 4) for v in extent],
            "n_frames_used": int(mins_arr.shape[0]),
        }
    except Exception as e:
        return {"error": f"aggregate_aabbs_median failed: {e}"}


@tool
def aggregate_aabbs_robust(aabbs: list[dict],
                           config: RunnableConfig = None) -> dict:
    """Aggregate per-frame AABB endpoints with Tukey inner-fence outlier handling.

    For each world axis, the lower endpoints and upper endpoints are treated as
    separate repeated measurements.  Q1, Q3, and IQR=Q3-Q1 define the standard
    inner fences [Q1-1.5*IQR, Q3+1.5*IQR].  The aggregate lower endpoint is the
    smallest observed lower endpoint inside its fence; the aggregate upper
    endpoint is the largest observed upper endpoint inside its fence.  These are
    the box-plot adjacent values.  The rule is fixed by the standard estimator,
    not by benchmark outcomes.

    Args:
        aabbs: dicts with three-element `min_xyz_p5` and `max_xyz_p95` lists.
            Entries missing either endpoint are ignored.

    Returns:
        {min_xyz_p5, max_xyz_p95, centroid, extent_xyz, n_frames_used,
         outlier_rule, n_lower_endpoint_outliers, n_upper_endpoint_outliers}
        or {error}.  No data-dependent fallback estimator is used.
    """
    try:
        entries = [a for a in (aabbs or []) if isinstance(a, dict)]
        n_dropped_degenerate = 0
        all_flagged = False
        if _DG_GATE and entries:
            def _dg_aabb_flagged(a):
                return bool(a.get("low_confidence")
                            or a.get("bbox_quality_warning")
                            or a.get("mask_quality_warning")
                            or a.get("mask_truncation_warning"))
            clean = [a for a in entries if not _dg_aabb_flagged(a)]
            if clean:
                n_dropped_degenerate = len(entries) - len(clean)
                entries = clean
            else:
                all_flagged = True

        mins, maxs = [], []
        for a in entries:
            lo = a.get("min_xyz_p5")
            hi = a.get("max_xyz_p95")
            if not (isinstance(lo, list) and isinstance(hi, list)
                    and len(lo) == 3 and len(hi) == 3):
                continue
            try:
                lo_f = [float(v) for v in lo]
                hi_f = [float(v) for v in hi]
            except (TypeError, ValueError):
                continue
            if not (np.all(np.isfinite(lo_f)) and np.all(np.isfinite(hi_f))):
                continue
            mins.append(lo_f)
            maxs.append(hi_f)
        if not mins:
            return {"error": "No usable AABBs in input."}

        mins_arr = np.asarray(mins, dtype=float)
        maxs_arr = np.asarray(maxs, dtype=float)

        def _adjacent_values(samples, take_min):
            q1, q3 = np.percentile(samples, [25.0, 75.0], axis=0)
            iqr = q3 - q1
            inside = ((samples >= q1 - 1.5 * iqr)
                      & (samples <= q3 + 1.5 * iqr))
            if not np.all(np.any(inside, axis=0)):
                raise ValueError("Tukey fence left an axis without an adjacent value")
            kept = np.where(inside, samples, np.nan)
            values = np.nanmin(kept, axis=0) if take_min else np.nanmax(kept, axis=0)
            rejected = np.sum(~inside, axis=0).astype(int)
            return values, rejected

        agg_min, lower_rejected = _adjacent_values(mins_arr, True)
        agg_max, upper_rejected = _adjacent_values(maxs_arr, False)
        if np.any(agg_max < agg_min):
            return {"error": "Robust endpoint aggregation produced an invalid AABB."}

        centroid = (agg_min + agg_max) / 2.0
        extent = agg_max - agg_min
        result = {
            "min_xyz_p5": [round(float(v), 4) for v in agg_min],
            "max_xyz_p95": [round(float(v), 4) for v in agg_max],
            "centroid": [round(float(v), 4) for v in centroid],
            "extent_xyz": [round(float(v), 4) for v in extent],
            "n_frames_used": int(mins_arr.shape[0]),
            "outlier_rule": "tukey_inner_fence_1.5_iqr_adjacent_values",
            "n_lower_endpoint_outliers": lower_rejected.tolist(),
            "n_upper_endpoint_outliers": upper_rejected.tolist(),
        }
        if _DG_GATE:
            if n_dropped_degenerate:
                result["n_frames_dropped_degenerate"] = n_dropped_degenerate
            _dg_fl = []
            if all_flagged:
                _dg_fl.append("all_input_frames_flagged")
                result["warning"] = ("WARNING: every input AABB carries a "
                                     "degeneracy/truncation flag — nothing could "
                                     "be dropped; this aggregate is low-confidence.")
            cents = (mins_arr + maxs_arr) / 2.0
            if cents.shape[0] >= 2:
                spread = float(np.linalg.norm(
                    cents - np.median(cents, axis=0), axis=1).max())
                result["cross_frame_centroid_spread_m"] = round(spread, 4)
                if spread > 1.0:
                    _dg_fl.append("cross_frame_centroid_spread_>1.0m")
            _dg_apply(result, _dg_fl)
        return result
    except Exception as e:
        return {"error": f"aggregate_aabbs_robust failed: {e}"}


@tool
def cluster_3d_points(points_3d: list[list[float]], eps: float = 0.5,
                      min_samples: int = 5,
                      config: RunnableConfig = None) -> dict:
    """Cluster 3D points using standard Euclidean DBSCAN semantics.

    Defaults inherit scikit-learn's shipped parameter convention: eps=0.5,
    min_samples=5, Euclidean distance.  `min_samples` includes the point itself;
    points not density-reachable from a core point receive label -1 as noise.
    No support>=2 recount, singleton absorption, cannot-link split, or chain-merge
    reinterpretation is applied after DBSCAN.
    """
    try:
        from sklearn.cluster import DBSCAN
    except Exception as e:
        return {"error": f"sklearn not available for DBSCAN: {e}"}

    pts = np.asarray(points_3d, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 3:
        return {"error": f"Expected an (N,3) array of 3D points, got shape {tuple(pts.shape)}."}
    if len(pts) == 0:
        return {"num_clusters": 0, "cluster_medians": [],
                "cluster_sizes": [], "labels": []}
    if not np.all(np.isfinite(pts)):
        return {"error": "points_3d must contain only finite coordinates"}

    try:
        labels = DBSCAN(
            eps=float(eps), min_samples=int(min_samples), metric="euclidean"
        ).fit_predict(pts)
    except (TypeError, ValueError) as e:
        return {"error": f"Invalid DBSCAN parameters: {e}"}

    kept_ids = sorted(i for i in set(labels.tolist()) if i != -1)
    medians, sizes = [], []
    for cid in kept_ids:
        cluster_pts = pts[labels == cid]
        medians.append([round(float(v), 4) for v in np.median(cluster_pts, axis=0)])
        sizes.append(int(len(cluster_pts)))
    result = {
        "num_clusters": len(kept_ids),
        "cluster_medians": medians,
        "cluster_sizes": sizes,
        "labels": labels.tolist(),
    }
    if config is not None:
        trace_list = config.get("configurable", {}).get("trace_list")
        if trace_list is not None:
            trace_list.append({"tool": "cluster_3d_points", "response": str(result)})
    return result


# ─────────────────────────────────────────────────────────────────────────────
# NF-7 (r210, env NF7_GROUNDING_UNION=1): multi-frame grounding union
# ─────────────────────────────────────────────────────────────────────────────

def _ground_union_instances(detections: list, eps: float = None) -> dict:
    """NF-7 (r210) helper: reduce per-frame detections into physical-instance
    rows. `detections` is a list of (frame_idx, instance_id, centroid(3,),
    p5_xyz(3,), p95_xyz(3,)) tuples. Clusters the detection centroids with
    standard cluster_3d_points defaults, then
    aggregates each cluster into one table row (per-axis median of the member
    detections' p5/p95 corners — same robust reduction as aggregate_aabbs_median).
    Deterministic; offline-testable. Returns {"instances": [...]} or {"error"}."""
    if not detections:
        return {"instances": []}
    cents = [[float(v) for v in d[2]] for d in detections]
    kwargs = {} if eps is None else {"eps": eps}
    res = cluster_3d_points.func(cents, **kwargs)
    if not isinstance(res, dict) or "error" in res:
        return {"error": f"centroid clustering failed: {res}"}
    labels = res.get("labels", [])
    rows = []
    for cid in sorted(set(labels)):
        if cid == -1:
            continue
        members = [d for d, l in zip(detections, labels) if l == cid]
        frames_seen = sorted({int(m[0]) for m in members})
        cents_m = np.asarray([m[2] for m in members], dtype=float)
        mn = np.median(np.asarray([m[3] for m in members], dtype=float), axis=0)
        mx = np.median(np.asarray([m[4] for m in members], dtype=float), axis=0)
        rows.append({
            "instance_idx":  int(cid),
            "n_frames_seen": len(frames_seen),
            "frames_seen":   frames_seen,
            "n_detections":  len(members),
            "centroid_xyz":  [round(float(v), 4) for v in np.median(cents_m, axis=0)],
            "min_xyz_p5":    [round(float(v), 4) for v in mn],
            "max_xyz_p95":   [round(float(v), 4) for v in mx],
            "extent_xyz":    [round(float(b - a), 4) for a, b in zip(mn, mx)],
        })
    rows.sort(key=lambda r: (-r["n_frames_seen"], r["instance_idx"]))
    for i, r in enumerate(rows):
        r["instance_idx"] = i
    return {"instances": rows}


@tool
def ground_object_all_frames(scene_id: str, object_label: str,
                             config: RunnableConfig = None,
                             point_cloud_source: str = POINT_CLOUD_DEFAULT_SOURCE) -> dict:
    """
    Multi-frame grounding union: runs text-prompted instance segmentation
    (SAM3) for `object_label` over ALL available frames (1-32), lifts each
    detected instance mask to a robust 3D point set, and clusters the
    per-detection 3D centroids into distinct physical instances. Deterministic
    perception/geometry primitive — segmentation + clustering only, no VLM,
    no question-specific logic.

    Use this when single-frame grounding may miss instances that are only
    visible in a few frames — e.g. to enumerate every physical instance of a
    label in the scene before measuring or comparing them. Frames where the
    label is not detected are skipped.

    Args:
        scene_id: VSIBench scene identifier.
        object_label: Natural-language label, e.g. "door", "window".
        point_cloud_source: Optional source for lifting masks. Default
            "g3t_scaled" is the same for every question; alternatives are
            "mapanything" and "unik3d". Choose explicitly inside the trace.

    Returns:
        dict —
          "object_label":            str
          "n_frames_processed":      int
          "n_frames_with_detection": int
          "n_detections":            int   # per-frame detections lifted to 3D
          "n_instances":             int   # physical instance clusters
          "instances": per-instance table, one row per physical instance:
              {"instance_idx", "n_frames_seen", "frames_seen", "n_detections",
               "centroid_xyz", "min_xyz_p5", "max_xyz_p95", "extent_xyz"}
        Returns {"error": "..."} on failure.
    """
    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError as e:
        return {"error": str(e)}
    dense = _load_dense(scene_id, point_cloud_source=source_key)
    if dense is None:
        return {"error": f"Dense outputs not found for scene {scene_id}."}
    cache = _load_frames_cache()
    if not cache or scene_id not in cache:
        return {"error": f"Scene {scene_id} not found."}
    frame_names = cache[scene_id]["frame_names"]
    n_frames = min(len(frame_names), 32)
    detections = []
    index_miss = []
    frames_with_det = set()
    for fi in range(1, n_frames + 1):
        if not frame_names[fi - 1]:
            continue
        # Reuse the deployed single-frame SAM3 machinery + its process cache.
        insts = predict_2d_segmentation_masks.func(scene_id, fi, object_label, config=None)
        if not isinstance(insts, list):
            continue
        for inst in insts:
            if not isinstance(inst, dict) or "error" in inst:
                continue
            pts = _count3d_detection_pts(
                inst.get("mask_handle"), scene_id, fi, dense, miss_sink=index_miss)
            if pts is None or len(pts) == 0:
                continue
            detections.append((fi, inst.get("instance_id", 0),
                               np.median(pts, axis=0),
                               np.percentile(pts, 5, axis=0),
                               np.percentile(pts, 95, axis=0)))
            frames_with_det.add(fi)
    if index_miss:
        result = {"error": "frame_index_unmappable",
                  "frames": sorted(set(index_miss)),
                  "scene_id": scene_id, "point_cloud_source": source_key,
                  "detail": "dense store index mismatch — count withheld (fail-closed)"}
        if config is not None:
            trace_list = config.get("configurable", {}).get("trace_list")
            if trace_list is not None:
                trace_list.append({"tool": "ground_object_all_frames", "response": str(result)})
        return result
    union = _ground_union_instances(detections)
    if "error" in union:
        return union
    result = {
        "object_label":            object_label,
        "n_frames_processed":      n_frames,
        "n_frames_with_detection": len(frames_with_det),
        "n_detections":            len(detections),
        "n_instances":             len(union["instances"]),
        "instances":               union["instances"],
        "point_cloud_source":      source_key,
    }
    if config is not None:
        trace_list = config.get("configurable", {}).get("trace_list")
        if trace_list is not None:
            trace_list.append({"tool": "ground_object_all_frames", "response": str(result)})
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Coordinate / math tools (no VLM, no dense data)
# ─────────────────────────────────────────────────────────────────────────────
# NOTE: get_room_dimensions and get_all_object_instances_3d were intentionally
# removed from this agent — see amazing_tools.py.

@tool
def transform_to_observer_frame(observer_position: list[float],
                                observer_facing: list[float],
                                target_points: list[list[float]],
                                config: RunnableConfig = None) -> dict:
    """
    Re-expresses 3D world points (Z-up) in an observer-centric frame and reports
    each as range / signed bearing / elevation plus an 8-sector direction label.

    Deterministic geometry primitive — no VLM, no estimation. Builds the
    observer frame from a position and a horizontal facing direction (both in
    world Z-up coordinates), rotates each target point into that frame, and
    reports where each point lies relative to the observer.

    Args:
        observer_position: [x, y, z] world coordinates of the observer (meters).
            A 2-element [x, y] is accepted (z assumed 0).
        observer_facing: the world-space direction the observer faces, as
            [dx, dy] or [dx, dy, dz]; only the horizontal (XY) component is
            used and it need not be unit length. E.g. facing toward a point P
            from position O: use [P[0]-O[0], P[1]-O[1]].
        target_points: list of [x, y, z] world points to re-express
            ([x, y] accepted, z assumed 0).

    Returns:
        dict:
            "points": one entry per target point —
                "range_m":       Euclidean observer->point distance (meters)
                "horizontal_range_m": XY-plane distance (meters)
                "bearing_deg":   signed horizontal angle from the facing
                                 direction; positive = LEFT of facing,
                                 negative = RIGHT of facing, 0 = dead ahead,
                                 +/-180 = directly behind
                "elevation_deg": vertical angle above (+) / below (-) the
                                 observer's horizontal plane
                "sector":        one of "front", "front-left", "left",
                                 "back-left", "back", "back-right", "right",
                                 "front-right" (45-degree sectors centered on
                                 the bearing)
            "n_points": int
        Returns {"error": "..."} on malformed input.
    """
    try:
        op = np.asarray(observer_position, dtype=float).ravel()
        if op.size == 2:
            op = np.array([op[0], op[1], 0.0])
        if op.size != 3 or not np.isfinite(op).all():
            return {"error": "observer_position must be [x, y, z] finite floats"}
        fv = np.asarray(observer_facing, dtype=float).ravel()
        fx, fy = float(fv[0]), float(fv[1])
        norm = float(np.hypot(fx, fy))
        if not np.isfinite(norm) or norm < 1e-9:
            return {"error": "observer_facing must have a non-zero horizontal (XY) component"}
        fx, fy = fx / norm, fy / norm
        out = []
        _SECTORS = ["front", "front-left", "left", "back-left",
                    "back", "back-right", "right", "front-right"]
        for tp in target_points:
            t = np.asarray(tp, dtype=float).ravel()
            if t.size == 2:
                t = np.array([t[0], t[1], 0.0])
            if t.size != 3 or not np.isfinite(t).all():
                out.append({"error": f"bad target point {tp}"})
                continue
            d = t - op
            ahead = d[0] * fx + d[1] * fy           # along facing
            left  = -d[0] * fy + d[1] * fx          # 90 deg CCW from facing
            bearing = float(np.degrees(np.arctan2(left, ahead)))
            hr = float(np.hypot(d[0], d[1]))
            rng = float(np.linalg.norm(d))
            elev = float(np.degrees(np.arctan2(d[2], hr))) if hr > 1e-9 else (
                90.0 if d[2] > 0 else (-90.0 if d[2] < 0 else 0.0))
            sector = _SECTORS[int(((bearing + 22.5) % 360.0) // 45.0)]
            out.append({"range_m": round(rng, 4),
                        "horizontal_range_m": round(hr, 4),
                        "bearing_deg": round(bearing, 2),
                        "elevation_deg": round(elev, 2),
                        "sector": sector})
        result = {"points": out, "n_points": len(out)}
        if config is not None:
            trace_list = config.get("configurable", {}).get("trace_list")
            if trace_list is not None:
                trace_list.append({"tool": "transform_to_observer_frame",
                                   "response": str(result)})
        return result
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


@tool
def get_camera_pose(scene_id: str, frame_index: int,
                    point_cloud_source: str = POINT_CLOUD_DEFAULT_SOURCE) -> list[list[float]]:
    """
    Returns the 4×4 camera-to-world pose matrix for a given frame.

    WORLD COORDINATE SYSTEM: floor = XY plane, Z = up (vertical height).

    Use this when you need the camera position itself (e.g. to determine what direction
    the camera is facing, or for any task requiring the camera trajectory or
    per-frame viewpoint). You do NOT need this tool just to get 3D object
    positions — use get_world_3d_point_from_2d instead.

    Args:
        scene_id: VSIBench scene identifier.
        frame_index: 1-based frame number (1–32).
        point_cloud_source: Optional source for the pose table. Default
            "g3t_scaled" is the same for every question; alternatives are
            "mapanything" and "unik3d". Choose explicitly inside the trace.

    Returns:
        4×4 list-of-lists matrix M where M[:3, 3] is the camera's world position (meters)
        and M[:3, :3] is the rotation matrix. Returns [["Error: ..."]] on failure.
    """
    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError as e:
        return [[f"Error: {e}"]]
    dense = _load_dense(scene_id, point_cloud_source=source_key)
    if dense is not None:
        npz_idx = _frame_index_to_npz_idx(scene_id, frame_index, dense)
        if npz_idx is not None:
            pose = dense["camera_poses"][npz_idx]
            return [[round(float(v), 4) for v in row] for row in pose.tolist()]

    # [addendum-131 F2] Fail closed: the primary dense-npz pose lookup did not
    # yield a pose — either the store npz is missing for this scene, or the
    # canonical frame index is absent from the store's own `indices` array (see
    # _frame_index_to_npz_idx's fail-closed None). The former JSON fallback here
    # (default source only) was doubly unsafe: (1) it read
    # agent/mapanything_poses_vsibench.json — RAW, un-rescaled MapAnything poses,
    # a DIFFERENT backbone from metric g3t_scaled, mixing metric frames under a
    # g3t_scaled label; and (2) it composed T_world @ M_opencv @ T_cam whose 3x3
    # block has determinant -1 (an improper rotation / mirror, since
    # det(T_cam[:3,:3]) = -1), so it handed back a reflected pose with no mismatch
    # signal to the trace. No promoted VSTI-450 / VSI-500q scene reaches this path
    # (the 43 g3t_scaled-missing scenes are disjoint from both promoted sets), so
    # removing it changes no promoted result. Surface a hard error instead so no
    # trace can consume a mis-provenanced pose.
    return [[f"Error: camera pose unavailable for scene {scene_id} frame "
             f"{frame_index} in point_cloud_source={source_key} "
             f"(dense store missing or frame index absent from store)."]]


@tool
def apply_coordinate_transform(local_camera_point: list[float], pose_matrix: list[list[float]]) -> list[float]:
    """
    Converts a 3D point from camera space to world space using a pose matrix.

    Use this ONLY when you have a camera-frame point from a non-dense source
    (e.g. you measured depth manually). For normal use, prefer get_world_3d_point_from_2d
    which returns world coordinates directly.

    WORLD COORDINATE SYSTEM: floor = XY plane, Z = up (vertical height).

    Args:
        local_camera_point: [X, Y, Z] in camera coordinates (meters).
        pose_matrix: 4×4 camera-to-world matrix from get_camera_pose.

    Returns:
        [X, Y, Z] in world coordinates (meters).
    """
    try:
        p_world = np.array(pose_matrix) @ np.array(local_camera_point[:3] + [1.0])
        return [round(float(v), 4) for v in p_world[:3]]
    except Exception as e: return [f"Error: {e}"]


def _alpha_shape_area(points_xy, alpha: float = 0.6) -> float:
    """concave-hull (alpha-shape) area of 2D XY points — a footprint-area
    estimator that follows the true outline of a concave point set, unlike a
    bounding rectangle or convex hull which systematically OVER-estimate
    L-shaped / concave regions by filling the empty region. Implementation:
    sum the areas of Delaunay triangles whose
    circumradius <= `alpha` metres (the alpha-complex). `alpha` ~0.5-0.8 m spans
    floor sampling gaps without bridging real concavities/holes. Deterministic;
    no external deps beyond scipy/numpy. Returns area in m^2 (0.0 on failure)."""
    from scipy.spatial import Delaunay as _Del
    p = np.asarray(points_xy, dtype=float)
    if p.ndim != 2 or p.shape[1] != 2 or len(p) < 3:
        return 0.0
    if len(p) > 60000:
        p = p[np.random.default_rng(0).choice(len(p), 60000, replace=False)]
    try:
        tri = _Del(p)
    except Exception:
        return 0.0
    s = p[tri.simplices]
    a = np.linalg.norm(s[:, 0] - s[:, 1], axis=1)
    b = np.linalg.norm(s[:, 1] - s[:, 2], axis=1)
    c = np.linalg.norm(s[:, 2] - s[:, 0], axis=1)
    sp = (a + b + c) / 2.0
    area = np.sqrt(np.clip(sp * (sp - a) * (sp - b) * (sp - c), 0, None))
    nz = area > 1e-9
    circ = np.full_like(area, np.inf)
    circ[nz] = (a[nz] * b[nz] * c[nz]) / (4.0 * area[nz])
    return float(area[(circ <= float(alpha)) & nz].sum())


def _closest_point_distance(pts_a, pts_b) -> dict:
    """DG-GATE (r214): robust closest-approach distance between two 3D point
    clouds. The hard `cKDTree(a).query(b)[0].min()` collapses to ~0 m when a
    single bled/misgrounded pixel of one cloud lands inside the other; the 5th
    percentile of the per-point nearest-neighbor distances is a low-percentile
    consensus that survives isolated contaminated points. An inter-cloud
    distance < 0.10 m between two DISTINCT labels is flagged as co-location
    (the same surface was likely grounded twice — re-ground one object)."""
    from scipy.spatial import cKDTree
    a = np.asarray(pts_a, dtype=np.float64).reshape(-1, 3)
    b = np.asarray(pts_b, dtype=np.float64).reshape(-1, 3)
    if len(a) == 0 or len(b) == 0:
        return {"error": "empty point cloud"}
    d = cKDTree(a).query(b)[0]
    dist = float(np.percentile(d, 5))
    out = {"distance": round(dist, 4),
           "min_raw": round(float(d.min()), 4),
           "n_a": int(len(a)), "n_b": int(len(b))}
    if dist < 0.10:
        out["co_location_flag"] = True
        out["instruction"] = ("distance < 0.10 m between two distinct labels — "
                              "likely the same surface grounded twice; re-ground "
                              "one object on a different frame before trusting "
                              "this distance.")
    return out


@tool
def execute_python_code(code: str) -> str:
    """
    Executes Python code in a sandboxed subprocess. Use for math calculations
    AND for raw dense-array geometry the question requires.

    Available in scope:
      - `np` (numpy), `math`.
      - `load_dense(scene_id, point_cloud_source="g3t_scaled") -> dict` returns
        the raw dense outputs for the scene (non-RANSAC). Keys: `pts3d_world` (N,H,W,3) world Z-up
        points, `depth_z` (N,H,W), `intrinsics` (N,3,3), `conf` (N,H,W),
        `mask` (N,H,W) valid-pixel mask, `camera_poses` (N,4,4) cam2world,
        `indices` (N,) original frame indices. N is the per-scene frame count
        (typically 32 for the legacy outputs).
      - `load_ransac_dense(scene_id, point_cloud_source="g3t_scaled") -> dict`
        same layout but gravity-aligned when that source has a RANSAC variant
        (RANSAC-rotated so the floor lies in the XY plane). Use this when you
        need the floor or gravity-aligned vertical extent. Falls back to
        load_dense if the RANSAC file is missing for that source/scene.
      - Valid point_cloud_source values: g3t_scaled (default for every question;
        best validated overall metric cloud for scale-sensitive geometry),
        mapanything (stable multi-view layout/trajectory fallback), and unik3d
        (metric depth-oriented alternative for independent scale/depth checks).
        Select inside this code only when the question/evidence justifies it;
        do not rely on launcher/category/GT preselection.
      - `alpha_shape_area(points_xy, alpha=0.6) -> float`: concave-hull
        (alpha-shape) area in m^2 of a 2D XY point set. A smaller alpha hugs the
        outline more tightly (and may fragment a sparse set); a larger alpha
        fills concavities toward the convex hull. Useful for the footprint area
        of a non-convex point set, where a bounding rectangle or convex hull
        over-estimates by filling empty region.

    Cannot call other agent tools (predict_2d_bounding_box, etc.) — gather VLM
    outputs first, then compute everything else here.
    60-second timeout. Print your final result; the last stdout is returned.

    r47: load_dense / load_ransac_dense added to the sandbox so the agent can
    write its own dense-aggregation code (e.g. floor-plan area via a 2D
    occupancy grid, or class-class horizontal distance over the full point
    cloud) without depending on any "delivers-the-answer" tool.

    Args:
        code: Python code string. Do NOT include markdown fences.

    Returns:
        String output from the code's print() statements, or an error message.
    """
    # r107: blocklist GT-bearing files. r106 had 33/150 traces (22%) read
    # `original_vsibench_full.json` directly to get answers — benchmark
    # integrity issue. The verifier flagged this in some traces but the agent
    # ignored its FAIL verdict. Block at the sandbox boundary so the file is
    # unreachable, not just discouraged.
    _BLOCKED_GT_SUBSTRINGS = (
        "original_vsibench_full",
        "tiny_centroids_last_10_vsibench",
        "tiny_last_15_vsibench",
        "gt_eval_raw",
        "gt_eval_ransac",
        "offline_labels", "vsi_590k.jsonl", "train50k_scene_reuse_labels",
        "baseline_annotations", "answer_banks",
    )
    code_lower = code.lower()
    for blocked in _BLOCKED_GT_SUBSTRINGS:
        if blocked in code_lower:
            return f"Error: forbidden — code references blocked GT-bearing file ('{blocked}'). Use perception tools to derive answers, do not read benchmark files."

    import multiprocessing
    def _worker(c, q):
        out = io.StringIO()
        try:
            # SANDBOX ISOLATION (clean round r310; AGENTS section 7 answer-valued-tool ban): the
            # planner must COMPOSE the answer from primitives in code it writes — never import a
            # project module to call a pre-built answer function (tools_room_area.estimate_room_area,
            # amazing_tools.get_room_dimensions / get_all_object_instances_3d, or this agent module's
            # own count_instances_3d / estimate_scene_footprint) to shortcut the retired tools. This
            # runs in a forked subprocess, so we make NO repo .py importable in the sandbox: (1) drop
            # every repo dir from sys.path (blocks `import X` AND importlib.import_module for repo
            # files), and (2) purge any already-loaded repo module from THIS child's import cache (the
            # running agent module lives there). numpy / scipy / stdlib still import; the sandbox
            # primitives (load_dense, ...) are LIVE objects.
            import sys as _sys
            _REPO_ROOTS = (os.path.realpath("/home/jjyeung/agent_project"),
                           os.path.realpath(os.path.dirname(__file__)))
            def _is_project_path(value):
                resolved = os.path.realpath(value)
                return any(resolved == root or resolved.startswith(root + os.sep) for root in _REPO_ROOTS)
            # NOTE: realpath("") resolves to cwd, so the empty-string ("" = cwd) sys.path entry
            # is filtered too (cwd is the repo's agent/ dir at runtime — without this it leaks).
            _sys.path[:] = [p for p in _sys.path if not _is_project_path(p)]
            for _name in list(_sys.modules):
                _f = getattr(_sys.modules.get(_name), "__file__", None)
                if _f and _is_project_path(_f):
                    _sys.modules.pop(_name, None)
            # r314 SANDBOX HARDENING — PREVENTION (not detection) of the answer-leak escapes that the
            # sys.path/sys.modules purge above does NOT close (all verified live in r310/r311). Three
            # confirmed escapes + the fixes:
            #   (1) RE-IMPORT: `import sys; sys.path.insert(0, '<repo>/agent'); import tools_room_area`
            #       re-imports a retired answer module (the one-time path purge is reversible).
            #       FIX: a guarded __import__ that blocks repo/answer modules BY TOP-LEVEL NAME, so
            #       sys.path manipulation can't help.
            #   (2) OBJECT-GRAPH: `load_dense.__globals__['count_instances_3d' | 'estimate_scene_footprint'
            #       | 'get_all_object_instances_3d' | 'ground_object_all_frames' | '_room_area_module'
            #       | '_oracle_*'](...)` reaches an answer-valued fn without `import`.
            #       FIX: delete those names from the shared module global dict (load_dense.__globals__);
            #       all module fns share ONE dict so one pass closes every reachable path. (Defense in
            #       depth alongside the import guard, since _room_area_module itself re-imports.)
            #   (3) GT-FILE READ: `json.load(open('<repo>/agent/tiny_even_500_vsibench.json'))[...]['ground_truth']`
            #       reads the answer directly. FIX: a guarded open() that denies benchmark/GT file paths.
            # Also remove eval/exec/compile from the sandbox builtins (0 legitimate uses across 32,568
            # audited planner blocks; blocks dynamic reconstruction of the above). Everything is mutated
            # only in THIS forked child (COW) — the parent process's real tools are untouched. The
            # retained primitives (load_dense / load_ransac_dense / alpha_shape_area /
            # closest_point_distance) do not call any blocked name and keep working; legitimate
            # numpy/scipy/cv2/sklearn/stdlib imports and frame-image opens are unaffected.
            _SANDBOX_FORBIDDEN_GLOBALS = (
                "count_instances_3d", "count_object_instances_3d", "get_object_instances_3d",
                "estimate_scene_footprint", "get_room_footprint_area", "estimate_room_area",
                "get_all_object_instances_3d", "get_room_dimensions",
                "ground_object_all_frames", "_room_area_module",
                "_oracle_gt_3d_summary_for_object", "_oracle_projected_2d_bboxes",
            )
            _modg = _load_dense.__globals__
            for _bad in _SANDBOX_FORBIDDEN_GLOBALS:
                _modg.pop(_bad, None)

            # NOTE (team-lead decision 2026-06-26): we deliberately DO NOT add a restricted-builtins /
            # whitelist-import jail here. A 3-round dual-critique proved in-process CPython sandboxing
            # is not airtight (sys.modules['builtins'] / numpy-C-open / importlib-by-file-path bypass
            # any in-process guard, and sys/os/numpy must stay available for the legal primitives), and
            # the paper does NOT claim an airtight jail. The honest, provable claim is "tools return
            # only primitives; answer-valued tools are NOT registered; a zero-exploit audit of every
            # execute_python_code block finds zero GT-reads / answer-imports" (see
            # agent/audit_sandbox_exploits.py = the real assurance). The __globals__ blocklist-del above
            # + that post-run audit are the cheap defense-in-depth; an OS-level bwrap jail is a
            # documented back-pocket (COMBINED_FINDINGS.md) if a reviewer demands OS isolation. Keeping
            # the exec namespace standard avoids destabilizing legit planner code (15,895 audited
            # blocks) right before the clean headline run. (A validated whitelist-import variant exists
            # in git history at commit 6cc6cb5 if stronger casual-path blocking is ever wanted.)
            sandbox = {
                'np': np,
                'math': math,
                'load_dense': _load_dense,
                'load_ransac_dense': _load_ransac_dense,
                'point_cloud_sources': sorted(_POINT_CLOUD_SOURCES),
                'alpha_shape_area': _alpha_shape_area,   # concave-hull floor area primitive
            }
            if _DG_GATE:
                # DG-GATE (r214): robust closest-point primitive replaces the
                # collapse-prone hard cKDTree min() in agent-written code.
                sandbox['closest_point_distance'] = _closest_point_distance
            with contextlib.redirect_stdout(out):
                exec(c, sandbox)
            q.put(out.getvalue())
        except Exception as e: q.put(str(e))
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=_worker, args=(code.strip('`').replace('python\n', ''), q))
    # r203: 60s (was 10s) — the baked tools run their voxel-merge/alpha-shape/KD-tree
    # compute UNBOUNDED; capping the agent's equivalent in-sandbox compute at 10s
    # unfairly timed out legitimate heavy geometry. 60s = ~30x the heaviest measured numpy.
    p.start(); p.join(timeout=60)
    if p.is_alive(): p.terminate(); return "Error: Timeout (exceeded 60s)."
    return q.get() if not q.empty() else "Error: No output."


# ─────────────────────────────────────────────────────────────────────────────
# Verification tools
# ─────────────────────────────────────────────────────────────────────────────

def _verifier_status(text: str) -> str:
    """Convert a provider verifier response to typed routing metadata."""
    normalized = (text or "").lstrip().upper()
    if normalized.startswith("VERDICT: FAIL"):
        return "FAIL"
    if normalized.startswith("VERDICT: PASS") or normalized.startswith("VERDICT: OK"):
        return "PASS"
    return "OTHER"


def _run_verifier(prompt: str, config: RunnableConfig, tool_name: str) -> tuple[str, dict]:
    """r111: never return an empty string from the verifier — the agent
    interprets empty responses as `<ANSWER>` cues and emits guesses (route_planning
    qid 5096 lost a correct B answer this way). On API error or empty response,
    return an explicit non-empty SKIPPED disclosure so it cannot be mistaken for
    a verifier approval."""
    fallback = ("VERDICT: SKIPPED — verifier unavailable; verification was NOT performed "
                "(this is not an approval). Re-check your own execution summary and "
                "computation before committing your answer.")
    try:
        text = _google_multimodal(
            [("text", prompt)],
            model=_verifier_model(),
            temperature=0.0,
            thinking_level="high",
            max_output_tokens=2048,
            usage_sink=_usage_sink_from_config(config),
        )
        if not text or not text.strip():
            text = fallback
            trace_list = config.get("configurable", {}).get("trace_list")
            if trace_list is not None:
                trace_list.append({"tool": tool_name, "response": text,
                                   "verifier_skipped": True,
                                   "verifier_status": "SKIPPED",
                                   "error_class": "empty_response"})
            return text, {"verifier_status": "SKIPPED", "error_class": "empty_response"}
        trace_list = config.get("configurable", {}).get("trace_list")
        status = _verifier_status(text)
        if trace_list is not None:
            trace_list.append({"tool": tool_name, "response": text,
                               "verifier_status": status})
        return text, {"verifier_status": status}
    except Exception as e:
        # Raw exception text is telemetry-only by class. It must never enter model-visible
        # content because adversarial/provider text can contain verdict-shaped substrings.
        text = fallback
        trace_list = config.get("configurable", {}).get("trace_list")
        if trace_list is not None:
            trace_list.append({"tool": tool_name, "response": text,
                               "verifier_skipped": True,
                               "verifier_status": "SKIPPED",
                               "error_class": type(e).__name__})
        return text, {"verifier_status": "SKIPPED", "error_class": type(e).__name__}


def _tool_verifier_status(message) -> str:
    """Read verifier routing only from the ToolMessage's typed artifact."""
    artifact = getattr(message, "artifact", None)
    if not isinstance(artifact, dict):
        return "MISSING"
    status = artifact.get("verifier_status")
    return status if status in {"FAIL", "PASS", "OTHER", "SKIPPED"} else "MISSING"


def _post_verify_done_notification_text(last_message) -> str:
    """Planner post-verify else-branch notification (skip-aware, routing-identical)."""
    if _tool_verifier_status(last_message) == "SKIPPED":
        return (
            "[SYSTEM NOTIFICATION]: Post-verification was SKIPPED (verifier unavailable) — your "
            "execution summary was NOT reviewed. Your verify budget is used. Re-check your computation "
            "yourself, then emit ONLY <ANSWER>...</ANSWER> now — no more tool calls."
        )
    return (
        "[SYSTEM NOTIFICATION]: Post-verification step complete. "
        "You have used your single post-verify. "
        "Emit ONLY <ANSWER>...</ANSWER> now — no more tool calls."
    )


def _pre_verify_not_failed_notification_text(last_message) -> str:
    """Planner pre-verify not-failed-branch notification (skip-aware, routing-identical)."""
    if _tool_verifier_status(last_message) == "SKIPPED":
        return (
            "[SYSTEM NOTIFICATION]: Verification was SKIPPED (verifier unavailable) — your plan was "
            "NOT reviewed. Proceed carefully: execute your plan now — call your next "
            "geometry/perception tool to gather evidence. Do NOT emit <ANSWER> yet, do NOT return an "
            "empty step."
        )
    return (
        "[SYSTEM NOTIFICATION]: Your plan was APPROVED. Execute it now — "
        "call your next geometry/perception tool to gather evidence. "
        "Do NOT emit <ANSWER> yet, do NOT return an empty step."
    )


@tool(response_format="content_and_artifact")
def verify_plan_pre_execution(plan_text: str, question: str, config: RunnableConfig) -> tuple[str, dict]:
    """
    MANDATORY before fetching any data. Critiques your step-by-step plan for correctness.

    Submit your full plan including:
    - Which tools you will call in what order
    - The placeholder Python code you plan to run
    - Your aggregation strategy (median, clustering, etc.)

    Args:
        plan_text: Your detailed plan, including pseudocode.
        question: The original question being answered.

    Returns:
        "VERDICT: PASS" if the plan is correct, or "VERDICT: FAIL" with explanation.
    """
    prompt = (
        f"Question: {question}\n\nCritique this spatial reasoning PLAN (pre-execution):\n{plan_text}\n\n"
        + _VERIFIER_RULES
    )
    return _run_verifier(prompt, config, "verify_plan_pre_execution")


@tool(response_format="content_and_artifact")
def verify_plan_post_execution(execution_summary: str, question: str, config: RunnableConfig) -> tuple[str, dict]:
    """
    MANDATORY after computing the final answer. Checks for hallucinated coordinates
    and math errors in the executed code.

    Submit your full execution trace including:
    - All tool call results (exact numbers returned)
    - The Python code you ran
    - The final computed answer

    Args:
        execution_summary: Your execution trace with all tool outputs and code.
        question: The original question being answered.

    Returns:
        "VERDICT: PASS" if execution is correct, or "VERDICT: FAIL" with exact hallucination details.
        If the verifier service is unavailable, returns "VERDICT: SKIPPED" — verification was not
        performed; do not treat it as approval.
    """
    prompt = (
        f"Question: {question}\n\nCritique this spatial reasoning EXECUTION (post-execution):\n{execution_summary}\n\n"
        + _VERIFIER_RULES
    )
    return _run_verifier(prompt, config, "verify_plan_post_execution")


_VERIFIER_RULES = """
You are a Senior Spatial Engineer and Code Reviewer.

WORLD COORDINATE SYSTEM:
  - Floor lies in the XY plane. Z is the vertical axis (up).
  - "Horizontal distance" / "floor distance" uses only X and Y.
  - "Height" / "vertical" uses Z.
  - All 3D tools return coordinates in this convention.

TOOL SEMANTICS:
  - `find_frames_with_object(scene_id, object_label, num_frames)`:
      "5" (default) → 5 best frames for 3D localization, including first and last visible.
      "1" → the first chronological frame the object is visible in.
      "all" → every frame the object is clearly visible in.
  - `get_frame_image(scene_id, frame_index)` → local PNG path for the frame.
  - `predict_2d_bounding_box(scene_id, frame_index, object_label)` → normalized [0,1] bboxes for all visible instances. A bbox with xmin>=xmax, ymin>=ymax, or area > 90% of the image is a detection artifact.
  - Point-cloud source policy: every question defaults to `point_cloud_source="g3t_scaled"`. Valid explicit alternatives are `mapanything` (stable multi-view layout/trajectory fallback, but weaker metric scale) and `unik3d` (metric depth-oriented, useful for independent scale/depth checks but less vetted for multi-view layout). Do not assume a launcher/category preselected a source, do not use benchmark GT/category score history to choose one, and do not mix points from one source with poses from another.
  - `predict_2d_points(scene_id, frame_index, query, point_cloud_source="g3t_scaled")` → list of {pixel_norm, world, label, point_cloud_source}, each pixel averaged over a small patch and lifted to world XYZ from the selected source.
  - `predict_2d_segmentation_masks(scene_id, frame_index, object_label)` → list of {instance_id, score, bbox_pixels, bbox_norm, area_norm, mask_handle}. Mask is a binary (H,W) bool stored on disk; np.load(mask_handle) inside execute_python_code yields the array.
  - `predict_2d_segmentation_masks_video(scene_id, object_label, frame_indices)` → SAM3 native VIDEO tracking; returns per-frame instance masks where `instance_id` is CONSISTENT across frames (same physical instance keeps its id), plus per-frame and cross-frame instance tallies. This IS a valid, registered tool — NEVER output VERDICT: FAIL on the grounds that this tool "does not exist" or "is hallucinated"; using it is correct.
  - `query_3d_bbox_catalogue(scene_id, frame_index=None, score_min=0.3)` → {n_dets, scores, boxes_2d, boxes_3d_center_world (Z-up), boxes_3d_size, frame_indices}. Capped to top-K by score (50 scene-wide, 25 per-frame). No semantic vocabulary — boxes are class-agnostic.
  - `get_world_3d_point_from_2d(scene_id, frame_index, x, y, point_cloud_source="g3t_scaled")` → world-space [X,Y,Z] for one normalized pixel.
  - `get_3d_points_in_bbox(scene_id, frame_index, xmin, ymin, xmax, ymax, point_cloud_source="g3t_scaled")` → {centroid, extent_xyz_p90, min_xyz_p5, max_xyz_p95, floor_z_estimate, num_valid_points, point_cloud_source}. `extent_xyz_p90` is the only extent reported (the robust p95-p5 form). The raw (max-min) extent is not exposed because it is systematically inflated by depth bleed into walls/ceiling. Use (0,0,1,1) for the full frame.
  - `get_3d_points_in_mask(scene_id, frame_index, mask_dense_handle, point_cloud_source="g3t_scaled")` → identical return shape as `get_3d_points_in_bbox`, but the input region is the SAM 3 dense-resampled mask. Tighter — silhouette-follows-object. AABB-summary stats only.
  - `cluster_3d_points(points, eps=0.5, min_samples=5)` → standard Euclidean DBSCAN; returns `num_clusters`, cluster medians/sizes, and labels (`-1` is noise). `min_samples` includes the point itself. No post-DBSCAN support recount or singleton absorption is applied.
  - `aggregate_aabbs_median(aabbs)` → reduces a list of per-frame get_3d_points_in_bbox results into one robust AABB via per-axis median of min_xyz_p5/max_xyz_p95 across frames. Always prefer this over a hand-written min(mins)/max(maxs) UNION — the union silently grows the box with every per-frame outlier, whereas the median of each corner across frames is the robust reduction.
  - `aggregate_aabbs_robust(aabbs)` → endpointwise Tukey adjacent-value AABB: exclude values beyond the standard 1.5×IQR inner fences, then take the smallest retained lower endpoint and largest retained upper endpoint on each axis.
  - `get_camera_pose(scene_id, frame_index, point_cloud_source="g3t_scaled")` → cam2world 4×4 in Z-up from the selected source.
  - `apply_coordinate_transform(points, matrix)` → deterministic 4×4 transform. Output of get_3d_points_in_bbox or get_world_3d_point_from_2d is already world-space — do not double-transform.
  - `execute_python_code(code)` → runs numpy/math snippets and returns print() output. The sandbox has `np` (numpy), `math`, plus two pre-registered data loaders that are NOT hallucinated tools: `load_dense(scene_id, point_cloud_source="g3t_scaled")` and `load_ransac_dense(scene_id, point_cloud_source="g3t_scaled")` — both return dicts with dense outputs (pts3d_world, depth_z, intrinsics, conf, mask, camera_poses, indices, point_cloud_source). Use load_ransac_dense whenever the code filters by world-Z (floor extraction, vertical extents, slab-based area). Judge inputs/outputs, not style.

SIMPLICITY PRINCIPLE:
  - If the agent's plan is simple AND correct, return VERDICT: PASS.
  - Only fail when the plan is actually incorrect. "More evidence" is not a valid failure reason.

STRICT RULES:
1. 3D Math: Euclidean distance is sqrt(dx^2 + dy^2 + dz^2). Drop Z only for horizontal/floor distance questions.
2. Aggregation: Multi-frame centroid observations should be aggregated (median across frames) to reject outliers.
3. Hallucination Check (post-execution only): any RAW INPUT coordinate the code hard-codes (i.e. a number presented as having come from a tool — a centroid, bbox corner, or world point) MUST exactly match that tool's actual output; a fabricated or miscopied INPUT is 'VERDICT: FAIL' (specify which). BUT values the code COMPUTES from valid inputs — distances, medians, aggregates, extents, cluster counts, cKDTree minima — are expected DERIVED outputs, NOT hallucinations: never FAIL a correctly-derived result merely because the number does not appear verbatim in a prior tool output. Only the hard-coded inputs must be traceable.
4. Floor-area estimator (post-execution only, general geometric guidance): for the 2D footprint area of a concave or only-partially-observed point set, a bounding rectangle / convex hull / PCA-OBB systematically OVER-estimates by filling empty region (e.g. an L-shaped or alcoved room), while a concave-hull / alpha-shape area follows the true outline more faithfully. If the final area came from a bounding rectangle on a clearly non-rectangular footprint, note that it is likely inflated so the agent can reconsider a tighter outline — but do not mandate one specific estimator. This is generic computational-geometry guidance, not tied to any benchmark.
5. Magnitude sanity (post-execution only — generic geometric outliers):
   a. Inter-object distances: if two distinct named objects are reported as < 0.30 m apart, the bounding boxes likely overlap or one collapsed onto the other; output 'VERDICT: FAIL' with "candidate distance below sensor noise floor — re-ground with a different frame or call predict_2d_segmentation_masks".
   b. Cross-room contamination: if any single-object centroid spans > 5 m on any axis across frames OR a multi-frame AABB has an extent > 5 m on any axis, the bbox is bleeding across rooms or absorbing depth-clip; output 'VERDICT: FAIL' with "centroid/extent exceeds plausible single-object span — drop the outlier frame or re-bbox".
   c. Estimator disagreement on area scalars: if multiple area estimators are present and max/min > 2.0, the floor mask is misclassified; output 'VERDICT: FAIL' with "estimators disagree by >2× — refit the floor slab and rerun".
   d. Distance-vs-room-extent: if a predicted distance exceeds 2× the longest extent of `query_3d_bbox_catalogue`'s scene-wide AABBs, the frames are mismatched; output 'VERDICT: FAIL'.
   These checks fire on numeric outputs in `execute_python_code` stdout — they are question-agnostic geometric sanity checks, not category-specific solution rules.
6. Closest-point distance must use raw point clouds, not AABB summaries (post-execution only). When the question asks for the distance between two physical objects (any "how far is X from Y" / "what's the distance between X and Y" / "which is closer" phrasing), the executed code must (a) load raw 3D points for each object via `np.load(mask_dense_handle) & valid_mask` indexed into `pts3d_world`, and (b) compute pairwise minimum distance via `scipy.spatial.cKDTree(pts_a).query(pts_b)[0].min()`. AABB-to-AABB distances (from `get_3d_points_in_bbox`, `get_3d_points_in_mask`, or `aggregate_aabbs_*` summaries alone) collapse to ~0 m whenever two AABBs overlap and are mathematically the wrong primitive — output 'VERDICT: FAIL' with "use raw point-cloud cKDTree query, not AABB summary" if the executed code derived its distance from `min_xyz_p5`/`max_xyz_p95` instead of `np.load`+cKDTree. Generic geometric rule, applies to any closest-point distance query.
7. Trust pre-verified deterministic-primitive outputs (post-execution only). When `verify_plan_pre_execution` already returned PASS on a plan whose final answer is read directly from a deterministic-primitive return field — `cluster_3d_points.num_clusters`, `aggregate_aabbs_median.extent_xyz`, `aggregate_aabbs_robust.extent_xyz`, `get_3d_points_in_*.centroid` / `.extent_xyz_p90`, `cKDTree(...).query(...)[0].min()` — and that primitive call has actually executed and returned a value without an `error` field — the agent should commit that value. If the executed code re-runs the same primitive with different parameters (e.g. a different `eps`) AFTER the pre-approved plan and the final answer differs from the first successful call's value, that is over-iteration and the agent has no audit-able reason to override the pre-verified pipeline. Output 'VERDICT: FAIL' with "the pre-verified plan already produced X via <primitive>; the second-pass override is unjustified — commit X". Generic — triggers whenever a primitive's first successful call produced a canonical numeric output and the agent re-ran the same primitive with no error from the first call.
8. Numeric-vs-prose consistency check (post-execution only). When the executed `execute_python_code` stdout prints a final numeric or categorical decision (e.g. `signed_angle = 172.0`, `pred = 'B'`, `num_clusters = 3`) AND the agent's prose summary in the post-execution context disagrees with that printed value, the prose has overridden the audit-able number without justification. Output 'VERDICT: FAIL' with "prose answer disagrees with computed value: stdout=<x>, prose=<y>". Generic discipline — fires whenever computed and reported answers are inconsistent.
9. Prefer a committed deterministic computation over re-grounding (post-execution only). When the answer is a deterministic function of already-grounded perception outputs (a sort, an argmax, a comparison, a count), re-grounding the same objects across many extra frames or "eyeballing" a revised answer does NOT improve it and is a common failure mode. If the executed reasoning reached a clean deterministic result from valid perception outputs and then overrode it with an un-audited manual revision, output 'VERDICT: FAIL' with "commit the deterministic computation; the manual override is unjustified". Generic discipline — not tied to any question category.

Output 'VERDICT: PASS' if sound, otherwise 'VERDICT: FAIL' with a specific explanation.
"""

if _NF7_GROUNDING_UNION:
    # NF-7 (r210): teach the verifier the gated tool exists (same defense as
    # the predict_2d_segmentation_masks_video "is hallucinated" precedent).
    _VERIFIER_RULES = _VERIFIER_RULES.replace(
        "  - `query_3d_bbox_catalogue(",
        "  - `ground_object_all_frames(scene_id, object_label)` → SAM3 segmentation of the label "
        "over ALL frames, 3D lift of every detection, centroid clustering into physical instances; "
        "returns {n_instances, instances: [{instance_idx, n_frames_seen, centroid_xyz, min_xyz_p5, "
        "max_xyz_p95, extent_xyz}]}. This IS a valid, registered tool — NEVER output VERDICT: FAIL "
        "on the grounds that it does not exist.\n"
        "  - `query_3d_bbox_catalogue(",
        1)

if _DG_GATE:
    # DG-GATE (r214): gated so the control arm's tool schemas + verifier rules
    # stay byte-identical to r213. (1) Teach the planner the consolidated
    # low-confidence fields; (2) teach planner+verifier the robust closest-point
    # consensus instead of the collapse-prone hard cKDTree min().
    _DG_FLAG_DOC = (
        "\n\nWhen `low_confidence: true` is present in the result, the lifted "
        "region is degenerate (`flags` lists why: huge/tiny region, >=2 image "
        "edges clipped, too few 3D points, sub-floor or near-world-origin "
        "centroid) — follow the attached `instruction` and re-ground on a "
        "different frame instead of consuming the measurement."
    )
    get_3d_points_in_bbox.description += _DG_FLAG_DOC
    get_3d_points_in_mask.description += _DG_FLAG_DOC
    aggregate_aabbs_robust.description += (
        "\n\nDegenerate-aware: input AABBs carrying a degeneracy/truncation "
        "flag (`low_confidence`, `bbox_quality_warning`, `mask_quality_warning`, "
        "`mask_truncation_warning`) are dropped when at least one clean frame "
        "remains (`n_frames_dropped_degenerate` reports how many); when EVERY "
        "frame is flagged a loud `warning` is returned instead. A "
        "`cross_frame_centroid_spread_>1.0m` flag means the per-frame centroids "
        "disagree by >1 m (pose drift) — re-ground before trusting the aggregate."
    )
    execute_python_code.description += (
        "\n\nThe sandbox also provides `closest_point_distance(pts_a, pts_b) -> "
        "dict` — the robust closest-approach distance between two (N,3) point "
        "clouds: `distance` is the 5th percentile of nearest-neighbor distances "
        "(consensus robust to single bled pixels that collapse a hard min() to "
        "~0; `min_raw` is the old hard minimum, for reference). A "
        "`co_location_flag: true` means the clouds are < 0.10 m apart — for two "
        "distinct labels that signals the same surface grounded twice; re-ground "
        "before trusting it. Use this INSTEAD of cKDTree(...).query(...)[0].min()."
    )
    _VERIFIER_RULES = _VERIFIER_RULES.replace(
        "compute pairwise minimum distance via "
        "`scipy.spatial.cKDTree(pts_a).query(pts_b)[0].min()`.",
        "compute the closest-approach distance via the sandbox helper "
        "`closest_point_distance(pts_a, pts_b)` (p5 of nearest-neighbor "
        "distances — a low-percentile consensus robust to single bled pixels "
        "that collapse a hard min() to ~0), or equivalently "
        "`np.percentile(scipy.spatial.cKDTree(pts_a).query(pts_b)[0], 5)`. A "
        "computed distance < 0.10 m between two DISTINCT named objects is a "
        "co-location artifact (the same surface grounded twice) — require "
        "re-grounding on a different frame instead of accepting it.",
        1)


# ─────────────────────────────────────────────────────────────────────────────
# r218: IDANCHOR — get_annotated_scene_overview (env IDANCHOR=1)
# Lazy-imports tools_idanchor from the agent dir (3 levels up from this file).
# ─────────────────────────────────────────────────────────────────────────────

_IDANCHOR_MODULE = None
_IDANCHOR_REGISTRY_CACHE: dict = {}   # scene_id -> list[dict]
_IDANCHOR_FRAMES_CACHE: dict = {}     # scene_id -> list[(video_idx, path, n_visible)]
_IDANCHOR_LOCK = threading.Lock()


def _idanchor_module():
    global _IDANCHOR_MODULE
    if _IDANCHOR_MODULE is None:
        agent_dir = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        if agent_dir not in sys.path:
            sys.path.insert(0, agent_dir)
        import tools_idanchor as _m
        _IDANCHOR_MODULE = _m
    return _IDANCHOR_MODULE


@tool
def get_annotated_scene_overview(scene_id: str, config: RunnableConfig = None) -> list:
    """Return several video frames annotated with persistent instance-ID badges — \
every detected physical object instance in the scene carries one stable numeric ID \
across all frames — together with a table giving each ID's 3D center (x,y,z) and \
extent (dx,dy,dz) in meters, world Z-up. Useful for unambiguously referring to and \
distinguishing individual object instances.

Args:
    scene_id: VSIBench scene identifier.

Returns:
    A multimodal list: alternating text summary / image_url content blocks for
    ~6-8 annotated frames from across the trajectory, followed by a text block
    containing the serialized instance-ID table (ID, center, extent in meters).
    Returns [{"type": "text", "text": "Error: ..."}] on failure.
"""
    import base64 as _b64

    mod = _idanchor_module()

    with _IDANCHOR_LOCK:
        cached_registry = _IDANCHOR_REGISTRY_CACHE.get(scene_id)
        cached_frames = _IDANCHOR_FRAMES_CACHE.get(scene_id)

    if cached_registry is None or cached_frames is None:
        try:
            raw_registry = mod.build_instance_registry(scene_id, DENSE_DIR)
        except Exception as e:
            return [{"type": "text", "text": f"Error: build_instance_registry failed for {scene_id}: {e}"}]

        # Quality filter: n_views >= 2, then renumber densely.
        n_before = len(raw_registry)
        filtered = [inst for inst in raw_registry if inst.get("n_views", 0) >= 2]
        n_after = len(filtered)
        for new_id, inst in enumerate(filtered, start=1):
            inst["id"] = new_id

        if config is not None:
            tl = config.get("configurable", {}).get("trace_list")
            if tl is not None:
                tl.append({"tool": "get_annotated_scene_overview",
                            "note": f"registry: {n_before} raw -> {n_after} after n_views>=2 filter"})

        # Annotate a spread of ~6-8 frames evenly across the trajectory.
        dataset = _resolve_dataset(scene_id)
        npz_path = os.path.join(DENSE_DIR, dataset, f"{scene_id}.npz")
        try:
            npz_indices = np.load(npz_path, allow_pickle=False)["indices"]
            n_dense_frames = len(npz_indices)
        except Exception:
            n_dense_frames = 32
        n_spread = max(6, min(8, n_dense_frames))
        spread_positions = sorted(set(
            int(round(v)) for v in np.linspace(0, n_dense_frames - 1, n_spread)))
        spread_video_indices = []
        try:
            _npz_indices = np.load(npz_path, allow_pickle=False)["indices"].tolist()
            spread_video_indices = [int(_npz_indices[p]) for p in spread_positions
                                    if p < len(_npz_indices)]
        except Exception:
            spread_video_indices = list(spread_positions)

        try:
            frame_results = mod.annotate_frames(
                scene_id,
                dense_dir=DENSE_DIR,
                frame_subset=spread_video_indices,
                max_badges_per_frame=25,
            )
        except Exception as e:
            return [{"type": "text", "text": f"Error: annotate_frames failed for {scene_id}: {e}"}]

        with _IDANCHOR_LOCK:
            _IDANCHOR_REGISTRY_CACHE[scene_id] = filtered
            _IDANCHOR_FRAMES_CACHE[scene_id] = frame_results
        cached_registry = filtered
        cached_frames = frame_results

    # Serialize the registry (include_labels=False per spec)
    table_text = _idanchor_module().serialize_registry(cached_registry, include_labels=False)

    # Build return: one text+image block per frame, then the table.
    result = []
    for entry in cached_frames:
        if len(entry) == 3:
            fi, path, n_vis = entry
        else:
            fi, path = entry[:2]
            n_vis = "?"
        result.append({"type": "text",
                        "text": f"Frame video_idx={fi}, {n_vis} instance badges visible:"})
        try:
            img_bytes = _get_resized_image_bytes(path)
            b64 = _b64.b64encode(img_bytes).decode()
            result.append({"type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        except Exception as e:
            result.append({"type": "text", "text": f"  [image load error: {e}]"})

    result.append({"type": "text",
                    "text": f"Instance registry ({len(cached_registry)} instances after n_views>=2 filter):\n{table_text}"})
    return result


# ─────────────────────────────────────────────────────────────────────────────
# r218: ROOM_POLY — estimate_scene_footprint (env ROOM_POLY=1)
# Thin wrapper over tools_room_area.estimate_room_area.
# ─────────────────────────────────────────────────────────────────────────────

_ROOM_AREA_MODULE = None


def _room_area_module():
    global _ROOM_AREA_MODULE
    if _ROOM_AREA_MODULE is None:
        agent_dir = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        if agent_dir not in sys.path:
            sys.path.insert(0, agent_dir)
        import tools_room_area as _m
        _ROOM_AREA_MODULE = _m
    return _ROOM_AREA_MODULE


@tool
def estimate_scene_footprint(scene_id: str, config: RunnableConfig = None,
                             point_cloud_source: str = POINT_CLOUD_DEFAULT_SOURCE) -> dict:
    """Deterministically compute the scanned scene's floor-plan footprint from the \
dense reconstruction: occupied space projected to the floor plane. Returns footprint \
area (m2), convex-hull area (m2), perimeter (m), and the detected floor height.

Args:
    scene_id: VSIBench scene identifier.
    point_cloud_source: Optional source. Default "g3t_scaled" is the same for
      every question. Alternatives: "mapanything" for stable layout fallback and
      "unik3d" for metric depth checks. Choose explicitly; do not depend on
      category/GT pre-routing.

Returns:
    dict — {
      "footprint_area_m2": float,  # raster polygon area (largest connected component)
      "hull_area_m2":      float,  # convex-hull area (upper bound)
      "perimeter_m":       float,  # perimeter of the footprint outline in metres
      "floor_z":           float,  # detected floor Z coordinate in world frame
      "note":              str,    # coverage caveat
    }
    Returns {"error": "..."} on failure.
"""
    try:
        source_key = _point_cloud_source_key(point_cloud_source)
        raw = _room_area_module().estimate_room_area(
            scene_id, dense_dir=_POINT_CLOUD_SOURCES[source_key]["dense_dir"])
    except Exception as e:
        return {"error": str(e)}

    result = {
        "footprint_area_m2": raw["area_m2"],
        "hull_area_m2":      raw["hull_area_m2"],
        "perimeter_m":       raw["perimeter_m"],
        "floor_z":           raw["floor_z"],
        "point_cloud_source": source_key,
        "note": ("footprint_area is a lower bound under partial scan coverage; "
                 "hull_area is an upper bound."),
    }
    if config is not None:
        tl = config.get("configurable", {}).get("trace_list")
        if tl is not None:
            tl.append({"tool": "estimate_scene_footprint", "response": str(result)})
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Agent graph
# ─────────────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    verification_attempts: int
    pre_verify_attempts:  int
    post_verify_attempts: int
    total_tool_steps:     int
    # r124: tracks whether the agent has consumed its single post-verify-FAIL
    # retry slot. When verify_plan_post_execution returns FAIL we inject one
    # corrective execute_python_code attempt; this flag prevents looping.
    post_verify_retry_used: bool
    # r133: r132 added a `post_verify_force_attempted` field here as a hard-gate
    # bounce flag; it perturbed the LangGraph schema and shifted LLM trajectories
    # on UNRELATED counting questions (−0.207). Reverted — post-verify enforcement
    # is now prompt-only via STRICT RULE 9 in prompt_base_133.txt.

# Pre-verification: still allow up to 2 retries to fix a broken plan.
# Post-verification: exactly 1 verifier call permitted. r124: after the verifier
# returns FAIL the agent gets ≤1 follow-up tool call (typically execute_python_code)
# to fix the issue before being routed to `answer`. PASS still routes straight to
# `answer` — no retry slot is opened.
MAX_PRE_VERIFY   = 2
MAX_POST_VERIFY  = 1
FORCE_ANSWER_STEP_CAP = int(os.environ.get("STEP_CAP", "80"))  # r117 compromise: 60 too tight for route/appearance/abs_distance, 100 too loose for room_size. r162: env-configurable so the launch sets a LOWER per-category cap for slow-recursion cats (size_estimation, counting) — forces earlier commit from the in-scratch value (recovered by stdout/tool fallbacks), recovering RECURSION nulls + speeding runs, WITHOUT changing the 80 default route/appearance/abs need.


# ─────────────────────────────────────────────────────────────────────────────
# r181: Top-down Bird's-Eye-View render (deterministic, no VLM in the geometry).
# Returns the rendered PNG to the planner as a multimodal ToolMessage so the
# Gemini planner can SEE the scene layout. The gate that justified this:
# LangGraph's ToolNode passes a list of content blocks through verbatim when each
# block's `type` is in TOOL_MESSAGE_BLOCK_TYPES ('text'/'image_url'/...), and
# langchain-google-genai's _convert_tool_message_to_parts turns an image_url
# data-URL block inside a ToolMessage into a Gemini inline_data image Part.
# ─────────────────────────────────────────────────────────────────────────────

def _bev_ground_centroids(scene_id: str, object_labels, dense, conf_thresh: float,
                          miss_sink: list | None = None):
    """For each requested label, ground it (SAM3) on the frames where it is most
    visible, lift the dense mask to a robust 3D centroid, and return
    {label: [X, Y, Z]}. Question-agnostic perception: SAM3 mask -> median of
    confident world points under the mask. Best-effort — labels that fail to
    ground are simply omitted. No VLM question-answering happens here.
    """
    out = {}
    if not object_labels:
        return out
    cache = _load_frames_cache()
    n_frames = dense["pts3d_world"].shape[0]
    for label in object_labels:
        label = str(label).strip()
        if not label:
            continue
        # Probe a spread of frames; collect per-frame centroids, take the median.
        probe = sorted(set(int(round(v)) for v in np.linspace(1, n_frames, num=min(6, n_frames))))
        per_frame_cent = []
        for fi in probe:
            try:
                res = _run_sam3_request(
                    scene_id, fi, label,
                    mask_dir=_sam3_mask_dir(scene_id, label, f"bev_f{fi}"),
                )
            except Exception:
                continue
            if not isinstance(res, dict):
                continue
            for inst in (res.get("instances") or []):
                mh = inst.get("mask_handle")
                if not mh or not os.path.exists(mh):
                    continue
                try:
                    mask_img = np.load(mh)
                except Exception:
                    continue
                npz_idx = _frame_index_to_npz_idx(scene_id, fi, dense)
                if npz_idx is None:
                    if miss_sink is not None:
                        miss_sink.append(int(fi))
                    continue
                pts3d = dense["pts3d_world"][npz_idx]
                valid = dense["mask"][npz_idx]
                conf  = dense["conf"][npz_idx] if "conf" in dense else None
                # Resample mask to dense H,W if needed.
                if mask_img.shape != pts3d.shape[:2]:
                    try:
                        im = Image.fromarray((mask_img.astype(np.uint8) * 255))
                        im = im.resize((pts3d.shape[1], pts3d.shape[0]), resample=Image.NEAREST)
                        mask_img = (np.asarray(im) > 127)
                    except Exception:
                        continue
                region = mask_img.astype(bool) & valid
                if conf is not None:
                    region = region & (conf >= conf_thresh)
                pts = pts3d[region]
                if len(pts) < 10:
                    continue
                per_frame_cent.append(np.median(pts, axis=0))
        if per_frame_cent:
            out[label] = [round(float(v), 3) for v in np.median(np.vstack(per_frame_cent), axis=0)]
    return out


@tool
def render_topdown_bev(scene_id: str, config: RunnableConfig, object_labels: list[str] = None,
                       point_cloud_source: str = POINT_CLOUD_DEFAULT_SOURCE) -> list:
    """
    Renders a deterministic top-down (Bird's-Eye-View) map of the scene and
    returns the image to you so you can SEE the spatial layout. Pure
    perception/geometry — no VLM answers the question; it only orthographically
    projects the reconstructed 3D point cloud onto the world XY (floor) plane.

    Use this as a top-down map view to reason about overall room layout, the
    relative arrangement of objects, cardinal/relative directions, and the
    camera's path through the scene. It complements the numeric geometry tools
    by giving you a single picture instead of many coordinate lookups.

    Args:
        scene_id: VSIBench scene identifier.
        object_labels: Optional list of natural-language object labels (e.g.
            ["sofa", "tv"]). Each is grounded and drawn as a labeled colored
            marker at its top-down (X, Y) position. Omit to render just the
            point cloud + camera trajectory.
        point_cloud_source: Optional source. Default "g3t_scaled" is the same
            for every question. Alternatives: "mapanything" for stable layout
            fallback and "unik3d" for metric depth checks. Choose explicitly;
            do not depend on category/GT pre-routing.

    Returns:
        A multimodal message: the rendered BEV PNG plus a short text summary
        (scene extent in meters, number of objects drawn). The map is oriented
        with world +X to the right and world +Y up ("north"); a scale bar and a
        north arrow are drawn for reference. Camera trajectory is the gray line;
        green arrow = first camera (start) heading, red arrow = last camera (end)
        heading.

    Coordinate convention: world Z-up; this is a projection onto the XY plane,
    colored by height Z (viridis: low = floor/blue, high = ceiling/yellow).
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import base64 as _b64

    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError as e:
        return [{"type": "text", "text": f"Error: {e}"}]
    dense = _load_dense(scene_id, point_cloud_source=source_key)
    if dense is None:
        return [{"type": "text", "text": f"Error: Dense outputs not found for scene {scene_id}."}]

    pts3d = dense["pts3d_world"]            # (N,H,W,3)
    mask  = dense["mask"]                   # (N,H,W)
    conf  = dense["conf"] if "conf" in dense else None
    conf_thresh = 0.5

    sel = mask.astype(bool)
    if conf is not None:
        sel = sel & (conf >= conf_thresh)
    pts = pts3d[sel]                        # (M,3)
    if len(pts) == 0:
        return [{"type": "text", "text": f"Error: No confident 3D points for scene {scene_id}."}]

    # Robust extent (drop the extreme 1% tails so a few stray points don't blow up the view).
    xlo, xhi = np.percentile(pts[:, 0], [1, 99])
    ylo, yhi = np.percentile(pts[:, 1], [1, 99])
    in_view = ((pts[:, 0] >= xlo) & (pts[:, 0] <= xhi) &
               (pts[:, 1] >= ylo) & (pts[:, 1] <= yhi))
    pts_v = pts[in_view]
    # Subsample for plotting speed (deterministic stride).
    if len(pts_v) > 120000:
        stride = len(pts_v) // 120000 + 1
        pts_v = pts_v[::stride]

    index_miss = []
    obj_centroids = _bev_ground_centroids(
        scene_id, object_labels, dense, conf_thresh, miss_sink=index_miss)
    if index_miss:
        return [{"type": "text", "text":
                 f"Error: frame_index_unmappable — dense store index mismatch for frames "
                 f"{sorted(set(index_miss))} of scene {scene_id} "
                 f"(point_cloud_source={source_key}); labeled BEV withheld (fail-closed)."}]

    # Camera trajectory (translations) + first/last heading.
    cam = dense["camera_poses"]            # (N,4,4)
    cam_xy = cam[:, :2, 3]                 # (N,2)
    def _heading_xy(R):
        # OpenCV camera forward is +Z in cam space; world heading = R @ [0,0,1].
        h = R @ np.array([0.0, 0.0, 1.0])
        return h[:2]

    fig, ax = plt.subplots(figsize=(8, 8), dpi=110)
    sc = ax.scatter(pts_v[:, 0], pts_v[:, 1], c=pts_v[:, 2], s=1.2,
                    cmap="viridis", linewidths=0, alpha=0.6)
    cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("height Z (m)")

    # Camera path.
    ax.plot(cam_xy[:, 0], cam_xy[:, 1], "-", color="0.35", lw=1.2, alpha=0.9, zorder=4)
    span = max(xhi - xlo, yhi - ylo)
    arrow_len = max(0.4, 0.08 * span)
    for idx, color, tag in ((0, "lime", "start"), (len(cam) - 1, "red", "end")):
        cx, cy = float(cam[idx, 0, 3]), float(cam[idx, 1, 3])
        hx, hy = _heading_xy(cam[idx, :3, :3])
        nrm = math.hypot(hx, hy) or 1.0
        ax.arrow(cx, cy, arrow_len * hx / nrm, arrow_len * hy / nrm,
                 head_width=arrow_len * 0.4, head_length=arrow_len * 0.4,
                 fc=color, ec=color, zorder=6, length_includes_head=True)
        ax.scatter([cx], [cy], c=color, s=40, edgecolors="black", zorder=6)

    # Object markers.
    marker_colors = plt.cm.tab10.colors
    for i, (label, c3) in enumerate(obj_centroids.items()):
        col = marker_colors[i % len(marker_colors)]
        ax.scatter([c3[0]], [c3[1]], marker="*", s=320, color=col,
                   edgecolors="black", linewidths=1.2, zorder=8)
        ax.annotate(label, (c3[0], c3[1]), textcoords="offset points",
                    xytext=(6, 6), fontsize=10, fontweight="bold",
                    color="black",
                    bbox=dict(boxstyle="round,pad=0.2", fc=col, ec="black", alpha=0.85),
                    zorder=9)

    # North arrow (+Y) + scale bar.
    ax.annotate("N (+Y)", xy=(0.04, 0.96), xycoords="axes fraction",
                xytext=(0.04, 0.84), textcoords="axes fraction",
                ha="center", fontsize=10, fontweight="bold",
                arrowprops=dict(arrowstyle="->", lw=2, color="black"))
    # 1 m scale bar (or a round fraction of the span if the room is tiny).
    bar_m = 1.0 if span >= 3 else round(span / 4.0, 1) or 0.5
    bx0 = xlo + 0.06 * (xhi - xlo)
    by0 = ylo + 0.06 * (yhi - ylo)
    ax.plot([bx0, bx0 + bar_m], [by0, by0], "-", color="black", lw=3, zorder=10)
    ax.text(bx0 + bar_m / 2, by0 + 0.015 * (yhi - ylo), f"{bar_m:g} m",
            ha="center", va="bottom", fontsize=9, fontweight="bold", zorder=10)

    ax.set_xlim(xlo, xhi)
    ax.set_ylim(ylo, yhi)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("world X (m)")
    ax.set_ylabel("world Y (m)")
    ax.set_title(f"Top-down BEV — {scene_id}")
    fig.tight_layout()

    out_dir = os.path.join(_RUN_OUTPUT_ROOT, "runtime", "bev_renders")
    os.makedirs(out_dir, exist_ok=True)
    png_path = os.path.join(out_dir, f"{scene_id}_bev.png")
    fig.savefig(png_path, format="png")
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    png_bytes = buf.getvalue()
    b64 = _b64.b64encode(png_bytes).decode()

    extent_x = round(float(xhi - xlo), 2)
    extent_y = round(float(yhi - ylo), 2)
    summary = (
        f"Top-down BEV rendered for {scene_id} using point_cloud_source={source_key}. World-XY extent ≈ "
        f"{extent_x} m (X) × {extent_y} m (Y). Objects drawn: "
        f"{len(obj_centroids)}"
        + (f" ({', '.join(obj_centroids.keys())})." if obj_centroids else ".")
        + " Map: +X right, +Y up (north); colorbar = height Z; gray line = "
          "camera path; green=start heading, red=end heading. PNG saved to "
        + png_path
    )

    trace_list = config.get("configurable", {}).get("trace_list") if config else None
    if trace_list is not None:
        trace_list.append({"tool": "render_topdown_bev",
                           "response": f"extent {extent_x}x{extent_y} m, "
                                       f"{len(obj_centroids)} objects, "
                                       f"point_cloud_source={source_key}, png={png_path}"})

    return [
        {"type": "text", "text": summary},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
    ]


# ---------------------------------------------------------------------------
# r205: novel-view renderer
# ---------------------------------------------------------------------------
def _rot_z_nv(theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float64)


def _rot_x_nv(theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=np.float64)


def _build_virtual_cam_nv(base_pose: np.ndarray, centroid: np.ndarray,
                           d_az_deg: float, d_el_deg: float) -> np.ndarray:
    """Rotate base camera around scene centroid (world Z-up).
    d_az_deg: horizontal spin around world Z; d_el_deg: local-X tilt."""
    az_rad = math.radians(d_az_deg)
    el_rad = math.radians(d_el_deg)
    R_az = _rot_z_nv(az_rad)
    R_el = _rot_x_nv(el_rad)
    t_rel = base_pose[:3, 3] - centroid
    t_new = centroid + R_az @ t_rel
    R_new = R_az @ base_pose[:3, :3] @ R_el
    pose = np.eye(4, dtype=np.float64)
    pose[:3, :3] = R_new
    pose[:3, 3] = t_new
    return pose


@tool
def render_novel_view(scene_id: str, config: RunnableConfig,
                      azimuth_deg: float = 45.0,
                      elevation_deg: float = 0.0,
                      base_frame: int = None,
                      point_cloud_source: str = POINT_CLOUD_DEFAULT_SOURCE) -> list:
    """
    Renders the scene's point cloud from a VIRTUAL camera viewpoint rotated by the
    given azimuth/elevation from a base frame, returning an image you can look at to
    see the layout and relative positions of objects from a different angle (coherent
    up to ~±45° azimuth; larger rotations leave holes).

    The virtual camera is created by rotating the base camera's position around the
    scene centroid by azimuth_deg (horizontal, world Z-up) and elevation_deg
    (vertical tilt, positive = tilt up). The point cloud from ALL frames is projected
    into this virtual view using a numpy z-buffer.

    Args:
        scene_id: VSIBench scene identifier.
        azimuth_deg: Horizontal rotation around scene centroid in degrees (default 45).
            Positive = counter-clockwise when viewed from above. Coherent up to ~±45°.
        elevation_deg: Vertical tilt in degrees (default 0). Positive = tilt camera up.
        base_frame: 0-based index into the dense arrays for the base camera pose and
            intrinsics. If None, the median-trajectory frame (best-covered) is used.
        point_cloud_source: Optional source. Default "g3t_scaled" is the same
            for every question. Alternatives: "mapanything" for stable layout
            fallback and "unik3d" for metric depth checks. Choose explicitly;
            do not depend on category/GT pre-routing.

    Returns:
        A multimodal message: the rendered novel-view PNG plus a short text summary
        (base frame, coverage, number of projected points). Colors are from the scene's
        actual RGB frames when available; otherwise height-shaded (viridis).
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import base64 as _b64

    try:
        source_key = _point_cloud_source_key(point_cloud_source)
    except ValueError as e:
        return [{"type": "text", "text": f"Error: {e}"}]
    dense = _load_dense(scene_id, point_cloud_source=source_key)
    if dense is None:
        return [{"type": "text", "text": f"Error: Dense outputs not found for scene {scene_id}."}]

    pts3d = dense["pts3d_world"]            # (N, H, W, 3)
    mask  = dense["mask"].astype(bool)      # (N, H, W)
    conf  = dense["conf"] if "conf" in dense else None
    conf_thresh = 0.5
    N, H, W = pts3d.shape[:3]

    sel = mask.copy()
    if conf is not None:
        sel = sel & (conf >= conf_thresh)

    # Pick base frame: median-trajectory frame by default (avoids degenerate frame 0
    # seen in some ARKit scenes where coverage is poor).
    if base_frame is None:
        # Use the frame whose mask has the most valid (confident) points.
        valid_counts = sel.reshape(N, -1).sum(axis=1)   # (N,)
        base_frame_idx = int(np.argmax(valid_counts))
    else:
        base_frame_idx = int(base_frame)
        if not (0 <= base_frame_idx < N):
            return [{"type": "text",
                     "text": f"Error: base_frame={base_frame_idx} out of range [0,{N})."}]

    pts_world = pts3d[sel].astype(np.float64)   # (M, 3)
    if len(pts_world) == 0:
        return [{"type": "text", "text": f"Error: No confident 3D points for scene {scene_id}."}]

    # ---- Color the points via per-frame RGB if available, else height-shade ----
    colors = None
    _fc = _load_frames_cache()
    if _fc and scene_id in _fc:
        frame_names = _fc[scene_id].get("frame_names", [])
        all_colors = np.zeros((N, H, W, 3), dtype=np.float32)
        loaded_any = False
        for fi, fname in enumerate(frame_names[:N]):
            fpath = _get_local_image(scene_id, fname)
            if fpath is not None:
                try:
                    img_rgb = Image.open(
                        io.BytesIO(_read_r740_registered_frame(fpath))
                    ).convert("RGB")
                    img_rgb = img_rgb.resize((W, H), Image.Resampling.BILINEAR)
                    all_colors[fi] = np.array(img_rgb, dtype=np.float32) / 255.0
                    loaded_any = True
                except Exception:
                    pass
        if loaded_any:
            colors = all_colors[sel]   # (M, 3)

    if colors is None:
        z = pts_world[:, 2]
        zlo, zhi = np.percentile(z, [2, 98])
        zn = np.clip((z - zlo) / max(zhi - zlo, 1e-6), 0, 1)
        colors = plt.cm.viridis(zn)[:, :3].astype(np.float32)

    # ---- Build virtual camera ----
    cam_poses = dense["camera_poses"]                          # (N, 4, 4)
    scene_centroid = np.median(pts_world, axis=0)             # (3,)
    base_pose = cam_poses[base_frame_idx].astype(np.float64)
    virtual_pose = _build_virtual_cam_nv(base_pose, scene_centroid,
                                          azimuth_deg, elevation_deg)

    # ---- Intrinsics scaled to output resolution ----
    img_h, img_w = H, W
    K = dense["intrinsics"][base_frame_idx].astype(np.float64)   # (3, 3)

    # ---- Project points ----
    R_cw = virtual_pose[:3, :3].T
    t_cw = -R_cw @ virtual_pose[:3, 3]
    pts_cam = (R_cw @ pts_world.T).T + t_cw       # (M, 3)
    in_front = pts_cam[:, 2] > 0.05
    pts_cam  = pts_cam[in_front]
    colors_f = colors[in_front]

    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]
    z_d = pts_cam[:, 2]
    u = (pts_cam[:, 0] * fx / z_d + cx).astype(np.int32)
    v = (pts_cam[:, 1] * fy / z_d + cy).astype(np.int32)
    in_bounds = (u >= 0) & (u < img_w) & (v >= 0) & (v < img_h)
    u, v, z_d = u[in_bounds], v[in_bounds], z_d[in_bounds]
    colors_f = colors_f[in_bounds]

    # ---- Z-buffer ----
    img = np.zeros((img_h, img_w, 3), dtype=np.float32)
    zbuf = np.full((img_h, img_w), np.inf, dtype=np.float32)
    order = np.argsort(z_d)[::-1]   # farthest first
    u_s, v_s, z_s = u[order], v[order], z_d[order].astype(np.float32)
    c_s = colors_f[order].astype(np.float32)
    CHUNK = 500_000
    for start in range(0, len(u_s), CHUNK):
        end = min(start + CHUNK, len(u_s))
        uc, vc, zc, cc = u_s[start:end], v_s[start:end], z_s[start:end], c_s[start:end]
        closer = zc < zbuf[vc, uc]
        zbuf[vc[closer], uc[closer]] = zc[closer]
        img[vc[closer], uc[closer]] = cc[closer]

    # ---- 2-px dilation to fill splat holes ----
    from PIL import ImageFilter
    _pil_img = Image.fromarray((img * 255).astype(np.uint8), mode="RGB")
    # Fill black pixels by dilating once with max filter (nearest-neighbor splat fill)
    _mask_filled = np.array(_pil_img).sum(axis=2) == 0
    if _mask_filled.any():
        _dilated = np.array(_pil_img.filter(ImageFilter.MaxFilter(size=3)), dtype=np.float32) / 255.0
        img[_mask_filled] = _dilated[_mask_filled]

    coverage = (zbuf < np.inf).mean()
    n_pts = int(in_bounds.sum())

    # ---- Save and encode ----
    out_dir = os.path.join(_RUN_OUTPUT_ROOT, "runtime", "novel_view_renders")
    os.makedirs(out_dir, exist_ok=True)
    png_path = os.path.join(out_dir,
        f"{scene_id}_f{base_frame_idx}_az{azimuth_deg:+.0f}_el{elevation_deg:+.0f}.png")

    fig, ax = plt.subplots(figsize=(6, 5), dpi=110)
    ax.imshow(img)
    ax.set_title(
        f"{scene_id} | az={azimuth_deg:+.0f}° el={elevation_deg:+.0f}°\n"
        f"base_frame={base_frame_idx} | coverage={coverage:.1%} | {n_pts} pts",
        fontsize=9,
    )
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(png_path, format="png", bbox_inches="tight")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    b64 = _b64.b64encode(buf.getvalue()).decode()

    summary = (
        f"Novel-view render for {scene_id} using point_cloud_source={source_key}: "
        f"az={azimuth_deg:+.0f}°, el={elevation_deg:+.0f}°, "
        f"base_frame={base_frame_idx}, coverage={coverage:.1%}, {n_pts} projected points. "
        f"PNG saved to {png_path}. "
        "Colors: actual RGB if frame images available, else height-shaded viridis."
    )

    trace_list = config.get("configurable", {}).get("trace_list") if config else None
    if trace_list is not None:
        trace_list.append({"tool": "render_novel_view",
                           "response": f"az={azimuth_deg:+.0f} el={elevation_deg:+.0f} "
                                       f"frame={base_frame_idx} coverage={coverage:.1%} "
                                       f"point_cloud_source={source_key} png={png_path}"})

    return [
        {"type": "text", "text": summary},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
    ]


_SALVAGE_RUNNABLE = None  # set by get_agent_app(); used by salvage_commit()


def _req73_usage(response) -> dict:
    usage = getattr(response, "usage_metadata", None) or {}
    if not isinstance(usage, dict):
        usage = {
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0),
        }
    normalized = {key: int(usage.get(key, 0) or 0)
                  for key in ("input_tokens", "output_tokens", "total_tokens")}
    output_details = usage.get("output_token_details") or {}
    normalized["thoughts_tokens"] = int(output_details.get("reasoning", 0) or 0)
    return normalized


def _req73_invoke_with_retry(runnable, messages, attempt_sink, family):
    """Invoke one logical planner call and persist every provider attempt."""
    if reference_policy.budget_terminal(attempt_sink):
        raise RuntimeError("planner invocation after terminal cap refused")
    call_index = 1 + max(
        (int(row.get("call_index", 0)) for row in (attempt_sink or [])), default=0)
    max_attempts = max(1, int(os.environ.get("NV_RETRY_ATTEMPTS", "3")))
    for attempt in range(max_attempts):
        started = time.time()
        started_monotonic_ns = time.monotonic_ns()
        try:
            time.sleep(5.0)
            response = custody_effect(runnable.invoke, messages)
            ended_monotonic_ns = time.monotonic_ns()
            metadata = getattr(response, "response_metadata", None) or {}
            served = next((metadata.get(key) for key in
                           ("model_name", "model_version", "model")
                           if metadata.get(key)), _planner_model())
            if attempt_sink is not None:
                attempt_sink.append({
                    "family": family, "provider": "google-native", "call_index": call_index,
                    "attempt_index": attempt + 1, "status": "ok",
                    "requested_model": _planner_model(), "served_model": str(served),
                    "elapsed_ms": int((time.time() - started) * 1000),
                    "started_unix": started,
                    "started_monotonic_ns": started_monotonic_ns,
                    "ended_monotonic_ns": ended_monotonic_ns,
                    "output_budget_tokens": PLANNER_MAX_OUTPUT_TOKENS,
                    "request_controls": reference_policy.request_controls(),
                    "finish_reason": metadata.get("finish_reason"),
                    "usage": _req73_usage(response),
                    "raw_response": _langchain_raw_response(response),
                })
            return response
        except Exception as exc:
            native_cap = reference_policy.native_cap_since(started)
            if attempt_sink is not None:
                attempt_sink.append({
                    "native_output_cap_evidence": native_cap,
                    "family": family, "provider": "google-native", "call_index": call_index,
                    "attempt_index": attempt + 1, "status": "error",
                    "requested_model": _planner_model(), "served_model": None,
                    "elapsed_ms": int((time.time() - started) * 1000),
                    "started_unix": started,
                    "started_monotonic_ns": started_monotonic_ns,
                    "ended_monotonic_ns": time.monotonic_ns(),
                    "output_budget_tokens": PLANNER_MAX_OUTPUT_TOKENS,
                    "request_controls": reference_policy.request_controls(),
                    "finish_reason": "MAX_TOKENS" if native_cap else None,
                    "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                    "raw_response": None,
                    "error_class": type(exc).__name__, "http_status": _extract_http_status(exc),
                })
            if (_is_transient_api_error(exc)
                    and attempt + 1 < _transient_max_attempts(exc, max_attempts)):
                time.sleep(_transient_api_backoff_seconds(exc, attempt))
                continue
            raise


def salvage_commit(messages, attempt_sink=None):
    """PLN-2 (r208): one out-of-graph forced-commit invoke (tool_choice='none')
    over the accumulated messages. Called by the runner when the graph died
    (GraphRecursionError / step-cap / stream error) before emitting <ANSWER>.
    Retries on 429 like the in-graph planner. Raises if get_agent_app() has
    not been called yet in this process."""
    if _SALVAGE_RUNNABLE is None:
        raise RuntimeError("call get_agent_app() before salvage_commit()")
    return _req73_invoke_with_retry(
        _SALVAGE_RUNNABLE, messages, attempt_sink, "salvage")


# ── CI3D_GUARD (r219, env CI3D_GUARD=1) ──────────────────────────────────────
# Counting-collapse EA (experiment_r217_frozen_s1/errors.md): after the
# pre-execution verifier REJECTED a plan that included count_instances_3d
# ("VERDICT: FAIL" naming the tool), the planner bypassed the verdict and
# called count_instances_3d directly (qids 68/99/4416 immediately after budget
# exhaustion; 81/121 later in the episode), committing noisy 1-3-overcounts.
# Guard: such direct calls return a structured refusal payload instead of
# executing — until at least one OTHER perception tool call has succeeded
# since the (most recent) rejection, i.e. the agent has gathered independent
# evidence first. Stateless: derived from the message history each call.

_CI3D_REFUSAL = {
    "error": "ci3d_guarded",
    "reason": "plan including this tool was rejected by the verifier; gather "
              "independent evidence (per-frame masks/video tracking) before "
              "re-attempting",
}

# Perception tools whose successful output counts as "independent evidence
# gathered since the rejection" (lifts the guard). Deliberately excludes
# count_instances_3d itself, both verifiers, and execute_python_code (pure
# computation is not new perception evidence).
_CI3D_GUARD_PERCEPTION_TOOLS = frozenset({
    "find_frames_with_object", "get_frame_image",
    "predict_2d_bounding_box", "predict_2d_points",
    "predict_2d_segmentation_masks", "predict_2d_segmentation_masks_video",
    "ground_object_all_frames", "get_world_3d_point_from_2d",
    "get_3d_points_in_bbox", "get_3d_points_in_mask",
    "query_3d_bbox_catalogue", "get_object_instances_3d",
    "get_annotated_scene_overview",
})


def _msg_content_str(m) -> str:
    c = getattr(m, "content", None)
    if isinstance(c, list):
        c = " ".join(x.get("text", "") if isinstance(x, dict) else str(x)
                     for x in c)
    return c if isinstance(c, str) else str(c)


def _ci3d_guard_active(messages) -> bool:
    """True when the most recent pre-verifier rejection of a
    count_instances_3d plan has NOT yet been followed by a successful
    non-CI3D perception tool call (the observed r217 bypass window)."""
    rejected_at = None
    for i, m in enumerate(messages):
        if isinstance(m, ToolMessage) and getattr(m, "name", None) == "verify_plan_pre_execution":
            c = _msg_content_str(m)
            if "VERDICT: FAIL" in c and "count_instances_3d" in c:
                rejected_at = i
    if rejected_at is None:
        return False
    for m in messages[rejected_at + 1:]:
        if not (isinstance(m, ToolMessage)
                and getattr(m, "name", None) in _CI3D_GUARD_PERCEPTION_TOOLS):
            continue
        low = _msg_content_str(m).strip().lower()
        if low and not low.startswith("error") and not low.startswith("{'error'") \
                and "traceback" not in low:
            return False  # independent evidence gathered — guard lifted
    return True


def _make_ci3d_guarded_tools_node(base_tool_node):
    """Wrap the graph's ToolNode: while the guard is active, count_instances_3d
    tool calls get a refusal ToolMessage (other calls in the same AI message
    still execute). Outside the guard window, delegates verbatim."""
    def guarded_tools(state, config: RunnableConfig = None):
        messages = state["messages"]
        last = messages[-1] if messages else None
        if not (isinstance(last, AIMessage) and getattr(last, "tool_calls", None)):
            return base_tool_node.invoke(state, config)
        if not any(tc.get("name") == "count_instances_3d" for tc in last.tool_calls):
            return base_tool_node.invoke(state, config)
        if not _ci3d_guard_active(messages[:-1]):
            return base_tool_node.invoke(state, config)
        refusals = [
            ToolMessage(content=str(_CI3D_REFUSAL), name="count_instances_3d",
                        tool_call_id=tc.get("id") or "ci3d_guarded")
            for tc in last.tool_calls if tc.get("name") == "count_instances_3d"
        ]
        allowed = [tc for tc in last.tool_calls if tc.get("name") != "count_instances_3d"]
        if not allowed:
            return {"messages": refusals}
        pruned = last.model_copy(update={"tool_calls": allowed})
        out = base_tool_node.invoke(
            {**state, "messages": list(messages[:-1]) + [pruned]}, config)
        executed = out.get("messages", []) if isinstance(out, dict) else list(out)
        return {"messages": refusals + list(executed)}
    return guarded_tools


def _build_planner_bindings(tools):
    """Current planner transport boundary; no Qwen overlay is implemented here."""
    planner_model = _planner_model()
    if _gp_native():
        ChatGoogleGenerativeAI = reference_policy.planner_class()
        llm = ChatGoogleGenerativeAI(
            model=planner_model,
            temperature=0.0,
            max_tokens=PLANNER_MAX_OUTPUT_TOKENS,
            vertexai=False,
            include_thoughts=True,
            thinking_level="high",
            max_retries=0,
        )
        return llm.bind_tools(tools), llm.bind_tools(tools, tool_choice="none")
    base_url, data_classification, _ = _nvidia_transport_config()
    llm_kwargs = {
        "model": planner_model,
        "api_key": _require_nvidia_api_key(),
        "base_url": base_url,
        "default_headers": {"dataClassification": data_classification},
        "max_tokens": PLANNER_MAX_OUTPUT_TOKENS,
        "max_retries": 0,
        "timeout": float(os.environ.get("NV_TIMEOUT_SECONDS", "300")),
    }
    if not _omit_temperature_for_model(planner_model):
        llm_kwargs["temperature"] = 0.0
    llm = ChatOpenAI(**llm_kwargs)
    return (
        llm.bind_tools(tools, parallel_tool_calls=False),
        llm.bind_tools(tools, parallel_tool_calls=False, tool_choice="none"),
    )


def get_agent_app():
    # Unregistered legacy tools removed; see git history.
    tools = [
        find_frames_with_object,
        get_frame_image,
        predict_2d_bounding_box,
        predict_2d_points,
        get_world_3d_point_from_2d,
        get_3d_points_in_bbox,
        get_3d_points_in_mask,            # r126: mask-based 3D extent (paired with SAM3 mask_dense_handle)
        predict_2d_segmentation_masks,    # r123: re-registered, daemon-backed
        predict_2d_segmentation_masks_video,  # r134: SAM3 native video tracking — consistent instance_id across frames
        aggregate_aabbs_median,
        aggregate_aabbs_robust,           # Tukey 1.5-IQR adjacent-value endpoint aggregator
        cluster_3d_points,
        get_camera_pose,
        apply_coordinate_transform,
        render_topdown_bev,               # r181: deterministic top-down BEV render returned as an image to the planner
        render_novel_view,                # r205: novel-view renderer — virtual camera at arbitrary azimuth/elevation
        execute_python_code,
        verify_plan_pre_execution,
        verify_plan_post_execution,
    ]
    expected = {'find_frames_with_object','get_frame_image','predict_2d_bounding_box',
        'predict_2d_points','get_world_3d_point_from_2d','get_3d_points_in_bbox',
        'get_3d_points_in_mask','predict_2d_segmentation_masks',
        'predict_2d_segmentation_masks_video','aggregate_aabbs_median',
        'aggregate_aabbs_robust','cluster_3d_points','get_camera_pose',
        'apply_coordinate_transform','render_topdown_bev','render_novel_view',
        'execute_python_code','verify_plan_pre_execution','verify_plan_post_execution'}
    assert {tool.name for tool in tools} == expected, 'training tool roster mismatch'
    from gt_tool_bindings import assert_bindings
    assert_bindings(sys.modules[__name__], tools)
    llm_with_tools, llm_answer = _build_planner_bindings(tools)
    # PLN-2 (r208): expose the no-tools answer binding for the runner's
    # out-of-graph salvage commit (fires when the graph dies via
    # GraphRecursionError / step-cap before emitting <ANSWER>).
    global _SALVAGE_RUNNABLE
    _SALVAGE_RUNNABLE = llm_answer

    def planner(state, config: RunnableConfig):
        messages = state["messages"]
        attempt_sink = config.get("configurable", {}).get("req73_planner_attempts")
        pre  = state.get("pre_verify_attempts", 0)
        post = state.get("post_verify_attempts", 0)

        # r133: removed the r132 bounce-back. Mandate is now prompt-only
        # (STRICT RULE 9). Adding a state field here perturbed unrelated
        # categories' trajectories.

        if len(messages) > 0 and isinstance(messages[-1], ToolMessage) and messages[-1].name in ("verify_plan_pre_execution", "verify_plan_post_execution"):
            phase  = messages[-1].name
            verifier_status = _tool_verifier_status(messages[-1])
            failed = verifier_status == "FAIL"
            if phase == "verify_plan_post_execution":
                # r124: when the verifier flags FAIL and the retry slot is
                # unused, give the agent ONE more execute_python_code attempt
                # to fix the issue. Otherwise (PASS, or retry already used)
                # route straight to the answer node as before.
                retry_used = state.get("post_verify_retry_used", False)
                if failed and not retry_used:
                    # NF-4 (r208): the retry turn may RE-GROUND, not just recompute —
                    # 4 rel_dist qids had the verifier correctly prescribe re-grounding
                    # but the old text hard-restricted to execute_python_code, converting
                    # caught errors into guaranteed losses.
                    notif = HumanMessage(content=(
                        "[SYSTEM NOTIFICATION]: Post-verifier returned FAIL. "
                        "You have ONE more tool call to fix the specific issue the "
                        "verifier flagged — use execute_python_code for a computation "
                        "fix, or a perception tool (predict_2d_segmentation_masks, "
                        "get_3d_points_in_mask, find_frames_with_object, ...) if the "
                        "verifier flagged bad grounding — then emit "
                        "<ANSWER>...</ANSWER>. Do not re-invoke the verifier — your "
                        "verify budget is exhausted."
                    ))
                    resp = _req73_invoke_with_retry(
                        llm_with_tools, list(messages) + [notif], attempt_sink, "planner")
                    return {"messages": [notif, resp], "post_verify_retry_used": True}
                notif = HumanMessage(content=_post_verify_done_notification_text(
                    messages[-1]
                ))
                resp = _req73_invoke_with_retry(
                    llm_answer, list(messages) + [notif], attempt_sink, "planner")
                return {"messages": [notif, resp]}
            if failed and pre < MAX_PRE_VERIFY:
                remaining = MAX_PRE_VERIFY - pre
                notif = HumanMessage(content=f"[SYSTEM NOTIFICATION]: Your plan was rejected. You have {remaining} pre-verify retries left. Fix your logic based on the critique above, then continue. You may also ignore the critique and commit to your best answer if the critique is nonsensical.")
                resp = _req73_invoke_with_retry(
                    llm_with_tools, list(messages) + [notif], attempt_sink, "planner")
                return {"messages": [notif, resp]}
            if failed:
                notif = HumanMessage(content="[SYSTEM NOTIFICATION]: Pre-verifier budget exhausted. Proceed with your best plan — no more pre-verify calls allowed.")
                resp = _req73_invoke_with_retry(
                    llm_with_tools, list(messages) + [notif], attempt_sink, "planner")
                return {"messages": [notif, resp]}
            # r56: planner-bailout retry — after a pre-verify PASS, an empty
            # AIMessage (no text, no tool_calls) can route to the answer node
            # without executing the approved plan. Inject an explicit reminder
            # on the PASS path so the planner executes the plan.
            if phase == "verify_plan_pre_execution" and not failed:
                notif = HumanMessage(content=_pre_verify_not_failed_notification_text(
                    messages[-1]
                ))
                resp = _req73_invoke_with_retry(
                    llm_with_tools, list(messages) + [notif], attempt_sink, "planner")
                return {"messages": [notif, resp]}

        resp = _req73_invoke_with_retry(
            llm_with_tools, messages, attempt_sink, "planner")
        return {"messages": [resp]}

    def route_after_planner(state):
        last_msg = state["messages"][-1]
        if reference_policy.is_capped(last_msg):
            return END
        if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
            # r133: post-verify enforcement is now prompt-only (STRICT RULE 9).
            # The r132 hard-gate via state field perturbed AgentState's schema
            # and shifted unrelated counting trajectories (−0.207). Reverted.
            # r220 EMPTYAI_RETRY: a truly EMPTY emission (no text, no tool
            # calls) with < 2 evidence tool-results gets a bounded retry nudge
            # instead of the zero-evidence forced answer (qids 25/4487). An AI
            # message WITH text (e.g. an organic <ANSWER>) is never intercepted.
            if _EMPTYAI_RETRY and isinstance(last_msg, AIMessage) \
                    and _emptyai_should_retry(state["messages"]):
                return "emptyai_nudge"
            return "answer"
        # After a post-verify call just finished, route straight to answer
        # (no more tools) — UNLESS the r124 retry slot has just been opened,
        # in which case the agent gets exactly ONE more tool call (typically
        # execute_python_code) to act on the verifier's critique before being
        # forced to answer. The post_verify_retry_used flag is set by the
        # planner when it injects the retry notification. After that single
        # retry tool runs, any further tool call is squashed → "answer".
        msgs = state["messages"]
        retry_used = state.get("post_verify_retry_used", False)
        for m in reversed(msgs[:-1]):
            if isinstance(m, ToolMessage):
                if m.name == "verify_plan_post_execution":
                    if not retry_used:
                        return "answer"
                    # retry slot is open — allow this single tool call.
                else:
                    if retry_used:
                        # Retry tool has already executed; no further tools.
                        return "answer"
                break
        # Step cap as a second safety net
        if state.get("total_tool_steps", 0) >= FORCE_ANSWER_STEP_CAP:
            return "answer"
        # Block over-budget verifier calls
        pre  = state.get("pre_verify_attempts", 0)
        post = state.get("post_verify_attempts", 0)
        filtered = []
        for tc in last_msg.tool_calls:
            if tc["name"] == "verify_plan_pre_execution"  and pre  >= MAX_PRE_VERIFY:  continue
            if tc["name"] == "verify_plan_post_execution" and post >= MAX_POST_VERIFY: continue
            filtered.append(tc)
        if not filtered:
            return "answer"
        last_msg.tool_calls = filtered
        return "tools"

    def tool_incrementer(state):
        pre  = state.get("pre_verify_attempts", 0)
        post = state.get("post_verify_attempts", 0)
        steps = state.get("total_tool_steps", 0)
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                pre  += sum(1 for tc in msg.tool_calls if tc["name"] == "verify_plan_pre_execution")
                post += sum(1 for tc in msg.tool_calls if tc["name"] == "verify_plan_post_execution")
                steps += len(msg.tool_calls)
                break
        return {"pre_verify_attempts": pre, "post_verify_attempts": post, "total_tool_steps": steps}

    def answer(state, config: RunnableConfig):
        # Fix 2: force an <ANSWER>...</ANSWER> emission with no tools available.
        prompt = HumanMessage(content=(
            "Final step: emit ONLY <ANSWER>...</ANSWER> with your best answer. "
            "Inside the tag: one option letter (for multiple choice) OR one numeric "
            "value with no units/prose/trailing text (for numeric questions). "
            "If you have partial information, commit to your best guess now. "
            "Do NOT call any more tools."
        ))
        attempt_sink = config.get("configurable", {}).get("req73_planner_attempts")
        return {"messages": [_req73_invoke_with_retry(
            llm_answer, list(state["messages"]) + [prompt], attempt_sink, "planner")]}

    def emptyai_nudge(state):
        # r220 EMPTYAI_RETRY: append the retry notification; the planner edge
        # re-invokes the model with it. No state fields touched (r132 lesson).
        return {"messages": [HumanMessage(content=(
            _EMPTYAI_NUDGE_MARK + " (no text, no tool call). You have not "
            "gathered enough evidence to answer yet. Continue your plan now — "
            "call your next geometry/perception tool, or emit "
            "<ANSWER>...</ANSWER> ONLY if you already have a defensible answer."
        ))]}

    workflow = StateGraph(AgentState)
    workflow.add_node("planner", planner)
    _tools_node = ToolNode(tools)
    if _CI3D_GUARD:
        # CI3D_GUARD (r219): verifier-bypass guard on count_instances_3d.
        _tools_node = _make_ci3d_guarded_tools_node(_tools_node)
    workflow.add_node("tools", _tools_node)
    workflow.add_node("answer", answer)
    workflow.add_node("increment", tool_incrementer)
    if _EMPTYAI_RETRY:
        workflow.add_node("emptyai_nudge", emptyai_nudge)
        workflow.add_edge("emptyai_nudge", "planner")
    workflow.add_edge(START, "planner")
    workflow.add_conditional_edges("planner", route_after_planner)
    workflow.add_edge("tools", "increment")
    workflow.add_edge("increment", "planner")
    workflow.add_edge("answer", END)
    return workflow.compile()


def print_and_save_trace(result, trace_list, q_id, question, gt, trace_file):
    trace_path = Path(trace_file).resolve(strict=False)
    if Path(_RUN_OUTPUT_ROOT).resolve(strict=False) not in trace_path.parents:
        raise RuntimeError("trace output escapes the sealed arm root")
    save_obj = {"question_id": q_id, "question": question, "gt_answer": gt, "trace": [_message_to_dict(m) for m in result["messages"]], "tool_telemetry": trace_list}
    with trace_path.open("x") as f: json.dump(save_obj, f, indent=2)
    return trace_file

# Training assets replace benchmark-only path resolvers before any graph is built.
from training_assets import bind_carrier_assets
bind_carrier_assets(sys.modules[__name__])
