"""Open, before the long steps, the two processor folders mode q reads.

The opener witness takes the folder of the model manifest's config.json pin; the forward takes the
root each model manifest names. Both must hold the processor files under their manifest names.

First, run the tree's own receipt predicates on the configured stream receipts, so that a receipt
the preparation would refuse is refused here, by name, before the long steps. After staging, frames()
checks one frame pin per stream source against the request's frame roots, and census() classifies the
first 100 rows of every stream source with the post-condition's classifier. audit_roots() names the
request's frame roots for the frame audit."""
from pathlib import Path


def audit_roots(roots):
    """The request's frame roots under the job folder's second name.

    The job folder is bound at the namespace (k/p.json), where the plan and the proof run and every
    reviewed path string is written, and at /tmp/jjyeung/<namespace without /tmp/>, the only name the
    tree's frame root map may target (orchard_paths.resolve_read). The frame audit compares resolved
    paths, so it gets each request root under the second name. A root that is not one real directory
    under both names refuses here, by name."""
    import os
    from z import load
    first = Path(load(Path(__file__).resolve().parents[1] / 'k/p.json')['namespace'])
    if first.parts[:2] != ('/', 'tmp') or len(first.parts) != 3 or first.name in ('jjyeung', '.', '..'):
        raise ValueError('E06')
    second = Path('/tmp/jjyeung') / first.name
    twins = []
    for root in roots:
        root = Path(root)
        if '..' in root.parts or root == first or not root.is_relative_to(first):
            raise ValueError('R1_FRAME_ROOT_NAME_REFUSED:' + str(root))
        twin = second / root.relative_to(first)
        try:
            one, two = os.stat(root), os.stat(twin)
        except OSError:
            raise ValueError('R1_FRAME_ROOT_MISSING:' + str(root)) from None
        if (not root.is_dir() or root.resolve() != root or twin.resolve() != twin
                or (one.st_dev, one.st_ino) != (two.st_dev, two.st_ino)):
            raise ValueError('R1_FRAME_ROOT_NAME_REFUSED:' + str(root))
        twins.append(str(twin))
    return twins


def receipts(cfg):
    """carrier_c1_run.prepare lines 536-541 on every non-pose stream receipt, against the run
    division (the pose mix division, or the pose preparation's inputs.division), and
    s1_routing._build line 229 (the routing receipt against the pointing receipt's division).
    Lines 543-547 read the pointing receipt that preparation rebuilds, not the configured one."""
    from student_pilot.p3_provenance import load, pinned
    from student_pilot.carrier_c1_run import division_admits
    from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
    streams = cfg['streams']
    pose = load(pinned(streams['pose']))
    division = pose.get('division') if pose.get('schema') == 'c1-pose-mix-v1' else pose['inputs']['division']
    if division is None:
        raise ValueError('R1_STREAM_RECEIPT_REFUSED:pose(division_unknown)')
    failed = []
    for name, pin in streams.items():
        if name in ('pose', 'mdg'):
            continue
        receipt = load(pinned(pin))
        schema = ROUTING_SCHEMA if name == 'routing' else 'c1-stream-v1'
        parts = dict(schema=receipt.get('schema') != schema, stream=receipt.get('stream') != name,
                     division=not division_admits(receipt['division'], division),
                     heldout_overlap=receipt.get('heldout_overlap') != 0,
                     gt_masks_only=name == 'pointing' and receipt.get('gt_masks_only') is not True)
        bad = [k for k, v in parts.items() if v]
        if bad:
            failed.append(name + '(' + ','.join(bad) + ')')
    if 'routing' in streams and 'pointing' in streams:
        legacy = load(pinned(streams['routing']))
        if not division_admits(legacy['division'], load(pinned(streams['pointing']))['division']):
            failed.append('routing(s1_routing_division)')
    if failed:
        raise ValueError('R1_STREAM_RECEIPT_REFUSED:' + ';'.join(failed))


