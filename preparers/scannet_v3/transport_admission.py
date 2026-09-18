"""Structured rate-limit admission; provider content never supplies error identity."""

RATE_LIMIT_CLASSES = frozenset({'RateLimitError', 'TooManyRequests', 'ResourceExhausted'})
SAM3_TOOLS = frozenset({'predict_2d_segmentation_masks', 'predict_2d_segmentation_masks_video'})


def exception_http_status(error):
    """Read typed transport attributes only; never parse exception or body text."""
    for name in ('status_code', 'code', 'http_status'):
        value = getattr(error, name, None)
        if type(value) is int and 100 <= value <= 599:
            return value
    value = getattr(getattr(error, 'response', None), 'status_code', None)
    return value if type(value) is int and 100 <= value <= 599 else None


def is_rate_limit_error(row):
    if not isinstance(row, dict) or row.get('status') != 'error':
        return False
    status = row.get('http_status')
    if status is not None:
        # Any explicit status wins over class names. Malformed statuses do not
        # supply fallback retry authority; independent admission still applies.
        return type(status) is int and status == 429
    return (row.get('error_class') or row.get('error_type')) in RATE_LIMIT_CLASSES


def structured_transport_failure(trace):
    """Preserve the inherited answerless true-429 gate and planner group semantics."""
    if trace.get('pred') is not None:
        return None
    planner = ((trace.get('llm_usage') or {}).get('planner') or {})
    calls = planner.get('calls_detail')
    if isinstance(calls, list):
        last_by_group = {}
        for row in calls:
            if (isinstance(row, dict) and row.get('provider') == 'google-native'
                    and row.get('family') in {'planner', 'salvage'}
                    and type(row.get('call_index')) is int):
                last_by_group[row['call_index']] = row
        if any(is_rate_limit_error(row) for row in last_by_group.values()):
            return 'HTTP-429 transport failure'
    rows = trace.get('tool_telemetry')
    if isinstance(rows, list):
        for row in rows:
            if (isinstance(row, dict) and row.get('event') == 'native_google_call_terminal_v1'
                    and row.get('provider') == 'google' and row.get('model_role') in {'tool_vlm', 'verifier'}
                    and is_rate_limit_error(row)):
                return 'HTTP-429 transport failure'
    return None


def trusted_sam3_failure(trace):
    """Recognize the existing SAM3 error-branch telemetry without parsing status."""
    rows = trace.get('tool_telemetry')
    return isinstance(rows, list) and any(
        isinstance(row, dict) and row.get('tool') in SAM3_TOOLS
        and isinstance(row.get('response'), str) and row['response'].startswith('ERROR: ')
        for row in rows)
