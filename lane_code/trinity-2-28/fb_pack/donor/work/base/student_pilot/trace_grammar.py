"""Validate the bounded trace grammar using only the Python standard library.

Entry points:
    validate_trace(think_text, *, form, question='', options=(), answer=None,
                   n_frames=32, printed_text='', qtype=None) -> list[Violation]
        Validate a think-block body. form is 'direct' or 'program'; question and
        printed_text are strings; options is a sequence of strings; answer is
        optional; n_frames bounds frame citations; qtype identifies counting.
        Embedded tool responses are extracted as well as printed_text. An empty
        result means pass. Invalid form or negative n_frames raises ValueError.
    validate_row(row) -> list[Violation]
        Validate a dict's target layout and trace, using question, options,
        answer, optional form/type/question_type/category and frame_indices.
    RULES: dict[str, str] maps stable rule IDs to one-line descriptions.
    Violation(rule_id, line_no, line, detail): namedtuple; line_no is 1-based
        within think_text (including blank/response lines), or 0 for row layout.
    main(argv=None) -> int
        CLI: --jsonl FILE [--limit N]. Stream JSON objects and emit one JSON
        summary with row counts, per-rule counts (once per row), and up to three
        failing examples per rule. Return 1 for failures, 0 otherwise. Rows
        exceeding 4 Mi characters fail layout and are drained in bounded chunks.

This is a conservative lexical grammar, not a visual truth checker. Counts need
an earlier explicit list; printed numbers do not license invented units in
direct rows. Number words are allowed only when the same word/digit is in the
question, for the listed pronoun/turn idioms, or for exactly 'three dimensions'
when the question names length, width, and height. Options license numeric
literals but do not license number words. No answer statistics set thresholds.
"""

import argparse
from collections import Counter, namedtuple
from decimal import Decimal, DecimalException, ROUND_HALF_UP, localcontext
import json
import re

Violation = namedtuple('Violation', 'rule_id line_no line detail')
RULES = {
    'direct_call': 'Direct traces cannot contain calls or tool responses.',
    'empty_think': 'Every trace needs non-whitespace thinking content.',
    'layout': 'The target must use the exact form and matching answer.',
    'number_not_allowed': 'Numbers need frames, labels, question constants, printed values, lists, or arithmetic.',
    'frame_range': 'Frame indices must be integers within the supplied frame count.',
    'unit_quantity': 'Unit quantities require program responses or explicit arithmetic.',
    'number_word': 'Number words require question constants or permitted idioms.',
    'letter_restatement': 'Option-letter restatements require a preceding program call.',
    'no_evidence': 'Traces need substantive content and direct traces need a question entity.',
    'filler_only': 'Generic thinking instructions alone are not evidence.',
    'exhaustive_frames': 'Direct Locate lines cite one frame per object or distinct instance.',
    'absence_claim': 'Direct traces cannot assert absence from frames.',
    'stated_estimate': 'A direct numeric estimate belongs only in the answer; counts require lists.',
    'line_kind': 'Every nonempty line must be Locate, Relate, Step, or program Call.',
    'angle_or_coordinate': 'Direct traces cannot state coordinates or angle computations.',
    'duplicate_object': 'Direct Locate/Seen lines cannot locate the same object on different lines.',
    'relate_without_locate': 'An explicit Relate label requires an earlier Locate label.',
    'frame_unit': 'A frame index cannot carry a time or measurement unit.',
    'list_count': 'An explicit list count must equal its number of items.',
}
PROGRAM_TYPES = frozenset({
    'object_abs_distance', 'absolute_distance_object', 'room_size_estimation',
    'absolute_size_room', 'camera_displacement', 'camera_movement_direction',
    'camera_rotation',
})
# Numeric tokens deliberately include glued digits, Unicode digits, and exponents.
NUM_SRC = r'[+\-−]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+\-]?\d+)?(?:/\d+(?:\.\d+)?)?%?'
NUM = re.compile(NUM_SRC)
UNITS = r'(?:centimeters?|centimetres?|millimeters?|millimetres?|kilometers?|kilometres?|meters?|metres?|inches|inch|feet|foot|yards?|degrees?|square|sq|deg|cm|mm|km|ft|in|m(?:\^?2|²)?|°)'
UNIT_AFTER = re.compile(r'\s*' + UNITS + r'(?![A-Za-z])', re.I)
TAG = re.compile(r'<\s*/?\s*([A-Za-z_][\w.-]*)\b[^>]*>')
RESPONSE = re.compile(r'<tool_response\s*>(.*?)</tool_response\s*>', re.S)
STEP_LABEL = re.compile(r'^\s*Step\s+(' + NUM_SRC + r')\s*[:.]\s*', re.I)
FRAME = re.compile(r'\bframes?\s+(' + NUM_SRC + r'(?:\s*(?:,\s*(?:and\s+)?|and\s+|&)\s*' + NUM_SRC + r')*)', re.I)
RELATION = re.compile(r'\b(?:left|right|ahead|behind|front|back|nearest|farthest|closest|order|before|after|longest|larger|smaller|between|side|above|below|near|far|toward|away)\b', re.I)
ARITH = re.compile(r'(?P<a>' + NUM_SRC + r')\s*(?P<op>[+*/x×−-])\s*(?P<b>' + NUM_SRC + r')\s*=\s*(?P<c>' + NUM_SRC + r')', re.I)
CONVERSIONS = {'100', '1000', '3.28084', '39.3701', '10.7639', '0.3048', '2.54'}
WORD_VALUES = dict(zip(('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty').split(), range(21)))
WORD_VALUES.update(dict(zip('thirty forty fifty sixty seventy eighty ninety hundred thousand dozen quarter twice double'.split(), [30,40,50,60,70,80,90,100,1000,12,.25,2,2])))
FRACTION_DENOMINATOR = r'(?:third|quarter|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth)'
FRACTION_WORD = (r'(?:' + '|'.join(WORD_VALUES) + r')\s+' + FRACTION_DENOMINATOR + r's?'
                 r'|an?\s+' + FRACTION_DENOMINATOR + r'(?=\s+(?:of\b|' + UNITS + r'\b)|\s*(?:[.,;:!?)]|$))'
                 r'|' + FRACTION_DENOMINATOR + r'(?:s|(?=\s+of\b))')
