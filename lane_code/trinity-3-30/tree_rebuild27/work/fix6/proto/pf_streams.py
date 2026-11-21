"""Proposed addition to the kit's b/pf.py (prototype, not sealed, not installed).

Before the long steps of mode q, apply prepare()'s receipt checks (carrier_c1_run.py lines 536-541)
to the stream receipts the config names, with the tree's own division_admits, against the division of
the pose stream. s1_admission's builders copy each receipt's division pin through unchanged (twins
receipt, build_stream, s1_routing.build), so a receipt that fails here fails prepare() about 95 minutes
later. The same function runs at kit build time on any CPU host that holds the receipts and the two
division files. Call it where pf.check is called, inside the same relocation scope."""


def check_streams(cfg):
    from student_pilot.p3_provenance import load, pinned
    from student_pilot.carrier_c1_run import division_admits
    from student_pilot import carrier_c1_routing as routing
    try:
        pose = load(pinned(cfg['streams']['pose']))
        division = pose['division'] if pose.get('schema') == 'c1-pose-mix-v1' and 'division' in pose else pose['inputs']['division']
        for name, pin in cfg['streams'].items():
            if name in ('pose', 'mdg'):
                continue
            receipt = load(pinned(pin))
            schema = routing.ROUTING_SCHEMA if name == 'routing' else 'c1-stream-v1'
            failed = [label for label, bad in (
                ('schema', receipt.get('schema') != schema),
                ('stream', receipt.get('stream') != name),
                ('division', not division_admits(receipt['division'], division)),
                ('heldout_overlap', receipt.get('heldout_overlap') != 0),
                ('gt_masks_only', name == 'pointing' and receipt.get('gt_masks_only') is not True)) if bad]
            if failed:
                raise ValueError(name + ':' + ','.join(failed))
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise ValueError('R1_STREAM_RECEIPT_WOULD_REFUSE:' + str(error)) from error
