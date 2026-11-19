"""Pin local kit inputs and enumerate the union of first-seen counting sources."""
import collections, csv, hashlib, json, re, sqlite3
from pathlib import Path
from source_contract import sha, dump, encoded

ROOT = Path(__file__).resolve().parent
I = ROOT / 'inputs'
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
TREE = W / 'w19/work/tree_r1'
STORE_ROOT = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7')
STORE = STORE_ROOT / 'vqa/rows.sqlite'
STORE_SHA = '210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'

def main():
    pins = {}
    previous = json.loads((I / 'ROW_T_INPUTS.json').read_text())
    for name in ['split.json', 'reserve.json', 'aliases.json', 'build.json', 'visits.json',
                 'withheld.json', 'dev.json', 'bench.json', 'TREE_SEAL.json',
                 'wording_corpus.json', 'COVERAGE_V2_PUB.tar', 'coverage_rows_v2.py',
                 'check_cov_v2.py', 'R1_M200_TRACE_ANALYSIS_20261119.md']:
        digest = sha(I / name)
        assert digest == previous['pins'][name]['sha256'], name
        pins[name] = {'path': str(I / name), 'sha256': digest,
                      'cached_from': str(Path('/scratch/jjyeung/orch_n30/sb_rowT/inputs') / name)}
    for name, source in [('n.json', W / 'inputs/records/n.json'),
                         ('z.json', W / 'inputs/records/z.json'),
                         ('BUILD_MANIFEST.json', STORE_ROOT / 'BUILD_MANIFEST.json'),
                         ('FAMILY_INDEX_RANGES.json', STORE_ROOT / 'FAMILY_INDEX_RANGES.json'),
                         ('COUNTS_V7.json', STORE_ROOT / 'COUNTS_V7.json'),
                         ('EXCLUSIONS.json', STORE_ROOT / 'EXCLUSIONS.json')]:
        (I / name).write_bytes(source.read_bytes())
        pins[name] = {'path': str(source), 'sha256': sha(I / name)}
    assert sha(STORE) == STORE_SHA
    assert sha(W / 'w19/out/TREE_SEAL.json') == pins['TREE_SEAL.json']['sha256']
    pins['store'] = {'path': str(STORE), 'sha256': STORE_SHA}
    dependency = {k: v['sha256'] for k, v in pins.items()}
    dependency['prepare_inputs.py'] = sha(__file__)
    z = [json.loads(l) for l in (I / 'z.json').open() if l.strip()]
    zids = {r['row_key'] for r in z if r['reason'] == 'count_diag_first_seen_list_form'}
    cells = collections.Counter(); selected = collections.Counter(); overlap = collections.Counter()
    seen_z = set(); all_ids = []; facts = collections.defaultdict(dict); count = 0
    def fact(row, canonical, field):
        if not isinstance(canonical, str) or '/' not in canonical:
            return
        ds, scene = canonical.split('/', 1)
        native = {'scannetpp': 'scannetppv2'}.get(ds, ds)
        token = 'v' + hashlib.sha256(('rung1 scene ' + native + '/' + scene).encode()).hexdigest()[:12]
        if row.get('scene') == token:
            canonical = {'scannetppv2': 'scannetpp'}.get(ds, ds) + '/' + scene
            facts[row['dataset'] + '/' + token].setdefault(canonical, {'qid': row['qid'], 'field': field})
    con = sqlite3.connect(STORE.as_uri() + '?mode=ro', uri=True)
    with (I / 'source_rows.jsonl').open('w') as out, (I / 'SOURCE_SKIPS.jsonl').open('w') as skips:
        for raw, in con.execute('SELECT row FROM rows ORDER BY i'):
            row = json.loads(raw); count += 1
            all_ids.append([row['qid'], row.get('candidate_id')])
            for field, obj in [('provenance', row.get('provenance', {})),
                               ('retrace_a2', row.get('retrace_a2', {})), ('row', row)]:
                if obj.get('canonical'): fact(row, obj['canonical'], field + '.canonical')
                m = re.fullmatch(r'(scannet|scannetppv2|scannetpp|arkitscenes)__(.+)\.npz', obj.get('raster', ''))
                if m: fact(row, m[1] + '/' + m[2], field + '.raster')
            in_z = row['qid'] in zids
            if in_z: seen_z.add(row['qid'])
            if row.get('question_type') != 'object_counting' and not in_z: continue
            cell = row.get('question_type', '') + '|' + row.get('pool', '')
            cells[cell] += 1
            p = row.get('provenance', {})
            has_annotation = any(k in p for k in ('instances', 'total_categories')) or 'cited' in row.get('retrace_a2', {})
            has_list = bool(re.search(r'first (?:appears|appearance)|first-seen frame|by first appearance', row['target']))
            if in_z or has_annotation or has_list:
                out.write(raw + '\n'); selected[cell] += 1
                overlap['both' if in_z and (has_annotation or has_list) else 'z_only' if in_z else 'first_seen_only'] += 1
            else:
                skips.write(encoded({'old_qid': row['qid'], 'cell': cell,
                                     'reason': 'outside_first_seen_scope_no_instance_frames',
                                     'input_sha256': {'store': STORE_SHA, 'prepare_inputs.py': sha(__file__)}}) + '\n')
    con.close()
    assert count == 204413 and seen_z == zids
    assert all(len(v) == 1 for v in facts.values())
    dump(I / 'scene_facts.json', {'input_sha256': dependency, 'facts': facts,
                                'rule': 'Recorded canonical/raster field must reproduce the pinned rung1 scene-token hash.'})
    dump(I / 'source_ids.json', {'input_sha256': dependency, 'ids': all_ids})
    # Reuse the kit-wide wording extraction, verifying every contributing file.
    corpus = json.loads((I / 'wording_corpus.json').read_text())
    for path, digest in corpus['input_sha256'].items(): assert sha(path) == digest, path
    extra = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/vsti_rel_dev_r0/items.jsonl')
    corpus['input_sha256'][str(extra)] = sha(extra)
    def collect(value, location):
        if isinstance(value, dict):
            for key, item in value.items():
                if key.casefold() in ('question', 'question_text', 'prompt') and isinstance(item, str) and item.strip():
                    corpus['questions'].setdefault(item, []).append(location)
                elif isinstance(item, (dict, list)): collect(item, location)
        elif isinstance(value, list):
            for item in value: collect(item, location)
    for line in extra.open():
        if line.strip(): collect(json.loads(line), str(extra))
    corpus['searched_files'].append(str(extra))
    corpus['scope'] = 'All question/prompt fields in sealed W/w19 kit and fixtures JSON/JSONL/CSV, plus mirrored R0 VSTI items. Full external dev/benchmark corpora are not supplied.'
    dump(I / 'wording_corpus_expanded.json', corpus)
    for name in ['scene_facts.json', 'source_ids.json', 'source_rows.jsonl', 'SOURCE_SKIPS.jsonl', 'wording_corpus_expanded.json']:
        pins[name] = {'path': str(I / name), 'sha256': sha(I / name)}
    result = {'input_sha256': {k: v['sha256'] for k, v in pins.items()}, 'pins': pins,
              'tree': str(TREE), 'tree_sha256': json.loads((I / 'TREE_SEAL.json').read_text())['tree_sha256'],
              'store_rows': count, 'counting_cells': dict(cells), 'source_cells': dict(selected),
              'source_union': dict(overlap), 'z_list_qids': len(zids), 'prepare_script_sha256': sha(__file__),
              'wording_count': len(corpus['questions'])}
    dump(I / 'INPUTS.json', result)
    (ROOT / 'STATUS.md').write_text(f'Input stage complete: store v7 hash verified; {sum(selected.values()):,} first-seen source rows pinned, with {len(zids):,} z.json list qids accounted for. W/w19 seal and all wording contributors match their pins. The source census records every counting pool and all rows outside the first-seen scope. Conversion and validation are next.\n')
    print(json.dumps({k: result[k] for k in ('counting_cells', 'source_cells', 'source_union', 'z_list_qids', 'wording_count')}))

if __name__ == '__main__': main()