WORD_NUMBER = re.compile(r'\b(?:one and a half|a couple of|a pair of|half an?\s+\w+|' + FRACTION_WORD + r'|halfway|half|' + '|'.join(WORD_VALUES) + r')\b', re.I)
STOP = set(('a an the and or of to in on at by from for with as is are was were be been being i me my we it its this that these those each which what how many much if then than so no not do does would could should will can have has had am all any into out only also object objects thing things video frames frame question answer option options seen first second third standing stand facing face length width height dimension dimensions measured measuring measure centimeters metres meters turn turns left right back front ahead behind closest nearest farthest longest larger smaller order before after').split())
FILLER = re.compile(r'^(?:I (?:look at|watch|think about|will (?:answer|think|analyze|look|inspect))\b.*|Let me (?:analyze|think|look|inspect)\b.*|(?:I need to|We should) (?:think|analyze|answer)\b.*)$', re.I)
LETTER = re.compile(r'^(?:(?:So[, ]+)?(?:the )?(?:correct )?(?:answer|option)\s*(?:(?:is|:)\s*)?[A-Z](?:\s+is\s+(?:correct|the answer))?|[A-Z]\s+is\s+correct|I\s+(?:choose|select|pick)\s+(?:option\s+)?[A-Z]|[A-Z])[.!]?$', re.I)
INLINE_CHOICE = re.compile(
    r'\b(?i:(?:I\s+)?(?:choose|select|pick)\s+(?:option\s+)?|'
    r'(?:answer|option)\s*(?:(?:is|:)\s*)?)[(]?[A-Z](?![\w])'
    r'|\b(?i:so|hence|therefore|thus)\s*,?\s*[(]?[A-HJ-Z][)]?(?=\s*(?:[.,;:!?]|$))'
    r'|\b(?i:which\s+is)\s*\([A-Z]\)'
    r'|\b[A-Z]\s+(?i:is\s+(?:correct|the answer))\b')
QUOTED = re.compile(r'"[^"\n]*"|(?<!\w)\'[^\'\n]*\'|“[^”\n]*”|‘[^’\n]*’')


