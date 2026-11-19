"""Exercise step-400 admission/fill and return guards with tiny local fixtures."""
import argparse
import ast
import copy
import json
import os
from pathlib import Path
import sys
import types

import return_tools as rt
from test_remainder import dump, rejected

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'dbuild'))
import build_d
import place_fill_d as place


def block(path, function, start, end):
    body = next(n.body for n in ast.parse(path.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == function)
    module = ast.parse('')
    module.body = body[start(body):end(body)]
    return compile(module, str(path), 'exec')


def assignment(body, name):
    return next(i for i, n in enumerate(body) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--integration', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    negative = []
    binding = rt.read(HERE/'dbuild/bind_D400.json')
    assert (HERE/'dbuild/bind_D400.json').read_bytes() == (HERE.parent/'dbuild/bind_D400.json').read_bytes()
    assert (HERE/'dbuild/place_fill_d.py').read_bytes() == (HERE.parent/'dbuild/place_fill_d.py').read_bytes()
    assert (HERE/'score_base.py').read_bytes() == (HERE.parent/'dbuild/score_d.py').read_bytes()
    admission = block(HERE/'dbuild/build_d.py', 'build',
                      lambda b: assignment(b, 'binding'), lambda b: assignment(b, 'timing'))
    old = rt.read(HERE/'dbuild/bind_D200.json')
    manifest = rt.read(args.integration/'remainder.json')

    def admit(value, full=False):
        path = args.work/'binding.json'
        dump(path, value)
        exec(admission, dict(build_d.__dict__, binding_path=path,
             manifest={} if full else manifest,
             plan={'export_binding': {k:old[k] for k in build_d.KEYS}}))

    admit(binding)
    for key, value in [('run','wrong'), ('step',401), ('archive_sha256','0'*64),
                       ('object','wrong'), ('done','wrong'), ('member_directory','m544'),
                       ('preparation_sha256',dict(binding['preparation_sha256'],config='0'*64)),
                       ('parts',[dict(p,sha256='0'*64) for p in binding['parts']])]:
        bad = copy.deepcopy(binding);bad[key] = value
        # Full manifests must also reject noncanonical bindings, independently of parent equality.
        negative.append(rejected(lambda: admit(bad, True), 'binding '+key))
    negative.append(rejected(lambda: admit(old), 'parent export mismatch'))

    preflight = block(HERE/'dbuild/place_fill_d.py', 'run', lambda b: 0,
                      lambda b: assignment(b, 'package'))
    stage = args.work/'stage';stage.mkdir()
    dump(stage/'binding.json', binding)
    dump(stage/'BUILD.json', {'D': {'binding_sha256':place.sha(stage/'binding.json')}})
    os.environ['DONE_FROM'] = binding['done']
    os.environ['REUSE_PARTS_FROM'] = str(args.work/'parts')
    exec(preflight, dict(place.__dict__, stage=stage))
    os.environ['DONE_FROM'] = '/wrong/m400.done'
    negative.append(rejected(lambda: exec(preflight, dict(place.__dict__, stage=stage)), 'wrong done path'))
    os.environ['DONE_FROM'] = binding['done']
    os.environ.pop('REUSE_PARTS_FROM')
    negative.append(rejected(lambda: exec(preflight, dict(place.__dict__, stage=stage)), 'missing reuse'))

    fill = block(HERE/'dbuild/place_fill_d.py', 'run', lambda b: assignment(b, 'reuse'),
                 lambda b: next(i for i,n in enumerate(b) if isinstance(n,ast.Expr)
                     and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute)
                     and n.value.func.attr=='run'))
    source = args.work/'parts';source.mkdir()
    tiny = copy.deepcopy(binding)
    prep = {'config':dict(base_identity=binding['base_identity'],frame_layout='duplicate'),
            'receipt':dict(config_sha256=binding['config_sha256'],frame_layout='duplicate'),
            'data_receipt':{'synthetic':True}}
    for key, name in [('config','7'),('receipt','8'),('data_receipt','9')]:
        dump(source/name, prep[key]);tiny['preparation_sha256'][key] = place.sha(source/name)
    for i in range(4):
        path = source/str(i);path.write_bytes(('part%d'%i).encode())
        tiny['parts'][i] = dict(bytes=5,sha256=place.sha(path))
    done = source/'5'
    done.write_text('%s %s %s\n' % (binding['object'],binding['archive_bytes'],binding['archive_sha256']))
    os.environ.update(REUSE_PARTS_FROM=str(source),PREP_FROM=str(source))
    os.environ.pop('DONE_FROM');os.environ.pop('CLAIM_FROM',None)

    def fixture_path(value):
        return done if str(value)==binding['done'] else Path(value)

    def execute(value, label, fail_link=False):
        dest = args.work/label;dest.mkdir()
        def forbidden(*a, **kw):
            raise AssertionError('Unexpected copy or download')
        def no_link(*a, **kw):
            raise OSError('Synthetic cross-device link failure')
        scope = dict(place.__dict__, Path=fixture_path, binding=value, e=dest, pf={},
                     shutil=types.SimpleNamespace(copyfile=forbidden),
                     subprocess=types.SimpleNamespace(run=forbidden))
        if fail_link:
            scope['os'] = types.SimpleNamespace(environ=os.environ,link=no_link)
        try:
            exec(fill, scope)
        except (ValueError,AssertionError,FileNotFoundError,OSError):
            assert not (dest/'0').exists(), 'Linked before rejecting invalid inputs'
            raise
        assert all((dest/str(i)).stat().st_ino==(source/str(i)).stat().st_ino for i in range(4))

    execute(tiny,'valid')
    for key, value in [('base_identity','wrong'),('config_sha256','0'*64),('frame_layout','paired'),
                       ('parts',tiny['parts'][:3]+[dict(tiny['parts'][3],sha256='0'*64)]),
                       ('parts',tiny['parts'][:3]+[dict(tiny['parts'][3],bytes=6)])]:
        bad = copy.deepcopy(tiny);bad[key] = value
        label = 'fill_%d_%s' % (len(negative),key)
        negative.append(rejected(lambda: execute(bad,label), label))
    for key in prep:
        bad = copy.deepcopy(tiny);bad['preparation_sha256'][key] = '0'*64
        negative.append(rejected(lambda: execute(bad,'prep_'+key), 'preparation '+key))
    try:
        execute(tiny,'failed_link',True)
    except OSError:
        negative.append(dict(test='hardlink failure',rejected='OSError; no copy or download'))
    else:
        raise AssertionError('Accepted failed hardlink')
    done.write_text('wrong receipt\n')
    negative.append(rejected(lambda: execute(tiny,'wrong_done'), 'done contents'))

    ret = args.integration/'final/ret'
    items = args.integration/'remainder.json'
    package = args.integration/'child_package'
    rows, meta = rt.load(ret, items, package)
    assert len(rows)==250 and meta['step']==400
    mutations = [('metadata/IDENTITY.json',['plan'],'f'*64),
                 ('metadata/IDENTITY.json',['operator_sha256'],'f'*64),
                 ('metadata/reads/0/metadata/journals/3/0/environment.json',['binding','step'],544)]
    for key in ('run','step','member_directory','object','archive_sha256','config_sha256'):
        mutations.append(('metadata/EXPORT_PIN.json',[key],544 if key=='step' else 'wrong'))
    for key in prep:
        mutations.append(('metadata/EXPORT_PIN.json',['preparation',key,'sha256'],'0'*64))
    for name, keys, value in mutations:
        path = ret/name;raw = path.read_bytes();bad = json.loads(raw.decode());target = bad
        for key in keys[:-1]:target = target[key]
        target[keys[-1]] = value
        try:
            dump(path,bad)
            negative.append(rejected(lambda: rt.load(ret,items,package), 'return '+'.'.join(keys)))
        finally:
            path.write_bytes(raw)
    result = dict(passed=True,negative=negative,negative_cases=len(negative),valid_hardlinks=4)
    dump(args.work/'TEST_RESULTS.json',result)
    print(json.dumps(dict(passed=True,negative_cases=len(negative),valid_hardlinks=4)))


if __name__=='__main__':
    main()
