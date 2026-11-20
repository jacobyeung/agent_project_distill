import ast
import copy
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                  XDG_CACHE_HOME=str(ROOT/'out/cache'),HF_HOME=str(ROOT/'out/cache/hf'))


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);sys.modules[name]=result;spec.loader.exec_module(result)
    return result


probe=module('probe',ROOT/'src/probe.py')
builder=module('builder',ROOT/'build.py')
score=module('score',ROOT/'score.py')


def members(raw):
    with tarfile.open(fileobj=io.BytesIO(raw)) as t:
        ms=t.getmembers();assert all(m.isfile() for m in ms)
        assert len({m.name for m in ms})==len(ms)
        return {m.name:t.extractfile(m).read() for m in ms}


FILES=members((ROOT/'out/delivery.tgz').read_bytes())
PAYLOAD=members(FILES['0.tgz'])
DATA=builder.storage.loads(PAYLOAD['1.json'])


class Tokenizer:
    def __init__(self,pieces):self.pieces=pieces
    def decode(self,ids,skip_special_tokens=False):
        assert not skip_special_tokens
        return ''.join(self.pieces[i] for i in ids)


def generate(pieces):
    seen=[]
    def advance(ids):seen.append(list(ids));return len(ids)
    out=probe.decode(0,lambda x:x,advance,Tokenizer(pieces),{999})
    return out,seen


