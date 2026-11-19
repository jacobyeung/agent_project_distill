"""Recount source identities and emitted inventories independently of the generator."""
import argparse, collections, copy, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
I = ROOT / 'inputs'
sys.dont_write_bytecode = True

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4194304), b''): h.update(block)
    return h.hexdigest()

def load(path): return json.loads(Path(path).read_text())
def rows(path):
    with Path(path).open() as f:
        for line in f:
            if line.strip(): yield json.loads(line)
def need(value, message):
    if not value: raise ValueError(message)

def audit(out, form):
    manifest = load(I / 'INPUTS.json'); pins = manifest['pins']
    sys.path.insert(0, manifest['tree'])
    from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
    from student_pilot.r1_rooms import Rooms
    from student_pilot.s1_exclusions import Exclusions
    rooms = Rooms({k: {'path': str(I / (k + '.json')), 'sha256': pins[k + '.json']['sha256']}
                   for k in ('split', 'reserve', 'aliases', 'build', 'visits')})
    ex = Exclusions({'path': str(I / 'dev.json'), 'sha256': pins['dev.json']['sha256']},
                    {'path': str(I / 'bench.json'), 'sha256': pins['bench.json']['sha256']})
    facts = load(I / 'scene_facts.json')['facts']; withheld = set(load(I / 'withheld.json')['rooms'])
    source = {r['qid']: r for r in rows(I / 'source_rows.jsonl')}
    mappings = list(rows(out / 'QID_MAP.jsonl')); by_new = {m['new_qid']: m for m in mappings}
    refusal = list(rows(out / 'REFUSALS.jsonl')); refused = {m['old_qid'] for m in refusal}
    all_old = load(I / 'source_ids.json')['ids']; oldids = {r[0] for r in all_old}; oldcids = {r[1] for r in all_old if r[1]}
    z = {r['row_key'] for r in rows(I / 'z.json')}; n = {r['row_key'] for r in rows(I / 'n.json')}
    qids = set(); cids = set(); used = set(); histogram = collections.Counter(); cell_counts = collections.Counter()
    repeats = 0; entry_total = 0; annotation_total = 0
    for row in rows(out / 'rows.jsonl'):
        m = by_new[row['qid']]; original = source[m['old_qid']]; note = row['provenance']['sb_rowF']
        need(m['old_qid'] not in used and m['old_qid'] not in refused, 'source repeated or refused')
        used.add(m['old_qid'])
        need(row['qid'] not in qids and row['qid'] not in oldids, 'duplicate or reused qid')
        need(row['candidate_id'] not in cids and row['candidate_id'] not in oldcids, 'duplicate or reused candidate')
        qids.add(row['qid']); cids.add(row['candidate_id'])
        recovered = copy.deepcopy(row)
        for key in ('qid', 'target', 'candidate_id'):
            if key in original: recovered[key] = original[key]
            else: recovered.pop(key, None)
        recovered['provenance'].pop('sb_rowF')
        need(recovered == original, 'unexpected source field difference')
        expected_record = {'qid': row['qid'], 'scene': original['scene'],
                           'frame_indices': original['student_input']['frame_indices'], 'type': original['question_type'],
                           'question': original['student_input']['question'], 'options': original['student_input']['options'],
                           'trace_revision': 'sb_rowF-v1-' + form}
        need(note['candidate_identity_record'] == expected_record, 'candidate payload differs')
        need(row['candidate_id'] == candidate_identity(expected_record), 'candidate formula differs')
        need(row['qid'] == 'sb_rowF_' + form + '_' + hashlib.sha256(m['old_qid'].encode()).hexdigest()[:24], 'qid mapping differs')
        canonical = rooms.canonical(original)[0]
        if canonical is None:
            candidates = facts[original['dataset'] + '/' + original['scene']]
            need(len(candidates) == 1, 'canonical ambiguity'); canonical = next(iter(candidates))
        physical = rooms.room(canonical)
        need(canonical == note['canonical'] == m['canonical'] and physical == note['physical_room'] == m['physical_room'], 'canonical mismatch')
        probe = dict(original, canonical=canonical, physical_group=physical)
        need(rooms.status(probe)[0] == 'ok' and physical not in withheld and not ex.excluded(probe), 'excluded room emitted')
        # Recover names and frame occurrences from the source header independently.
        source_inventory = {}; source_order = []
        for line in original['target'].replace('\\n', '\n').splitlines():
            if ': frame ' not in line: continue
            header, body = line.rsplit(': ', 1)
            matched = re.search(r'(?:list each distinct (.+?) once, by the frame where it first appears|locate each distinct (.+?) at its first appearance|list the distinct (.+?) instances by first appearance|find each distinct (.+?), using its first-seen frame)$', header)
            need(matched is not None, 'unknown source category header')
            name = next(s for s in matched.groups() if s is not None)
            need(name not in source_inventory and name in original['student_input']['question'], 'source category differs')
            items = re.findall(r'frame (\d+)(?: \((left|middle|right)\))?', body)
            source_inventory[name] = collections.Counter((int(f), region or '') for f, region in items)
            source_order.append(name)
        need(set(m['category_totals']) == set(source_inventory), 'mapping category differs')
        # Count annotated IDs; the output text and stored answer do not define GT.
        provenance = original['provenance']; annotated = {}; identities = {}; annotated_regions = {}
        if 'total_categories' in provenance:
            for cat in provenance['total_categories']:
                annotated[cat['name']] = collections.Counter(cat['frames']); identities[cat['name']] = cat['ids']
        elif 'instances' in provenance:
            need(len(source_order) == 1, 'single instances on multiple categories'); name = source_order[0]
            annotated[name] = collections.Counter(x['frame'] for x in provenance['instances'])
            identities[name] = [x['id'] for x in provenance['instances']]
            annotated_regions[name] = collections.Counter((x['frame'], x['region']) for x in provenance['instances'])
        elif 'cited' in original.get('retrace_a2', {}):
            need(len(source_order) == 1, 'single cited map on multiple categories'); name = source_order[0]
            cited = original['retrace_a2']['cited']; identities[name] = list(cited); annotated[name] = collections.Counter(cited.values())
        else: raise ValueError('independent annotation absent')
        need(set(annotated) == set(source_inventory), 'annotation categories differ')
        for name, ids in identities.items():
            need(len(ids) == len(set(ids)) == sum(annotated[name].values()), 'annotation duplicate IDs or length mismatch')
            need(all(type(f) is int and 1 <= f <= 32 for f in annotated[name]), 'annotation frames not sampled indices')
        expected_answer = sum(map(len, identities.values()))
        need(expected_answer == int(original['answer']) == int(row['answer']), 'independent GT mismatch')
        actual = {}; declared = {}; category_lines = []; step_numbers = []
        for line in row['target'].splitlines():
            if line.startswith('Step '): step_numbers.append(int(re.match(r'Step (\d+):', line)[1]))
            if not line.startswith('Step ') or ': add them:' in line: continue
            if form == 'B':
                head = re.fullmatch(r'Step \d+: I count (\d+) distinct (.+) instances?, each by the frame where it first appears: (.*)\.', line)
                need(head is not None, 'bad B header'); name = head[2]; announced = int(head[1]); body = head[3]
                entries = [] if body == 'none' else body.split('; ')
                need(len(entries) == announced, 'B announced count differs')
                inventory = collections.Counter()
                for index, entry in enumerate(entries, 1):
                    part = re.fullmatch(r'(\d+) of (\d+), frame (\d+)(?: \((left|middle|right)\))?', entry)
                    need(part is not None and int(part[1]) == index and int(part[2]) == announced, 'B ordinals/denominator differ')
                    frame = int(part[3]); need(1 <= frame <= 32, 'B frame outside range')
                    inventory[(frame, part[4] or '')] += 1
            else:
                head = re.fullmatch(r'Step \d+: (.+?): (.*), total (\d+)\.', line)
                need(head is not None, 'bad A header'); name = head[1]; body = head[2]; announced = int(head[3])
                entries = [] if body == 'none' else body.split('; '); inventory = collections.Counter(); last = 0
                for entry in entries:
                    part = re.fullmatch(r'frame (\d+): (\d+)(?: \((.*)\))?', entry)
                    need(part is not None, 'A entry syntax'); frame, value = int(part[1]), int(part[2])
                    need(last < frame <= 32 and value > 0, 'A frame order/range or count'); last = frame
                    if part[3]:
                        tags = re.findall(r'(left|middle|right): (\d+)', part[3]); need(len(tags) == len(set(k for k, _ in tags)), 'A region repeats')
                        need(sum(int(v) for _, v in tags) == value, 'A region sum differs')
                        for region, count in tags: inventory[(frame, region)] += int(count)
                    else: inventory[(frame, '')] = value
                need(sum(inventory.values()) == announced, 'A tally differs')
            need(name not in actual, 'output repeats category'); actual[name] = inventory; declared[name] = announced; category_lines.append(name)
        need(category_lines == source_order, 'category order changed')
        need(step_numbers == list(range(1, len(step_numbers) + 1)), 'step numbering differs')
        need(actual == source_inventory, 'source frame/region multiplicities changed')
        for name, inventory in actual.items():
            frame_counts = collections.Counter()
            for (frame, region), count in inventory.items(): frame_counts[frame] += count
            need(frame_counts == annotated[name], 'output differs from annotated frames')
            if name in annotated_regions: need(inventory == annotated_regions[name], 'output differs from annotated regions')
            need(declared[name] == len(identities[name]) == m['category_totals'][name], 'category count differs')
            repeats += int(any(count > 1 for count in inventory.values())); entry_total += sum(inventory.values())
        annotation_total += expected_answer
        need(sum(declared.values()) == expected_answer, 'total differs')
        if len(source_order) > 1:
            addition = re.search(r'add them: (\d+(?: \+ \d+)+) = (\d+)\.', row['target'])
            need(addition is not None and list(map(int, addition[1].split(' + '))) == [declared[k] for k in source_order], 'addition operands differ')
            need(int(addition[2]) == expected_answer, 'addition result differs')
        need(row['target'].endswith('\n</think>\n\n' + str(expected_answer)), 'final answer differs')
        histogram[min(expected_answer, 10)] += 1; cell_counts[m['cell']] += 1
    need(used | refused == set(source) and not used & refused, 'incomplete source accounting')
    need(len(refused) == len(refusal) and len(by_new) == len(mappings) == len(qids), 'duplicate mapping/refusal')
    need(dict(cell_counts) == load(I / 'EXPECTED_CELLS.json')['eligible_cells'], 'exact cell counts differ')
    hist_expected = {str(k) if k < 10 else '10+': histogram[k] for k in range(11)}
    need(hist_expected == load(out / 'TRUTH_HISTOGRAM.json')['converted'], 'histogram mismatch')
    remove = list(rows(out / 'REMOVE.json'))
    need({r['row_key'] for r in remove} == used - z - n, 'REMOVE set differs')
    need(len(remove) == len({r['row_key'] for r in remove}), 'duplicate removal')
    for r in remove:
        need(set(r) == {'pool', 'question_type', 'reason', 'row_key', 'scene'}, 'REMOVE schema differs from n.json')
        s = source[r['row_key']]
        need(r['pool'] == s['pool'] and r['question_type'] == s['question_type'] and r['scene'] == s['dataset'] + '/' + s['scene'], 'REMOVE metadata mismatch')
    checks = {'status': 'PASS', 'form': form, 'rows': len(qids), 'refusals': len(refused),
              'additional_removals': len(remove), 'instance_entries': entry_total,
              'independent_annotated_id_count': annotation_total, 'categories_with_shared_frame_region': repeats,
              'counts_per_cell': dict(cell_counts), 'truth_histogram': hist_expected,
              'verified': ['source partition', 'source used once', 'fresh unique qids and candidates', 'kit candidate formula',
                           'only allowed fields changed', 'independent annotated IDs and frames', 'source region preservation',
                           'frame indices 1..32', 'numbered B entries or strictly increasing A frames', 'category and final sums',
                           'room exclusions', 'exact census cells', 'minimal N-format removal delta'],
              'input_sha256': {name: sha(out / name) for name in ('rows.jsonl', 'QID_MAP.jsonl', 'REFUSALS.jsonl', 'REMOVE.json', 'TRUTH_HISTOGRAM.json')},
              'source_input_sha256': {name: sha(I / name) for name in ('INPUTS.json', 'source_rows.jsonl', 'EXPECTED_CELLS.json', 'scene_facts.json',
                  'source_ids.json', 'split.json', 'reserve.json', 'aliases.json', 'build.json', 'visits.json', 'withheld.json', 'dev.json', 'bench.json', 'n.json', 'z.json')},
              'auditor_sha256': sha(__file__)}
    (out / 'INDEPENDENT_CHECKS.json').write_text(json.dumps(checks, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k: checks[k] for k in ('status', 'form', 'rows', 'refusals', 'additional_removals', 'instance_entries')}))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default='out'); ap.add_argument('--form', choices=('A', 'B'), default='B')
    args = ap.parse_args(); path = (ROOT / args.out).resolve(); need(path.is_relative_to(ROOT), 'outside workspace'); audit(path, args.form)
