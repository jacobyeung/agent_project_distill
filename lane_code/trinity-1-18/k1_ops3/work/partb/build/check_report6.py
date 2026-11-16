"""Small regression checks for configuration, pinned metadata and budgets."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import types

import job_support as H
from audit_config import audit
from phase_support import budget

def main():
    config = json.loads(Path('packet/CONFIG.json').read_text())
    audit(config)
    rejected = []
    for name, value in [('members','xx/<sha>.png plus ANCHORS_MANIFEST.json'),
                        ('generation','PENDING_UPLOAD_METADATA'), ('bytes','2646947840')]:
        bad = deepcopy(config); bad['anchors'][name] = value
        try:
            audit(bad)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError(name)
    tree = ast.parse(Path('stage_job.py').read_text())
    stage = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='stage')
    resolved = next(n for n in stage.body if isinstance(n,ast.FunctionDef) and n.name=='resolved')
    item = config['code']
    metadata = dict(size=item['bytes'], generation=item['generation'], crc32c_hash=item['crc32c'])
    commands = []
    def run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command,0,json.dumps(metadata),'')
    env = dict(json=json, subprocess=types.SimpleNamespace(run=run,PIPE=subprocess.PIPE),
               S=types.SimpleNamespace(cloud_environment=lambda path:{}),assets=config['assets'])
    exec(compile(ast.Module(body=[resolved],type_ignores=[]),'stage_job.py','exec'),env)
    assert env['resolved'](item)==item
    assert commands[0][4].endswith('#1794820770137604')
    refused = []
    for key, bad in [('size',1),('generation','1'),('crc32c_hash','AAAAAA==')]:
        old = metadata[key]; metadata[key] = bad
        try:
            env['resolved'](item)
        except ValueError:
            refused.append(key)
        else:
            raise AssertionError(key)
        metadata[key] = old
    assert budget(1800,3000,900,allocation_seconds=10800)['max_seconds']==5100
    assert budget(0,1,1,allocation_seconds=0)['max_seconds']==0
    assert budget(0,1,1,allocation_seconds=10800,started_unix=1000,deadline_unix=999)['max_seconds']==0
    assert budget(0,1,1,allocation_seconds=5,started_unix=1000,deadline_unix=99999)['max_seconds']==3
    result = dict(passed=True, invalid_config_rejected=rejected,
                  metadata_mismatch_rejected=refused, describe_uri=commands[0][4],
                  short_budget=True, zero_budget=True, expired_deadline=True,
                  deadline_cannot_extend_allocation=True)
    H.dump('evidence/REPORT6_REGRESSIONS.json',result)
    print(json.dumps(result))

if __name__=='__main__': main()
