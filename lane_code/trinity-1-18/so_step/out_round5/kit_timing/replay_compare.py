"""Accept OFF, OFF, ON replays only with matched state, CPU inputs and switch provenance."""
import argparse
import json
import math
from pathlib import Path
import struct
import sys


def replay_order():
    return [('off1','off'), ('off2','off'), ('on','prefetch')]


def loss_acceptance(off1, off2, on):
    finite = bool(off1) and len(off1) == len(off2) == len(on) and all(
        math.isfinite(x) for values in (off1,off2,on) for x in values)
    bits = lambda values: b''.join(struct.pack('!d', x) for x in values)
    stable = finite and bits(off1) == bits(off2)
    spread = [abs(a-b) for a,b in zip(off1,off2)]
    # Fixed before observing ON: pool the absolute differences within each rank.
    # Two OFF draws cannot estimate a calibrated confidence interval.
    off_max = max(spread, default=0.)
    on_max = max((max(abs(c-a),abs(c-b)) for a,b,c in zip(off1,off2,on)), default=0.)
    threshold = 2. * off_max
    accepted = finite and (bits(on) == bits(off1) if stable else on_max <= threshold)
    return dict(accepted=accepted, off_repeats_bitwise=stable, off_spread=spread,
                off_max_abs=off_max, on_max_abs=on_max, multiplier=2., threshold=threshold,
                on_minus_off1=[c-a for a,c in zip(off1,on)],
                rule='bitwise' if stable else 'per-rank max ON-to-either-OFF <= 2 * max OFF-to-OFF')


def losses(record):
    result=[]
    for key in ('components','stream_means'):
        result.extend(record[key][k] for k in sorted(record[key]))
    result.extend(record['first_step_micro_losses'])
    return result


def compare(output, audit_dir):
    from row_hash import compare_rows
    report = dict(accepted=True, order=[name for name,_ in replay_order()], ranks=[])
    for rank in range(4):
        manifests=[]; records=[]
        for name,arm in replay_order():
            folder=output/name/f'rank{rank}'
            manifest=json.loads((folder/'manifest.json').read_text())
            steps=json.loads((folder/'steps.json').read_text())
            progress=json.loads((folder/'progress.json').read_text())
            if progress['stage'] != 'complete' or len(steps) != 1 or manifest['arm'] != arm:
                raise ValueError('Need three completed one-step replays in OFF, OFF, ON order')
            manifests.append(manifest); records.append(steps[0])
        for m in manifests[1:]:
            for key in ('start_step','resume','trainables','config_sha256','binding','threads'):
                if m[key] != manifests[0][key]:
                    raise ValueError('Replay state differs: '+key)
        if any(r['plan_sha256'] != records[0]['plan_sha256'] or r['step'] != records[0]['step'] for r in records):
            raise ValueError('Replay row plan or step differs')
        for r in records[1:]:
            if r['components'].keys() != records[0]['components'].keys() or r['stream_means'].keys() != records[0]['stream_means'].keys():
                raise ValueError('Loss field names differ')
        for i, r in enumerate(records):
            expected=manifests[i]['switches']
            performance=r.get('performance', {})
            for key,value in expected.items():
                if performance.get(key,'0') != value:
                    raise ValueError('Step performance provenance differs: '+key)
        if records[2].get('performance',{}).get('C1_CPU_PREFETCH') != '1':
            raise ValueError('ON replay did not record C1_CPU_PREFETCH=1')
        if any(m['switches']['C1_CPU_PREFETCH'] != flag for m,flag in zip(manifests,('0','0','1'))):
            raise ValueError('Replay switches are not OFF, OFF, ON')
        if len({m['switches']['C1_BATCH_METRICS'] for m in manifests}) != 1:
            raise ValueError('Hold 03 constant across replays')
        for arm in ('off','prefetch'):
            path=audit_dir/f'data_{arm}_rank{rank}.json'
            data=json.loads(path.read_text())
            meta=json.loads(Path(str(path)+'.manifest.json').read_text())
            if (len(data) != 10 or meta['start_step'] != manifests[0]['start_step'] or meta['resume'] != manifests[0]['resume']
                    or meta['config_sha256'] != manifests[0]['config_sha256']
                    or data[0]['plan_sha256'] != records[0]['plan_sha256']
                    or meta['rank'] != rank or meta['world_size'] != 4 or meta['plans_checked'] != 10
                    or not meta['coverage_required'] or not meta['augmented_pose_rows']
                    or not meta.get('grid_rows',0)
                    or (arm == 'prefetch' and not any(n.startswith('c1-row-cpu')
                        for n in meta.get('augmentation_threads',[])))
                    or meta['peak_group_tensor_bytes'] > meta['group_budget_bytes']
                    or not all(r['global_rng_unchanged'] for r in data)):
                raise ValueError('CPU audit does not cover the admitted continuation')
            if arm == 'off':
                reference = data
            else:
                compare_rows(reference,data)
        result=loss_acceptance(*(losses(r) for r in records))
        report['ranks'].append(dict(rank=rank, **result))
        report['accepted'] &= result['accepted']
    (output/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n')
    if not report['accepted']:
        raise ValueError('ON loss exceeds the fixed replay bound; keep prefetch OFF')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--audit-dir',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(compare(args.out,args.audit_dir),indent=2))


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit_profile'))
    from privacy import filter_streams
    filter_streams()
    main()
