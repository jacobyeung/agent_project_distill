"""Publish native scene evidence and count the prepared native row selection."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from z import load


def publish(kit, root, cfg, job):
    from rv import location, put, encoded
    from student_pilot.p3_provenance import pinned, file_pin
    from student_pilot.carrier_c1_run import Rows
    from student_pilot.s1_exclusions import Exclusions
    from student_pilot.r1_rooms import Rooms
    from student_pilot.r2_withheld import Withheld, room
    live, _ = location(Path(kit), Path(root), job)
    rule = Exclusions(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions'])
    rooms = Rooms(cfg['r1_training']['room_authority'])
    withheld = Withheld()
    rp = pinned(cfg['r2_scene_rebuild'])
    cp = pinned(cfg['scene_coverage']['reference'])
    payload = {'s0.json':rp.read_bytes(), 's1.json':cp.read_bytes()}
    counts = {s:dict.fromkeys(('benchmark','dev','R0','withheld','K1_heldout','admitted'),0)
              for s in ('pose','vqa','routing','pointing')}
    def emit(status):
        payload['s2.json'] = encoded(dict(status=status, counts=counts,
            receipt=dict(file='s0.json',sha256=file_pin(rp)['sha256']),
            coverage=dict(file='s1.json',sha256=file_pin(cp)['sha256']),
            scene_coverage=cfg['scene_coverage'], files=rule.files,
            authority=cfg['r1_training']['room_authority'], withheld_sha256=__import__('student_pilot.r2_withheld',fromlist=['SHA256']).SHA256,
            counts_scope='native prepared Rows selection; statuses can overlap'))
        if sum(map(len,payload.values())) >= 1_000_000:
            raise ValueError('R1_SCENE_EVIDENCE_TOO_LARGE')
        for name,raw in payload.items():put(live/name,raw)
    reader = Rows(load(pinned(cfg['preparation'])), None)
    try:
        for stream in counts:
            for i in range(reader.count(stream)):
                row,_ = reader.row(stream,i)
                match=rule.matches(row)
                status,_,_=rooms.status(row)
                if status=='unresolved':
                    emit('REFUSE');raise ValueError('R1_SCENE_STATUS_UNRESOLVED')
                flags=dict(benchmark=match['benchmark'],dev=match['dev'],R0=status=='r0',
                    withheld=any(room(x) in withheld.aliases for x in rule.identifiers(row)),K1_heldout=status=='k1_heldout')
                counts[stream]['admitted']+=1
                for name,hit in flags.items():counts[stream][name]+=int(hit)
                if any(flags.values()):
                    emit('REFUSE');raise ValueError('R1_SCENE_PROTECTED_ADMITTED_ROWS')
    finally:reader.close()
    emit('PASS')
    return counts
