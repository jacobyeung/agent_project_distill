"""Check the released A/B contract and reject partial forecast admission."""
import copy
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
LOW = Path('/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres/out')


def main():
    spec = importlib.util.spec_from_file_location('entry', ROOT/'0.py')
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)
    cfg, worker = entry.verify(ROOT)
    recipe = json.loads((LOW/'RECIPE_K3.json').read_text())
    assert recipe['anchors'] == recipe['pixel_exact'] == 320
    assert recipe['selected_recipe'] == recipe['recipe']
    for name, summary in recipe['candidates'].items():
        values = [r['candidates'][name] for r in recipe['records']]
        assert len(values) == summary['anchors'] == 320
        assert sum(v['pixel_exact'] for v in values) == summary['exact']
        assert sum(v['png_byte_exact'] for v in values) == summary['png_byte_exact']
        assert max(v['max_abs'] for v in values) == summary['max_abs']
        assert all(not v['png_byte_exact'] or v['pixel_exact'] for v in values)
    assert cfg['xr'] == [0, 1]
    assert worker.tasks(cfg) == [(r, a) for a in (0, 1) for r in range(10)]
    assert cfg['xq'] == 20 and worker.forecast(cfg) < 1500
    for row in cfg['x3']:
        assert len(row['x4']) == 3 and row['x4'][2] is None
        a, b = row['x4'][:2]
        assert len(a['x0']) == 32 and len(b['x0']) == 63
        assert not any(a['x5']) and sum(b['x5']) == 31
        assert [b['x1'][s] for s in b['x2']] == a['x1']
        assert [b['x6'][s] for s in b['x2']] == a['x6']
    original_load = entry.load
    for bad in (dict(cfg, xq=19), dict(cfg, x7=[1501.]+cfg['x7'][1:])):
        def load(path):
            return copy.deepcopy(bad) if Path(path).name == '1.json' else original_load(path)
        with patch.object(entry, 'load', load):
            try:
                entry.verify(ROOT)
            except ValueError as error:
                assert str(error) == 'E21'
            else:
                raise AssertionError('Invalid forecast admission accepted')
    decoded = json.loads((ROOT/'DECODE_K3b.json').read_text())
    assert decoded['anchors'] == 320
    assert all(r['matches_served'] and r['matches_recipe'] for r in decoded['records'])
    dry = json.loads((ROOT/'DRY.json').read_text())
    assert dry['stub'] and dry['complete'] and dry['ran'] == [[0, 0], [0, 1]]
    assert [len(a['c2w']) for a in dry['rows'][0]['arms'][:2]] == [32, 63]
    print(json.dumps(dict(passed=True, anchors=320, tasks=20,
                         forecast_seconds=worker.forecast(cfg), admission_rejections=2)))


if __name__ == '__main__':
    main()
