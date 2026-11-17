"""Injected into the stdlib deriver; constants come from pinned local references."""

def validate_selection_equality(over):
    spec = over.get('config', {}).get('s1_routing', {})
    additions = {n: p for n, p in over.get('add_k', {}).items() if ADD_K_DATA.fullmatch(n)}
    selection = spec.get('selection')
    proof = over.get('selection_equality')
    if selection is None:
        if additions or proof or 'selection_equality.json' in over.get('add_k', {}):
            refuse('selection evidence without a selection override')
        return
    # Retaining the exact registered D0 input is permitted only as a blocked artifact.
    if selection.get('sha256') == SELECTION_REFERENCE:
        if 'code_tree' in over and over.get('status', 'BLOCKED') != 'BLOCKED':
            refuse('stale selection cannot authorize preparation or training')
        if proof or 'selection_equality.json' in over.get('add_k', {}):
            refuse('stale selection cannot carry an equality verdict')
        return
    if proof is None or over.get('add_k', {}).get('selection_equality.json') != proof:
        refuse('new selection requires a pinned equality report in add_k')
    if len(additions) != 1:
        refuse('equality requires one new selection record')
    name, pin = next(iter(additions.items()))
    candidate = json.loads(read_override_pin(pin).read_text())
    if selection != dict(path=KIT_LOGICAL + name, sha256=pin['sha256']):
        refuse('equality selection pin differs')
    report = json.loads(read_override_pin(proof).read_text())
    code = json.loads(read_override_pin(over.get('code_tree', {}).get('pin')).read_text())
    body = {k: v for k, v in candidate.items() if k != 'implementation'}
    if digest(body) != SELECTION_CONTENT or digest(candidate.get('implementation')) != SELECTION_IMPLEMENTATION:
        refuse('selection content or native implementation differs')
    if any(code['files'].get(n) != h for n, h in candidate['implementation'].items()):
        refuse('selection implementation is not in the sealed tree')
    expected = dict(schema='selection-equality-v1', status='EQUAL', regenerated=True,
        reference_sha256=SELECTION_REFERENCE, raw_reference_sha256=SELECTION_RAW_REFERENCE,
        selection_sha256=pin['sha256'], content_sha256=SELECTION_CONTENT,
        raw_content_sha256=SELECTION_RAW_CONTENT, implementation_sha256=SELECTION_IMPLEMENTATION,
        tree_sha256=code['tree_sha256'], code_sha256=sha(read_override_pin(over['code_tree']['pin'])),
        tool_sha256=SELECTION_TOOL, differences=[], raw_differences=[],
        fields={k: True for k in body}, indices=SELECTION_INDICES, production_authorized=False)
    if any(enc(report.get(k)) != enc(v) for k, v in expected.items()):
        refuse('equality report is incomplete, negative or bound to other bytes')
    inputs = report.get('inputs', {})
    if set(inputs) != set(SELECTION_INPUT_SIZES) or any(
            not isinstance(inputs[h], dict) or inputs[h].get('bytes') != size
            or not isinstance(inputs[h].get('path'), str) for h, size in SELECTION_INPUT_SIZES.items()):
        refuse('equality report input inventory differs')
