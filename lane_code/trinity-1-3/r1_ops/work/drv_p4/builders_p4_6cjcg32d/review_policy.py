"""Validate the independent review chain without turning conditions into GO."""
import hashlib
import re

REVIEWERS = ('review_r1p', 'review_r1p2', 'review_r1p3', 'review_r1p4', 'review_r1p5', 'review_r1p6')
REVIEW_FILES = ('r1.txt', 'r2.txt', 'r3.txt', 'r4.txt', 'r5.txt', 'r6.txt')

def verdict(text, reviewer):
    header = next((line.strip() for line in text.splitlines() if line.strip()), '')
    header = header.lstrip('# ').replace('**', '')
    match = re.match(r'(?:REVIEW_VERDICT_R1P[23456]?\s*:\s*)?(GO AFTER FIXES|GO|NO[- ]GO)\b', header, re.I)
    if not match or match.group(1).upper() not in ('GO', 'GO AFTER FIXES'):
        raise ValueError(reviewer+' must state GO or GO AFTER FIXES on its first nonblank line')
    if reviewer == 'review_r1p6':
        tail = header[match.end():].strip()
        if tail and not tail.startswith(('(', '—', '–', '- ', ':')):
            raise ValueError('final verdict has an ambiguous suffix')
        if re.search(r'\b(?:AFTER|PENDING|CONDITIONAL|IF|UNLESS|SUBJECT TO|PROVIDED|CONTINGENT|NO[- ]GO)\b|[?]', tail, re.I):
            raise ValueError('final verdict has an unresolved condition')
    return match.group(1).upper()

def low_fixes(text):
    """Require explicit LOW labels on every remaining fix."""
    body = '\n'.join(text.strip().splitlines()[1:]).replace('**', '')
    # Findings may be numbered, bullets, or Markdown headings. Collect multiline
    # findings through the next item/heading; unlabelled fixes fail closed.
    chunks = []
    current = []
    for line in body.splitlines():
        if re.match(r'^\s*(?:\d+[.)]\s|[-*]\s|#{1,6}\s)', line) and current:
            chunks.append('\n'.join(current))
            current = []
        current.append(line)
    if current:
        chunks.append('\n'.join(current))
    notes = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        label = re.sub(r'^(?:\d+[.)]\s*|[-*]\s*|#{1,6}\s*)', '', chunk)
        # A PASS finding can describe a resolved issue; it is not a remaining fix.
        if re.match(r'PASS\b', label, re.I):
            continue
        if re.search(r'\b(?:HIGH|MEDIUM|CRITICAL|BLOCKER)\b', chunk, re.I):
            raise ValueError('final conditional review contains a severity above LOW')
        has_low = bool(re.search(r'\bLOW\b', chunk, re.I))
        actionable = bool(re.search(r'\b(?:fix|fixes|required|must|should|todo)\b', chunk, re.I))
        item = bool(re.match(r'(?:\d+[.)]\s|[-*]\s)', chunk))
        # Section titles alone do not constitute a finding.
        title = chunk.lstrip('# ').strip().lower().rstrip(':')
        if title in ('fixes', 'remaining fixes', 'low non-blocking fixes', 'findings'):
            continue
        if has_low or actionable or item:
            nonblocking = re.search(r'\bnon[- ]blocking\b|\bdoes not block\b', chunk, re.I)
            blocking = re.search(r'\b(?:blocks?|blocking|required before|must (?:fix|resolve))\b',
                                 re.sub(r'non[- ]blocking|does not block', '', chunk, flags=re.I), re.I)
            if not has_low or blocking:
                raise ValueError('every final conditional fix must be explicitly LOW without blocking conditions')
            notes.append(chunk)
    if not notes:
        raise ValueError('final GO AFTER FIXES must list explicit LOW fixes')
    return notes

