"""Check supplied timestamp arithmetic against the named raw logs."""
from datetime import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
mirror = Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30')
logs = {'172660': (mirror / 'r1_ops6/work/mon/last.txt').read_text(),
        '171377': (mirror / 'swarm_opt/work/o/look1.out').read_text()}
rows = json.loads((ROOT / 'out/phase_timing.json').read_text())
for row in rows:
    elapsed = (datetime.fromisoformat(row['end']) - datetime.fromisoformat(row['start'])).total_seconds()
    assert elapsed == row['seconds']
    assert round(elapsed / 60, 4) == row['minutes']
    if row['evidence'].startswith(('raw timestamps', 'measured timestamps')):
        for key in ('start', 'end'):
            assert row[key].replace('+00:00', 'Z') in logs[row['job']], row
by_key = {(r['job'], r['phase']): r for r in rows}
assert by_key['172660', 'native_mode_p']['seconds'] == 8434
assert by_key['171377', 'native_mode_p']['seconds'] == 8716
c_three = by_key['172660', 'preflight_to_stage']['seconds']
c_one = by_key['172660', 'mode_p_to_second_stage']['seconds']
a_three = by_key['171377', 'preflight_to_stage']['seconds']
a_one = by_key['171377', 'mode_p_to_second_stage']['seconds']
assert (c_three, c_one, a_three, a_one) == (675, 86, 1, 1)
assert 'mem 1842 GiB' in logs['172660']
print(f'PASS: {len(rows)} interval arithmetic rows; measured endpoints occur in named raw logs')
print('MEASURED: mode p 8434 s (140.5667 min), 8716 s (145.2667 min)')
print('MEASURED: checkpoint guard envelopes 675 s and 86 s; no-checkpoint baseline 1 s each')
print(f'INFERRED: three warm passes = 3 * (86 - 1) = {3 * (c_one - a_one):g} s')
print(f'CONDITIONAL ESTIMATE: 2 * (675 / 3) + 86 = {2 * (c_three / 3) + c_one:g} s')
