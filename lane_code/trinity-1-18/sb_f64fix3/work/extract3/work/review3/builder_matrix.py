"""Review sb_f64rev2's pilot_gate_matrix.py controls, rerun against this workspace's kit/scripts/mem_pilot.py.
The three reviewer cases are unchanged; ceiling_violation is added. Fixtures are the reviewer's retained real encodes
(read-only); every write stays under this workspace. Usage: bash work/scripts/run_fix.sh work/review2/pilot_gate_matrix.py"""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
REV = Path('/scratch/jjyeung/orch_n30/sb_f64rev2')
N30 = Path('/scratch/jjyeung/orch_n30'); OUT = N30 / 'sb_f64fix3/out/fix3'
KIT = N30 / 'sb_f64fix3/kit'; CFG = KIT / 'configs/r1_config_f64.json'
sys.path[:0] = [str(KIT / 'scripts'), os.environ['F64_TREE']]


def guard(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)) and (args[2] or 0) & (
            os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
        if not Path(os.fsdecode(args[0])).absolute().is_relative_to(N30 / 'sb_f64fix3'):
            raise RuntimeError('write outside workspace: ' + os.fsdecode(args[0]))


sys.addaudithook(guard)
import token_audit as T  # noqa: E402
import mem_pilot as P  # noqa: E402
FIXTURE_SHA256 = {'complete_0.jsonl': '046f7985477bd6f808d3268aa8b31905b7b59af2baa2789b8fe21c548d38d4b5',
                  'complete_1.jsonl': 'd596db36a37ca06f341bf34af8899840a428acc7c4c6d7aea376db92636f1e59'}
paths = sorted((REV / 'tmp/dryrun').glob('token_audit_*/complete_*.jsonl')); assert len(paths) == 2
assert {p.name: T.file_sha256(p) for p in paths} == FIXTURE_SHA256, 'reviewer fixtures changed'
source = {str(p): T.file_sha256(p) for p in [Path(__file__), ROOT / 'run_cpu.sh', REV / 'pilot_gate_matrix.py', N30 / 'sb_f64fix2/work/review2/pilot_gate_matrix.py', N30 / 'sb_f64rev3/builder_matrix.py',
                                             CFG, KIT / 'scripts/token_audit.py', KIT / 'scripts/mem_pilot.py', *paths]}
records = {p: [json.loads(x) for x in p.read_text().splitlines()] for p in paths}
vqa_first = min(r['index'] for lines in records.values() for r in lines[1:-1] if r['stream'] == 'vqa')
required = dict(passing='accept', tripwire_only='accept', failed_check='refuse', ceiling_violation='refuse')
values = {}
for case in required:
    folder = ROOT / 'tmp/builder_matrix' / ('pilot_matrix_' + case); folder.mkdir(parents=True, exist_ok=False); generated = []
    for p, lines in records.items():
        identity = json.loads(json.dumps(lines[0]['identity'])); rows = [dict(r) for r in lines[1:-1]]
        if case == 'tripwire_only':
            identity['limits']['tripwire_tokens'] = 9200
            for r in rows: r['over_tripwire'] = r['tokens'] > 9200
        if case == 'failed_check':
            for r in rows:
                if r['stream'] == 'routing' and r['index'] == 0: r['check_row'] = 'ValueError: injected invalid row (synthetic control)'
        if case == 'ceiling_violation':
            for r in rows:
                if r['stream'] == 'vqa' and r['index'] == vqa_first: r['over_ceiling'] = True
        items = [((r['stream'], r['index']), (r['first_step'], r['rank'])) for r in rows]
        q = folder / p.name; T.write_shard(q, identity, lines[0]['shard']['index'], items, lambda part, sink: [sink(r) for r in rows]); generated.append(str(q))
    summary = T.summarize(generated, T.file_sha256(CFG)); q = folder / 'summary.json'; q.write_text(json.dumps(summary))
    try: P.check_audit(q, CFG); accepted = True; error = None
    except ValueError as e: accepted = False; error = str(e)
    values[case] = dict(pilot_accepted=accepted, launch_ready=summary['launch_ready'], errors=summary['errors'],
                        failed_rows=sum(v['failed'] for v in summary['streams'].values()),
                        over_ceiling_rows=sum(v['over_ceiling'] for v in summary['streams'].values()),
                        tripwire_rows=sum(v['over_tripwire'] for v in summary['streams'].values()),
                        longest_row_count=sum(len(v) for v in summary['longest'].values()),
                        required_behavior=required[case], met=accepted == (required[case] == 'accept'), error=error)
value = dict(command='bash run_cpu.sh builder_matrix.py',
             scope='Reviewer sb_f64rev2 synthetic controls from its retained real encode fixtures, plus ceiling_violation; '
                   'no production admission or GPU execution.',
             input_sha256=source, cases=values, all_required_behaviors_met=all(v['met'] for v in values.values()))
(OUT / 'builder_matrix.json').write_text(json.dumps(value, indent=2) + '\n'); print(json.dumps(values, indent=2))
sys.exit(0 if value['all_required_behaviors_met'] else 1)
