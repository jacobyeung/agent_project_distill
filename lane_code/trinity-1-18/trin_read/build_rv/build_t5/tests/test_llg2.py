import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as NS

import pytest
import trinity_read as T
import compare_tokens as C


def run_stub(tmp_path, code, default=False):
    log = tmp_path/'llg_stub_calls.jsonl'
    env = dict(os.environ, TMPDIR=str(tmp_path), PYTHONDONTWRITEBYTECODE='1')
    env.pop('LLG_STUB_LOG', None)
    if not default: env['LLG_STUB_LOG'] = str(log)
    prefix = 'import sys; sys.path.insert(0, '+repr(str(T.LLG_STUB.parent))+'); import llguidance\n'
    p = subprocess.run([sys.executable, '-I', '-B', '-c', prefix+code], env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return p, [json.loads(line) for line in log.read_text().splitlines()]


@pytest.mark.parametrize('name', ['LLMatcher', 'LLTokenizer', 'LLInterpreter'])
def test_class_always_logs_before_raising(tmp_path, name):
    p, rows = run_stub(tmp_path, 'llguidance.'+name+'(None)')
    assert p.returncode != 0 and 'RuntimeError: llguidance stub:' in p.stderr
    assert rows[0]['event'] == 'import' and rows[0]['module'] == 'llguidance' and rows[0]['pid'] > 0
    assert rows[1] == dict(event='call', name=name)


@pytest.mark.parametrize('code,name', [('llguidance.unknown', 'llguidance.unknown'),
    ('llguidance.LLMatcher.grammar_from_json_schema({})', 'LLMatcher.grammar_from_json_schema'),
    ('import llguidance.hf', 'llguidance.hf'), ('import llguidance.torch', 'llguidance.torch')])
def test_other_guidance_use_raises_and_logs(tmp_path, code, name):
    p, rows = run_stub(tmp_path, code, default=True)
    assert p.returncode and 'RuntimeError: llguidance stub:' in p.stderr
    assert rows[-1] == dict(event='call', name=name)
    if name in ('llguidance.hf', 'llguidance.torch'):
        assert rows[-2]['event'] == 'import' and rows[-2]['module'] == name


def test_import_only_and_concurrent_log(tmp_path):
    log = tmp_path/'shared.jsonl'
    code = 'import sys; sys.path.insert(0, '+repr(str(T.LLG_STUB.parent))+'); import llguidance'
    children = [subprocess.Popen([sys.executable, '-I', '-B', '-c', code], env=dict(os.environ, LLG_STUB_LOG=str(log))) for _ in range(4)]
    assert [p.wait(timeout=20) for p in children] == [0]*4
    usage = T.stub_usage(log)
    assert usage['passed'] and usage['import_events_count'] == 4 and usage['call_events_count'] == 0


@pytest.mark.parametrize('contents', ['', '{bad\n', '{"event":"call","name":"LLMatcher"}\n'])
def test_audit_fails_closed(tmp_path, contents):
    path = tmp_path/'calls'; path.write_text(contents)
    assert not T.stub_usage(path)['passed']


def test_sandbox_receipt_captures_all_binds(tmp_path, monkeypatch):
    T.physical(tmp_path, T.LLG_TARGET).mkdir(parents=True)
    command = T.namespace(tmp_path, gpu=True)
    monkeypatch.setattr(T, 'capture_command', lambda argv: dict(argv=argv, stdout='glibc fixture\n' if argv[0]=='ldd' else 'driver fixture\n', returncode=0))
    p = dict(versions=dict(python='3.12', vllm='0.32', torch='2', transformers='5'), glibc='glibc 2.28',
             imports=dict(driver_resolution=[dict(name='libcuda.so.1', paths=[])]), passed=True)
    result = T.sandbox_receipt(command, dict(path=command[0],sha256='fixture',version='0.4'), T.llguidance_evidence(), p)
    expected = [(command[i+1],command[i+2], 'ro' if arg=='--ro-bind' else 'rw') for i,arg in enumerate(command) if arg in ('--ro-bind','--bind','--dev-bind')]
    assert [(b['source'],b['target'],b['mode']) for b in result['binds']] == expected
    assert result['host_glibc'] == 'glibc fixture' and result['namespace_glibc'] == p['glibc']
    assert result['versions'] == p['versions'] and result['llguidance_stub']['sha256'] == T.LLG_PINS
    assert [p['path'] for p in result['host_driver_libraries']] == ['/usr/lib64/libcuda.so.1','/usr/lib64/libnvidia-ml.so.1']


def test_probe_executes_installed_compile_method_fixture(tmp_path):
    # Exercise the installed method's exact source with import fixtures; this is not a real namespace probe.
    source = T.physical(T.DEFAULT_ROOT, T.VLLM_ENV/'lib/python3.12/site-packages/vllm/v1/structured_output/backend_guidance.py')
    tree = ast.parse(source.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'GuidanceBackend')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'compile_grammar')
    serialize = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'serialize_guidance_grammar')
    lines = source.read_text().splitlines()
    import textwrap
    method_source = textwrap.dedent('\n'.join(lines[method.lineno-1:method.end_lineno]))
    serialize_source = '\n'.join(lines[serialize.lineno-1:serialize.end_lineno])
    fixture = '''
import sys, types, os
from enum import Enum
for name in ('vllm', 'torch', 'transformers', 'vllm.model_executor', 'vllm.model_executor.models',
             'vllm.v1', 'vllm.v1.engine', 'vllm.v1.engine.core', 'vllm.v1.worker', 'vllm.v1.worker.gpu_model_runner',
             'vllm.v1.structured_output', 'vllm.v1.structured_output.backend_guidance'):
    module = types.ModuleType(name); module.__version__ = 'fixture'; module.__path__ = []
    sys.modules[name] = module
sys.modules['vllm'].LLM = object
sys.modules['vllm.model_executor.models'].qwen3_5 = object
class StructuredOutputOptions(Enum):
    JSON=1; JSON_OBJECT=2; REGEX=3; GRAMMAR=4; CHOICE=5; STRUCTURAL_TAG=6
'''
    fixture += '\nexec('+repr('from __future__ import annotations\n'+serialize_source+'\n'+method_source)+')\n'
    fixture += "m=sys.modules['vllm.v1.structured_output.backend_guidance']; m.GuidanceBackend=type('GuidanceBackend', (), {'compile_grammar': compile_grammar}); m.StructuredOutputOptions=StructuredOutputOptions\n"
    p, rows = run_stub(tmp_path, fixture+T.PROBE_CODE)
    assert p.returncode == 0, p.stderr
    report = json.loads(p.stdout.split(T.PROBE_MARKER)[1])
    assert report['structured_output']['stub_runtime_error']
    assert report['structured_output']['stage'].startswith('GuidanceBackend.compile_grammar')
    assert rows[-1] == dict(event='call', name='llguidance.grammar_from')


