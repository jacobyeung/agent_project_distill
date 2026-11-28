#!/usr/bin/env python3
"""Direct v1beta Inline-JPEG Gemini API Client for Native Grounding & Trace Authoring.

Follows GEMINI_NATIVE_LABELING_20261111.md and cluster IO/rate governance:
  - Direct HTTPS calls to https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
  - Inline base64 JPEGs ONLY (0.0 bytes uploaded to Gemini File API!).
  - Image-first part ordering, systemInstruction rules, [ymin, xmin, ymax, xmax] 0-1000 boxes,
    and strict responseJsonSchema structured outputs.
  - Polls OVER_CAP every 15 s, logs token usage to GEMINI_USAGE_LOG & GEMINI_USAGE_SHARED,
    and applies exponential backoff + jitter on HTTP 429/503 (with optional Neon -> Carbon fallback).
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import random
import socket
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import httpx
from PIL import Image, ImageDraw

from geo_solver import box_iou_1000

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_OVER_CAP_PATH = Path(
    os.environ.get(
        "GEMINI_OVER_CAP",
        "/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/gemini_subagents/OVER_CAP",
    )
)
DEFAULT_LOCAL_USAGE_LOG = Path(
    os.environ.get("GEMINI_USAGE_LOG", f"/scratch/{os.environ.get('USER', 'jjyeung')}/gemini_runs/usage.jsonl")
)
DEFAULT_SHARED_USAGE_LOG = Path(
    os.environ.get(
        "GEMINI_USAGE_SHARED",
        f"/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/gemini_subagents/usage/usage.{socket.gethostname().split('.')[0]}.jsonl",
    )
)

DEFAULT_THINKING_LEVEL: Dict[str, Optional[str]] = {
    "gemini-4-carbon": "MEDIUM",
    "gemini-4-argon": "HIGH",
    "gemini-4-neon": "MEDIUM",
    "gemini-4-hydrogen": "LOW",
    "gemini-3.8-flash": None,
}

NATIVE_BOX_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "present": {
            "type": "boolean",
            "description": "True iff the queried target object is clearly visible in this image.",
        },
        "referent_clear": {
            "type": "boolean",
            "description": "True iff the target referent is visually unambiguous (not occluded beyond recognition).",
        },
        "box_2d": {
            "type": "array",
            "description": "Tight 2D bounding box [ymin, xmin, ymax, xmax] normalized to 0-1000, or [0,0,0,0] if absent.",
            "items": {"type": "integer"},
            "minItems": 4,
            "maxItems": 4,
        },
        "visible_count": {
            "type": "integer",
            "description": "Number of distinct instances of this object category visible in this single frame.",
        },
    },
    "required": ["present", "referent_clear", "box_2d", "visible_count"],
}

TRACE_AUTHOR_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "think_steps": {
            "type": "array",
            "description": (
                "Concise grounded <think> strings, one per trajectory step (including the final answer step). "
                "Step 0 MUST start with 'Intent: ...'. Total words across all steps MUST be <= 140. "
                "Never guess metric numbers before tool return; verify tool status and units cleanly."
            ),
            "items": {"type": "string"},
        },
        "paraphrased_prompt": {
            "type": "string",
            "description": "Optional natural linguistic paraphrase preserving exact entities, frame numbers, facing direction, and requested unit.",
        },
        "visual_sanity_ok": {
            "type": "boolean",
            "description": "True iff the contact-sheet frames visually support the queried room and objects.",
        },
    },
    "required": ["think_steps", "visual_sanity_ok"],
}


def encode_frame_jpeg_b64(
    image_path: str | Path,
    max_size: Tuple[int, int] = (640, 480),
    quality: int = 82,
) -> Tuple[str, int, Tuple[int, int]]:
    """Encode a local PNG/JPG into a ruler-free inline base64 JPEG (returns b64, raw_bytes, (w, h))."""
    with Image.open(image_path) as im:
        rgb = im.convert("RGB")
        rgb.thumbnail(max_size, Image.Resampling.BILINEAR)
        w, h = rgb.size
        buf = io.BytesIO()
        rgb.save(buf, format="JPEG", quality=quality, optimize=True)
        raw = buf.getvalue()
    return base64.b64encode(raw).decode("ascii"), len(raw), (w, h)


def build_contact_sheet_jpeg_b64(
    frame_items: Sequence[Tuple[int, str | Path]],
    cols: int = 3,
    tile_wh: Tuple[int, int] = (360, 270),
    quality: int = 78,
) -> Tuple[str, int]:
    """Build a compact multi-view contact sheet with clean 'f{k}' corner badges (0 File API bytes)."""
    if not frame_items:
        raise ValueError("frame_items cannot be empty")
    n = len(frame_items)
    rows = (n + cols - 1) // cols
    tw, th = tile_wh
    canvas = Image.new("RGB", (cols * tw, rows * th), (18, 18, 18))
    draw = ImageDraw.Draw(canvas)

    for idx, (frame_num, path) in enumerate(frame_items):
        r, c = divmod(idx, cols)
        x0, y0 = c * tw, r * th
        with Image.open(path) as im:
            tile = im.convert("RGB").resize((tw, th), Image.Resampling.BILINEAR)
        canvas.paste(tile, (x0, y0))
        badge = f"f{frame_num}"
        draw.rectangle([x0 + 4, y0 + 4, x0 + 46, y0 + 24], fill=(0, 0, 0))
        draw.text((x0 + 9, y0 + 8), badge, fill=(255, 255, 255))

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=quality, optimize=True)
    raw = buf.getvalue()
    return base64.b64encode(raw).decode("ascii"), len(raw)


def _append_usage_line(path: Path, line: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o664)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
    except OSError:
        pass


@dataclass
class APITelemetry:
    calls_total: int = 0
    calls_ok: int = 0
    http_429: int = 0
    http_503: int = 0
    http_other_err: int = 0
    timeouts: int = 0
    neon_to_carbon_fallbacks: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    thought_tokens: int = 0
    outbound_b64_bytes: int = 0
    inbound_json_bytes: int = 0
    latencies_s: List[float] = field(default_factory=list)
    by_model_calls: Dict[str, int] = field(default_factory=dict)
    by_model_latencies: Dict[str, List[float]] = field(default_factory=dict)

    def summary(self, wall_seconds: float) -> Dict[str, Any]:
        lats = sorted(self.latencies_s)
        n = len(lats)
        p50 = lats[n // 2] if n else 0.0
        p90 = lats[min(n - 1, int(0.9 * n))] if n else 0.0
        per_model = {}
        for m, mlats in sorted(self.by_model_latencies.items()):
            ms = sorted(mlats)
            per_model[m] = {
                "ok_calls": len(ms),
                "median_s": round(ms[len(ms) // 2], 2) if ms else 0.0,
                "mean_s": round(sum(ms) / len(ms), 2) if ms else 0.0,
            }
        total_attempts = max(1, self.calls_total)
        return {
            "wall_seconds": round(wall_seconds, 2),
            "calls_total": self.calls_total,
            "calls_ok": self.calls_ok,
            "http_429": self.http_429,
            "http_503": self.http_503,
            "http_other_err": self.http_other_err,
            "timeouts": self.timeouts,
            "rate_429_503": round((self.http_429 + self.http_503) / total_attempts, 4),
            "neon_to_carbon_fallbacks": self.neon_to_carbon_fallbacks,
            "prompt_tokens": self.prompt_tokens,
            "output_tokens": self.output_tokens,
            "thought_tokens": self.thought_tokens,
            "outbound_mb": round(self.outbound_b64_bytes / (1024 * 1024), 3),
            "inbound_mb": round(self.inbound_json_bytes / (1024 * 1024), 3),
            "internet_mb_per_s": round(
                (self.outbound_b64_bytes + self.inbound_json_bytes) / (1024 * 1024) / max(0.1, wall_seconds),
                4,
            ),
            "file_api_bytes_uploaded": 0,
            "latency_p50_s": round(p50, 2),
            "latency_p90_s": round(p90, 2),
            "per_model": per_model,
        }


class GeminiInlineClient:
    """Async direct Gemini v1beta inline-JPEG client with backoff, OVER_CAP guard & metering."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        concurrency: int = 16,
        request_timeout_s: float = 180.0,
        max_retries: int = 4,
        caller_tag: str = "e05_api_factory",
        over_cap_path: Path = DEFAULT_OVER_CAP_PATH,
        enable_usage_log: bool = True,
    ) -> None:
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is required for live Gemini API calls")
        self.semaphore = asyncio.Semaphore(concurrency)
        self.request_timeout_s = request_timeout_s
        self.max_retries = max_retries
        self.caller_tag = caller_tag
        self.over_cap_path = over_cap_path
        self.enable_usage_log = enable_usage_log
        self.telemetry = APITelemetry()
        self._last_cap_check = 0.0
        self._over_cap_cached = False
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "GeminiInlineClient":
        limits = httpx.Limits(max_keepalive_connections=32, max_connections=64)
        self._client = httpx.AsyncClient(timeout=self.request_timeout_s, limits=limits)
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _respect_over_cap(self) -> None:
        now = time.monotonic()
        if now - self._last_cap_check >= 15.0:
            self._last_cap_check = now
            self._over_cap_cached = self.over_cap_path.exists()
        if self._over_cap_cached:
            # Polite auto-throttle when Main/subagent OVER_CAP marker is active
            await asyncio.sleep(5.0)
            self._over_cap_cached = self.over_cap_path.exists()

    async def generate_json(
        self,
        model: str,
        prompt_text: str,
        inline_jpegs_b64: Sequence[str] = (),
        system_instruction: Optional[str] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        thinking_level: Optional[str] = "AUTO",
        fallback_model: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Send native image-first generateContent call and parse structured JSON response."""
        if self._client is None:
            raise RuntimeError("Use GeminiInlineClient inside 'async with' context")

        for b64 in inline_jpegs_b64:
            if b64.startswith("http://") or b64.startswith("https://") or "files/" in b64[:16]:
                raise ValueError("File API URIs are forbidden; pass raw base64 JPEG data only")

        # Native format: ALL images FIRST, specific prompt text LAST
        parts: List[Dict[str, Any]] = [
            {"inlineData": {"mimeType": "image/jpeg", "data": b64}} for b64 in inline_jpegs_b64
        ]
        parts.append({"text": prompt_text})

        active_model = model
        b64_bytes = sum(len(x) for x in inline_jpegs_b64)

        for attempt in range(self.max_retries + 1):
            await self._respect_over_cap()
            lvl = DEFAULT_THINKING_LEVEL.get(active_model) if thinking_level == "AUTO" else thinking_level
            gen_cfg: Dict[str, Any] = {"responseMimeType": "application/json"}
            if response_schema is not None:
                gen_cfg["responseJsonSchema"] = response_schema
            if lvl:
                gen_cfg["thinkingConfig"] = {"thinkingLevel": lvl}

            payload: Dict[str, Any] = {
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": gen_cfg,
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            url = f"{GEMINI_API_BASE}/{active_model}:generateContent"
            async with self.semaphore:
                self.telemetry.calls_total += 1
                self.telemetry.by_model_calls[active_model] = self.telemetry.by_model_calls.get(active_model, 0) + 1
                self.telemetry.outbound_b64_bytes += b64_bytes
                t0 = time.monotonic()
                try:
                    resp = await self._client.post(
                        url,
                        headers={"x-goog-api-key": self.api_key},
                        json=payload,
                    )
                    dt = time.monotonic() - t0
                except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.PoolTimeout):
                    self.telemetry.timeouts += 1
                    if fallback_model and active_model != fallback_model:
                        self.telemetry.neon_to_carbon_fallbacks += 1
                        active_model = fallback_model
                    elif active_model == "gemini-4-argon" and thinking_level in ("AUTO", "HIGH"):
                        thinking_level = "MEDIUM"
                    if attempt < self.max_retries:
                        await asyncio.sleep(min(8.0, (1.5 ** attempt) + random.uniform(0.1, 0.5)))
                        continue
                    raise
                except httpx.HTTPError:
                    self.telemetry.http_other_err += 1
                    if attempt < self.max_retries:
                        await asyncio.sleep(min(8.0, (1.5 ** attempt) + random.uniform(0.1, 0.5)))
                        continue
                    raise

            if resp.status_code in (429, 500, 502, 503, 504):
                if resp.status_code == 429:
                    self.telemetry.http_429 += 1
                elif resp.status_code == 503:
                    self.telemetry.http_503 += 1
                else:
                    self.telemetry.http_other_err += 1

                # Seamless Neon -> Carbon fallback on 503 demand spikes
                if (
                    resp.status_code == 503
                    and fallback_model
                    and active_model != fallback_model
                ):
                    self.telemetry.neon_to_carbon_fallbacks += 1
                    active_model = fallback_model
                    await asyncio.sleep(random.uniform(0.15, 0.5))
                    continue
                if resp.status_code == 503 and active_model == "gemini-4-argon" and thinking_level in ("AUTO", "HIGH"):
                    thinking_level = "MEDIUM"

                if attempt < self.max_retries:
                    backoff = min(30.0, (2.0 ** attempt) + random.uniform(0.25, 1.25))
                    await asyncio.sleep(backoff)
                    continue
                raise RuntimeError(f"Gemini HTTP {resp.status_code} on {active_model}: {resp.text[:240]}")

            if resp.status_code != 200:
                self.telemetry.http_other_err += 1
                raise RuntimeError(f"Gemini HTTP {resp.status_code} on {active_model}: {resp.text[:240]}")

            raw_bytes = resp.content
            self.telemetry.inbound_json_bytes += len(raw_bytes)
            doc = json.loads(raw_bytes)
            usage = doc.get("usageMetadata", {})
            p_tok = int(usage.get("promptTokenCount") or 0)
            c_tok = int(usage.get("candidatesTokenCount") or 0)
            t_tok = int(usage.get("thoughtsTokenCount") or 0)

            self.telemetry.calls_ok += 1
            self.telemetry.prompt_tokens += p_tok
            self.telemetry.output_tokens += c_tok
            self.telemetry.thought_tokens += t_tok
            self.telemetry.latencies_s.append(dt)
            self.telemetry.by_model_latencies.setdefault(active_model, []).append(dt)

            if self.enable_usage_log:
                rec = json.dumps({
                    "epoch": round(time.time(), 3),
                    "run_dir": "/scratch/jjyeung/orch_home_distill/e05_api_factory",
                    "caller": self.caller_tag,
                    "workdir": "/scratch/jjyeung/orch_home_distill/e05_api_factory",
                    "model": f"gemini/{active_model}",
                    "alias": active_model,
                    "status": 200,
                    "prompt_tokens": p_tok,
                    "output_tokens": c_tok,
                    "thought_tokens": t_tok,
                }) + "\n"
                _append_usage_line(DEFAULT_LOCAL_USAGE_LOG, rec)
                _append_usage_line(DEFAULT_SHARED_USAGE_LOG, rec)

            candidates = doc.get("candidates") or []
            if not candidates or "content" not in candidates[0]:
                if attempt < self.max_retries:
                    await asyncio.sleep(1.0)
                    continue
                raise RuntimeError(f"Empty candidates from {active_model}: {str(doc)[:220]}")

            resp_parts = candidates[0]["content"].get("parts") or []
            text_out = ""
            for p in reversed(resp_parts):
                if "text" in p and not p.get("thought"):
                    text_out = p["text"]
                    break
            if not text_out and resp_parts:
                text_out = resp_parts[-1].get("text", "")

            try:
                parsed = json.loads(text_out)
            except json.JSONDecodeError:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.8)
                    continue
                raise

            meta = {
                "model_used": active_model,
                "latency_s": round(dt, 3),
                "prompt_tokens": p_tok,
                "output_tokens": c_tok,
                "thought_tokens": t_tok,
            }
            return parsed, meta

        raise RuntimeError(f"Exhausted retries on {active_model}")

    async def verify_referent_argon_carbon(
        self,
        frame_jpeg_b64: str,
        object_label: str,
        spatial_hint: str = "",
        gt_box_1000: Optional[Sequence[int]] = None,
        min_ac_iou: float = 0.55,
        argon_level: str = "HIGH",
    ) -> Dict[str, Any]:
        """Independent blind Argon + Carbon native box & visibility gate (GEMINI_NATIVE_LABELING)."""
        sys_inst = (
            "You are a precision 2D visual grounding verifier for indoor 3D scenes. "
            "Inspect the image carefully. Report present=true ONLY if the target object is clearly visible. "
            "Output tight box_2d as [ymin, xmin, ymax, xmax] on 0-1000 integer coordinates."
        )
        hint_clause = f" ({spatial_hint})" if spatial_hint else ""
        query = (
            f"Target object: '{object_label}'{hint_clause}. "
            "Is this target clearly visible and unambiguous in this frame? Return JSON."
        )

        (argon_res, argon_meta), (carbon_res, carbon_meta) = await asyncio.gather(
            self.generate_json(
                model="gemini-4-argon",
                prompt_text=query,
                inline_jpegs_b64=[frame_jpeg_b64],
                system_instruction=sys_inst,
                response_schema=NATIVE_BOX_SCHEMA,
                thinking_level=argon_level,
            ),
            self.generate_json(
                model="gemini-4-carbon",
                prompt_text=query,
                inline_jpegs_b64=[frame_jpeg_b64],
                system_instruction=sys_inst,
                response_schema=NATIVE_BOX_SCHEMA,
                thinking_level="MEDIUM",
            ),
        )

        a_pres = bool(argon_res.get("present")) and bool(argon_res.get("referent_clear"))
        c_pres = bool(carbon_res.get("present")) and bool(carbon_res.get("referent_clear"))
        a_box = [max(0, min(1000, int(v))) for v in argon_res.get("box_2d", [0, 0, 0, 0])]
        c_box = [max(0, min(1000, int(v))) for v in carbon_res.get("box_2d", [0, 0, 0, 0])]
        ac_iou = box_iou_1000(a_box, c_box) if (a_pres and c_pres) else 0.0

        consensus_box = [int(round((a_box[i] + c_box[i]) / 2.0)) for i in range(4)]
        gt_iou = box_iou_1000(consensus_box, gt_box_1000) if (gt_box_1000 and a_pres and c_pres) else None

        # Multi-instance scenes may have Argon & Carbon pick two visible chairs unless spatial_hint binds one;
        # require both present + Argon∩Carbon IoU >= min_ac_iou (or either matches GT target >=0.55 when multi-inst).
        multi_vis = int(argon_res.get("visible_count", 1)) > 1 or int(carbon_res.get("visible_count", 1)) > 1
        gt_match_ok = False
        if gt_box_1000 and multi_vis and a_pres and c_pres:
            gt_match_ok = max(box_iou_1000(a_box, gt_box_1000), box_iou_1000(c_box, gt_box_1000)) >= 0.55

        agreed = bool(a_pres and c_pres and (ac_iou >= min_ac_iou or gt_match_ok))
        return {
            "agreed": agreed,
            "argon_present": a_pres,
            "carbon_present": c_pres,
            "argon_box_1000": a_box,
            "carbon_box_1000": c_box,
            "consensus_box_1000": consensus_box,
            "argon_carbon_iou": round(ac_iou, 4),
            "gt_iou": round(gt_iou, 4) if gt_iou is not None else None,
            "visible_count_argon": int(argon_res.get("visible_count", 0)),
            "visible_count_carbon": int(carbon_res.get("visible_count", 0)),
            "latency_argon_s": argon_meta["latency_s"],
            "latency_carbon_s": carbon_meta["latency_s"],
        }

    async def author_grounded_trace(
        self,
        contact_sheet_b64: str,
        task_spec: Dict[str, Any],
        scaffold_steps: List[Dict[str, Any]],
        preferred_model: str = "gemini-4-carbon",
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Author concise (<250-token), zero-guessing SPLIT + GeoAPI-v2 CoT steps on real frames."""
        n_expected = len(scaffold_steps)
        sys_inst = (
            "You author concise, grounded SPLIT-style spatial reasoning traces (<think> steps) "
            "over multi-view room contact sheets and deterministic GeoAPI-v2 tool executions.\n"
            "HARD RULES:\n"
            "1. Return EXACTLY one concise <think> string per step in `think_steps` (same length as input steps).\n"
            "2. `think_steps[0]` MUST start with 'Intent: ' naming the geometric operation and requested unit.\n"
            "3. NEVER guess metric distances, sizes, or bearings before a tool returns.\n"
            "4. When a tool returns UNSEEN, LOW_PARALLAX, or MULTI_SLOT, briefly diagnose the epistemic state "
            "and justify the recovery action (inspect frame + box_hint, wide-baseline frames, or slot binding).\n"
            "5. Keep total words across ALL `think_steps` combined <= 110 words (crisp, zero fluff, zero frame loops).\n"
            "6. Only mention frame numbers that actually appear in the contact sheet or tool outputs."
        )

        steps_desc = []
        for idx, st in enumerate(scaffold_steps):
            if "call" in st:
                obs_txt = st.get("tool_response") or st.get("tool_obs") or ""
                steps_desc.append(f"Step {idx}: executes {st['call']} -> returns {obs_txt}")
            else:
                steps_desc.append(f"Step {idx} (final): emits <answer>{st['answer']}</answer>")

        prompt_txt = (
            f"Task family: {task_spec['task_family']} | Epistemic mode: {task_spec['epistemic_mode']}\n"
            f"User question: {task_spec['prompt']}\n"
            f"Executed GeoAPI-v2 trajectory ({n_expected} steps):\n"
            + "\n".join(steps_desc)
            + f"\n\nWrite `think_steps` (array of {n_expected} crisp strings) and set `visual_sanity_ok`."
        )

        fallback = "gemini-4-carbon" if preferred_model == "gemini-4-neon" else None
        res, meta = await self.generate_json(
            model=preferred_model,
            prompt_text=prompt_txt,
            inline_jpegs_b64=[contact_sheet_b64],
            system_instruction=sys_inst,
            response_schema=TRACE_AUTHOR_SCHEMA,
            thinking_level="AUTO",
            fallback_model=fallback,
        )

        thinks = [str(x).strip() for x in (res.get("think_steps") or [])]
        # Guarantee exact step alignment if model merged or split a step
        if len(thinks) != n_expected:
            padded = []
            for i in range(n_expected):
                if i < len(thinks) and thinks[i]:
                    padded.append(thinks[i])
                else:
                    padded.append(scaffold_steps[i].get("default_think", "Verify tool output and finalize answer."))
            thinks = padded
        if not thinks[0].startswith("Intent:"):
            thinks[0] = f"Intent: {task_spec['task_family']} ({task_spec.get('unit', 'canonical')}). " + thinks[0]

        merged_turns: List[Dict[str, Any]] = []
        for st, th in zip(scaffold_steps, thinks):
            turn_out = {"think": th}
            if "call" in st:
                turn_out["call"] = st["call"]
            if "answer" in st:
                turn_out["answer"] = st["answer"]
            merged_turns.append(turn_out)

        meta["visual_sanity_ok"] = bool(res.get("visual_sanity_ok", True))
        meta["paraphrased_prompt"] = res.get("paraphrased_prompt")
        return merged_turns, meta