def _value(s):
    """Parse a bounded ASCII numeric literal; do not normalize disguised digits."""
    if any(ord(c) > 127 for c in s) or len(s) > 100:
        return None
    try:
        with localcontext() as ctx:
            ctx.prec = 120
            body = s.rstrip('%')
            parts = body.split('/')
            value = Decimal(parts[0])
            if len(parts) == 2:
                value /= Decimal(parts[1])
            if s.endswith('%'):
                value /= 100
            return value if value.is_finite() and abs(value) < Decimal('1e50') else None
    except DecimalException:
        return None


def _equal(a, b):
    av, bv = _value(a), _value(b)
    if av is None or bv is None:
        return False
    with localcontext() as ctx:
        ctx.prec = 120
        return av.quantize(Decimal('.01'), rounding=ROUND_HALF_UP) == bv.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def _unit_exponents(text):
    spans = set()
    for match in re.finditer(NUM_SRC + r'\s*m(?:\^?(2)|(²))\b', text, re.I):
        spans.add(match.span(1) if match.group(1) else match.span(2))
    return spans


def _tokens(text):
    # Exponents attached to a measured area are unit syntax, not quantities.
    exponents = _unit_exponents(text)
    return [m for m in NUM.finditer(text) if m.span() not in exponents]


def _words(text):
    words = re.findall(r'[a-z]+', text.lower())
    result = set()
    for word in words:
        if word in STOP or len(word) == 1:
            continue
        result.add(word)
        if word.endswith('s'):
            result.add(word[:-1])
        if word.endswith('es'):
            result.add(word[:-2])
    return result


def _letter(line):
    line = re.sub(r'^(?:Relate|Locate|Step|Conclusion)\s*:\s*', '', line, flags=re.I)
    return line.strip().rstrip('.!').upper() != 'I' and bool(LETTER.fullmatch(line.strip()))


def _choice_text(line, question):
    """Hide quoted questions without hiding a choice elsewhere in the line."""
    return QUOTED.sub(lambda m: ' ' * len(m.group())
                      if '?' in m.group() or m.group()[1:-1].strip() == question.strip()
                      else m.group(), line)


def _masked_responses(text):
    """Preserve original line numbers and offsets while hiding response bodies."""
    bodies = []
    def mask(match):
        bodies.append((match.start(), match.group(1)))
        return re.sub(r'[^\n]', ' ', match.group(0))
    return RESPONSE.sub(mask, text), bodies


def _word_errors(line, question):
    question_words = set(re.findall(r'\b\w+\b', question.lower()))
    question_nums = [m.group() for m in _tokens(question)]
    # These idioms carry order or reference, not a measured quantity.
    masked = re.sub(r'\bone by one\b|\b(?:a )?half turn\b', lambda m: ' ' * len(m.group()), line, flags=re.I)
    errors = []
    for match in WORD_NUMBER.finditer(masked):
        word = match.group().lower()
        following = masked[match.end():]
        if word == 'halfway' and re.match(r'\s+(?:between|along|across|down|up|through)\b', following, re.I):
            continue
        if word == 'one' and re.match(r'\s*(?:[.,;:!?)]|$|\b(?:is|was|that|which|by|at|near|behind|ahead|to|on|of|and|or|has|would|should|can|will|in)\b)', following):
            preceding = masked[:match.start()].lower()
            if re.search(r'\b(?:nearest|closest|farthest|this|that|each|which|other|the)\s+$', preceding) or not preceding.strip():
                continue
        if word in question_words or (' ' in word and re.search(r'\b' + re.escape(word) + r'\b', question, re.I)) or (word in WORD_VALUES and any(_value(n) == Decimal(str(WORD_VALUES[word])) for n in question_nums)):
            continue
        if word == 'three' and re.match(r'\s+dimensions\b', following) and {'length', 'width', 'height'} <= question_words:
            continue
        errors.append(word)
    # Roman numerals are forbidden only in a quantity/frame construction.
    for match in re.finditer(r'\b[IVXLCDM]+\b(?=\s+(?:' + UNITS + r'\b|[A-Za-z]+s\b))|(?<=frame )\b[IVXLCDM]+\b', line, re.I):
        errors.append(match.group())
    return errors


def _list_count(line, frames):
    distinct = bool(re.search(r'\b(?:distinct|instances?|each .*?once)\b', line, re.I))
    if distinct and frames:
        return len(frames)
    if ':' not in line:
        return None
    tail = line.split(':', 1)[1].strip().rstrip('.')
    if not re.search(r'[;,]', tail):
        return 1 if re.search(r'\b(?:list|instances?)\b', line, re.I) and tail else None
    items = [part.strip() for part in re.split(r'[;,]', tail)]
    # Frame enumerations for one object are not instance lists.
    if re.search(r'\bframes\b', tail, re.I) and not distinct:
        return None
    return len(items) if all(items) else None


