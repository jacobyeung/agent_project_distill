import argparse
import copy
import hashlib
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


FORMAT = 'compact_counted_v1'
MAX_TOKENS = 1536
SEED = 17
MARKER = 'End of reasoning.'
VARIANT_DIRECTORY = 'pilot_variant_derivation_citations'
TOKENIZER = Path('/data2/jjyeung/cache/huggingface/hub/models--OneThink--OneThinker-8B/snapshots/2b7032f4179d8c032d2eac67b3692263f85be0fc')
TIER_I_CHECKS = ('answer_equality', 'artifact_lint', 'measurement_templates', 'native_final_not_cited',
                 'own_record_binding', 'qualification_scope', 'schema', 'source_snapshot', 'student_input_schema')
RECORD_GROUPS = ('records', 'appearances', 'calculations_v2', 'qualifications_v2', 'conventions_v2')
# Operand quantity kinds whose value can enter each calculation operation. Every (operation, operand
# quantity) pair present in the 3,852 reviewed sources appears here or is dropped by omission: a
# visibility record states presence and carries no quantity, a centroid and a floor elevation do not
# enter an extent, and only an extent operation consumes the p90 extent and the p5/p95 corners. An
# operation outside this table defers the qid as unknown_operation.
OPERAND_QUANTITIES = {
    'closest_point_distance': (),
    'cross_z_xy': ('centroid',),
    'direction_xy': ('centroid',),
    'displacement_xy': ('centroid',),
    'displacement_xyz': ('centroid',),
    'distance_xyz': ('centroid',),
    'extent_xyz': ('extent_xyz_p90', 'max_xyz_p95', 'min_xyz_p5'),
    'projection_xy': ('centroid',),
    'raw_result': ('centroid', 'extent_xyz_p90', 'floor_z_estimate', 'max_xyz_p95', 'min_xyz_p5'),
    'signed_turn_xy': ('centroid',),
}
# A counting answer is the number of distinct instances, which only the typed identity records name.
ROSTER_TYPES = ('object_counting',)
ROSTER_TEMPLATE = 'Distinct instances observed: {names}.'
ROSTER_ID = 'ROSTER'
ROSTER_KIND = 'roster'
ROSTER_NAME = re.compile(r'[A-Za-z][A-Za-z /\'-]*')
# The reviewed pilot found appearance-order targets answerable from the appearance lines alone; every
# other type without a Calculations section loses the lines its answer depends on and defers.
CALCULATION_FREE_TYPES = ('obj_appearance_order',)
# Orchestrator ruling 2026-09-19: a derivation whose operands all lack a quantity keeps its target and
# loses the clause, because the derivation prose still names what it compares; defer stays available.
UNBOUND_POLICIES = ('drop_clause', 'defer')
# Admission check to the reason a failure records in DEFERRED.jsonl.
REASON_CODES = {'byte_fidelity': 'byte_fidelity_changed', 'numeric_tokens': 'ungrounded_numeric_tokens',
                'record_binding': 'record_binding_failed', 'counted_layout': 'counted_layout_invalid',
                'observation_references': 'invalid_observation_reference', 'terminal_answer': 'terminal_answer_invalid',
                'source_tier_i': 'source_tier_i_failed', 'token_budget': 'over_budget',
                'selected_observations': 'no_selected_observations', 'citation_policy': 'citation_policy_failed',
                'answer_support': 'no_calculations', 'roster_identities': 'roster_identity_mismatch',
                'roster_answer': 'roster_answer_mismatch', 'derivation_binding': 'unbound_derivation'}
# Fields the student trainer's candidate gate compares between an index entry and its row.json, as
# (row key, index key): student_pilot/finetune_lane.py gate_candidates and provisional.py
# load_provisional_candidates. The emitted row must agree with its candidate on every one of them.
TRAINER_COMPARED_FIELDS = (('qid', 'qid'), ('scene', 'scene'), ('category', 'question_type'),
                           ('dataset', 'dataset'), ('generation_commit', 'generation_commit'),
                           ('validation_commit', 'validation_commit'))
# The compact render owns these; the reviewed row's values move to source_<row key>.
ROW_ALIGNED_FIELDS = TRAINER_COMPARED_FIELDS + (('config_sha256', 'config_sha256'),)
OPERANDS = re.compile(r'\bOperands: (?P<ids>[A-Z]\d+(?:, [A-Z]\d+)*)\.')
OPERANDS_SPACED = re.compile(r'(?P<gap> ?)\bOperands: (?P<ids>[A-Z]\d+(?:, [A-Z]\d+)*)\.')
USES = re.compile(r'Uses observations (?P<indices>[1-9]\d*(?:, [1-9]\d*)*)\.')
NUMBER = re.compile(r'(?<!\w)[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?(?!\w)')
CITATION = re.compile(r'E([1-9]\d*)\.L([1-9]\d*)(?:-L([1-9]\d*))?')
ANSWER = re.compile(r'(?:[A-Za-z]|[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?)')


class Deferral(ValueError):
    def __init__(self, reason, detail=''):
        self.reason = reason
        self.detail = detail
        super().__init__(reason + (': ' + detail if detail else ''))


@dataclass
class Selection:
    observations: list
    derivations: list
    omitted: list
    operands: dict


@dataclass
class Context:
    """What the question asks: its type and its text, which names the counted category."""
    question_type: str
    question: str


@dataclass
class RenderedTarget:
    target: str
    lines: list
    omitted_lines: list


@dataclass
class Source:
    entry: dict
    row: dict
    lines: list
    records: dict
    checks: dict
    evidence: dict
    pins: dict


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest_json(value):
    return sha256_bytes(canonical_bytes(value))


def safe_path(path):
    path = Path(path)
    if any(word in str(path).lower() for word in ('offline_labels', 'answer_bank')):
        raise Deferral('protected_path', str(path))
    resolved = path.resolve()
    if any(word in str(resolved).lower() for word in ('offline_labels', 'answer_bank')):
        raise Deferral('protected_path', str(path))
    return resolved


