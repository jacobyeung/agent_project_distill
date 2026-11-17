"""CPU coverage for ordered type selection in source and authenticated payload."""
import itertools
import json
from pathlib import Path
import tarfile
from types import ModuleType, SimpleNamespace

import pytest

from orchard_h10.common import ORDER, sha, write

K = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module', params=['source', 'payload'])
def implementation(request):
    modules = {}
    with tarfile.open(K/'orchard_h10/package/0.tgz') as archive:
        for name in ('job', 'runner'):
            path = K/f'orchard_h10/{name}.py'
            raw = path.read_bytes() if request.param == 'source' else archive.extractfile(f'orchard_h10/{name}.py').read()
            module = ModuleType(f'test_types_{name}_{request.param}')
            module.__file__ = str(path)
            exec(compile(raw, str(path), 'exec'), module.__dict__)
            modules[name] = module
    return SimpleNamespace(**modules)


@pytest.fixture
def admission():
    cfg = dict(token='abcdef0123456', logical='/sj/abcdef0123456')
    pins = dict(
        artifact='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef',
        heads='8bb5e1510ee3a5a3959e82f2149c69903e98f46880b8a038bf4b951b8c21de91',
        full_weights='211ae87b0bb03bb0c3d43c1c1412e0f346591ab4ddc75b4d754de2740da0a302',
        g3t_weights='d460957b'+'0'*56, g3t_config='5aeb2acd'+'0'*56,
        sam_checkpoint='9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e',
        selector_weights='6d97c52407b7e106a7b475040558ba313589514c23c33b6994f4e7a0bb1df6c1')
    for name in ('sam_receipt', 'selector_config', 'base_config', 'original_model', 'environment', 'policy'):
        pins[name] = 'a'*64
    root = cfg['logical']+'/d'
    inputs = dict(schema=1, archives=[dict(sha256='b'*64, expanded_bytes=1,
        destination=f"sj/{cfg['token']}/d", parts=[dict(
            path='/project/community/jjyeung/input.tgz', sha256='c'*64, bytes=1)])],
        files={name: dict(path=root+'/'+name, sha256=pin, bytes=1) for name, pin in pins.items()},
        frames_root=root+'/frames', sam_source=root+'/sam', python='/usr/bin/python3',
        policy=dict(vnice=root+'/vnice', terminator=root+'/terminator'),
        environment_receipt='environment', policy_receipt='policy')
    return inputs, cfg


@pytest.mark.parametrize('selection', [None, *[
    list(group) for n in range(1, len(ORDER)+1) for group in itertools.combinations(ORDER, n)]])
def test_valid_selection(implementation, admission, selection):
    inputs, cfg = admission
    if selection is not None:
        inputs['types'] = selection
    assert implementation.job.check_inputs(inputs, cfg) is inputs


@pytest.mark.parametrize('selection', [
    None, [], '', ORDER[3], ','.join(ORDER[3:]), tuple(ORDER[3:]), {}, 3, False,
    ['unknown'], [ORDER[3], ORDER[3]], [ORDER[4], ORDER[3]],
    [ORDER[0], ORDER[2], ORDER[1]], [ORDER[3], None], [3, 4],
    [[ORDER[3]]], [{'name': ORDER[3]}], [ORDER[3].upper()]])
def test_invalid_selection(implementation, admission, selection):
    inputs, cfg = admission
    inputs['types'] = selection
    with pytest.raises(ValueError, match='^Invalid type selection$'):
        implementation.job.check_inputs(inputs, cfg)


