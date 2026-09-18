"""Keep native provider evidence when Gemini resets ordinary tool history."""

import copy

SCHEMA = 'r1308-discarded-message-history-v1'

NATIVE_EVENTS = frozenset({
    'native_google_call_start_v1', 'native_google_call_terminal_v1',
    'native_openai_verifier_start_v1', 'native_openai_verifier_terminal_v1',
})
LEGACY_NATIVE_SITES = frozenset({
    '_google_multimodal', 'predict_2d_bounding_box', 'predict_2d_points',
})


def is_provider_history(row):
    if not isinstance(row, dict):
        return False
    if row.get('event') in NATIVE_EVENTS:
        return True
    # Preserve malformed records from these origins too; admission must reject
    # missing payload fields rather than letting recovery silently erase them.
    return (not row.get('event') and row.get('where') in LEGACY_NATIVE_SITES
            and row.get('model_role') in {'tool_vlm', 'verifier'})


def clear_ordinary_history(trace_list):
    """Retain the same list and provider objects, order, and repeated occurrences."""
    trace_list[:] = [row for row in trace_list if is_provider_history(row)]


def new_discarded_history():
    return {'schema': SCHEMA, 'recoveries': []}


def discarded_tool_messages(trace):
    """Expose retained tool payloads to the existing standing error predicates."""
    history = trace.get('discarded_message_history')
    if isinstance(history, dict) and isinstance(history.get('recoveries'), list):
        for segment in history['recoveries']:
            if isinstance(segment, dict) and isinstance(segment.get('messages'), list):
                for message in segment['messages']:
                    if isinstance(message, dict) and str(message.get('role')).lower() == 'tool':
                        yield message


def capture_discarded_messages(history, messages, synthetic_messages, planner_attempts,
                               *, recovery_ordinal, reset_site, serialize_segment):
    """Snapshot actual tagged messages before reset without retaining mutable aliases."""
    history['recoveries'].append({
        'recovery_ordinal': recovery_ordinal,
        'reset_site': reset_site,
        'provider_attempts_seen': len(planner_attempts),
        'messages': copy.deepcopy(serialize_segment(messages, synthetic_messages)),
    })


def native_ai_evidence(trace, planner_attempts):
    """Validate ordered native correspondence across authentic discarded segments."""
    history = trace.get('discarded_message_history')
    if (not isinstance(history, dict) or set(history) != {'schema', 'recoveries'}
            or history['schema'] != SCHEMA or not isinstance(history['recoveries'], list)):
        raise ValueError('discarded-message evidence schema missing or invalid')
    current = trace.get('trace')
    if not isinstance(current, list) or len(current) < 2:
        raise ValueError('current initial messages missing')
    initial = current[:2]
    if any(not isinstance(row, dict) for row in initial):
        raise ValueError('initial messages malformed')
    if initial[0].get('role') != 'system' or initial[1].get('role') not in {'human', 'user'}:
        raise ValueError('initial message roles invalid')
    combined, previous = [], 0

    def match_segment(messages, attempts):
        if not isinstance(messages, list) or messages[:2] != initial:
            raise ValueError('discarded initial messages differ from current input')
        if any(not isinstance(row, dict) for row in messages):
            raise ValueError('discarded message record malformed')
        ai = [row for row in messages if row.get('role') in {'ai', 'assistant'}]
        if any(row.get('provenance') != 'provider' for row in ai):
            raise ValueError('synthetic or untagged AI cannot supply native correspondence')
        successful = [row for row in attempts if row.get('status') == 'ok']
        if [row.get('raw_response') for row in ai] != [row.get('raw_response') for row in successful]:
            raise ValueError('native segment correspondence is missing, altered or reordered')
        for row, call in zip(ai, successful):
            raw = call.get('raw_response')
            if not isinstance(raw, dict):
                raise ValueError('native response missing')
            for key in ('id', 'content', 'tool_calls', 'response_metadata', 'usage_metadata'):
                if row.get(key) != raw.get(key):
                    raise ValueError('native segment field changed: ' + key)
        return ai

    for ordinal, segment in enumerate(history['recoveries'], 1):
        if (not isinstance(segment, dict) or set(segment) != {
                'recovery_ordinal', 'reset_site', 'provider_attempts_seen', 'messages'}
                or type(segment['recovery_ordinal']) is not int
                or segment['recovery_ordinal'] != ordinal
                or segment['reset_site'] not in {'stream_creation', 'stream_iteration'}):
            raise ValueError('discarded recovery identity or ordering invalid')
        seen = segment['provider_attempts_seen']
        if type(seen) is not int or not previous <= seen <= len(planner_attempts):
            raise ValueError('discarded provider-attempt boundary invalid')
        attempts = planner_attempts[previous:seen]
        for call in attempts:
            finish = str(call.get('finish_reason', '')).strip().lower().split('.')[-1]
            if call.get('status') == 'ok' and finish in {'length', 'max_tokens', 'max_output_tokens'}:
                raise ValueError('planner cap cannot authorize discarded recovery')
        combined.extend(match_segment(segment['messages'], attempts))
        previous = seen
    combined.extend(match_segment(current, planner_attempts[previous:]))
    ids = [row.get('id') for row in combined]
    if not all(ids) or len(set(ids)) != len(ids):
        raise ValueError('native response IDs missing or duplicated across recovery')
    return combined
