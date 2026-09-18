"""Check native tool census against the preserved full Gemini response records."""
from __future__ import annotations

import native_google_telemetry as native

SITES = {'predict_2d_bounding_box', 'predict_2d_points', '_google_multimodal'}


def native_rows(rows):
    return [row for row in rows if row.get('event') in {native.START, native.TERMINAL}]


def native_projection(rows):
    return [dict(row, requested_model=row.get('model')) for row in native_rows(rows)
            if row.get('model_role') == 'tool_vlm']


def _without_none(value):
    if isinstance(value, dict):
        return {key: _without_none(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_without_none(item) for item in value]
    return value


def legacy_summary(rows):
    """Project only the existing non-event model summaries; native evidence stays intact."""
    return [{'where': row.get('where'), 'requested_model': row.get('model'),
             'provider_served_model': row.get('provider_served_model')}
            for row in rows if row.get('model_role') == 'tool_vlm' and not row.get('event')]


def summary_representation(trace):
    """Recognize the single r1308 serialization defect without modifying the trace."""
    rows = trace.get('tool_telemetry')
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError('native tool telemetry absent or malformed')
    actual = trace.get('tool_vlm_responses')
    if actual == legacy_summary(rows):
        return 'canonical_legacy_summary'
    receipt = trace.get('run_receipt') or {}
    if (receipt.get('round') == 1308 and receipt.get('schema') == 'r1308-training-episode-v1'
            and actual == native_projection(rows)
            and actual == trace.get('native_google_tool_responses')):
        return 'r1308_exact_native_projection'
    raise ValueError('legacy tool model summary changed')


def validate_native_tools(trace):
    rows = trace.get('tool_telemetry')
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError('native tool telemetry absent or malformed')
    captured = native_rows(rows)
    view = {'tool_telemetry': captured,
            'native_google_provider_calls': trace.get('native_google_provider_calls'),
            'tool_vlm_responses': trace.get('native_google_tool_responses')}
    count = native.validate(view)
    summary_representation(trace)
    terminals = [row for row in captured if row.get('event') == native.TERMINAL]
    legacy = [row for row in rows if row.get('where') in SITES and not row.get('event')]
    # Direct failures return no SDK response; streams retain any received chunks.
    expected = [row for row in terminals if row.get('status') == 'ok' or row.get('where') == '_google_multimodal']
    if len(legacy) != len(expected):
        raise ValueError('native call census differs from preserved response history')
    unmatched = list(legacy)
    for terminal in expected:
        # Concurrent tool calls may append their legacy rows in a different order.
        matches = [index for index, record in enumerate(unmatched)
                   if all(terminal.get(key) == record.get(key)
                          for key in ('where', 'model', 'provider_served_model', 'finish_reason'))
                   and _without_none(record.get('raw_response') if isinstance(record.get('raw_response'), list)
                                     else [record.get('raw_response')]) == terminal.get('raw_response')]
        if not matches:
            raise ValueError('native terminal differs from preserved response metadata')
        record = unmatched.pop(matches[0])
        payload = record.get('raw_response')
        chunks = payload if isinstance(payload, list) else [payload]
        if any(not isinstance(chunk, dict) for chunk in chunks):
            raise ValueError('complete native response payload is missing')
        if _without_none(chunks) != terminal.get('raw_response'):
            raise ValueError('complete native response history changed')
        candidates = [candidate for chunk in chunks for candidate in (chunk.get('candidates') or [])]
        if _without_none(candidates) != terminal.get('native_candidates'):
            raise ValueError('native candidate content or thoughts changed')
        text, thoughts = '', ''
        finish, usage, served = None, None, None
        for chunk in chunks:
            if chunk.get('usage_metadata') is not None:
                usage = _without_none(chunk['usage_metadata'])
            if chunk.get('model_version'):
                served = chunk['model_version']
            values = chunk.get('candidates') or []
            if values:
                if values[0].get('finish_reason') is not None:
                    finish = values[0]['finish_reason']
                for part in (values[0].get('content') or {}).get('parts') or []:
                    if part.get('text') is not None:
                        if part.get('thought'):
                            thoughts += part['text']
                        else:
                            text += part['text']
        if (terminal.get('content'), terminal.get('thoughts'), terminal.get('finish_reason'),
                terminal.get('usage'), terminal.get('provider_served_model')) != (text, thoughts, finish, usage, served):
            raise ValueError('native content/finish/usage/served-model projection changed')
    return count
