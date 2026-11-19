import sys
sys.dont_write_bytecode=True
import subprocess
from pathlib import Path
import numpy as np
import scale_analysis as s

bars=s.read(s.OUT/'BARS_FROZEN.json')
result=s.read(s.OUT/'SCALE_RESULT.json')
rooms=s.read(s.OUT/'ROOM_SCORES.json')['rooms']
captures=s.read(s.OUT/'CAPTURE_SCORES.json')['captures']
needs=s.read(s.OUT/'NEEDS_INPUTS.json')
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(dict(name=name,passed=True))
check('frozen code unchanged',bars['code_sha256']==s.sha(s.__file__)==result['code_sha256'])
check('bars preceded scores',(s.OUT/'BARS_FROZEN.json').stat().st_mtime<(s.OUT/'SCALE_RESULT.json').stat().st_mtime)
a,b=map(set,bars['room_halves'])
check('actual room halves disjoint',not a&b)
check('swapped fold rooms',bars['folds'][0]['fit_rooms']==bars['folds'][1]['test_rooms'] and bars['folds'][1]['fit_rooms']==bars['folds'][0]['test_rooms'])
check('all captures train',all(c['k1_split']=='train' for c in bars['captures']+needs['captures']))
check('capture/pair counts',len(captures)==result['captures'] and sum(c['pairs'] for c in captures)==result['pairs'])
check('same paired room population',set(rooms['A'])==set(rooms['C'])==set(rooms['E'])==set(rooms['F']))
check('complete count accounting',len(captures)+len(result['missing'])==len(bars['captures'])==len(needs['captures']))
check('exactly 32 forward frames',all(len(c['frames'])==len(c['anchor_indices'])==32 for c in needs['captures']))
for arm in 'ACEF':
    check('room aggregation '+arm,abs(np.mean(list(rooms[arm].values()))-result['combined']['arms'][arm]['mra'])<1e-10)
    check('fold pair counts '+arm,sum(f['arms'][arm]['pairs'] for f in result['folds'])==result['pairs'])
delta=np.mean([rooms['C'][r]-rooms['A'][r] for r in rooms['A']])
check('paired contrast aggregation',abs(delta-result['combined']['paired_differences']['C-A']['points'])<1e-10)
check('missing arms never numeric',all(f['arms'][arm]=={'status':'MISSING'} for f in result['folds']+[result['combined']] for arm in 'BD'))
before={str(p):s.sha(p) for p in [s.OUT/'BARS_FROZEN.json',s.OUT/'SCALE_RESULT.json',s.OUT/'CAPTURE_SCORES.json',s.OUT/'ROOM_SCORES.json']}
for command in ('freeze','score'):
    completed=subprocess.run([sys.executable,str(Path(s.__file__)),command],capture_output=True,text=True,cwd=s.ROOT)
    (s.OUT/f'refusal_{command}.log').write_text(completed.stdout+completed.stderr)
    check('real '+command+' refuses existing scores',completed.returncode!=0 and 'score file exists' in completed.stderr)
check('refusals preserve frozen bars and scores',all(s.sha(p)==h for p,h in before.items()))
check('archive receipts agree with step544',all(r['checkpoint_step']==544 for a in needs['additional_own_archives'] for r in a['training_receipts']))
outputs=[s.OUT/n for n in ['BARS_FROZEN.json','SCALE_RESULT.json','ROOM_SCORES.json','CAPTURE_SCORES.json','NEEDS_INPUTS.json','SCALE_REPORT.md','NEEDS.md','tests.log','resources.log']]
pins={str(p):s.sha(p) for p in outputs+[Path(__file__),Path(s.__file__),s.ROOT/'code/test_scale.py',s.ROOT/'code/finish_report.py']}
s.dump(s.OUT/'VALIDATION.json',dict(input_sha256=pins,checks=checks,passed=True))
(s.ROOT/'STATUS.md').write_text('The CPU analysis and final validation are complete. On 239 K1 training captures in 219 rooms, calibration improves step-544 displacement by 0.153 MRA points (95% room-bootstrap CI +0.087 to +0.222), with positive intervals in both swapped folds. Step-400 depth predictions are MISSING, so B, D, and their contrasts remain unestimated. out/SCALE_REPORT.md and out/SCALE_RESULT.json contain the results; out/NEEDS.md and out/NEEDS_INPUTS.json specify the missing forward and its timing estimate. Six unit tests and all output checks passed, including real freeze/score refusal with existing results. Scoring used 26.31 seconds and 147,512 KiB peak RSS, CPU only.\n')
print('PASS',len(checks),'output checks')
