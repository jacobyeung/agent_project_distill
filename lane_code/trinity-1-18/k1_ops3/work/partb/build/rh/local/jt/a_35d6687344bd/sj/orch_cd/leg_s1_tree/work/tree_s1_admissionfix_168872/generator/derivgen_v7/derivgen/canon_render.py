"""Serialize canonical paragraph events without evaluating any arithmetic.

canonical_text and canonical_paragraph extend the existing role/kind contract.
The remaining call/response fields follow Trace's published-value API.
Offsets are half-open Unicode character positions, as in the existing renderer.
"""
from .common import Refusal
from .trace import loss_spans


def render(events, answer):
    parts, spans, cursor = [], [], 0

    def emit(text, index=None, call_id=None):
        nonlocal cursor
        start = cursor
        parts.append(text)
        cursor += len(text)
        if call_id is not None:
            spans.append({"start": start, "end": cursor, "role": "tool", "target_loss": 0,
                          "event_index": index, "event_id": f"event-{index}", "call_id": call_id})

    emit("<think>\n")
    for index, event in enumerate(events):
        kind = event["kind"]
        if kind == "plan": emit(event["text"] + "\n\n")
        elif kind in ("canonical_text", "correction"): emit(event["text"])
        elif kind == "canonical_paragraph": emit("\n\n")
        elif kind in ("tool_call", "calculator_call"):
            emit(event.get("prefix", "") + event.get("command", event.get("token", "")))
        elif kind in ("tool_response", "calculator_response"):
            text = event["response"]["text"] if kind == "calculator_response" else event["text"]
            emit("<tool_response>" + text + "</tool_response>", index, event["call_id"])
        elif kind != "decision": raise Refusal("canonical_event_kind", kind)
    emit("\n</think>\n\n" + str(answer))
    target = "".join(parts)
    return {"target": target, "tool_output_spans": spans, "loss_spans": loss_spans(target, spans)}