def packet_a_section(text):
    """Accept one explicit A section or A verdict row; never borrow B's text."""
    lines = text.replace('**', '').replace('`', '').splitlines()
    starts = []
    for i, line in enumerate(lines):
        label = re.sub(r'^\s*(?:#{1,6}\s*|[-*]\s*)', '', line).strip()
        if re.match(r'Packet\s+A\b', label, re.I) or re.match(r'\|\s*(?:Packet\s+)?A\s*\|', label, re.I):
            starts.append(i)
    if len(starts) != 1:
        raise ValueError('final review requires exactly one explicit Packet A section or verdict row')
    start = starts[0]
    first = lines[start]
    if first.lstrip().startswith('|'):
        section = first
    else:
        end = len(lines)
        level = len(first.lstrip()) - len(first.lstrip().lstrip('#'))
        for j in range(start+1, len(lines)):
            line = lines[j]
            label = re.sub(r'^\s*(?:#{1,6}\s*|[-*]\s*)', '', line).strip()
            heading = re.match(r'^\s*(#{1,6})\s+', line)
            if re.match(r'Packet\s+[AB]\b', label, re.I) or (level and heading and len(heading[1]) <= level):
                end = j
                break
        section = '\n'.join(lines[start:end])
    declarations = []
    for line in section.splitlines():
        label = line.lstrip('# -*').strip()
        if re.match(r'(?:Packet\s+A\b|(?:Final\s+)?Verdict\s*:|GO\b|NO[- ]GO\b)', label, re.I) or label.startswith('|'):
            found = list(re.finditer(r'(?<![A-Za-z-])(GO AFTER FIXES|NO[- ]GO|GO)(?![A-Za-z-])', label, re.I))
            declarations.extend((match.group(1).upper(), label[match.end():]) for match in found)
    if len(declarations) != 1:
        raise ValueError('Packet A must have exactly one unambiguous verdict')
    value, tail = declarations[0]
    tail = tail.strip()
    if tail and not tail.startswith(('(', '—', '–', '- ', ':', '|', '.')):
        raise ValueError('Packet A verdict has an ambiguous suffix')
    if value not in ('GO', 'GO AFTER FIXES'):
        raise ValueError('Packet A is not approved')
    if re.search(r'\b(?:AFTER|PENDING|CONDITIONAL|IF|UNLESS|SUBJECT TO|PROVIDED|CONTINGENT)\b|[?]', tail, re.I):
        raise ValueError('Packet A verdict has an unresolved condition')
    return value, section


def build_chain(texts, identity, tree, outer):
    if set(texts) != set(REVIEW_FILES):
        raise ValueError('all six independent verdicts are required')
    reviews = {}
    for name, short in zip(REVIEWERS, REVIEW_FILES):
        text = texts[short]
        value = packet_a_section(text)[0] if name == REVIEWERS[-1] else verdict(text, name)
        reviews[name] = dict(verdict=value, sha256=hashlib.sha256(text.encode()).hexdigest(),
                             file=short, role='final' if name == REVIEWERS[-1] else 'antecedent')
    value, final = packet_a_section(texts['r6.txt'])
    if not any(re.search(r'(?<![0-9a-f])'+pin+r'(?![0-9a-f])', final) for pin in (identity, outer)):
        raise ValueError('Packet A section must name its full archive SHA or config identity')
    fix_body = '\n'.join(line for line in final.splitlines() if not re.match(r'^\s*(?:#{1,6}\s*|[-*]\s*)?(?:Packet A\b|(?:Final )?Verdict\s*:|GO(?: AFTER FIXES)?\b)', line, re.I))
    notes = low_fixes('# '+value+'\n'+fix_body) if value == 'GO AFTER FIXES' else []
    return dict(config_sha256=identity, source_revision='sha256:'+tree,
                operator_archive_sha256=outer, packet='A', reviews=reviews,
                reviewers=list(REVIEWERS), final_reviewer='review_r1p6',
                final_verdict=value, fix_rounds=[4, 5, 6, 7, 8, 9, 10], nonblocking_fixes=notes,
                accepted_for_cpu_proof=True, production_go_granted=False)
