"""Per-row admission against the deployed operand and response contract."""
import re
from .phrases import candidate_phrases, normalize_phrase, phrase_set
from trace_format.contracts import RUNTIME_STATUSES, response_status, new_contracts

OPERATOR_FAULTS = ('requires a fixed named candidate universe', 'outside the fixed candidate universe',
    'form_requires_v3.13', 'form_requires_v3.14', 'frozen_fusion_requires_depth_cut_receipt',
    'mask_source_unavailable_for_type')


def admission_phrases(question, options, cache_phrases, operands=()):
    names = candidate_phrases(question, options, cache_phrases)
    if any(normalize_phrase(n) not in names for n in operands):
        raise ValueError('contract_operand_outside_candidates')
    return names


def call_responses(row):
    events = row.get('routing', row).get('events', [])
    pending = None
    for event in events:
        kind = event.get('kind', '')
        if 'call' in event and 'response' in event:
            if pending is not None:
                yield pending, None
                pending = None
            yield event['call'], event['response']
        elif kind.endswith('_call') or ('call' in event and 'response' not in event):
            if pending is not None:
                yield pending, None
            pending = event.get('token', event.get('command', event.get('text', event.get('call', '')))).strip()
        elif kind.endswith('_response'):
            value = event.get('text', event.get('response'))
            if isinstance(value, dict):
                value = value.get('text', value.get('injected_text'))
            yield pending, value
            pending = None
    if pending is not None:
        yield pending, None


def _audit_training_contract(rows, manifest=None):
    """Return one verdict per row; callers defer failures, never abort the pool.

    After the first failed ground, permit one ground of a different listed name.
    No further call is legal, even if that retry succeeds. End in a direct answer.
    """
    verdicts = []
    for row in rows:
        reason = None
        pairs = list(call_responses(row))
        if not new_contracts() or not pairs:
            verdicts.append(None)
            continue
        entry = manifest.get(str(row.get('qid'))) if manifest is not None else row.get('candidate_manifest', row.get('cache_phrases', row.get('candidate_phrases')))
        cache_reader = row.get('mask_source') in ('sam3', 'cached_sam3', 'cache') or row.get('uses_mask_cache', False)
        named = any(isinstance(call,str) and re.search(r'obj="',call) for call,_ in pairs)
        if named and entry is None and (manifest is not None or cache_reader):
            verdicts.append('contract_manifest_missing')
            continue
        if isinstance(entry, dict):
            entry = entry.get('phrases', [])
        inputs = row.get('student_input', row)
        names = admission_phrases(inputs.get('question',''), inputs.get('options',[]), entry)
        if named and not names and entry is None:
            verdicts.append('contract_manifest_missing')
            continue
        failed = None
        retried = False
        for call, text in pairs:
            if not isinstance(call,str) or not isinstance(text,str) or not text.strip():
                reason = 'contract_missing_response'
                break
            if any(code in text for code in OPERATOR_FAULTS + RUNTIME_ONLY_FAULTS):
                reason = 'contract_operator_fault'
                break
            match = re.search(r'^<ground obj="([^"]+)"',call)
            name = normalize_phrase(match[1]) if match else None
            if name is not None and name not in names:
                reason = 'contract_operand_outside_candidates'
                break
            if failed is not None:
                if retried or name is None or name == failed:
                    reason = 'contract_call_after_failed_ground'
                    break
                retried = True
            body = text.strip().removeprefix('<tool_response>').removesuffix('</tool_response>').strip()
            status = response_status(body)
            if call.startswith(('<ground','<gap')) and status != 'error':
                from .live_trace313 import parse_response
                try:
                    parse_response(call,body,row.get('trace_revision',row.get('routing',{}).get('trace_revision','3.14')))
                except (ValueError, IndexError, TypeError):
                    reason = 'contract_unknown_status'
                    break
            partial_ground = status == 'heading unavailable' and bool(re.match(
                re.escape(match[1])+r': (?:frames |[1-9][0-9]* (?:instances|found)\n)', body)) if match else False
            if call.startswith('<ground') and status != 'ok' and not partial_ground:
                failed = failed or name or '<malformed ground>'
        target = row.get('target', row.get('suffix',''))
        if reason is None and failed is not None and not re.search(r'(?:<answer>.+</answer>|</think>\s*\S.*)$',target,re.S):
            reason = 'contract_recovery_without_answer'
        verdicts.append(reason)
    return verdicts


RUNTIME_ONLY_FAULTS = ('head_readout', 'head readout unavailable', 'own depth head unavailable',
    'invalid own depth', 'missing_or_invalid_K_transform', 'camera_rotation_not_proper',
    'native_mdg_requires_generate_binding', 'geometry_unavailable', 'mask_provider_unavailable',
    'gravity_unavailable', 'invalid own gravity', 'invalid own FoV', 'zero quaternion',
    'own pose readout must be finite', 'own FoV readout must be finite', 'depth query order differs')


def audit_training_contract(rows, manifest=None):
    """Malformed records defer locally; model call errors retain runtime recovery text."""
    verdicts = []
    for row in rows:
        try:
            if not isinstance(row, dict):
                raise TypeError('row')
            routing = row.get('routing', row)
            if not isinstance(routing, dict) or not isinstance(routing.get('events', []), list):
                raise TypeError('routing')
            for event in routing.get('events', []):
                if not isinstance(event, dict) or not isinstance(event.get('kind', ''), str):
                    raise TypeError('event')
                for key in ('call', 'token', 'command'):
                    if key in event and not isinstance(event[key], str):
                        raise TypeError('call')
            verdicts.extend(_audit_training_contract([row], manifest))
        except Exception:
            verdicts.append('contract_malformed_row')
    return verdicts
