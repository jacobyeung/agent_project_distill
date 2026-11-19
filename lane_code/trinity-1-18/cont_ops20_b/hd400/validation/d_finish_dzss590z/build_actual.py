"""Build the three release fixtures serially from the authenticated local B5 archive."""
import json
import os
import subprocess
from pathlib import Path

WORK = Path(__file__).resolve().parent
ROOT = WORK.parent.parent
for step in (200, 400, 544):
    env = dict(os.environ, STAGE=str(WORK / ('actual%d' % step)),
               STEP=str(step), WALLTIME='04:00:00', KROOT=str(WORK / 'K'),
               SOURCE_1TGZ=str(ROOT / 'in/B5_1.tgz'),
               SOURCE_SHA256='c3187ab9f88b3eb5a7ab1e30a8010e4ef86acb49d6c76e98fd97eec393b4e45a')
    with (WORK / ('actual%d.log' % step)).open('w') as log:
        subprocess.run(['bash', str(ROOT / 'dbuild/o_build_D.sh')],
                       env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    report = json.loads((WORK / ('actual%d/BUILD.json' % step)).read_text())['D']
    print(json.dumps(dict(step=step, token=report['token'], walltime=report['walltime'],
                         budget_fits=report['budget_fits'])), flush=True)