@pytest.mark.parametrize('selection', [None, list(ORDER), list(ORDER[3:])])
@pytest.mark.parametrize('optional', [False, True])
def test_selected_runner(implementation, tmp_path, monkeypatch, selection, optional):
    from h1eval import items as I
    from h1eval.cli import modes
    from h1eval.modes import DEFAULT_MODES, plan

    runner = implementation.runner
    base = [dict(id=f'{t}-{i}', question_type=kind) for t, kind in enumerate(ORDER) for i in range(2)]
    reserve = [dict(id=f'extra-{i}', question_type='object_counting') for i in range(2)]
    monkeypatch.setattr(I, 'load_manifest', lambda p: dict(items=reserve if str(p).endswith('8.json') else base))
    source = tmp_path/'7.json'
    write(source, dict(items=base))
    cfg = dict(package=str(K), output=str(tmp_path/'r'), python='/usr/bin/python3',
               items=str(source), device='cpu', plan_sha256='a'*64,
               export='x', binding='x', settings='x', stop_margin=10, return_margin=5)
    if selection is not None:
        cfg['types'] = selection
    if optional:
        receipt = tmp_path/'6.json'; write(receipt, dict(verified=True))
        extra = tmp_path/'8.json'; write(extra, dict(items=reserve))
        cfg['optional'] = dict(items=str(extra), receipt=str(receipt), sha256=sha(receipt))
    expected_types = list(range(5)) if selection != list(ORDER[3:]) else [3, 4]
    phases = expected_types + ([5] if optional else [])
    calls = []

    def launch(argv, **kwargs):
        dispatch = json.loads((Path(kwargs['cwd'])/argv[-1]).read_text())
        t, i = dispatch['type'], dispatch['index']
        assert argv[-1] == f'{t}{i}.json'
        assert t in phases and dispatch['cards'] == 2
        assert dispatch['stop_at'] == 90 and dispatch['finish_by'] == 95
        args = runner.worker_args(dispatch)
        root = Path(cfg['output'])/'metadata/journals'/str(t)/str(i)
        assert args[args.index('--out')+1] == str(root)
        if t < 5:
            assert args[args.index('--types')+1] == ORDER[t]
        else:
            assert '--types' not in args and args[args.index('--modes')+1] == 'none'
        chosen = [v for v in base[i::2] if v['question_type'] == ORDER[t]] if t < 5 else reserve[i::2]
        wanted = plan(chosen, ['own'], [{'name': 'none'}, *modes(DEFAULT_MODES)] if t < 5 else [{'name': 'none'}])
        root.mkdir(parents=True, exist_ok=True)
        (root/'items.jsonl').write_text(''.join(json.dumps(dict(
            id=a, arm=b, mode=m, complete=True, seconds=.25))+'\n' for a, b, m in sorted(wanted)))
        calls.append((t, i))
        return SimpleNamespace(wait=lambda: 0)

    summary = runner.run(cfg, ['0', '1'], 100, launcher=launch, clock=lambda: 0)
    assert calls == [(t, i) for t in phases for i in range(2)]
    expected = (22 if len(expected_types) == 5 else 8) + (2 if optional else 0)
    assert summary['complete'] and summary['completed'] == summary['expected'] == expected
    assert summary['optional_admitted'] is optional
    assert [r['type'] for r in summary['shards']] == [t for t, i in calls]
    out = Path(cfg['output'])
    assert json.loads((out/'SUMMARY.json').read_text()) == summary
    assert {p.name for p in (out/'metadata/journals').iterdir()} == {str(t) for t in phases}
    assert {p.name for p in (out/'logs').iterdir()} == {f'{t}{i}.log' for t, i in calls}
    identity = json.loads((out/'metadata/IDENTITY.json').read_text())
    assert identity['order'] == list(ORDER)
    assert identity['types'] == (selection if selection is not None else list(ORDER))
    assert json.loads((out/'metadata/projection.json').read_text())['sample_reads'] == expected

    if expected_types == [3, 4]:
        # Unselected journals cannot affect selected counts or timing samples.
        stray = out/'metadata/journals/0/0/items.jsonl'
        stray.parent.mkdir(parents=True)
        stray.write_text('unselected journal must not be read\n')
        assert runner.summarize(cfg, ['0', '1'])['expected'] == expected
        assert runner.run(cfg, ['0', '1'], 100, launcher=launch, clock=lambda: 0)['complete']
        assert json.loads((out/'metadata/projection.json').read_text())['sample_reads'] == expected
        with pytest.raises(ValueError, match='Resume requires'):
            runner.run(dict(cfg, types=list(ORDER)), ['0', '1'], 100, launcher=launch, clock=lambda: 0)
