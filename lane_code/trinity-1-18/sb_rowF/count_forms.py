"""Proposed counting-form contract; this is not an amendment to N's live kit."""
import collections
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def render(categories, answer, form='B'):
    require(form in ('A', 'B'), 'unknown form')
    lines = []
    totals = []
    for step, (name, entries) in enumerate(categories, 1):
        n = len(entries); totals.append(n)
        if form == 'B':
            parts = [f'{i} of {n}, frame {frame}' + (f' ({region})' if region else '')
                     for i, (frame, region) in enumerate(sorted(entries), 1)]
            noun = 'instance' if n == 1 else 'instances'
            lines.append(f'Step {step}: I count {n} distinct {name} {noun}, each by the frame where it first appears: '
                         + ('; '.join(parts) if parts else 'none') + '.')
        else:
            frames = collections.defaultdict(collections.Counter)
            for frame, region in entries: frames[frame][region] += 1
            parts = []
            for frame, regions in sorted(frames.items()):
                require(not regions[''] or len(regions) == 1, 'mixed region evidence')
                tags = ', '.join(f'{r}: {regions[r]}' for r in ('left', 'middle', 'right') if regions[r])
                parts.append(f'frame {frame}: {sum(regions.values())}' + (f' ({tags})' if tags else ''))
            lines.append(f'Step {step}: {name}: ' + ('; '.join(parts) if parts else 'none') + f', total {n}.')
    require(sum(totals) == int(answer), 'answer does not match inventory')
    if len(categories) > 1:
        lines.append(f'Step {len(categories) + 1}: add them: ' + ' + '.join(map(str, totals)) + f' = {answer}.')
        lines.append(f'So there are {answer} instances in total.')
    else:
        n = totals[0]
        lines.append(f'So there {"is" if n == 1 else "are"} {n} {categories[0][0]} {"instance" if n == 1 else "instances"}.')
    return '<think>\n' + '\n'.join(lines) + '\n</think>\n\n' + str(answer)


def validate(target, answer, form='B'):
    """Parse the entire target; return category frame/region multisets and totals.

    Form B permits equal frames for different numbered instances. It never
    permits repeated ordinals, skipped ordinals, or a different denominator.
    Form A permits each frame once and requires positive integer increments.
    """
    match = re.fullmatch(r'<think>\n(.+)\n</think>\n\n(\d+)', target, re.S)
    require(match is not None, 'invalid trace envelope')
    require(str(answer) == match[2], 'final answer differs')
    lines = match[1].splitlines(); inventory = {}; totals = {}; step = 1
    while lines and not re.match(r'Step \d+: add them:', lines[0]) and lines[0].startswith('Step '):
        line = lines.pop(0)
        if form == 'B':
            m = re.fullmatch(r'Step (\d+): I count (\d+) distinct (.+) (instance|instances), each by the frame where it first appears: (.+)\.', line)
            require(m is not None, 'malformed B category')
            idx, n, name, noun, body = int(m[1]), int(m[2]), m[3], m[4], m[5]
            require(noun == ('instance' if n == 1 else 'instances'), 'instance agreement')
            parts = [] if body == 'none' else body.split('; ')
            require(len(parts) == n, 'announced count differs from entries')
            counter = collections.Counter()
            for expected, part in enumerate(parts, 1):
                e = re.fullmatch(r'(\d+) of (\d+), frame (\d+)(?: \((left|middle|right)\))?', part)
                require(e is not None, 'malformed B entry')
                ordinal, denominator, frame = map(int, e.groups()[:3])
                require(ordinal == expected and denominator == n, 'ordinal or denominator mismatch')
                require(1 <= frame <= 32, 'frame outside 1..32')
                counter[(frame, e[4] or '')] += 1
        elif form == 'A':
            m = re.fullmatch(r'Step (\d+): (.+?): (.+), total (\d+)\.', line)
            require(m is not None, 'malformed A category')
            idx, name, body, n = int(m[1]), m[2], m[3], int(m[4])
            counter = collections.Counter(); previous = 0
            for part in ([] if body == 'none' else body.split('; ')):
                e = re.fullmatch(r'frame (\d+): (\d+)(?: \((.+)\))?', part)
                require(e is not None, 'malformed A entry')
                frame, increment = int(e[1]), int(e[2])
                require(previous < frame <= 32 and increment > 0, 'frame order/range or increment')
                previous = frame
                if e[3]:
                    tags = {}
                    for tag in e[3].split(', '):
                        t = re.fullmatch(r'(left|middle|right): (\d+)', tag)
                        require(t is not None and t[1] not in tags and int(t[2]) > 0, 'invalid region tally')
                        tags[t[1]] = int(t[2])
                    require(sum(tags.values()) == increment, 'region tally differs')
                    counter.update({(frame, region): count for region, count in tags.items()})
                else: counter[(frame, '')] = increment
            require(sum(counter.values()) == n, 'category tally differs')
        else: raise ValueError('unknown form')
        require(idx == step and name not in inventory, 'step order or repeated category')
        require(sum(counter.values()) == n, 'category entries differ')
        inventory[name] = counter; totals[name] = n; step += 1
    require(bool(inventory), 'no categories')
    if len(inventory) > 1:
        require(bool(lines), 'missing addition')
        m = re.fullmatch(r'Step (\d+): add them: (\d+(?: \+ \d+)+) = (\d+)\.', lines.pop(0))
        require(m is not None, 'missing or malformed addition')
        require(int(m[1]) == step and list(map(int, m[2].split(' + '))) == list(totals.values()), 'addition operands differ')
        require(int(m[3]) == sum(totals.values()) == int(answer), 'addition result differs')
        conclusion = f'So there are {answer} instances in total.'
    else:
        name, n = next(iter(totals.items()))
        conclusion = f'So there {"is" if n == 1 else "are"} {n} {name} {"instance" if n == 1 else "instances"}.'
    require(sum(totals.values()) == int(answer), 'inventory differs from answer')
    require(lines == [conclusion], 'conclusion differs or unexpected text')
    return inventory, totals