class ProbeTests(unittest.TestCase):
    def test_split_opener(self):
        result,seen=generate(['I need ', '<', 'gro', 'und', ' NEVER'])
        self.assertTrue(result['g']);self.assertEqual(result['n'],4)
        self.assertEqual(len(seen),3);self.assertEqual(result['text'],'I need <ground')

    def test_other_and_partial(self):
        for i,opener in enumerate(probe.OPENINGS):
            result,seen=generate([opener,' NEVER'])
            self.assertEqual(result['g'],i==0)
            self.assertEqual(result['o'],[] if i==0 else [i])
            self.assertEqual(seen,[])
        self.assertEqual(probe.detect('<grou'),[])
        self.assertEqual(probe.detect('<GROUND'),[])
        self.assertEqual(probe.detect('"<ground'),[0])
        self.assertEqual(probe.detect('<grounding'),[0])

    def test_exact_cap_boundaries(self):
        result,seen=generate(['x']*63+['<ground',' extra'])
        self.assertEqual((result['n'],result['g'],result['finish']),(64,True,'call'))
        self.assertEqual(len(seen),63)
        result,seen=generate(['x']*64+['<ground'])
        self.assertEqual((result['n'],result['g'],result['finish']),(64,False,'cap'))
        self.assertEqual(len(seen),63)
        result,_=generate(['x']*63+['<grou','nd'])
        self.assertFalse(result['g'])

    def test_eos_no_advance(self):
        result=probe.decode(None,lambda _:999,lambda _:self.fail('advanced after EOS'),
                            Tokenizer({999:'<eos>'}),{999})
        self.assertEqual(result['finish'],'eos');self.assertEqual(result['n'],1)

    def test_multiple_openings_in_one_token(self):
        result,_=generate(['<gap <ground'])
        self.assertTrue(result['g']);self.assertEqual(result['o'],[5])

    def test_frozen(self):
        raw=(ROOT/'FROZEN.json').read_bytes();f=json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),(ROOT/'FROZEN.sha256').read_text().split()[0])
        self.assertEqual(list(probe.OPENINGS),[f['generation']['ground_opening']]+f['generation']['other_openings'])
        self.assertEqual(probe.CAP,f['generation']['max_new_tokens'])
        for name,h in f['sources'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),h)

    def test_labels_and_pairing(self):
        original=json.loads((ROOT/'in/D400/src/items/dist580.json').read_text())
        source={r['id']:r for r in original['items']}
        mapping=json.loads((ROOT/'PAIR_MAP.json').read_text())
        self.assertEqual(set(DATA),{'rows','captures'})
        self.assertEqual(len(DATA['rows']),580);self.assertEqual(len(DATA['captures']),98)
        self.assertEqual({r['source_id'] for r in mapping},set(original['sets']['R0-dev-twin']))
        captures=json.loads((ROOT/'in/D400/src/inputs/room_captures.json').read_text())['captures']
        for j,m in enumerate(mapping):
            a,b=DATA['rows'][2*j:2*j+2];old=source[m['source_id']]
            self.assertEqual(set(a),{'i','r','a','q'});self.assertEqual(set(b),set(a))
            self.assertEqual(a['q'],old['question'])
            self.assertEqual(b['q'],a['q'].replace('the distance between','the direct distance between'))
            self.assertEqual((a['i'],a['r'],a['a']),(m['i'],m['r'],0))
            self.assertEqual((b['i'],b['r'],b['a']),(m['i'],m['r'],1))
            c=DATA['captures'][a['r']]
            self.assertEqual(set(c),{'frames','anchor_indices','anchor_slots','fps','timestamps','total_num_frames'})
            for k in c:self.assertEqual(c[k],captures[old['native']][k])
            self.assertEqual(len(c['frames']),32)
            for frame in c['frames']:self.assertEqual(set(frame),{'path','sha256','index'})
        bad={'answer','answers','label','labels','truth','ground_truth','gt','target','scores','score','label_provenance'}
        def walk(x):
            if isinstance(x,dict):
                self.assertFalse(set(x)&bad)
                for v in x.values():walk(v)
            elif isinstance(x,list):
                for v in x:walk(v)
        for name,raw in FILES.items():
            if name.endswith('.json'):walk(json.loads(raw))
        code=builder.storage.loads(FILES['8.bin'])
        self.assertTrue(all(n.endswith('.py') or n=='c/tree/trace_format/vsi_scannet_vocab.json' for n in code))
        self.assertFalse(any('/tests/' in n or '/items/' in n or '/inputs/' in n for n in code))
        # Known item identifiers and the original label-field serialization must
        # never survive inside encoded executable source either.
        joined='\n'.join(code.values())
        self.assertTrue(all(m['source_id'] not in joined for m in mapping))

    def test_public_namespace(self):
        def check(value):
            hits=[w for w in builder.DENY if w in value.lower()]
            self.assertFalse(hits,(value[:100],hits))
        for container in (FILES,PAYLOAD):
            for name,raw in container.items():
                check(name)
                if name.endswith(('.py','.sh')):check(raw.decode())
        cfg=builder.storage.loads(FILES['2.json']);check(cfg['package']);check(cfg['token'])
        for a in cfg['inputs']['archives']:
            for part in a['parts']:check(part['path'])
        for key in ('python','frames_root'):check(cfg['inputs'][key])
        # Operating-system mount flags and private module API identifiers are
        # not scheduler names. They remain visible in the local audit sources.

    def test_real_staging_allowance(self):
        vendor=ROOT/'in/D400/src/orchard_h10/vendor';sys.path.insert(0,str(vendor))
        stage=module('orchard_stage_test',vendor/'orchard_stage.py')
        job=ast.parse((ROOT/'in/D400/src/orchard_h10/job.py').read_text())
        node=next(n for n in job.body if isinstance(n,ast.FunctionDef) and n.name=='stage')
        calls=[n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='extract_stream']
        limit=eval(compile(ast.Expression(calls[0].args[3]),'<allowance>','eval'),{'__builtins__':{}})
        self.assertEqual(limit,32*1024**2)
        target=ROOT/'out'/('stage_'+uuid.uuid4().hex);target.mkdir()
        with (ROOT/'out/delivery.tgz').open('rb') as f:
            inventory=stage.extract_stream(f,target/'d',None,limit)
        self.assertEqual(set(inventory),set(FILES))
        inventory=stage.extract_stream(io.BytesIO(FILES['0.tgz']),target/'p',None,limit)
        self.assertEqual(set(inventory),set(PAYLOAD))
        for name,pin in inventory.items():self.assertEqual(pin,builder.pin(PAYLOAD[name]))
        with self.assertRaisesRegex(ValueError,'allowance'):
            stage.extract_stream(io.BytesIO(FILES['0.tgz']),target/'negative',None,1)

    def test_runtime_compiles_and_native_imports(self):
        for p in (ROOT/'src').glob('*.py'):compile(p.read_text(),str(p),'exec')
        # Import native interfaces in the CPU environment. No model or processor
        # is constructed and no remote/local weight is opened.
        code=builder.storage.loads(FILES['8.bin'])
        root=ROOT/'out'/('imports_'+uuid.uuid4().hex)
        builder.storage.materialize(root,code)
        from e2e_reader.parity import load_native,trainer_row
        from parity_kit.stage_restore import stage
        from student_pilot.carrier_c1_decode import _prepare_decode,consume_cache_tokens
        from evalpath.runtime import prompt_batch
        self.assertTrue(all(callable(x) for x in (load_native,trainer_row,stage,_prepare_decode,consume_cache_tokens,prompt_batch)))
        row=DATA['rows'][0];cap=DATA['captures'][row['r']]
        task=dict(id=row['i'],dataset='a',scene=row['r'],question_type='object_abs_distance',question=row['q'],options=[])
        bound=trainer_row(task,cap,'/tmp/0',verify=False)
        self.assertEqual(bound['student_input']['question'],row['q'])
        self.assertEqual(bound['student_input']['frame_indices'],cap['anchor_indices'])
        self.assertFalse({'answer','ground_truth','gt'}&set(bound))

    def test_submission_resources_and_guards(self):
        control=module('control',ROOT/'src/control.py')
        # Exercise the real submit constructor with I/O limited to a local fake
        # package. The subprocess itself is intercepted, so no Slurm runs.
        from unittest.mock import patch
        from types import SimpleNamespace
        p=ROOT/'out'/('submit_'+uuid.uuid4().hex);(p/'a').mkdir(parents=True)
        (p/'9.py').write_bytes(FILES['9.py']);(p/'4.sh').write_bytes(FILES['4.sh']);(p/'2.json').write_bytes(FILES['2.json'])
        expected=dict(passed=True,package='p',payload='q',frozen='f')
        (p/'a/4.json').write_text(json.dumps(expected))
        calls=[]
        def fake(args,**kw):calls.append((args,kw));return SimpleNamespace(returncode=0,stdout=b'12345\n')
        with patch.object(control,'check',return_value=expected),patch.object(control.subprocess,'run',side_effect=fake):
            control.submit(p,'c')
            control.submit(p,'g')
            with self.assertRaisesRegex(ValueError,'already attempted'):control.submit(p,'g')
        self.assertEqual(len(calls),2)
        cpu,cpu_kw=calls[0];args,kw=calls[1]
        normalize=lambda values:[v for v in values if not v.startswith(('--export=', '--gres='))]
        self.assertEqual(normalize(cpu),normalize(args))
        self.assertEqual(cpu_kw,kw)
        self.assertIn('--export=A_M=c',cpu);self.assertIn('--export=A_M=g',args)
        self.assertIn('--chdir=/tmp',cpu)
        self.assertTrue(any(v.startswith('--output=/tmp/') for v in cpu))
        self.assertTrue(any(v.startswith('--error=/tmp/') for v in cpu))
        for flag in ('--partition=general','--gres=gpu:1','--cpus-per-task=16','--mem=200G',
                     '--time=00:30:00','--exclude=orchard-community-4','--no-requeue'):
            self.assertIn(flag,args)
        self.assertEqual(kw['input'],FILES['4.sh'])
        body=(ROOT/'src/runtime.py').read_text()
        self.assertIn('time.time()+1500',body)
        self.assertNotIn('generate_real(',body)
        self.assertNotIn('perception_factory(',body)
        self.assertNotIn('.respond(',body)

    def test_operator_compatibility_and_namespace_rejection(self):
        source=(ROOT/'src/control.py').read_text()
        ast.parse(source,feature_version=(3,6))
        self.assertNotIn('file_digest',source)
        self.assertNotIn('capture_output=',source)
        self.assertNotIn('.removeprefix(',source)
        control=module('control_compat',ROOT/'src/control.py')
        for term in builder.DENY:
            with self.assertRaises(ValueError):control.opaque(['/tmp/'+term])
            with self.assertRaises(ValueError):control.opaque(['A_X='+term])
        control.opaque(['a15_cot_apabcdef123'])
        self.assertEqual(set(control.EXTERNAL), {'--dev-bind','/dev'})
        with self.assertRaises(ValueError):control.opaque(['CUDA_VISIBLE_DEVICES=ground'])

    def test_sealed_package(self):
        pins=json.loads(FILES['0.json'])
        self.assertEqual(set(pins['files']),set(FILES)-{'0.json'})
        for name,pin in pins['files'].items():self.assertEqual(pin,builder.pin(FILES[name]))
        for name in PAYLOAD:self.assertEqual(PAYLOAD[name],FILES[name])

    def test_score_gate_bootstrap_and_incomplete(self):
        mapping=json.loads((ROOT/'PAIR_MAP.json').read_text())
        rows=[dict(i=m['i'],r=m['r'],a=a,text='<ground',tokens=[1],n=1,g=True,o=[],finish='call') for m in mapping for a in (0,1)]
        f=json.loads((ROOT/'FROZEN.json').read_text())
        receipt=dict(frozen=hashlib.sha256((ROOT/'FROZEN.json').read_bytes()).hexdigest(),
            artifact=f['checkpoint']['artifact']['sha256'],mode='g',tools_served=0,
            max_new_tokens=64,external_components_loaded=False,records=580,passed=True)
        result=score.score(rows,receipt)
        self.assertEqual(result['gate'],'no change')
        self.assertEqual(result['REVSI_minus_ORIG']['ci95'],[0,0])
        for j in range(15):rows[2*j+1].update(text='done',tokens=[1],n=1,g=False,finish='eos')
        result=score.score(rows,receipt)
        self.assertEqual(result['gate'],'report to orchestrator via lane')
        self.assertEqual(result,score.score(rows,receipt))
        self.assertEqual(result['draws'],10000);self.assertEqual(result['seed'],20261120)
        self.assertEqual(score.score(rows[:-1],dict(receipt,records=579,passed=False))['gate'],'incomplete; no verdict')
        with self.assertRaises(AssertionError):score.score(rows+[rows[0]],dict(receipt,records=581))
        wrong=copy.deepcopy(rows);wrong[0]['n']=65
        with self.assertRaises(AssertionError):score.score(wrong,receipt)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ProbeTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    (ROOT/'TEST_RESULTS.json').write_text(json.dumps(dict(passed=result.wasSuccessful(),tests=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),synthetic=True,
        frozen=hashlib.sha256((ROOT/'FROZEN.json').read_bytes()).hexdigest(),
        delivery=builder.pin((ROOT/'out/delivery.tgz').read_bytes())),sort_keys=True,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