def _exhaustive(line, frames):
    coordinated = re.fullmatch(r'(?:Seen|Locate):\s*(.+?)\s+in frames\s+(\d+) and (\d+)\.', line, re.I)
    if coordinated and len(coordinated.group(1).split(' and ')) == 2:
        return False
    if any(len(list(NUM.finditer(m.group(1)))) > 1 for m in frames):
        return True
    if len(frames) <= 1:
        return False
    if re.search(r'\b(?:distinct|instances?|each .*?once)\b', line, re.I):
        return False
    names = []
    previous_end = 0
    for match in frames:
        prefix = line[previous_end:match.start()]
        previous_end = match.end()
        words = _words(prefix) - {'locate', 'find', 'step', 'clearly', 'visible'}
        ordinal = re.search(r'\b(?:first|second|third|fourth|fifth)\b', prefix, re.I)
        # An ordinal marks an instance only when it directly modifies a noun.
        instance = ordinal.group().lower() if ordinal and re.match(r'\s+(?!seen\b)[a-z]+', prefix[ordinal.end():], re.I) else None
        if not words:
            return True
        if any(words & earlier and instance == earlier_instance for earlier, earlier_instance in names):
            return True
        names.append((words, instance))
    return False


def _located_names(body):
    """Extract explicit labelled citations; retain distinct instance suffixes."""
    if not re.match(r'^(?:Locate|Seen):', body, re.I):
        return []
    text = re.sub(r'^(?:Locate|Seen):\s*', '', body, flags=re.I)
    result = []
    for part in re.split(r';|,(?=\s*(?:the )?[A-Za-z])', text):
        match = re.match(r'(?:the )?(.+?)\s+(?:(?:is |are )?(?:first )?(?:seen |visible )?)in frames?\s+\d+', part.strip(), re.I)
        if match:
            result.extend(re.sub(r'^the\s+', '', n.strip().lower()) for n in match.group(1).split(' and '))
    return result


def _citation_names(body):
    """Extract names from labelled and supported prose Locate dialects."""
    body = re.sub(r'^Step\s+\d+:\s*', '', body, flags=re.I)
    names = _located_names(body)
    if names:
        return names
    appearance = re.match(r'find the first frame showing each object:\s*(.*)', body, re.I)
    if appearance:
        return [m.group(1).strip() for p in appearance.group(1).rstrip('.').split(';')
                for m in [re.fullmatch(r'\s*(.+?) frame \d+', p)] if m]
    for pattern in (
        r'^(?:find the|the) (.+?)(?:,| is) first seen in frame \d+',
        r'^locate the (.+?) at its first appearance in frame \d+',
        r'^the first appearance of the (.+?) is in frame \d+',
        r'^(?:find|locate) the (.+?) in frame \d+',
        r'^the (.+?) (?:is seen|appears) in frame \d+',
    ):
        match = re.match(pattern, body, re.I)
        if match:
            return [match.group(1)]
    return []


def _named_in_question(name, question, options):
    vocabulary = re.sub(r'\(s\)', 's', question + '\n' + '\n'.join(options), flags=re.I).lower()
    name = re.sub(r'\(s\)', 's', name, flags=re.I).lower()
    name = re.sub(r'^(?:the |first |second |third |fourth |fifth )+', '', name)
    variants = [name]
    if re.search(r'\s+[a-z]$', name):
        variants.append(name[:-2])  # Named instances such as chair a / chair b.
    for value in list(variants):
        if value.endswith('s'):
            variants.append(value[:-1])
    return any(re.search(r'(?<!\w)' + re.escape(value) + r'(?:s|es)?(?!\w)', vocabulary) for value in variants)


