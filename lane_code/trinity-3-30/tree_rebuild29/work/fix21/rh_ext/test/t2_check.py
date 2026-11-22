"""Checks of test 2: t2_check.py <out> <kit>. Prints one JSON verdict with the evidence."""
import base64, hashlib, json, sys, tarfile
from pathlib import Path

out, kit = Path(sys.argv[1]), Path(sys.argv[2])


def read(p):
    v = json.loads(Path(p).read_text())
    return json.loads(base64.b64decode(v['payload'])) if 'payload' in v else v


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def lines(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


policy = read(kit / 'k/n.json')['checkpoint_disk_guard']
ranks = [json.loads(p.read_text()) for p in sorted(out.glob('t2_rank*.json'))]
ev0 = lines(out / 'log/ev_rank0.jsonl')
guards = [r for r in ev0 if r['kind'] == 'DISK_GUARD']
sink = out / 'sink'
files = {str(p.relative_to(out)): p.stat().st_size for p in sorted(out.rglob('*')) if p.is_file()}
states = sorted(sink.glob('checkpoint_*/complete.json'))
exports = sorted(sink.glob('m*/artifact.json'))
receipts = sorted((sink / 'persist').glob('*.local.json'))
archives = []
for r in receipts:
    v = json.loads(r.read_text())
    a = Path(v['archive']['path'])
    with tarfile.open(a) as t:
        members = sorted(m.name for m in t.getmembers())
    src = Path(v['source']['path']).parent
    archives.append(dict(receipt=str(r.relative_to(out)), kind=v['kind'], durable=v['durable'], parts=v['parts'],
                         archive=str(a.relative_to(out)), archive_bytes=a.stat().st_size, archive_sha_ok=sha(a) == v['archive']['sha256'],
                         members_equal_source=members == sorted(str(p.relative_to(src)) for p in src.rglob('*') if p.is_file())))
plan = json.loads((out / 'log/plan.json').read_text()) if (out / 'log/plan.json').exists() else {}
up_records = sorted(str(p.relative_to(sink / 'up')) for p in (sink / 'up').rglob('*.part*.json'))
checks = {
    'ranks_pass': all(r.get('status') == 'PASS' for r in ranks),
    'one_checkpoint': len(states) == 1,
    'one_export': len(exports) == 1,
    'archive_copy_of_each': sorted(a['kind'] for a in archives) == ['checkpoint', 'export'] and all(a['archive_sha_ok'] and a['members_equal_source'] for a in archives),
    'local_only_no_parts': all(a['durable'] is False and a['parts'] == [] for a in archives),
    'guard_called_for_both_with_job_policy': [g['write'] for g in guards if 'refused' not in g][:2] == ['checkpoint', 'export']
        and all(g['policy'] == {**policy} for g in guards if 'refused' not in g),
    'guard_refuses_impossible_plan': all('Insufficient checkpoint disk space' in r.get('refusal', '') for r in ranks)
        and not list((out / 'sink_refuse').glob('checkpoint_*')),
    'export_reloads': ranks[0].get('reload', {}).get('finite') is True,
    'planner_pass': plan.get('status') == 'PASS' and all(plan.get('sent', {}).values()) and len(plan.get('sent', {})) == 2,
    'planner_local_only': not plan.get('network_events') and not plan.get('foreign_spawn') and not plan.get('outside_run')
        and all(p.startswith(str(out) + '/') for p in plan.get('receipt_paths', []) if p),
    'planner_records_8_parts': len(up_records) == 8,
    'planner_netns_loopback_only': plan.get('network_devices') == ['lo'],
}
print(json.dumps(dict(world=len(ranks), persist_seconds={r['stage']: r['seconds'] for r in ev0 if r['kind'] == 'END' and r.get('stage', '').startswith(('save_', 'persist_'))}, verdict='PASS' if all(checks.values()) else 'FAIL', checks=checks,
    guards=[{k: g.get(k) for k in ('write', 'required_bytes', 'available_bytes', 'margin_bytes', 'state_tensor_bytes', 'export_tensor_bytes',
             'state_bytes', 'export_bytes', 'remaining_full_states', 'remaining_weight_exports', 'retained_archive_bytes', 'policy', 'completed', 'refused')} for g in guards],
    refusal=ranks[0].get('refusal'), reload=ranks[0].get('reload'), archives=archives,
    planner={k: plan.get(k) for k in ('status', 'network_devices', 'seconds', 'sent', 'order', 'receipt_paths', 'network_events', 'spawned', 'foreign_spawn', 'outside_run', 'session_labels')},
    planner_state={k: v for k, v in plan.get('state', {}).items()}, up_records=up_records,
    files_written=files, bytes_written=sum(files.values()), errors=[r.get('error') for r in ranks if r.get('error')]), indent=1, default=str))
