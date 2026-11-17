"""Run full families sequentially and retain compact authenticated returns."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import trinity_read as T
from records import write


def run(config):
    root = Path(config['spec']['run'])
    root.mkdir(parents=True)
    (root/'logs').mkdir(); (root/'metadata').mkdir()
    T.dump(root/'SPEC.json', config['spec'])
    T.dump(root/'metadata/ADMISSION.json', config['admission'])
    started = time.monotonic(); summaries = {}; values = []
    try:
        for family in config['families']:
            command = [config['spec']['interpreters']['vllm'], '-B', str(HERE/'worker.py'),
                       '--config', os.environ['A_JOB_CONFIG'], '--family', family]
            # Encode engine diagnostics before they reach a log line. Output
            # records retain exact answers and IDs in the data packet.
            with (root/'logs'/(family+'.hex')).open('x') as log:
                proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                for chunk in iter(lambda: proc.stdout.read(65536), b''):
                    log.write(chunk.hex()+'\n')
                proc.stdout.close()
                code = proc.wait()
            if code:
                raise RuntimeError('Family process failed: '+family+' '+str(code))
            summaries[family] = T.load(root/family/'COMPLETE.json')
            with (root/family/'ITEMS.jsonl').open() as stream:
                values.extend(json.loads(line) for line in stream)
        write(root/'ITEMS.jsonl', values)
        report = dict(step=config['spec']['step'], budget=2048, items=len(values),
                      families=summaries, seconds=time.monotonic()-started, complete=True)
        report['scores'] = {f: {t: dict(items=len(rs), score_pct=100*sum(r['score'] for r in rs)/len(rs))
            for t in sorted({r['task_type'] for r in values if r['family']==f})
            for rs in [[r for r in values if r['family']==f and r['task_type']==t]]} for f in config['families']}
        if 'types' in config['spec']:
            report['types'] = config['spec']['types']
            report['excluded'] = {f:summaries[f]['population']['excluded'] for f in config['families']}
            report['rooms_with_kept_items'] = {f:summaries[f]['population']['rooms_with_items'] for f in config['families']}
        if 'a7' in config['families']:
            from x7 import CONSTANTS
            report['coverage'] = {k:config['extra'][k] for k in ('registered_rooms','rooms_with_items','deferred_rooms','deferred_room_ids')}
            if 'types' in config['spec']:
                report['coverage']['rooms_with_items'] = summaries['a7']['population']['rooms_with_items']
            for task, values_by_type in report['scores']['a7'].items():
                values_by_type['no_information_pct'] = CONSTANTS[task]
        T.dump(root/'SUMMARY.json', report)
        T.dump(root/'COMPLETE.json', dict(plan_sha256=config['plan_sha256'], synthetic=False,
                                         items=len(values), step=config['spec']['step']))
    except BaseException as error:
        T.dump(root/'SUMMARY.json', dict(step=config['spec']['step'], complete=False,
                    families=summaries, seconds=time.monotonic()-started))
        T.dump(root/'FAILED.json', dict(error=type(error).__name__))
        raise


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--config',required=True); a=p.parse_args()
    run(T.load(a.config))