def _kind(line, *, entity, frames, printed, program):
    named = bool(_words(line))
    if re.fullmatch(r'The turns are:\s*(?:left|right|back)(?:,\s*(?:left|right|back))*[.]?', line, re.I):
        return 'Step'
    if frames and named:
        return 'Locate'
    if RELATION.search(line) and named:
        return 'Relate'
    if program and (re.search(r'\bI will (?:ground|project|measure|call|ask)\b', line, re.I) or
                    re.search(r'\b(?:tool|response)\b', line, re.I)):
        return 'Step'
    if program and any(any(_equal(m.group(), n) for n in printed) for m in _tokens(line)):
        return 'Call'
    if ARITH.search(line):
        return 'Step'
    if re.search(r'\b(?:find|locate|list)\b', line, re.I) and named:
        return 'Step'
    if re.search(r'\b(?:the question (?:asks|has|defines)|standing|facing|I (?:stand|go)|keep that heading|So (?:there are|the)|The turns are|(?:count|total|sum) (?:is|equals))\b', line, re.I) and (entity or named):
        return 'Step'
    if re.search(r'\b(?:first|second|third)\b', line, re.I) and entity:
        return 'Step'
    return None


def validate_trace(think_text, *, form, question='', options=(), answer=None,
                   n_frames=32, printed_text='', qtype=None):
    """Return all lexical violations of a think body; see module documentation."""
    if form not in {'direct', 'program'} or n_frames < 0:
        raise ValueError('form must be direct/program and n_frames must be nonnegative')
    violations = []
    seen = set()
    def add(rule, line_no, line, detail):
        key = (rule, line_no)
        if key not in seen:
            seen.add(key)
            violations.append(Violation(rule, line_no, line, detail))
    if not think_text.strip():
        add('empty_think', 1, think_text, 'The think body is empty.')
        add('no_evidence', 1, think_text, 'The trace contains no evidence.')
        return violations
    program = form == 'program'
    visible, responses = _masked_responses(think_text)
    originals = think_text.splitlines()
    # Only complete response bodies confer numeric provenance.
    printed = [m.group() for m in _tokens(printed_text)] if program else []
    all_printed = printed + ([m.group() for _, body in responses for m in _tokens(body)] if program else [])
    question_numbers = [m.group() for m in _tokens(question + '\n' + '\n'.join(options))]
    entities = _words(question + '\n' + '\n'.join(re.sub(r'^[A-Z]\.\s*', '', o) for o in options))
    prior_counts = set()
    prior_results = set()
    next_step = 1
    called = False
    content = False
    entity_seen = False
    filler_lines = []
    nonfiller_lines = []
    offset = 0
    response_index = 0
    located = {}
    explicit_locate = False
    numeric_answer = _value(str(answer)) if answer is not None else None
    counting = 'count' in str(qtype).lower()
    answer_variants = set()
    if numeric_answer is not None:
        with localcontext() as ctx:
            ctx.prec = 120
            answer_variants = {numeric_answer.quantize(Decimal(1).scaleb(-i), rounding=ROUND_HALF_UP) for i in range(3)} | {numeric_answer}
    for line_no, raw in enumerate(visible.splitlines(keepends=True), 1):
        original = originals[line_no - 1]
        while response_index < len(responses) and responses[response_index][0] < offset + len(raw):
            if program:
                printed.extend(m.group() for m in _tokens(responses[response_index][1]))
                called = True
                content = True
            response_index += 1
        offset += len(raw)
        # Inspect original tags even where the corresponding response is masked.
        tags = [m for m in TAG.finditer(original) if m.group(1).lower() not in {'think', 'answer'}]
        if not program and tags:
            add('direct_call', line_no, original, 'Calls and responses are forbidden in direct form.')
        if re.search(r'</?(?:think|answer)\b', original):
            add('layout', line_no, original, 'Nested think/answer tags are not allowed.')
        line = raw.strip()
        if not line:
            continue
        # Call attributes are syntax, not asserted quantities or numeric evidence.
        call_line = bool(tags) and all(m.group(1).lower() not in
            {'think', 'answer', 'tool_response'} for m in TAG.finditer(line)) and bool(
            re.fullmatch(r'(?:\s*<[A-Za-z_][\w.-]*(?:\s+[^<>]*)?/?>\s*)+', line))
        if program and call_line:
            called = True
            content = True
            nonfiller_lines.append(line_no)
            continue
        step = STEP_LABEL.match(line)
        step_spans = set()
        if step:
            if step.group(1) == str(next_step):
                step_spans.add(step.span(1))
            else:
                add('number_not_allowed', line_no, original, 'Step labels must count consecutively from 1.')
            next_step += 1
        body = line[step.end():] if step else line
        choice_body = _choice_text(body, question)
        is_letter = _letter(choice_body)
        has_choice = is_letter or bool(INLINE_CHOICE.search(choice_body))
        if not program:
            has_choice |= bool(re.search(r'\([A-Z]\)|\bthe (?:first|second|third|fourth|fifth|sixth|seventh|eighth|last)\b[^.;\n]*\boption\b', choice_body))
        line_entity = bool(_words(body) & entities)
        entity_seen |= line_entity and not is_letter
        frame_matches = list(FRAME.finditer(line))
        frame_spans = set()
        frame_values = []
        for fm in frame_matches:
            for nm in NUM.finditer(fm.group(1)):
                span = (fm.start(1) + nm.start(), fm.start(1) + nm.end())
                value = _value(nm.group())
                if value is None or value != int(value) or not 1 <= value <= n_frames:
                    add('frame_range', line_no, original, 'Frame indices must be integers in 1..n_frames.')
                else:
                    frame_spans.add(span)
                frame_values.append(nm.group())
        if not program:
            if re.search(r'\b(?:absent in|not visible in|not seen in frames?|missing from frames?|does not appear in|is invisible in|is never seen)\b', line, re.I):
                add('absence_claim', line_no, original, 'Direct traces cannot claim frame absence.')
            if re.search(r'\btool_response\s*:', line, re.I):
                add('direct_call', line_no, original, 'Untagged tool responses are forbidden in direct form.')
            if re.match(r'^Relate\s*:', body, re.I) and not explicit_locate:
                add('relate_without_locate', line_no, original, 'Explicit Relate requires an earlier Locate label.')
            explicit_locate |= bool(re.match(r'^Locate\s*:', body, re.I))
            for name in _citation_names(body):
                if name in located and located[name] != line_no:
                    add('duplicate_object', line_no, original, 'Object already located: ' + name)
                located[name] = line_no
            for fm in frame_matches:
                if re.match(r'\s*(?:seconds?|secs?|s|minutes?|mins?|hours?|h|milliseconds?|ms|meters?|metres?|cm|mm|degrees?|deg|°)(?![A-Za-z])', line[fm.end():], re.I):
                    add('frame_unit', line_no, original, 'Frame indices are positions, not measurements.')
            if re.search(r'\b(?:every frame|all frames)\b', line, re.I) or (
                    len(frame_values) >= n_frames > 0 and set(frame_values) == set(str(i) for i in range(1, n_frames + 1))
                    and re.search(r'\b(?:first|second|third)\s+(?!seen\b)\w+\s+in frame', line, re.I)):
                add('exhaustive_frames', line_no, original, 'An exhaustive pin enumeration is not a Locate citation.')
            unit_words = r'(?:metres?|meters?|centimetres?|centimeters?|millimetres?|millimeters?|feet|foot|inches|yards?|degrees?|radians?|seconds?|steps?)'
            if re.search(r'\b(?:about\s+)?(?:an?|a few|few|several)\s+' + unit_words + r'\b|\b' + unit_words + r'-long\b', line, re.I):
                add('unit_quantity', line_no, original, 'A quantity written in words still needs measurement evidence.')
            if re.search(r'\b(?:' + '|'.join(WORD_VALUES) + r'|\d+)-?ish\b', line, re.I):
                add('number_word', line_no, original, 'Approximate number spelling is not evidence.')
            if '°' in line or re.search(r'\bright angle\b', line, re.I):
                add('angle_or_coordinate', line_no, original, 'Direct traces cannot assert an angle.')
            if _exhaustive(body, list(FRAME.finditer(body))):
                add('exhaustive_frames', line_no, original, 'Use one frame per named object or distinct instance.')
            coord = r'\(\s*(?:' + NUM_SRC + r'|[xyz])\s*,\s*(?:' + NUM_SRC + r'|[xyz])(?:\s*,\s*(?:' + NUM_SRC + r'|[xyz]))?\s*\)'
            if re.search(r'\b(?:cross|dot|atan2|theta|bearing|degrees)\b', line, re.I) or re.search(coord, line, re.I):
                add('angle_or_coordinate', line_no, original, 'Direct traces use spatial words, not angle/coordinate calculations.')
        for word in ([] if is_letter else _word_errors(body, question)):
            add('number_word', line_no, original, 'Unlicensed number word: ' + word)
        if has_choice:
            if not program or not called:
                add('letter_restatement', line_no, original, 'A letter restatement requires a preceding program Call.')
        # Arithmetic validates operands before licensing its result or constants.
        arithmetic_spans = set()
        results = set()
        derived = set()
        def sourced(token):
            value = _value(token)
            return value is not None and (token in derived or value in prior_results or value in prior_counts or
                   any(_equal(token, n) for n in all_printed) or
                   any(value == _value(n) for n in question_numbers))
        for expr in ARITH.finditer(line):
            a, b, c = (expr.group(k) for k in ('a', 'b', 'c'))
            if not all(sourced(v) or v in CONVERSIONS for v in (a, b)):
                add('number_not_allowed', line_no, original, 'Arithmetic operands lack permitted provenance.')
                continue
            av, bv, cv = map(_value, (a, b, c))
            if None in (av, bv, cv):
                add('number_not_allowed', line_no, original, 'Arithmetic contains an invalid numeric literal.')
                continue
            try:
                with localcontext() as ctx:
                    ctx.prec = 120
                    op = expr.group('op')
                    expected = av + bv if op == '+' else av - bv if op in {'-', '−'} else av * bv if op.lower() in {'*', 'x', '×'} else av / bv
                    if '/' in c or '%' in c:
                        valid = expected == cv
                    else:
                        valid = expected.quantize(Decimal(1).scaleb(cv.as_tuple().exponent), rounding=ROUND_HALF_UP) == cv
                if valid:
                    arithmetic_spans.update(expr.span(k) for k in ('a', 'b', 'c'))
                    results.add(expr.span('c'))
                    derived.add(c)
                else:
                    add('number_not_allowed', line_no, original, 'Arithmetic result is incorrect at its written precision.')
            except DecimalException:
                add('number_not_allowed', line_no, original, 'Arithmetic is undefined or exceeds numeric bounds.')
        explicit_count = re.search(r'\blist\s*\[([^\]]*)\]\s*;\s*count\s*=\s*(\d+)', line, re.I)
        list_spans = set()
        if explicit_count:
            items = [x.strip() for x in explicit_count.group(1).split(';') if x.strip()]
            if int(explicit_count.group(2)) != len(items):
                add('list_count', line_no, original, 'Stated count differs from explicit list length.')
            list_spans.add(explicit_count.span(2))
        for index, char in enumerate(line):
            if char.isnumeric() and ord(char) > 127 and (index, index + 1) not in _unit_exponents(line):
                add('number_not_allowed', line_no, original, 'Non-ASCII numeric spelling: ' + char)
        for nm in _tokens(line):
            token, span = nm.group(), nm.span()
            value = _value(token)
            structural = span in step_spans or span in frame_spans or span in list_spans
            # Invalid indices/labels still denote structure, never an estimate.
            structure_context = (step is not None and span == step.span(1)) or any(
                fm.start(1) <= nm.start() and nm.end() <= fm.end(1) for fm in frame_matches)
            allowed = structural or span in arithmetic_spans or sourced(token)
            # Frame occurrences must satisfy range even when the question prints them.
            if not allowed:
                add('number_not_allowed', line_no, original, 'Number lacks permitted provenance: ' + token)
            unit = UNIT_AFTER.match(line, nm.end())
            if unit and unit.group().strip().lower() == 'in':
                # Attached 8in denotes a unit; spaced 'in' before prose is a preposition.
                if unit.group()[0].isspace() and not re.match(r'\s*(?:[.,;:!?)]|$)', line[unit.end():]):
                    unit = None
            if unit and (not program or not (span in results or any(_equal(token, n) for n in all_printed))):
                add('unit_quantity', line_no, original, 'Unit quantity needs a printed value or a correct explicit result: ' + token)
            if not program and not structure_context and numeric_answer is not None and not options and value in answer_variants:
                if not counting or (not structural and value not in prior_counts and value not in prior_results and span not in results):
                    add('stated_estimate', line_no, original, 'The direct numeric answer is stated without a licensed count.')
            if counting and not structural and span not in arithmetic_spans and value not in prior_counts and value not in prior_results:
                add('number_not_allowed', line_no, original, 'A count must match an earlier explicit list.')
        filler = bool(FILLER.match(body)) and not (line_entity or frame_matches or RELATION.search(body))
        if filler:
            filler_lines.append(line_no)
        else:
            nonfiller_lines.append(line_no)
        kind = _kind(body, entity=line_entity, frames=frame_matches, printed=printed, program=program)
        if not (kind or (program and call_line) or has_choice):
            add('line_kind', line_no, original, 'Line does not match Locate, Relate, Step, or Call.')
        if kind and not filler and not is_letter:
            content = True
        prior_results.update(_value(token) for token in derived)
        count = _list_count(body, frame_values)
        if count is not None and not is_letter and not filler:
            prior_counts.add(Decimal(count))
    if filler_lines and not nonfiller_lines and not content:
        add('filler_only', filler_lines[0], originals[filler_lines[0] - 1], 'Every substantive line is generic filler.')
    if not content or (not program and not entity_seen):
        add('no_evidence', 1, originals[0] if originals else '', 'Need substantive content and, in direct form, a question/option entity.')
    # Unmatched response delimiters cannot hide content or confer provenance.
    if visible.count('<tool_response') or visible.count('</tool_response'):
        add('layout', 0, '', 'Unbalanced tool_response tags.')
    return violations


