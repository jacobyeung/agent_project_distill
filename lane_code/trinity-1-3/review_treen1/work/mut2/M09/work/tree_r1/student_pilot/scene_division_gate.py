"""CPU input gate for every bound VQA and routing scene."""
from .p3_provenance import load, pinned


def check_rows(rows, division_pin, *, removals=None, scene_filter=None, stream='vqa'):
    division = load(pinned(division_pin))
    train, heldout = set(division['train_scenes']), set(division['heldout_scenes'])
    counts = dict(read=0, filtered=0, removed=0, outside=0, heldout=0, admitted=0)
    seen = set()
    for row in rows:
        counts['read'] += 1
        if scene_filter is not None and not scene_filter.keep(row, stream):
            counts['filtered'] += 1
            continue
        if removals is not None and not removals.keep(row):
            counts['removed'] += 1
            continue
        scene = row['dataset']+'/'+row['scene']
        counts['outside'] += scene not in train
        counts['heldout'] += scene in heldout
        if row['qid'] in seen:
            raise ValueError('SCENE_GATE_DUPLICATE_QID')
        seen.add(row['qid'])
        counts['admitted'] += scene in train and scene not in heldout
    if counts['heldout']:
        raise ValueError('SCENE_DIVISION_REFUSED:'+str(counts))
    return counts


def check_bound(cfg):
    """Read existing stores without creating a new store or changing any predicate."""
    import json, sqlite3
    from .row_removals import Removals
    from .s1_exclusions import Exclusions
    rule = Exclusions(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions'])
    results = {}
    for stream in ('vqa', 'routing'):
        source = cfg['streams'][stream]
        receipt = load(pinned(source))
        database = pinned(receipt['database'])
        conn = sqlite3.connect(database.as_uri()+'?mode=ro', uri=True)
        try:
            rows = (json.loads(row) for row, in conn.execute('SELECT row FROM rows ORDER BY i'))
            results[stream] = check_rows(rows, cfg['scene_division'], removals=Removals(cfg.get('remove_files', [])),
                scene_filter=rule, stream=stream)
        finally:
            conn.close()
    return results