def make_run(root, token, index, changed=False, calls=0):
    out = root/'runs'/(token+'_r'+str(index)); out.mkdir(parents=True)
    row = dict(example_id='one', token_ids=[1,2], raw_generation='A', extracted_answer='A', score=1.)
    reference = dict(ids=['one'], arms={arm:[copy.deepcopy(row)] for arm in C.ARMS})
    T.dump(out/'accepted.json', reference)
    if changed: row.update(token_ids=[1,3], extracted_answer='B', score=0.)
    for rel in C.ARMS.values():
        path = out/'b0/d0/results'/rel/'items_b0.jsonl'; path.parent.mkdir(parents=True)
        path.write_text(json.dumps(row)+'\n')
    (out/'MEMORY.jsonl').write_text('{"memory_used_mib":1}\n')
    log = out/'llg_stub_calls.jsonl'
    log.write_text('{"event":"import","module":"llguidance","pid":1}\n' + '{"event":"call","name":"LLMatcher"}\n'*calls)
    T.dump(out/'EXIT.json', dict(returncode=0, llguidance_stub=T.llguidance_evidence(), stub_usage=T.stub_usage(log)))
    C.write_report(out/'accepted.json', out/'b0/d0', 'b0', out, out/'MEMORY.jsonl', out/'EXIT.json')
    return out


@pytest.mark.parametrize('changed,calls', [(False,0),(True,0),(False,1)])
def test_repeated_comparison_and_call_rejection(tmp_path, changed, calls):
    token='p12345678'
    make_run(tmp_path, token, 1)
    second=make_run(tmp_path, token, 2, changed, calls)
    out=tmp_path/'summary'; out.mkdir()
    result=C.write_repeated(tmp_path,token,out)
    assert result['passed'] == (not changed and not calls)
    check=result['run_to_run']['arms']['ON16k']
    assert check['items'][0]['first_divergence_index'] == (1 if changed else None)
    assert check['answers_equal'] == (not changed) and check['scores_equal'] == (not changed)
    if calls:
        proof=T.load(second/'PROOF.json')
        assert not proof['passed'] and any('called 1' in e for e in proof['errors'])
    assert 'Run 1 vs accepted' in (out/'PROOF.md').read_text()
    assert 'Run 2 vs accepted' in (out/'PROOF.md').read_text()