def validate_row(row):
    """Validate a row mapping, including its full target serialization."""
    if not isinstance(row, dict):
        return [Violation('layout', 0, '', 'Row must be a JSON object.')]
    qtype = row.get('question_type') or row.get('type') or row.get('category')
    form = row.get('form', 'program' if qtype in PROGRAM_TYPES else 'direct')
    target = row.get('target', '')
    answer = str(row.get('answer', ''))
    if not isinstance(target, str) or form not in {'direct', 'program'}:
        return [Violation('layout', 0, '', 'Target must be text and form must be direct/program.')]
    ending = '\n\n' + answer if form == 'direct' else '\n<answer>' + answer + '</answer>'
    pattern = r'<think>\n(?P<body>.*?)\n</think>' + re.escape(ending) + r'\n?'
    match = re.fullmatch(pattern, target, re.S)
    errors = []
    if match is None or 'answer' not in row:
        errors.append(Violation('layout', 0, target[:240], 'Target layout or answer bytes do not match the selected form.'))
    body_match = re.search(r'<think>(.*?)</think>', target, re.S)
    if body_match is None:
        return errors
    # Validate precisely the content between tags; leading newline counts as line 1.
    inputs = row.get('student_input') or {}
    indices = row.get('frame_indices', inputs.get('frame_indices'))
    errors.extend(validate_trace(body_match.group(1), form=form,
        question=row.get('question', inputs.get('question', '')),
        options=row.get('options', inputs.get('options')) or (),
        answer=row.get('answer'), n_frames=len(indices) if indices is not None else 32,
        qtype=qtype))
    return errors