def safe_qid(qid):
    if not isinstance(qid, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', qid):
        raise Deferral('qid_schema', repr(qid))
    return qid


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise Deferral('duplicate_json_key', key)
        value[key] = item
    return value


def invalid_constant(value):
    raise Deferral('nonfinite_json', value)


def decode_json(payload):
    return json.loads(payload, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def load_json(path):
    return decode_json(safe_path(path).read_bytes())


def load_jsonl(path):
    with safe_path(path).open(encoding='utf-8') as stream:
        return [decode_json(line) for line in stream if line.strip()]


def binding(path, payload=None):
    path = safe_path(path)
    return {'path': str(path), 'sha256': sha256_bytes(path.read_bytes() if payload is None else payload)}


def save(path, value):
    path = safe_path(path)
    if not path.is_relative_to(Path('/data2')):
        raise Deferral('output_outside_data2', str(path))
    payload = value if isinstance(value, bytes) else canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise Deferral('immutable_output_exists', str(path))
    else:
        with path.open('xb') as stream:
            stream.write(payload)
    return binding(path, payload)


def operand_clauses(text):
    matches = list(OPERANDS.finditer(text))
    if text.count('Operands:') != len(matches):
        raise Deferral('malformed_operands', text)
    return matches


def select_lines(lines, records):
    if not isinstance(lines, list):
        raise Deferral('source_line_schema', 'Expected an array')
    indexed = {}
    for line in lines:
        if not isinstance(line, dict):
            raise Deferral('source_line_schema', 'Expected a line object')
        identifier, text = line.get('id'), line.get('student_text')
        if (not isinstance(identifier, str) or not re.fullmatch(r'[A-Z]\d+', identifier)
                or line.get('kind') not in ('appearance', 'measurement', 'qualification', 'calculation', 'convention')
                or not isinstance(text, str) or not text or len(text.splitlines()) != 1 or '\r' in text or '\n' in text):
            raise Deferral('source_line_schema', str(identifier))
        if identifier in indexed:
            raise Deferral('duplicate_line_id', identifier)
        indexed[identifier] = line
    calculations = [line for line in lines if line['kind'] == 'calculation']
    record_map = indexed_records(records)
    operands = {}
    for line in calculations:
        raw = [identifier for clause in operand_clauses(line['student_text']) for identifier in clause['ids'].split(', ')]
        for identifier in raw:
            if identifier not in indexed:
                raise Deferral('unresolved_operand', identifier)
            if indexed[identifier]['kind'] not in ('appearance', 'measurement', 'qualification'):
                raise Deferral('invalid_operand_kind', identifier)
        operation = (record_map.get(line.get('record_id')) or {}).get('operation')
        if raw and operation not in OPERAND_QUANTITIES:
            raise Deferral('unknown_operation', f"{line['id']}: {operation!r}")
        admissible = OPERAND_QUANTITIES.get(operation, ())
        quantities = {identifier: (record_map.get(identifier) or {}).get('quantity') for identifier in raw}
        operands[line['id']] = {'operation': operation, 'raw': raw, 'quantities': quantities,
                                'kept': [identifier for identifier in raw if quantities[identifier] in admissible],
                                'dropped': [identifier for identifier in raw if quantities[identifier] not in admissible]}
    referenced = {identifier for entry in operands.values() for identifier in entry['kept']}
    observations = [line for line in lines if line['kind'] == 'appearance' or line['id'] in referenced]
    emitted = {line['id'] for line in observations + calculations}
    return Selection(observations, calculations, [line for line in lines if line['id'] not in emitted], operands)


def expanded_citations(citations):
    expanded = []
    if not isinstance(citations, list) or not citations:
        raise Deferral('citation_schema', 'Expected nonempty citations')
    for citation in citations:
        match = CITATION.fullmatch(citation) if isinstance(citation, str) else None
        if not match:
            raise Deferral('citation_schema', repr(citation))
        entry, first = int(match[1]), int(match[2])
        last = int(match[3] or first)
        if last < first or last - first > 100000:
            raise Deferral('citation_schema', citation)
        expanded.extend((entry, number) for number in range(first, last + 1))
    return expanded


def citation_suffix(citations):
    groups = []
    for entry, number in sorted(set(expanded_citations(citations))):
        if groups and groups[-1][0] == entry and groups[-1][2] + 1 == number:
            groups[-1][2] = number
        else:
            groups.append([entry, number, number])
    ranges = [f'E{entry}.L{first}' + (f'-L{last}' if first != last else '') for entry, first, last in groups]
    return ' [' + ', '.join(ranges) + ']'


def derivation_text(text, indices, kept):
    """Name the observation indices of the operands whose quantity enters the operation. A clause whose
    operands all lack a quantity leaves the visible text; the sidecar keeps the raw operand list."""
    operand_clauses(text)

    def replace(match):
        references = [key for key in match['ids'].split(', ') if key in kept]
        if not references:
            return ''
        return match['gap'] + 'Uses observations ' + ', '.join(str(indices[key]) for key in references) + '.'

    return OPERANDS_SPACED.sub(replace, text)


def line_record(line, index, operands=None):
    record = {'index': index, **{key: copy.deepcopy(line.get(key)) for key in ('id', 'record_id', 'record_sha256', 'citations', 'kind')}}
    if operands is not None:
        record['operands'] = {'operation': operands['operation'], 'source': list(operands['raw']),
                              'used': list(operands['kept']), 'dropped': list(operands['dropped']),
                              'dropped_quantities': {key: operands['quantities'][key] for key in operands['dropped']}}
    return record


def queried_identities(records, context):
    """The typed identity records of the category the question counts, in source record order."""
    identities = records.get('identities') if isinstance(records, dict) else None
    if not isinstance(identities, list) or not identities:
        raise Deferral('roster_category_unresolved', 'No typed identity record')
    for identity in identities:
        if (not isinstance(identity, dict) or not isinstance(identity.get('id'), str)
                or not isinstance(identity.get('name'), str) or not isinstance(identity.get('label'), str)):
            raise Deferral('roster_identity_schema', 'Identity record schema')
    if not isinstance(context.question, str) or not context.question:
        raise Deferral('roster_category_unresolved', 'No question text')
    labels = sorted({identity['label'] for identity in identities
                     if identity['label'] and identity['label'] + '(s)' in context.question})
    if len(labels) != 1:
        raise Deferral('roster_category_unresolved', repr(labels))
    return [identity for identity in identities if identity['label'] == labels[0]]


def roster_entry(records, context, selected, index):
    """One roster line naming the distinct instances of the counted category, for a counting question
    whose source trace has no Calculations section and whose answer is that number of identities."""
    if selected.derivations or context.question_type not in ROSTER_TYPES:
        return None
    identities = queried_identities(records, context)
    names = [identity['name'] for identity in identities]
    if len(set(names)) != len(names) or not all(ROSTER_NAME.fullmatch(name) for name in names):
        raise Deferral('roster_name_schema', repr(names))
    record = {'index': index, 'id': ROSTER_ID, 'record_id': None, 'record_sha256': None,
              'citations': sorted({citation for identity in identities for citation in (identity.get('citations') or [])}),
              'kind': ROSTER_KIND,
              'identities': [{'identity_id': identity['id'], 'name': identity['name'], 'label': identity['label'],
                              'record_sha256': digest_json(identity),
                              'citations': copy.deepcopy(identity.get('citations'))} for identity in identities]}
    return {'text': ROSTER_TEMPLATE.format(names=', '.join(names)), 'names': names, 'line': record}


def render_target(source_lines, answer, records, context, derivation_citations=False):
    if not isinstance(answer, str) or not ANSWER.fullmatch(answer):
        raise Deferral('answer_schema', repr(answer))
    selected = select_lines(source_lines, records)
    indices = {line['id']: index for index, line in enumerate(selected.observations, 1)}
    roster = roster_entry(records, context, selected, len(selected.observations) + 1)
    count = len(selected.observations) + (1 if roster else 0)
    text, sidecar = [f'Observations ({count})'], []
    for index, line in enumerate(selected.observations, 1):
        text.append(f'{index}. ' + line['student_text'])
        sidecar.append(line_record(line, index))
    if roster:
        text.append(f"{roster['line']['index']}. " + roster['text'])
        sidecar.append(roster['line'])
    if selected.derivations:
        text.append(f'Derivations ({len(selected.derivations)})')
        for index, line in enumerate(selected.derivations, 1):
            rendered = derivation_text(line['student_text'], indices, selected.operands[line['id']]['kept'])
            if derivation_citations:
                rendered += citation_suffix(line['citations'])
            text.append(f'{index}. ' + rendered)
            sidecar.append(line_record(line, index, selected.operands[line['id']]))
    return RenderedTarget('\n'.join(text + [MARKER, answer]), sidecar, copy.deepcopy(selected.omitted))


def numeric_tokens(text):
    return Counter(NUMBER.findall(text))


def indexed_records(bundle):
    if not isinstance(bundle, dict):
        raise Deferral('records_schema', 'Expected a typed record bundle')
    indexed = {}
    for group in RECORD_GROUPS:
        records = bundle.get(group, [])
        if not isinstance(records, list):
            raise Deferral('records_schema', group)
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get('id'), str):
                raise Deferral('records_schema', group)
            indexed[record['id']] = record
    return indexed


def admit(rendered, source_lines, records, source_checks, evidence_index, answer, count_tokens, context,
          max_tokens=MAX_TOKENS, derivation_citations=False, unbound_policy=UNBOUND_POLICIES[0]):
    selected = select_lines(source_lines, records)
    expected = render_target(source_lines, answer, records, context, derivation_citations)
    observations, calculations = selected.observations, selected.derivations
    roster = roster_entry(records, context, selected, len(observations) + 1)
    n, m = len(observations) + (1 if roster else 0), len(calculations)
    lines = rendered.target.split('\n')
    positions = list(range(1, n + 1)) + (list(range(n + 2, n + m + 2)) if m else [])
    source = observations + calculations
    bodies, numbering = [], []
    for position in positions:
        match = re.fullmatch(r'([1-9]\d*)\. (.*)', lines[position]) if position < len(lines) else None
        numbering.append(int(match[1]) if match else None)
        bodies.append(match[2] if match else '')
    indices = {line['id']: index for index, line in enumerate(observations, 1)}
    expected_bodies = [line['student_text'] for line in observations]
    if roster:
        expected_bodies.append(roster['text'])
    expected_bodies += [derivation_text(line['student_text'], indices, selected.operands[line['id']]['kept'])
                        for line in calculations]
    citations_ok, factual_bodies, byte_checks, references_ok = True, [], [], True
    for offset, (expected_body, body) in enumerate(zip(expected_bodies, bodies)):
        is_calculation = offset >= n
        line = calculations[offset - n] if is_calculation else None
        if is_calculation and derivation_citations:
            suffix = citation_suffix(line['citations'])
            citations_ok &= body.endswith(suffix)
            body = body[:-len(suffix)] if body.endswith(suffix) else body
        citations_ok &= '[E' not in body
        byte_checks.append(body.encode('utf-8') == expected_body.encode('utf-8'))
        if is_calculation:
            kept = selected.operands[line['id']]['kept']
            matches = list(USES.finditer(body))
            actual_refs = [[int(value) for value in match['indices'].split(', ')] for match in matches]
            expected_refs = [reference for reference in
                             ([indices[key] for key in clause['ids'].split(', ') if key in kept]
                              for clause in operand_clauses(line['student_text'])) if reference]
            references_ok &= (body.count('Uses observations') == len(matches) and actual_refs == expected_refs
                              and all(1 <= index <= n for values in actual_refs for index in values))
            body = USES.sub('', body)
        factual_bodies.append(body)
    actual_numbers = numeric_tokens('\n'.join(factual_bodies))
    source_numbers = numeric_tokens('\n'.join(OPERANDS.sub('', line['student_text']) if line['kind'] == 'calculation'
                                               else line['student_text'] for line in source))
    record_map = indexed_records(records)
    binding_ok = rendered.lines == expected.lines
    own_binding, qualification_scope, operand_binding = True, True, True
    for line in source:
        record = record_map.get(line.get('record_id'))
        bound = (record is not None and line.get('id') == line.get('record_id')
                 and line.get('record_sha256') == digest_json(record) and record.get('kind') == line['kind']
                 and line.get('citations') == record.get('citations') and bool(line.get('citations')))
        binding_ok &= bound
        own_binding &= line.get('own_record_binding') is True
        if record is None:
            continue
        if line['kind'] == 'calculation':
            references = [key for clause in operand_clauses(line['student_text']) for key in clause['ids'].split(', ')]
            operand_binding &= references == record.get('operand_record_ids', [])
        if line['kind'] == 'qualification':
            original = next((item for item in records.get('qualifications', []) if item.get('id') == record.get('source_qualification_id')), None)
            qualification_scope &= (original is not None and record.get('scope') == original.get('scope')
                                    and record.get('source_text') == original.get('source_text')
                                    and record.get('source_scope_sha256') == digest_json(original.get('scope'))
                                    and record.get('student_text') == line['student_text'])
    evidence = {line['id']: line for line in evidence_index.get('lines', [])}
    citations_bound = True
    for line in source:
        try:
            cited = [f'E{entry}.L{number}' for entry, number in expanded_citations(line.get('citations'))]
        except Deferral:
            citations_bound = False
            continue
        citations_bound &= all(identifier in evidence and evidence[identifier].get('kind') != 'native_final' for identifier in cited)
    recorded_tier = source_checks.get('tier_i', {})
    tier = {key: recorded_tier.get('checks', {}).get(key, 'not_evaluated') for key in TIER_I_CHECKS}
    recomputed = {'own_record_binding': bool(binding_ok and own_binding and operand_binding),
                  'qualification_scope': bool(qualification_scope), 'native_final_not_cited': bool(citations_bound),
                  'answer_equality': source_checks.get('answer') == answer}
    for key, satisfied in recomputed.items():
        if not satisfied:
            tier[key] = 'defect'
    source_pass = (recorded_tier.get('all_deterministic_checks_satisfied') is True and recorded_tier.get('findings') == []
                   and all(value == 'satisfied' for value in tier.values()) and source_checks.get('outcome') == 'target'
                   and source_checks.get('schema_failed') is False)
    roster_bound, roster_counts = True, True
    if roster:
        identified = {line['identity_name'] for line in source_lines if isinstance(line.get('identity_name'), str)}
        by_identity = {item.get('id'): item for item in (records.get('identities') or []) if isinstance(item, dict)}
        queried = queried_identities(records, context)
        roster_bound = (roster['names'] == [identity['name'] for identity in queried]
                        and set(roster['names']) == {identity['name'] for identity in queried}
                        and set(roster['names']) <= identified
                        and all(item['name'] == (by_identity.get(item['identity_id']) or {}).get('name')
                                and item['record_sha256'] == digest_json(by_identity.get(item['identity_id']))
                                for item in roster['line']['identities']))
        roster_counts = not re.fullmatch(r'\d+', answer) or int(answer) == len(roster['names'])
    unbound = [line['id'] for line in calculations
               if selected.operands[line['id']]['raw'] and not selected.operands[line['id']]['kept']]
    wanted_numbering = list(range(1, n + 1)) + list(range(1, m + 1))
    layout_ok = (len(lines) == n + m + (4 if m else 3) and lines[0] == f'Observations ({n})'
                 and (not m or len(lines) > n + 1 and lines[n + 1] == f'Derivations ({m})')
                 and numbering == wanted_numbering and [line.get('index') for line in rendered.lines] == wanted_numbering)
    terminal_ok = (len(lines) >= 2 and rendered.target.count(MARKER) == 1 and lines[-2:] == [MARKER, answer]
                   and not rendered.target.endswith('\n'))
    tokens = count_tokens(rendered.target)
    if type(tokens) is not int or tokens < 0:
        raise Deferral('tokenizer_result_invalid', repr(tokens))
    checks = {'byte_fidelity': all(byte_checks), 'numeric_tokens': not (actual_numbers - source_numbers),
              'record_binding': bool(binding_ok), 'counted_layout': bool(layout_ok),
              'observation_references': bool(references_ok), 'terminal_answer': bool(terminal_ok),
              'source_tier_i': bool(source_pass), 'token_budget': tokens <= max_tokens,
              'selected_observations': n > 0, 'citation_policy': bool(citations_ok),
              'answer_support': bool(calculations) or roster is not None or context.question_type in CALCULATION_FREE_TYPES,
              'roster_identities': bool(roster_bound), 'roster_answer': bool(roster_counts),
              'derivation_binding': not unbound or unbound_policy == 'drop_clause'}
    failed = [REASON_CODES[key] for key, passed in checks.items() if not passed]
    return {'schema': 'compact-counted-checks-v1', 'passed': not failed, 'checks': checks, 'reason_codes': failed,
            'token_count': tokens, 'observation_count': n, 'derivation_count': m,
            'numeric_excess': dict(actual_numbers - source_numbers), 'source_tier_i': copy.deepcopy(recorded_tier),
            'roster': copy.deepcopy(roster['line']) if roster else None, 'unbound_derivations': unbound,
            'operand_filter': {line['id']: {key: list(selected.operands[line['id']][key]) for key in ('raw', 'kept', 'dropped')}
                               for line in calculations},
            'tier_i': {'checks': tier, 'all_deterministic_checks_satisfied': not failed,
                       'findings': [{'reason': reason} for reason in failed]},
            'numeric_scope': 'Factual line text only; verified counts, enumeration, operand indices, citations and copied answer are structural.',
            'byte_fidelity_scope': 'Observation bytes are exact; derivation bytes are exact except prescribed operand substitution and citation suffix.',
            'independent_review': 'pending', 'admitted': False, 'training_eligible': False,
            'provider_calls': 0, 'gpu_used': False}


def checked_payload(path, expected):
    path = safe_path(path)
    payload = path.read_bytes()
    if not isinstance(expected, str) or not re.fullmatch(r'[a-f0-9]{64}', expected):
        raise Deferral('source_pin_missing', str(path))
    if sha256_bytes(payload) != expected:
        raise Deferral('source_hash_mismatch', str(path))
    return payload


def load_source(entry, recovery_root, reviewed_root):
    qid = safe_qid(entry.get('qid'))
    recovery_root, reviewed_root = safe_path(recovery_root), safe_path(reviewed_root)
    directory = safe_path(recovery_root / qid)
    if directory.parent != recovery_root:
        raise Deferral('source_path_escape', qid)
    row_path, target_path = (safe_path(reviewed_root / 'targets' / qid / name) for name in ('row.json', 'target.txt'))
    if (row_path != safe_path(entry['row_path']) or target_path != safe_path(entry['target_path'])
            or not row_path.is_relative_to(reviewed_root) or not target_path.is_relative_to(reviewed_root)):
        raise Deferral('source_path_escape', qid)
    row_bytes = checked_payload(row_path, entry.get('row_sha256'))
    target_bytes = checked_payload(target_path, entry.get('sha256'))
    row = decode_json(row_bytes)
    if row.get('target', '').encode('utf-8') != target_bytes:
        raise Deferral('source_target_row_mismatch', qid)
    answer = entry.get('answer')
    if not isinstance(answer, str) or row['target'].split('\n')[-1] != answer or row.get('answer', answer) != answer:
        raise Deferral('source_answer_mismatch', qid)
    for row_key, index_key in (('qid', 'qid'), ('category', 'question_type'), ('scene', 'scene'), ('dataset', 'dataset')):
        if row.get(row_key) != entry.get(index_key):
            raise Deferral('source_identity_mismatch', row_key)
    checks_bytes = safe_path(directory / 'checks.json').read_bytes()
    checks = decode_json(checks_bytes)
    pins = {'reviewed_row': binding(row_path, row_bytes), 'reviewed_target': binding(target_path, target_bytes),
            'checks': binding(directory / 'checks.json', checks_bytes)}
    loaded = {}
    for name in ('rendered_lines', 'records', 'evidence_index'):
        path = safe_path(directory / (name + '.json'))
        if path.parent != directory:
            raise Deferral('source_path_escape', str(path))
        payload = checked_payload(path, checks.get('artifacts', {}).get(name, {}).get('sha256'))
        loaded[name] = decode_json(payload)
        pins[name] = binding(path, payload)
    if checks.get('qid') != qid or checks.get('answer') != answer:
        raise Deferral('source_identity_mismatch', 'recovery checks identity/answer')
    return Source(entry, row, loaded['rendered_lines'], loaded['records'], checks, loaded['evidence_index'], pins)


def renderer_config(tokenizer, derivation_citations=False, unbound_policy=UNBOUND_POLICIES[0]):
    if unbound_policy not in UNBOUND_POLICIES:
        raise Deferral('unknown_unbound_policy', repr(unbound_policy))
    return {'format': FORMAT, 'version': 2, 'max_tokens': MAX_TOKENS, 'seed': SEED,
            'selection': 'appearance union the quantity-bearing operands of the calculations; source file order',
            'operand_quantities': {operation: list(kinds) for operation, kinds in sorted(OPERAND_QUANTITIES.items())},
            'unbound_policy': unbound_policy,
            'unbound_derivation': 'A derivation whose operands all lack a quantity loses its Uses clause and keeps '
                                  'its target; under policy defer the qid is deferred as unbound_derivation instead',
            'roster': ROSTER_TEMPLATE + ' Emitted after the appearance lines for a ' + ', '.join(ROSTER_TYPES) +
                      ' question whose source trace has no Calculations section, naming the typed identity '
                      'records of the counted category in source order',
            'calculation_free_types': list(CALCULATION_FREE_TYPES),
            'observations_header': 'Observations (N)', 'derivations_header': 'Derivations (M)',
            'operand_replacement': 'Uses observations i, j.', 'closing_marker': MARKER,
            'answer': 'Exact reviewed answer alone; no trailing newline',
            'derivation_citations': derivation_citations, 'tokenizer': str(tokenizer), 'add_special_tokens': False,
            'record_hash': 'sha256 of UTF-8 sorted indented JSON, ensure_ascii=False, trailing newline',
            'numeric_scope': 'Factual line text excluding validated structural tokens and copied answer',
            'row_metadata': 'Preserve every source row field except target and the candidate-aligned '
                            'provenance fields, whose reviewed values move to source_<field>',
            'row_provenance_alignment': [row_key for row_key, _ in ROW_ALIGNED_FIELDS],
            'independent_review_required': True}


def tokenizer_counter(path):
    from transformers import AutoTokenizer

    path = safe_path(path)
    tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True, trust_remote_code=False)
    pins = {name: binding(path / name) for name in ('tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'vocab.json', 'merges.txt')
            if (path / name).is_file()}
    return lambda text: len(tokenizer.encode(text, add_special_tokens=False)), pins


def distribution(values):
    values = sorted(values)
    result = {'n': len(values)}
    for name, fraction in (('min', 0), ('p10', .1), ('median', .5), ('p90', .9), ('p99', .99), ('max', 1)):
        if not values:
            result[name] = None
        else:
            position = fraction * (len(values) - 1)
            lower, upper = math.floor(position), math.ceil(position)
            result[name] = values[lower] + (values[upper] - values[lower]) * (position - lower)
    return result


def pilot_sample(rows, size=16, seed=SEED):
    groups = defaultdict(list)
    for row in sorted(rows, key=lambda row: row['qid']):
        groups[row['question_type']].append(row)
    generator = random.Random(seed)
    names = sorted(groups)
    generator.shuffle(names)
    for name in names:
        generator.shuffle(groups[name])
    result = []
    while len(result) < min(size, len(rows)):
        for name in names:
            if groups[name] and len(result) < size:
                result.append(groups[name].pop())
    return result


def pilot_qids(config, candidates):
    """The pilot qids: the pinned review list when the configuration carries one, else the seeded
    stratified sample of the candidates."""
    pinned = config.get('pilot_qids_pinned')
    if pinned:
        return list(pinned)
    return [row['qid'] for row in pilot_sample(candidates)]


def candidate_identity(source_entry, config, commit):
    """The identity and provenance the compact candidate carries, before its own path and hash pins."""
    return {**source_entry, 'postprocess': FORMAT, 'config_sha256': digest_json(config), 'generation_commit': commit}


def aligned_row(source_row, identity, target):
    """Copy the reviewed row, replace the target, and adopt the candidate's value for every field the
    trainer compares, keeping each overwritten reviewed value under source_<field>."""
    row = {**source_row, 'target': target}
    for row_key, index_key in ROW_ALIGNED_FIELDS:
        if index_key not in identity:
            raise Deferral('candidate_field_missing', index_key)
        if source_row.get(row_key) == identity[index_key]:
            continue
        source_key = 'source_' + row_key
        if source_key in source_row:
            raise Deferral('source_provenance_key_conflict', source_key)
        if row_key in source_row:
            row[source_key] = source_row[row_key]
        row[row_key] = identity[index_key]
    return row


def source_context(source):
    """The question a target answers, as the renderer reads it from the reviewed row."""
    student_input = source.row.get('student_input')
    question = student_input.get('question') if isinstance(student_input, dict) else None
    return Context(source.entry['question_type'], question if isinstance(question, str) else '')


def emit_source(source, output, config, commit, source_index_sha256, count_tokens):
    context = source_context(source)
    rendered = render_target(source.lines, source.entry['answer'], source.records, context, config['derivation_citations'])
    checks = admit(rendered, source.lines, source.records, source.checks, source.evidence, source.entry['answer'],
                   count_tokens, context, max_tokens=config['max_tokens'],
                   derivation_citations=config['derivation_citations'], unbound_policy=config['unbound_policy'])
    qid = source.entry['qid']
    directory = output / 'targets' / qid
    identity = candidate_identity(source.entry, config, commit)
    row = aligned_row(source.row, identity, rendered.target)
    target_pin = save(directory / 'target.txt', rendered.target.encode('utf-8'))
    row_pin = save(directory / 'row.json', row)
    lines_pin = save(directory / 'lines.json', rendered.lines)
    checks.update(qid=qid, question_type=source.entry['question_type'], generation_commit=commit,
                  config_sha256=digest_json(config), source_artifacts=source.pins,
                  omitted_lines=rendered.omitted_lines, row=row_pin, target=target_pin, lines=lines_pin)
    checks_pin = save(directory / 'checks.json', checks)
    entry = {**identity, 'target_path': target_pin['path'], 'sha256': target_pin['sha256'],
             'row_path': row_pin['path'], 'row_sha256': row_pin['sha256'],
             'source_index_sha256': source_index_sha256, 'tier_i': checks['tier_i']}
    disposition = {'qid': qid, 'question_type': source.entry['question_type'], 'passed': checks['passed'],
                   'reason_codes': checks['reason_codes'], 'token_count': checks['token_count'],
                   'observation_count': checks['observation_count'], 'derivation_count': checks['derivation_count'],
                   'roster': checks['roster'] is not None, 'unbound_derivations': list(checks['unbound_derivations']),
                   'artifacts': {'target': target_pin, 'row': row_pin, 'lines': lines_pin, 'checks': checks_pin}}
    return entry, disposition


def heartbeat(output, step, progress):
    output = safe_path(output)
    if not output.is_relative_to(Path('/data2')):
        raise Deferral('output_outside_data2', str(output))
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with (output / 'HEARTBEAT.log').open('a', encoding='utf-8') as stream:
        stream.write(f'{stamp} | {step}\n')
    (output / 'PROGRESS.md').write_text('# Compact counted target lane\n' + progress + '\n', encoding='utf-8')


def stats_text(membership, dispositions):
    rendered = [row for row in dispositions if 'token_count' in row]
    candidates = [row for row in rendered if row['passed']]
    deferred = [row for row in dispositions if not row['passed']]
    primary = Counter(row['reason_codes'][0] for row in deferred)
    reasons = Counter(reason for row in deferred for reason in row['reason_codes'])
    lines = ['# Compact counted target statistics', '',
             f"Recovery qids: {membership['recovery_count']}; reviewed rows: {membership['reviewed_count']}; intersection denominator: {membership['intersection_count']}.",
             f'Written renderings: {len(rendered)}; eligible candidates: {len(candidates)}; deferred: {len(deferred)}.',
             'All candidates remain provisional until independent review. Quantiles use linear interpolation at (n - 1) p.', '',
             '## Token counts', '', '| population | question_type | n | min | p10 | median | p90 | p99 | max |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for population, rows in (('all rendered', rendered), ('eligible candidates', candidates)):
        for kind in [None] + sorted({row['question_type'] for row in dispositions}):
            selected = [row for row in rows if kind is None or row['question_type'] == kind]
            values = distribution([row['token_count'] for row in selected])
            display = [str(values['n'])] + [f"{values[key]:.2f}" if values[key] is not None else 'NA'
                                         for key in ('min', 'p10', 'median', 'p90', 'p99', 'max')]
            lines.append('| ' + ' | '.join([population, kind or 'overall'] + display) + ' |')
    lines += ['', '## Observation and derivation counts', '',
              '| population | question_type | kind | total | min | p10 | median | p90 | p99 | max |',
              '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for population, rows in (('all rendered', rendered), ('eligible candidates', candidates)):
        for kind in [None] + sorted({row['question_type'] for row in dispositions}):
            selected = [row for row in rows if kind is None or row['question_type'] == kind]
            for field in ('observation_count', 'derivation_count'):
                counts = [row[field] for row in selected]
                values = distribution(counts)
                display = [str(sum(counts))] + [f"{values[key]:.2f}" if values[key] is not None else 'NA'
                                              for key in ('min', 'p10', 'median', 'p90', 'p99', 'max')]
                lines.append('| ' + ' | '.join([population, kind or 'overall', field] + display) + ' |')
    lines += ['', '## Deferrals', '', '| reason | primary qids | all affected qids |', '|---|---:|---:|']
    for reason in sorted(reasons):
        lines.append(f'| {reason} | {primary[reason]} | {reasons[reason]} |')
    if not reasons:
        lines.append('| none | 0 | 0 |')
    kinds = sorted({row['question_type'] for row in dispositions})
    by_kind = Counter((row['reason_codes'][0], row['question_type']) for row in deferred if row['reason_codes'])
    lines += ['', '## Primary deferral reason by question type', '',
              '| reason | ' + ' | '.join(kinds) + ' | total |', '|---' + '|---:' * (len(kinds) + 1) + '|']
    for reason in sorted(reasons):
        counts = [by_kind[(reason, kind)] for kind in kinds]
        lines.append('| ' + ' | '.join([reason] + [str(count) for count in counts] + [str(sum(counts))]) + ' |')
    if not reasons:
        lines.append('| none | ' + ' | '.join(['0'] * (len(kinds) + 1)) + ' |')
    rosters = [row for row in rendered if row.get('roster')]
    lines += ['', '## Identity rosters and operand filtering', '',
              f'Targets carrying an identity roster: {len(rosters)} rendered, {sum(1 for row in rosters if row["passed"])} eligible.',
              f'Rendered targets with a derivation whose operands all lack a quantity: {sum(1 for row in rendered if row.get("unbound_derivations"))}.',
              'A roster line names the typed identity records of the counted category; its names and count are '
              'checked against those records and against the answer.',
              'An operand whose quantity cannot enter its operation leaves the visible Uses clause and stays in the '
              'sidecar operand list of that derivation.']
    lines += ['', 'Each deferred qid remains in MEMBERSHIP.json and DEFERRED.jsonl; multiple reasons do not multiply the denominator.',
              'The numeric check compares factual text only. Count headers, list indices, remapped references, citations, and the copied answer have separate checks.',
              'Observation text is byte-exact; derivation text changes only the prescribed operand clause. Omitted source lines remain in each checks.json sidecar.',
              'Recorded source Tier I passes are inherited, not independent semantic-review verdicts. Citation placement and calculation operand attribution remain review questions.']
    return '\n'.join(lines) + '\n'


def review_prompt(output, commit):
    return f'''# Independent review of compact_counted_v1

Review the implementation at commit {commit} and the 16 seed-17, question-type-stratified items in {output / 'PILOT_SAMPLE_16.json'}.
The current sandbox is ratified as sufficient; sandbox/isolation objections are out of scope. This is a CPU-only, zero-provider deterministic conversion, not training admission or a benchmark score.

For each item, read both target variants and their row.json, lines.json, and checks.json. Follow only the source_artifacts pins to the supplied rendered_lines.json, records.json, checks.json, and evidence_index.json. Never open a path containing offline_labels or answer_bank. Do not edit a source or trainer checkout.

1. Recompute each selected typed record hash. Match every emitted observation byte-for-byte to student_text and each derivation except its prescribed Operands-to-Uses substitution. Check units, signs, precision, identities, frame scopes, and qualifications against the typed records.
2. Reconstruct S as all appearance lines union the operand ids the filter keeps, in file order. Verify N and M, both contiguous local index sequences, each Uses observations reference, and the complete absence of convention or unreferenced qualification prose. Omitted lines remain in checks.json, not visible text.
3. Require exactly one End of reasoning. immediately before the bare, byte-exact reviewed answer. Require no trailing newline or extra content.
4. Check that numeric tokens in factual text are a multiset subset of selected source text. Validated count headers, enumeration, remapped indices, citations, and the copied answer are structural rather than invented measurements.
5. Decide whether own_record_binding, qualification_scope, and native_final_not_cited permit sidecar-only citations. If not, state whether derivation-only inline citations suffice. Check evidence kinds even when citations are hidden. The inline variant is review-only if its checks report over_budget.
6. Independently check that each calculation actually uses its named operands. A source deterministic Tier I pass does not resolve the operand-over-attribution mechanism documented in the source strip_calculations_v1.py. The converter does not repair source semantics or claim that hiding citations fixes them.
7. On a counting target whose source trace has no Calculations section, check the roster line: its names must be exactly the names of the typed identity records of the category the question counts, in record order, each bound in lines.json to that record's sha256, each also named by a source measurement line, and the number of names must equal the answer. Report any invented or omitted instance.
8. Check the operand filter on every derivation: lines.json records the source operand list, the operands the visible Uses clause keeps, and the operands it drops with their quantity kinds. An operand may be kept only if its quantity can enter the operation (CONFIG.json operand_quantities). Rule on whether the kept set is the set the calculation actually consumes, and whether dropping the rest removes the over-attribution rather than hiding evidence.
9. A derivation may legitimately carry no Uses observations clause. Under CONFIG.json unbound_policy drop_clause, a derivation whose operands are all quantity-free visibility records keeps its sentence and loses the clause rather than pointing at lines that carry no number; the dropped operands stay in lines.json. Under policy defer the qid is deferred as unbound_derivation instead. Judge whether the remaining sentence still states what it compares and what it yields, and report any derivation whose meaning depends on the operands the clause no longer names.
10. Verify that student_input and every row field other than target are unchanged. The index records the compact generation commit while the row retains its source generation commit, as the brief requires. Inspect the unchanged trainer compatibility receipt; do not waive or change its provenance guard.

Return PASS, REVISE, or REJECT with qid, variant, exact source/target evidence, violated acceptance condition, and impact for each material finding. State a separate explicit ruling on sidecar-only versus derivation-inline citations. No output is training-eligible before the orchestrator adjudicates this independent review.
'''


def build_dataset(index_path, recovery_root, output, config, commit, count_tokens, lane_output=None, qids=None,
                  make_pilot=True, variant_name=VARIANT_DIRECTORY):
    index_path, recovery_root, output = map(safe_path, (index_path, recovery_root, output))
    if not output.is_relative_to(Path('/data2')):
        raise Deferral('output_outside_data2', str(output))
    if output.exists():
        raise Deferral('immutable_output_exists', str(output))
    index_payload = index_path.read_bytes()
    entries = [decode_json(line) for line in index_payload.splitlines() if line.strip()]
    source_pin = binding(index_path, index_payload)
    ids = [safe_qid(row.get('qid')) for row in entries]
    if len(ids) != len(set(ids)):
        raise Deferral('duplicate_candidate_qid')
    recovery_ids = {child.name for child in recovery_root.iterdir() if child.is_dir() and re.fullmatch(r'vsi590k_\d+', child.name)}
    reviewed_ids = set(ids)
    intersection = recovery_ids & reviewed_ids
    if qids is not None:
        if not set(qids) <= intersection:
            raise Deferral('pilot_qid_not_in_intersection')
        intersection &= set(qids)
    membership = {'recovery_count': len(recovery_ids), 'reviewed_count': len(entries), 'intersection_count': len(intersection),
                  'qids': sorted(intersection), 'recovery_not_reviewed': sorted(recovery_ids - reviewed_ids),
                  'reviewed_not_recovery': sorted(reviewed_ids - recovery_ids)}
    output.mkdir(parents=True)
    config_pin = save(output / 'CONFIG.json', config)
    membership_pin = save(output / 'MEMBERSHIP.json', membership)
    dispositions, candidates = [], []
    last_heartbeat = 0
    with (output / 'candidate_index.jsonl').open('x', encoding='utf-8') as index_stream, (output / 'DEFERRED.jsonl').open('x', encoding='utf-8') as deferred_stream:
        for entry in entries:
            if entry['qid'] not in intersection:
                continue
            try:
                source = load_source(entry, recovery_root, index_path.parent)
                candidate, disposition = emit_source(source, output, config, commit, source_pin['sha256'], count_tokens)
            except (Deferral, OSError, ValueError, KeyError, TypeError) as error:
                disposition = {'qid': entry['qid'], 'question_type': entry['question_type'], 'passed': False,
                               'reason_codes': [error.reason if isinstance(error, Deferral) else 'source_load_error'],
                               'detail': str(error)}
            dispositions.append(disposition)
            if disposition['passed']:
                candidates.append(candidate)
                index_stream.write(json.dumps(candidate, sort_keys=True, ensure_ascii=False) + '\n')
                index_stream.flush()
            else:
                deferred_stream.write(json.dumps(disposition, sort_keys=True, ensure_ascii=False) + '\n')
                deferred_stream.flush()
            if lane_output and time.monotonic() - last_heartbeat >= 240:
                heartbeat(lane_output, 'Rendering compact targets and recording every disposition',
                          f'Done: {len(dispositions)} of {len(intersection)} source dispositions; {len(candidates)} candidates.\n'
                          'Doing: Render remaining sources and validate their source bindings.\nNext: Write pilot variants and verify trainer compatibility.\n'
                          'Blockers: Independent citation/operand review and the row/index generation-commit mismatch.')
                last_heartbeat = time.monotonic()
            if len(dispositions) % 100 == 0:
                print(json.dumps({'processed': len(dispositions), 'denominator': len(intersection), 'candidates': len(candidates)}), flush=True)
    if binding(index_path) != source_pin:
        raise Deferral('source_index_changed_during_render')
    stats_pin = save(output / 'STATS.md', stats_text(membership, dispositions).encode('utf-8'))
    samples, variants, pilot_pins = [], [], {}
    if make_pilot:
        variant_output = output.parent / variant_name
        variant_config = {**config, 'derivation_citations': True}
        pilot_pins['config'] = save(variant_output / 'CONFIG.json', variant_config)
        known = {item['qid']: item for item in dispositions}
        for qid in pilot_qids(config, candidates):
            if qid not in known:
                raise Deferral('pilot_qid_not_in_intersection', qid)
            default = known[qid]
            try:
                original = next(entry for entry in entries if entry['qid'] == qid)
                source = load_source(original, recovery_root, index_path.parent)
                entry, disposition = emit_source(source, variant_output, variant_config, commit, source_pin['sha256'], count_tokens)
            except (Deferral, OSError, ValueError, KeyError, TypeError) as error:
                entry = None
                disposition = {'qid': qid, 'question_type': default['question_type'], 'passed': False,
                               'reason_codes': [error.reason if isinstance(error, Deferral) else 'source_load_error'],
                               'detail': str(error)}
            variants.append({'entry': entry, 'disposition': disposition})
            samples.append({'qid': qid, 'question_type': default['question_type'],
                            'default': default, 'derivation_citations': disposition})
        pilot_pins['candidate_index'] = save(variant_output / 'candidate_index.jsonl', ''.join(json.dumps(item['entry'], sort_keys=True) + '\n' for item in variants if item['disposition']['passed']).encode())
        pilot_pins['deferred'] = save(variant_output / 'DEFERRED.jsonl', ''.join(json.dumps(item['disposition'], sort_keys=True) + '\n' for item in variants if not item['disposition']['passed']).encode())
        pilot_pins['sample'] = save(output / 'PILOT_SAMPLE_16.json', {'seed': SEED, 'count': len(samples), 'selection': 'balanced round-robin across seeded shuffled question types', 'samples': samples})
        pilot_pins['review_prompt'] = save(output / 'REVIEW_PROMPT_compact.md', review_prompt(output, commit).encode('utf-8'))
    manifest = {'schema': 'compact-counted-dataset-v1', 'generation_commit': commit, 'config': config_pin,
                'source_index': source_pin, 'recovery_root': str(recovery_root), 'membership': membership_pin,
                'candidate_index': binding(output / 'candidate_index.jsonl'), 'deferred': binding(output / 'DEFERRED.jsonl'),
                'statistics': stats_pin, 'candidate_count': len(candidates), 'deferred_count': len(dispositions) - len(candidates),
                'pilot_qids': [item['qid'] for item in samples],
                'dispositions': dispositions, 'pilot_variants': variants, 'pilot_artifacts': pilot_pins, 'independent_review': 'pending',
                'training_eligible': False, 'provider_calls': 0, 'gpu_used': False}
    save(output / 'MANIFEST.json', manifest)
    return manifest


def verify_emission(entry, disposition, source_entry, config, manifest, count_tokens):
    pins = disposition['artifacts']
    for pin in pins.values():
        checked_payload(pin['path'], pin['sha256'])
    source = load_source(source_entry, manifest['recovery_root'], Path(manifest['source_index']['path']).parent)
    row = load_json(pins['row']['path'])
    target = checked_payload(pins['target']['path'], pins['target']['sha256']).decode('utf-8')
    identity = candidate_identity(source_entry, config, manifest['generation_commit'])
    if row != aligned_row(source.row, identity, target):
        raise Deferral('row_metadata_changed', source_entry['qid'])
    saved_checks = load_json(pins['checks']['path'])
    rendered = RenderedTarget(target, load_json(pins['lines']['path']), saved_checks['omitted_lines'])
    checks = admit(rendered, source.lines, source.records, source.checks, source.evidence, source_entry['answer'],
                   count_tokens, source_context(source), config['max_tokens'], config['derivation_citations'],
                   config['unbound_policy'])
    if (any(saved_checks[key] != checks[key] for key in checks)
            or any(disposition[key] != checks[key] for key in ('passed', 'reason_codes', 'token_count', 'observation_count', 'derivation_count'))
            or rendered.omitted_lines != select_lines(source.lines, source.records).omitted or saved_checks['source_artifacts'] != source.pins
            or saved_checks['generation_commit'] != manifest['generation_commit'] or saved_checks['config_sha256'] != digest_json(config)):
        raise Deferral('output_revalidation_failed', source_entry['qid'])
    if entry is not None:
        expected = {**identity, 'target_path': pins['target']['path'], 'sha256': pins['target']['sha256'],
                    'row_path': pins['row']['path'], 'row_sha256': pins['row']['sha256'],
                    'source_index_sha256': manifest['source_index']['sha256'], 'tier_i': checks['tier_i']}
        if entry != expected or set(entry) != set(source_entry):
            raise Deferral('candidate_index_changed', source_entry['qid'])


def verify_dataset(output, count_tokens):
    output = safe_path(output)
    manifest = load_json(output / 'MANIFEST.json')
    for pin in [manifest[key] for key in ('config', 'source_index', 'membership', 'candidate_index', 'deferred', 'statistics')] + list(manifest['pilot_artifacts'].values()):
        checked_payload(pin['path'], pin['sha256'])
    config = load_json(manifest['config']['path'])
    membership = load_json(manifest['membership']['path'])
    entries = load_jsonl(manifest['candidate_index']['path'])
    deferred = load_jsonl(manifest['deferred']['path'])
    qids = [row['qid'] for row in entries + deferred]
    disposition_ids = [row['qid'] for row in manifest['dispositions']]
    if (len(qids) != len(set(qids)) or set(qids) != set(membership['qids']) or len(qids) != membership['intersection_count']
            or len(disposition_ids) != len(set(disposition_ids)) or set(disposition_ids) != set(qids)):
        raise Deferral('denominator_reconciliation_failed')
    source_entries = {row['qid']: row for row in load_jsonl(manifest['source_index']['path'])}
    outputs = {row['qid']: row for row in entries}
    deferred_by_id = {row['qid']: row for row in deferred}
    for disposition in manifest['dispositions']:
        qid = disposition['qid']
        if disposition['passed'] != (qid in outputs) or (not disposition['passed'] and disposition != deferred_by_id[qid]):
            raise Deferral('disposition_mismatch', qid)
        if 'artifacts' in disposition:
            verify_emission(outputs.get(qid), disposition, source_entries[qid], config, manifest, count_tokens)
    if manifest['pilot_artifacts']:
        variant_config = load_json(manifest['pilot_artifacts']['config']['path'])
        if variant_config != {**config, 'derivation_citations': True}:
            raise Deferral('pilot_configuration_changed')
        sample = load_json(manifest['pilot_artifacts']['sample']['path'])
        expected_ids = pilot_qids(config, entries)
        if (sample['seed'] != SEED or sample['count'] != len(expected_ids) or manifest['pilot_qids'] != expected_ids
                or [item['qid'] for item in sample['samples']] != expected_ids
                or [item['disposition']['qid'] for item in manifest['pilot_variants']] != expected_ids):
            raise Deferral('pilot_selection_changed')
        for variant in manifest['pilot_variants']:
            if 'artifacts' not in variant['disposition']:
                continue
            verify_emission(variant['entry'], variant['disposition'], source_entries[variant['disposition']['qid']],
                            variant_config, manifest, count_tokens)
        expected_variants = [item['entry'] for item in manifest['pilot_variants'] if item['disposition']['passed']]
        expected_deferred = [item['disposition'] for item in manifest['pilot_variants'] if not item['disposition']['passed']]
        if (load_jsonl(manifest['pilot_artifacts']['candidate_index']['path']) != expected_variants
                or load_jsonl(manifest['pilot_artifacts']['deferred']['path']) != expected_deferred):
            raise Deferral('pilot_disposition_mismatch')
    if len(entries) != manifest['candidate_count'] or len(deferred) != manifest['deferred_count']:
        raise Deferral('manifest_count_mismatch')
    return {'status': 'VERIFIED', 'checked_at': datetime.now(timezone.utc).isoformat(),
            'denominator': len(qids), 'candidates': len(entries), 'deferred': len(deferred),
            'pilot_variants': len(manifest['pilot_variants']), 'manifest': binding(output / 'MANIFEST.json'),
            'source_rows_preserved': True, 'all_rendered_admission_checks_replayed': True,
            'provider_calls': 0, 'gpu_used': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Deterministic compact counted targets; CPU only, no providers.')
    parser.add_argument('command', choices=('render', 'verify'))
    parser.add_argument('--candidate-index', type=Path)
    parser.add_argument('--recovery-root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tokenizer', type=Path, default=TOKENIZER)
    parser.add_argument('--derivation-citations', action='store_true')
    parser.add_argument('--unbound-policy', choices=UNBOUND_POLICIES, default=UNBOUND_POLICIES[0],
                        help='Disposition of a derivation whose operands all lack a quantity')
    parser.add_argument('--pilot-qids', type=Path,
                        help='PILOT_SAMPLE_16.json of an earlier render, to review the same qids again')
    parser.add_argument('--pilot-sample', type=Path)
    parser.add_argument('--lane-output', type=Path)
    parser.add_argument('--sidecar-suffix', default='',
                        help='Suffix for the configuration, provenance and pilot-variant siblings of the output set')
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9_]*', args.sidecar_suffix):
        parser.error('--sidecar-suffix accepts only letters, digits and underscores')
    os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
                      TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1', TOKENIZERS_PARALLELISM='false')
    count_tokens, tokenizer_pins = tokenizer_counter(args.tokenizer)
    if args.command == 'verify':
        receipt = verify_dataset(args.output, count_tokens)
        save(args.output / 'VERIFICATION.json', receipt)
        print(json.dumps(receipt, sort_keys=True), flush=True)
        return 0
    if args.candidate_index is None or args.recovery_root is None:
        parser.error('render requires --candidate-index and --recovery-root')
    qids = None
    if args.derivation_citations:
        if args.pilot_sample is None:
            parser.error('--derivation-citations requires --pilot-sample and is restricted to its at-most-16 qids')
        qids = [item['qid'] for item in load_json(args.pilot_sample)['samples']]
        if not 1 <= len(qids) <= 16 or len(set(qids)) != len(qids):
            parser.error('The citation variant requires 1 to 16 unique pilot qids')
    config = renderer_config(safe_path(args.tokenizer), args.derivation_citations, args.unbound_policy)
    config.update(tokenizer_files=tokenizer_pins, source_index=binding(args.candidate_index), recovery_root=str(safe_path(args.recovery_root)))
    if args.pilot_qids is not None:
        pinned = load_json(args.pilot_qids)
        pinned = [item['qid'] for item in pinned['samples']] if isinstance(pinned, dict) else list(pinned)
        if not 1 <= len(pinned) <= 16 or len(set(pinned)) != len(pinned):
            parser.error('--pilot-qids requires 1 to 16 unique qids')
        config['pilot_qids_pinned'] = [safe_qid(qid) for qid in pinned]
    if qids is not None:
        config['pilot_qids'] = qids
    output = safe_path(args.output)
    stem = 'derivation_citations' if args.derivation_citations else 'compact'
    config_path = output.parent / f'CONFIG_{stem}{args.sidecar_suffix}.json'
    save(config_path, config)
    from tools.provenance import provenance

    pin = provenance(config_path)
    if pin['dirty']:
        raise Deferral('dirty_worktree', 'Commit the renderer and tests before rendering')
    if pin['config_sha256'] != digest_json(config):
        raise Deferral('configuration_hash_mismatch')
    save(output.parent / f'PROVENANCE_{stem}{args.sidecar_suffix}.json', pin)
    manifest = build_dataset(args.candidate_index, args.recovery_root, output, config, pin['repo_commit'], count_tokens,
                             args.lane_output, qids, make_pilot=not args.derivation_citations,
                             variant_name=VARIANT_DIRECTORY + args.sidecar_suffix)
    print(json.dumps({key: manifest[key] for key in ('generation_commit', 'candidate_count', 'deferred_count', 'candidate_index')}, sort_keys=True), flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Deferral, OSError, ValueError) as error:
        print(f'BLOCKED: {error}', file=sys.stderr)
        sys.exit(2)
