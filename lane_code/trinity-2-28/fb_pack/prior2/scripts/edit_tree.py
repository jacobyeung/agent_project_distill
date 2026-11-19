from pathlib import Path
T=Path('work/new/student_pilot')
p=T/'r1_direction_twins.py';s=p.read_text();s=s[:s.index('def dimensions(row):')]+'''def direction_details(row):
    """Read the observer clause, answer side and explicit forward trace relation."""
    import re
    question = row.get('student_input', {}).get('question', row.get('question', ''))
    head = question.casefold().split('?', 1)[0].split(', is ', 1)[0]
    away = (r'\\b(?:fac(?:e|ing)|look(?:ing)?|turn(?:ed|ing)?)\\s+away\\b'
            r'|\\b(?:with\\s+)?my\\s+back\\s+(?:to|toward|towards)\\b'
            r'|\\bfacing in the opposite direction\\b')
    toward = (r'\\b(?:fac(?:e|ing)|look(?:ing)?|viewing|gazing at)\\b'
              r'|\\b(?:oriented|directed|aiming|turned) toward(?:s)?\\b'
              r'|\\bmy gaze fixed on\\b|\\bdirecting my view towards\\b'
              r'|\\bnext to me and the .+ ahead\\b|\\bahead of (?:me|you)\\b')
    clause = 'away' if re.search(away, head) else 'toward' if re.search(toward, head) else 'MISSING'
    difficulty = str(row.get('question_type', row.get('category', 'unknown'))).rsplit('_', 1)[-1]
    answer = str(row.get('answer', ''))
    options = row.get('student_input', {}).get('options', [])
    if isinstance(options, dict):
        label = options.get(answer, 'MISSING')
    else:
        matches = [re.sub(r'^[A-Z][.)]\\s*', '', v).strip() for v in options
                   if isinstance(v, str) and re.match(r'^'+re.escape(answer)+r'[.)]\\s*', v)]
        label = matches[0] if len(matches) == 1 else 'MISSING'
    label = str(label).casefold().strip()
    side = ('back' if re.search(r'\\b(?:back|behind)\\b', label) else
            'front' if re.search(r'\\bfront\\b', label) else
            'MISSING' if label == 'missing' else 'other')
    lines = [s for s in row.get('target', row.get('suffix', '')).splitlines()
             if s.startswith(('Step 2:', 'Standing at ', 'If I stood at '))]
    relation = 'MISSING'
    if len(lines) == 1:
        front = bool(re.search(r'\\bin front of me\\b|\\bahead of me\\b', lines[0], re.I))
        back = bool(re.search(r'\\bbehind me\\b|\\bin back of me\\b', lines[0], re.I))
        relation = ('front' if front and not back else 'behind' if back and not front else
                    'lateral' if not front and not back and re.search(
                        r'\\b(?:to|on|out to) my (?:left|right)\\b', lines[0], re.I) else 'MISSING')
    return clause, difficulty, side, relation


def dimensions(row):
    """Report clause/difficulty answer shares from the question and selected option."""
    return direction_details(row)[:3]
''';p.write_text(s)
p=T/'r1_population.py';s=p.read_text();s=s.replace("    unknown, pairs = Counter(), defaultdict(Counter)","    from .r1_direction_prior import Prior\n    prior_pin = (cfg or {}).get('r1_training', {}).get('direction_prior')\n    prior = Prior(prior_pin) if prior_pin is not None else None\n    unknown, pairs = Counter(), defaultdict(Counter)")
s=s.replace("            groups[kind].append(offset)","            groups[kind].append(offset)\n            if prior is not None:\n                prior.observe(row, stream, kind, offset)")
s=s.replace("    from .r1_mix import plans\n    next(plans", "    if prior is not None:\n        binding['direction_prior'] = prior.bind(binding, output/'direction_prior.json')\n    from .r1_mix import plans\n    next(plans")
p.write_text(s)
p=T/'r1_mix.py';s=p.read_text().replace("    consumed = Counter()\n    totals", "    schedules = {}\n    if 'direction_prior' in binding:\n        from .r1_direction_prior import schedules as prior_schedules\n        schedules = prior_schedules(binding, card, indices, proof, pools)\n    consumed = Counter()\n    totals")
s=s.replace("                selected.append(pool[consumed[kind] % len(pool)])", "                selected.append(schedules[kind][consumed[kind]] if kind in schedules\n                                else pool[consumed[kind] % len(pool)])")
p.write_text(s)
p=T/'r1_loader.py';s=p.read_text().replace("        for index in indices['cells'].get('direction', []):", "        for index in [i for k in ('direction', 'facing_pairs') for i in indices['cells'].get(k, [])]:").replace("                    if kind == 'direction':", "                    if kind in ('direction', 'facing_pairs'):")
s=s.replace("        result['direction']=dict(draws_per_row=dict(direction_draws),answer_shares=[", "        result['direction']=dict(cells=['direction', 'facing_pairs'],\n            draws_per_row=dict(direction_draws),answer_shares=[").replace("('front','back','other')", "('front','back','other','MISSING')")
p.write_text(s)