def frames(cfg, roots):
    """s1_admission.FrameAudit.keep on one frame pin per stream source, right after staging: the pin
    resolves through the tree's resolve_read (the frame root map) to a file under one of the request's
    frame roots, named as the frame audit gets them (audit_roots), or the job refuses here, by name,
    instead of in the frame audit after preparation."""
    import json
    import sqlite3
    from student_pilot.orchard_paths import resolve_read
    from student_pilot.r1_persisted import relocated
    resolved = [Path(root).resolve() for root in audit_roots(roots)]
    if not resolved or any(not root.is_dir() for root in resolved):
        raise ValueError('R1_FRAME_ROOT_MISSING:' + ','.join(str(root) for root in resolved))
    def read(pin):
        return json.loads(Path(relocated(pin)).read_text())
    sources = []
    for name, pin in sorted(cfg['streams'].items()):
        if name == 'mdg':
            continue
        value = read(pin)
        if value.get('schema') == 'c1-pose-mix-v1':
            # The mix keeps only rows whose frames all start with the source's frame_prefix
            # (c1_pose_mix._row_selected), so the sample row is taken from those.
            sources += [(name + '/' + str(i), part['receipt'], part.get('frame_prefix'))
                        for i, part in enumerate(value['sources']) if part.get('kind') == 'rows']
        else:
            sources.append((name, pin, None))
    checked = {}
    for label, pin, prefix in sources:
        database = Path(relocated(read(pin)['database']))
        if not database.is_file():
            raise ValueError('R1_FRAME_PREFLIGHT_DATABASE_MISSING:' + label)
        pins = None
        with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
            for (text,) in connection.execute('SELECT row FROM rows ORDER BY i LIMIT 50000'):
                found = json.loads(text).get('student_input', {}).get('frames')
                if (isinstance(found, list) and found and all(isinstance(f, dict) and isinstance(f.get('path'), str)
                                                             for f in found)
                        and (prefix is None or all(f['path'].startswith(prefix) for f in found))):
                    pins = found
                    break
        if not pins:
            raise ValueError('R1_FRAME_PIN_MISSING:' + label)
        path = resolve_read(pins[0]['path']).resolve()
        if not any(path.is_relative_to(root) for root in resolved) or not path.is_file():
            raise ValueError('R1_FRAME_ROOT_REFUSED:%s:%s' % (label, path))
        checked[label] = str(path)
    census(cfg)
    return checked


def census(cfg, limit=100):
    """The post-condition's classifier (b/sv.py, which b/cs.py runs on every admitted row after the
    forward) on the first `limit` rows of each stream source right after staging, pose rows taken among
    those the mix selects: a row it cannot place refuses here, by name. Flags are not judged here."""
    import json
    import sqlite3
    from student_pilot.r1_persisted import relocated
    from sv import classifier
    classify = classifier(cfg)
    def read(pin):
        return json.loads(Path(relocated(pin)).read_text())
    counts = {}
    for name, pin in sorted(cfg['streams'].items()):
        if name == 'mdg':
            continue
        value = read(pin)
        parts = ([(name + '/' + str(i), part['receipt'], part.get('frame_prefix'))
                  for i, part in enumerate(value['sources']) if part.get('kind') == 'rows']
                 if value.get('schema') == 'c1-pose-mix-v1' else [(name, pin, None)])
        for label, receipt, prefix in parts:
            database = Path(relocated(read(receipt)['database']))
            seen = 0
            with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
                for (text,) in connection.execute('SELECT row FROM rows ORDER BY i'):
                    row = json.loads(text)
                    frames = (row.get('student_input') or {}).get('frames') or []
                    if prefix is not None and not (frames and all(isinstance(f, dict) and str(f.get('path', '')).startswith(prefix)
                                                                  for f in frames)):
                        continue
                    try:
                        classify(row, name)
                    except ValueError as error:
                        raise ValueError('R1_CENSUS_PREFLIGHT_REFUSED:%s:row%d:%s' % (label, seen, error)) from error
                    seen += 1
                    if seen >= limit:
                        break
            if not seen:
                raise ValueError('R1_CENSUS_PREFLIGHT_NO_ROWS:' + label)
            counts[label] = seen
    return counts


def check(cfg, manifest_pin):
    receipts(cfg)
    from student_pilot.p3_provenance import load, pinned, sha256
    from student_pilot.decoupled_v_run import processor_for
    from student_pilot.mdg_parent import model_pin
    from launch_r1.p_opener_witness import prepared_vocabulary
    try:
        prepared_vocabulary(load(pinned(cfg['r1_training']['p_run']['config'])))
        pins = {pin['sha256']: pin for pin in (manifest_pin, model_pin(cfg))}
        for pin in pins.values():
            manifest = load(pinned(pin))
            root = Path(manifest['root'])
            for name, expected in manifest['files'].items():
                small = name.endswith(('.json', '.txt', '.jinja', '.model'))
                if Path(name).name != name or not (root/name).is_file() or small and sha256(root/name) != expected:
                    raise ValueError('file missing or changed: ' + name)
            processor_for(str(root))
    except (ValueError, KeyError, TypeError, OSError, RuntimeError, ImportError) as error:
        raise ValueError('R1_PROCESSOR_FOLDER_UNUSABLE:' + type(error).__name__ + ':' + str(error)) from error
