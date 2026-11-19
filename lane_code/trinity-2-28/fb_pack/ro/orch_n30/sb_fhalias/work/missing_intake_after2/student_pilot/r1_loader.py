"""Read sealed R1 rows with the native reader; report bounded examples and refusals."""
from collections import Counter
import json
from pathlib import Path
from .p3_provenance import digest, load, pinned, write
from .r1_training import row_check, STREAMS


def audit_rows(rows, stream, family, *, coverage=None):
    """A source slice proves syntax separately from independently covered admission."""
    from .r0_exclusion import reserve
    seen = Counter()
    examples = []
    for row in rows:
        seen['read'] += 1
        try:
            row_check(row, stream)
            reserve().check(row, stream)
        except (ValueError, KeyError, TypeError) as error:
            seen['refused:'+str(error)] += 1
            continue
        seen['text_eligible'] += 1
        if len(examples) < 5:
            examples.append(dict(qid=row.get('qid'), row_sha256=digest(row),
                                 target=row.get('target', row.get('suffix')), family=family))
        if coverage is None or row.get('qid') not in coverage:
            seen['unknown_scene_coverage'] += 1
            continue
        # This function accepts only results emitted by the existing full intake.
        if coverage[row['qid']] != digest(row):
            raise ValueError('R1_ADMITTED_ROW_IDENTITY_DIFFERS')
        seen['admitted'] += 1
    return dict(family=family, stream=stream, counts=dict(seen), examples=examples,
                complete=False, scope='bounded source text; full intake requires independent scene coverage')


def production_audit(cfg, output):
    import os
    if os.uname().nodename.startswith('trinity'):
        raise ValueError('R1_FULL_AUDIT_REQUIRES_FRAME_HOST')
    from .carrier_c1_run import Rows, prepared
    from .r1_mix import validate_binding, plans
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    receipt, _ = prepared(cfg)
    reader = Rows(receipt, None)
    binding = cfg.get('r2_sampling')
    if not binding:
        raise ValueError('R1_PRODUCTION_ROW_PLAN_MISSING')
    if cfg['r1_training'].get('row_plan_sha256') != digest(binding):
        raise ValueError('R1_PRODUCTION_ROW_PLAN_CHANGED')
    card, indices, allocation = validate_binding(binding)
    counts = {s:reader.count(s) for s in STREAMS}
    ownership = {(c['stream'], i):c['type'] for c in card['cells'] for i in indices['cells'][c['type']]}
    repeats = Counter(); draws = Counter(); examples = {}
    unique = set(); training_counts = {'recovery':0, 'units':{u:0 for u in ('cm','ft','in')}}
    unit_draws = Counter(); status_draws = Counter()
    try:
        for plan in plans(binding, counts, 1000):
            for stream, offsets in plan:
                for index in offsets:
                    row, _ = reader.row(stream, index)
                    row_check(row, stream)
                    kind = ownership[(stream, index)]
                    if card.get('counting_admission') == 'procedure_only_v1':
                        from .r1_counting import admit
                        admit(row, kind)
                    key = (stream, row['qid'])
                    unit, statuses = row_dimensions(row)
                    if unit:
                        unit_draws[unit] += 1
                    status_draws.update(statuses)
                    if key not in unique and stream == 'routing':
                        if kind == 'recovery':
                            training_counts['recovery'] += 1
                        if kind == 'units' and unit in training_counts['units']:
                            training_counts['units'][unit] += 1
                    unique.add(key)
                    repeats[(stream, row['qid'])] += 1
                    draws[kind] += 1
                    kept = examples.setdefault(kind, {})
                    if len(kept) < 5:
                        kept[row['qid']] = dict(qid=row['qid'], row_sha256=digest(row), target=row.get('target', row.get('suffix')))
        if max(repeats.values(), default=0) > 4:
            raise ValueError('R1_REPEAT_LIMIT_EXCEEDED')
        result = dict(complete=True, eligible=allocation['eligible'], draws=dict(draws),
                      sampling_shares={k:v/sum(draws.values()) for k,v in draws.items()},
                      routing_training_counts=training_counts,
                      asked_unit_draws=dict(unit_draws), printed_status_draws=dict(status_draws),
                      expected_repeats=allocation['repeats'], largest_repeat=max(repeats.values(), default=0),
                      examples={k:list(v.values()) for k,v in examples.items()},
                      card_sha256=binding['card']['sha256'], row_plan_sha256=digest(binding))
        write(output/'RESULT.json', result)
        return result
    finally:
        reader.close()


def row_dimensions(row):
    """Audit question units and printed tool status; never derive a target quantity."""
    import re
    from .r2_units import asked_unit
    unit = asked_unit(row)
    statuses = []
    for raw in re.findall(r'<tool_response>(.*?)</tool_response>', row.get('target', row.get('suffix','')), re.S):
        try:
            response = json.loads(raw)
        except (ValueError, TypeError):
            statuses.append('unparsed_printed_response')
            continue
        statuses.append(str(response.get('status', 'not_printed')) if isinstance(response,dict) else 'not_printed')
    return unit, statuses
