from pathlib import Path
L=Path(__file__).resolve().parents[1]
S=L/'work/src_r3'
def edit(rel,old,new):
    p=S/rel;s=p.read_text();assert old in s,(rel,old);p.write_text(s.replace(old,new))

p=S/'trace_format/contracts.py';s=p.read_text();a=s.index('    for line in text.splitlines():');b=s.index('\n\ndef status_text',a)
s=s[:a]+'''    first = text.splitlines()[0].strip()
    body = first.split(': ', 1)[1] if ': ' in first and not first.lower().startswith('error:') else first
    if body.lower().startswith('error:'):
        return 'error'
    if body == 'heading unavailable' and any(
            line.startswith(('size ', 'distance ', 'count ')) and 'unavailable' not in line
            for line in text.splitlines()[1:]):
        return 'ok'
    return body if body in RUNTIME_STATUSES else 'ok'
''' +s[b:]
s+='''

def epoch_class(sealed, current):
    """Keep a subclassable class while choosing the implementation at construction."""
    implementations = {}
    class EpochMeta(type):
        def __getattr__(cls, name):
            return getattr(current if new_contracts() else sealed, name)

        def __call__(cls, *args, **kwargs):
            key = (cls, new_contracts())
            if key not in implementations:
                base = current if key[1] else sealed
                implementations[key] = type(cls.__name__, (cls, base), {'__module__': cls.__module__})
            return type.__call__(implementations[key], *args, **kwargs)
    return EpochMeta(sealed.__name__, (), {'__module__': sealed.__module__})
'''
p.write_text(s)
for rel,names in [('generator/derivgen_v7/derivgen/ground_v313.py',['Session','GTInstances']),('generator/derivgen_v7/derivgen/box_v313.py',['BoxRegistry','FittedBoxProvider','FusedBoxProvider'])]:
    edit(rel,'response_status, new_contracts','response_status, new_contracts, epoch_class')
    for name in names:edit(rel,f'{name} = _epoch_dispatch({name}, _runtime.{name})',f'{name} = epoch_class({name}, _runtime.{name})')
edit('trace_format/calculator.py',"        if op in ('angle', 'turn') and any(not points[p].get('heading_defined', True) for p in refs):\n            text = 'u heading unavailable; v heading unavailable; dot '+text.split('; dot ', 1)[1]\n",'')
edit('student_pilot/carrier_c1_routing.py',"return f\"f1 centre {vec(self.camera_pose(k)['camera_t_L1'])} m, yaw heading unavailable (frame {k})\"", "return 'f1 centre '+partial_f1(self.camera_pose(k)['camera_t_L1'], f2)+f' m, yaw heading unavailable (frame {k})'")

p=S/'student_pilot/training_contract.py';s=p.read_text().replace('def audit_training_contract(rows, manifest=None):','def _audit_training_contract(rows, manifest=None):')
s=s.replace("entry = manifest.get(str(row.get('qid'))) if manifest is not None else row.get('candidate_phrases')", "entry = manifest.get(str(row.get('qid'))) if manifest is not None else row.get('candidate_manifest', row.get('cache_phrases', row.get('candidate_phrases')))\n        cache_reader = row.get('mask_source') in ('sam3', 'cached_sam3', 'cache') or row.get('uses_mask_cache', False)")
s=s.replace('named and entry is None and manifest is not None', 'named and entry is None and (manifest is not None or cache_reader)')
s=s.replace("if any(code in text for code in OPERATOR_FAULTS) or 'error:' in text.lower():", "if any(code in text for code in OPERATOR_FAULTS + RUNTIME_ONLY_FAULTS):")
s=s.replace("            if call.startswith(('<ground','<gap')):", "            if call.startswith(('<ground','<gap')) and status != 'error':")
s+='''

RUNTIME_ONLY_FAULTS = ('head_readout', 'head readout unavailable', 'own depth head unavailable',
    'invalid own depth', 'missing_or_invalid_K_transform', 'camera_rotation_not_proper',
    'native_mdg_requires_generate_binding', 'geometry_unavailable', 'mask_provider_unavailable')


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
'''
p.write_text(s)

p=S/'student_pilot/phrases.py';s=p.read_text()
s=s.replace("'people':'person', 'mice':'mouse'", "'people':'person', 'mice':'mouse', 'glasses':'glass', 'mattresses':'mattress',\n            'buses':'bus', 'knives':'knife', 'wives':'wife', 'lives':'life', 'leaves':'leaf',\n            'wolves':'wolf', 'halves':'half', 'loaves':'loaf', 'calves':'calf',\n            'lenses':'lens', 'cases':'case', 'houses':'house', 'noses':'nose',\n            'vases':'vase', 'roses':'rose', 'dresses':'dress', 'classes':'class', 'passes':'pass'")
s=s.replace("'series','species','news'", "'series','species','news','lens','canvas','chess','physics','headphones'")
s=s.replace("elif word.endswith('s') and not word.endswith(('ss','us','is')):", "elif word.endswith('s') and not word.endswith(('ss','us','is','ses','ves')):")
s=s.replace("    # Native MDG has no phrase cache.", "    question = question.replace(chr(34), '').replace('<', '').replace('>', '')\n    options = [o.replace(chr(34), '').replace('<', '').replace('>', '') for o in options]\n    # Native MDG has no phrase cache.")
s=s.replace("    if len(keys) > 1:\n        raise ValueError('duplicate_normalized_cache_phrase')\n    return keys[0] if keys else wanted", "    return min(keys, key=lambda key: (key != wanted, key.casefold(), key)) if keys else wanted")
p.write_text(s)

p=S/'student_pilot/s1_routing.py';s=p.read_text().replace('    source_deferrals = {}','    source_deferrals = {}\n    contract_deferred_qids = {}')
s=s.replace("        if refusal:\n            count(row['routing']['question_type'],", "        if refusal:\n            entry = contract_deferred_qids.setdefault(refusal, dict(count=0, qids=[]))\n            entry['count'] += 1\n            if len(entry['qids']) < 50:\n                entry['qids'].append(str(row.get('qid', '<missing>')))\n            routing_info = row.get('routing')\n            kind = routing_info.get('question_type', 'unknown') if isinstance(routing_info, dict) else 'unknown'\n            count(kind,")
s=s.replace('source_deferrals=source_deferrals,','source_deferrals=source_deferrals, contract_deferred_qids=contract_deferred_qids,')
p.write_text(s)