@pytest.mark.parametrize('fail_first', [False, True])
def test_repeat_sequential_same_card_and_no_retry(tmp_path, monkeypatch, fail_first):
    seen=[]
    def run(args):
        seen.append((args.run_name,args.gpu))
        index=len(seen)
        if fail_first: raise RuntimeError('Reader killed; do not retry')
        make_run(tmp_path,args.token,index)
    monkeypatch.setattr(T,'_launch_one',run)
    monkeypatch.setattr(T,'sandbox_receipt',lambda **kw: dict())
    args=NS(root=str(tmp_path),command='proof',token='p12345678',gpu='3',repeat=2)
    if fail_first:
        with pytest.raises(RuntimeError,match='Reader killed'): T.launch(args)
    else: T.launch(args)
    assert seen == [('p12345678_r1','3')]+([] if fail_first else [('p12345678_r2','3')])
    result=T.load(tmp_path/'runs/p12345678/RUN_TO_RUN.json')
    assert result['passed'] != fail_first
    assert (tmp_path/'runs/p12345678_r1/SANDBOX.json').exists()


@pytest.mark.parametrize('command', ['proof','read'])
@pytest.mark.parametrize('calls', [0,1])
def test_run_audit_receipt_and_packet(tmp_path, monkeypatch, command, calls):
    import milestone as M
    monkeypatch.setattr(M, 'inventory', lambda: {'main': {'items': {'one': 'fixture'}}})
    cfg=dict(spec=dict(package=str(T.SJ/'pkg'),models={}))
    monkeypatch.setattr(T,'require_stage',lambda root:copy.deepcopy(cfg))
    monkeypatch.setattr(T,'cpu_need',lambda *a:dict(ids=['one'],need=[]))
    monkeypatch.setattr(T,'read_space',lambda *a:0)
    monkeypatch.setattr(T,'check_card',lambda *a:dict(index='2'))
    monkeypatch.setattr(T,'capture_command',lambda argv:dict(stdout='fixture\n',returncode=0))
    monkeypatch.setattr(T,'probe',lambda *a:dict(passed=True,versions=dict(python='3.12',vllm='0.32',torch='fixture',transformers='fixture'),glibc='glibc 2.28'))
    monkeypatch.setattr(T,'ns_command',lambda *a,**k:['/usr/bin/bwrap','--bind',str(tmp_path),str(tmp_path),'fake-reader'])
    monkeypatch.setattr(T,'host_shm_ours',lambda:[])
    row=dict(example_id='one',token_ids=[1],raw_generation='A',extracted_answer='A',score=1.)
    T.dump(tmp_path/'sj/pkg/parity/DEV20.json',dict(ids=['one'],need=[],arms={a:[row] for a in C.ARMS}))
    out=tmp_path/'runs/p12345678' if command=='proof' else tmp_path/'packet'
    def reader(argv, env, *a):
        assert env['CUDA_VISIBLE_DEVICES']=='2'
        assert env['LLG_STUB_LOG']==str(out/'llg_stub_calls.jsonl')
        Path(env['LLG_STUB_LOG']).write_text('{"event":"import","module":"llguidance","pid":2}\n'+'{"event":"call","name":"LLMatcher"}\n'*calls)
        if command=='proof':
            for rel in C.ARMS.values():
                path=out/'b0/d0/results'/rel/'items_b0.jsonl';path.parent.mkdir(parents=True)
                path.write_text(json.dumps(row)+'\n')
        return 0,None
    monkeypatch.setattr(T,'run_reader',reader)
    class Sampler:
        def __init__(self,gpu,path):
            self.thread=NS(start=lambda:path.write_text('{"memory_used_mib":1}\n'),join=lambda **kw:None)
            self.stop=NS(set=lambda:None);self.errors=[]
    monkeypatch.setattr(T,'Sampler',Sampler)
    args=NS(root=str(tmp_path),command=command,token='p12345678',gpu='2',family='main',first=1,ids=None,
            out=str(out),artifact=str(T.LINEAGE/'m544/artifact.json'),sha256='a'*64,step=544)
    if calls:
        with pytest.raises(RuntimeError,match='llguidance audit failed'): T.launch(args)
    else: T.launch(args)
    receipt=T.load(out/'SANDBOX.json')
    assert receipt['namespace_executed'] and receipt['versions']['python']=='3.12'
    packet=out/'b0/d0' if command=='proof' else out
    assert T.load(packet/'SANDBOX.json')==receipt
    usage=T.load(packet/'LLGUIDANCE.json')['usage']
    assert usage['import_events_count']==1 and usage['call_events_count']==calls
    if command=='proof': assert T.load(out/'PROOF.json')['passed']==(calls==0)