def main(argv=None):
    """Stream a JSONL input and print one JSON summary; return failure status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jsonl', required=True)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error('--limit must be nonnegative')
    counts = Counter()
    examples = {rule: [] for rule in RULES}
    rows = failed = 0
    with open(args.jsonl, encoding='utf-8') as handle:
        # readline iteration streams input; no whole-file load or prefetch past limit.
        while args.limit is None or rows < args.limit:
            line = handle.readline(4 * 1024 * 1024 + 1)
            if not line:
                break
            rows += 1
            try:
                if len(line) > 4 * 1024 * 1024:
                    ended = line.endswith('\n')
                    line = line[:240]
                    while not ended:
                        chunk = handle.readline(4 * 1024 * 1024)
                        ended = not chunk or chunk.endswith('\n')
                    raise ValueError('Row exceeds the 4 Mi-character streaming bound')
                errors = validate_row(json.loads(line))
            except (ValueError, TypeError, AttributeError, KeyError) as exc:
                errors = [Violation('layout', 0, line[:240], 'Malformed JSON row: ' + str(exc))]
            if errors:
                failed += 1
            by_rule = {}
            for violation in errors:
                by_rule.setdefault(violation.rule_id, violation)
            for rule, violation in by_rule.items():
                counts[rule] += 1
                if len(examples[rule]) < 3:
                    examples[rule].append({'row_no': rows, **violation._asdict()})
    print(json.dumps({'rows': rows, 'passed': rows - failed, 'failed': failed,
                      'per_rule_counts': {rule: counts[rule] for rule in RULES},
                      'examples': examples}, ensure_ascii=False, indent=2))
    return int(failed > 0)


if __name__ == '__main__':
    raise SystemExit(main())
