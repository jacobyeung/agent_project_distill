"""Preserve native Google responses while recording every tool-provider boundary."""
import time
import uuid

START = "native_google_call_start_v1"
TERMINAL = "native_google_call_terminal_v1"


def _json(value):
    return value.model_dump(mode="json", exclude_none=True) if value is not None else None


class _Call:
    def __init__(self, sink, where, model_role, model, config):
        if not isinstance(sink, list):
            raise RuntimeError("native Google provider call requires the shared telemetry sink")
        self.sink = sink
        self.started = time.monotonic()
        self.identity = dict(call_id=uuid.uuid4().hex, where=where, model=str(model),
                             output_budget_tokens=config.max_output_tokens)
        self.row = dict(self.identity, event=TERMINAL, model_role=model_role,
                        provider="google", content="", thoughts="", finish_reason=None,
                        usage=None, provider_served_model=None, native_candidates=[], raw_response=[],
                        status="incomplete", tool_budget_terminal=False)
        sink.append(dict(self.identity, event=START))

    def observe(self, response):
        row = self.row
        row["raw_response"].append(_json(response))
        if response.usage_metadata is not None:
            row["usage"] = _json(response.usage_metadata)
            usage = response.usage_metadata
            row.update(input_tokens=usage.prompt_token_count,
                       output_tokens=usage.candidates_token_count,
                       total_tokens=usage.total_token_count,
                       thoughts_tokens=usage.thoughts_token_count)
        if response.model_version:
            row["provider_served_model"] = response.model_version
        candidates = response.candidates or []
        row["native_candidates"].extend(_json(candidate) for candidate in candidates)
        if candidates:
            candidate = candidates[0]
            if candidate.finish_reason is not None:
                row["finish_reason"] = getattr(candidate.finish_reason, "value", str(candidate.finish_reason))
            for part in (getattr(candidate.content, "parts", None) or []):
                if part.text is not None:
                    row["thoughts" if part.thought else "content"] += part.text
        if getattr(response, "prompt_feedback", None) is not None:
            row["prompt_feedback"] = _json(response.prompt_feedback)

    def finish(self, error=None):
        self.row["status"] = "error" if error else "ok"
        if error:
            self.row["error_type"] = type(error).__name__
            from transport_admission import exception_http_status
            self.row["http_status"] = exception_http_status(error)
        self.row["elapsed_ms"] = int((time.monotonic() - self.started) * 1000)
        self.row["tool_budget_terminal"] = self.row["finish_reason"] == "MAX_TOKENS"
        self.sink.append(self.row)


def generate_content(client, *, sink, where, model_role, model, contents, config):
    call = _Call(sink, where, model_role, model, config)
    try:
        response = client.models.generate_content(model=model, contents=contents, config=config)
        call.observe(response)
    except BaseException as error:
        call.finish(error)
        raise
    call.finish()
    return response


def generate_content_stream(client, *, sink, where, model_role, model, contents, config):
    call = _Call(sink, where, model_role, model, config)
    try:
        for response in client.models.generate_content_stream(model=model, contents=contents, config=config):
            call.observe(response)
            yield response
    except BaseException as error:
        call.finish(error)
        raise
    call.finish()


def census(rows):
    return [dict(row) for row in rows if row.get("event") == START]


def validate(trace, requested_model="gemini-3.5-flash"):
    """Require complete one-to-one provider evidence without changing cap grading."""
    rows = trace.get("tool_telemetry")
    calls = trace.get("native_google_provider_calls")
    if not isinstance(rows, list) or not isinstance(calls, list):
        raise RuntimeError("native Google provider census or shared telemetry missing")
    starts = census(rows)
    terminals = [row for row in rows if row.get("event") == TERMINAL]
    if starts != calls or len(starts) != len(terminals):
        raise RuntimeError("native Google provider call/terminal census mismatch")
    ids = [row.get("call_id") for row in starts]
    if len(ids) != len(set(ids)) or any(not isinstance(x, str) or not x for x in ids):
        raise RuntimeError("native Google provider call identity missing or duplicated")
    by_id = {row.get("call_id"): row for row in terminals}
    if len(by_id) != len(terminals) or set(by_id) != set(ids):
        raise RuntimeError("native Google terminal identity mismatch")
    for start in starts:
        row = by_id[start["call_id"]]
        if any(row.get(key) != start[key] for key in ("where", "model", "output_budget_tokens")):
            raise RuntimeError("native Google boundary identity mismatch")
        if row.get("model_role") == "tool_vlm" and row.get("model") != requested_model:
            raise RuntimeError("native Google requested tool model mismatch")
        if not all(isinstance(row.get(key), str) for key in ("content", "thoughts")):
            raise RuntimeError("native Google content/thought evidence missing")
        if row.get("tool_budget_terminal") is not (row.get("finish_reason") == "MAX_TOKENS"):
            raise RuntimeError("native Google tool-cap evidence mismatch")
        if row.get("status") == "ok":
            if not row.get("finish_reason") or not isinstance(row.get("usage"), dict) or not row.get("provider_served_model"):
                raise RuntimeError("native Google successful terminal metadata incomplete")
            if not isinstance(row.get("raw_response"), list) or not row["raw_response"]:
                raise RuntimeError("native Google native SDK response evidence missing")
            if any(not isinstance(row["usage"].get(key), int) or row["usage"][key] < 0
                   for key in ("prompt_token_count", "candidates_token_count", "total_token_count")):
                raise RuntimeError("native Google native usage evidence incomplete")
        elif row.get("status") != "error" or not row.get("error_type"):
            raise RuntimeError("native Google provider terminal status incomplete")
    expected = [dict(row, requested_model=row.get("model")) for row in rows
                if row.get("model_role") == "tool_vlm"]
    if trace.get("tool_vlm_responses") != expected:
        raise RuntimeError("native Google tool terminal projection mismatch")
    return len(starts)
