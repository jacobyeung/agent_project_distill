"""Validate the independent review chain without turning conditions into GO."""
import hashlib
import re

REVIEWERS = ('review_r1p', 'review_r1p2', 'review_r1p3', 'review_r1p4')
REVIEW_FILES = ('r1.txt', 'r2.txt', 'r3.txt', 'r4.txt')

def verdict(text, reviewer):
    header = next((line.strip() for line in text.splitlines() if line.strip()), '')
    header = header.lstrip('# ').replace('**', '')
    match = re.match(r'(?:REVIEW_VERDICT_R1P[234]?\s*:\s*)?(GO AFTER FIXES|GO|NO[- ]GO)\b', header, re.I)
    if not match or match.group(1).upper() not in ('GO', 'GO AFTER FIXES'):
        raise ValueError(reviewer+' must state GO or GO AFTER FIXES on its first nonblank line')
    if reviewer == 'review_r1p4' and match.group(1).upper() == 'GO':
        if re.search(r'\b(?:AFTER|PENDING|CONDITIONAL|IF|UNLESS|SUBJECT TO)\b', header, re.I):
            raise ValueError('final GO has an unresolved condition')
    return match.group(1).upper()

def low_fixes(text):
    """Require explicit LOW labels on every remaining fix."""
    body = '\n'.join(text.splitlines()[1:]).replace('**', '')
    # Findings may be numbered, bullets, or Markdown headings. Collect multiline
    # findings through the next item/heading; unlabelled fixes fail closed.
    chunks = re.split(r'(?m)^\s*(?=(?:\d+[.)]\s|[-*]\s|#{1,6}\s))', body)
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

def build_chain(texts, identity, tree, outer):
    if set(texts) != set(REVIEW_FILES):
        raise ValueError('all four independent verdicts are required')
    reviews = {}
    for name, short in zip(REVIEWERS, REVIEW_FILES):
        text = texts[short]
        value = verdict(text, name)
        reviews[name] = dict(verdict=value, sha256=hashlib.sha256(text.encode()).hexdigest(),
                             file=short, role='final' if name == REVIEWERS[-1] else 'antecedent')
    final = texts['r4.txt']
    if identity not in final and outer not in final:
        raise ValueError('review_r1p4 must name the full final archive SHA or config identity')
    notes = low_fixes(final) if reviews['review_r1p4']['verdict'] == 'GO AFTER FIXES' else []
    return dict(config_sha256=identity, source_revision='sha256:'+tree,
                operator_archive_sha256=outer, reviews=reviews,
                reviewers=list(REVIEWERS), final_reviewer='review_r1p4',
                final_verdict=reviews['review_r1p4']['verdict'],
                fix_rounds=[4, 5, 6, 7, 8], nonblocking_fixes=notes,
                accepted_for_cpu_proof=True, production_go_granted=False)
