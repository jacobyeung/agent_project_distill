"""CPU contracts; no GPU, network, SSH, model loading, or fixture deletion."""
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import uuid
import types
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import torch
torch.set_num_threads(8)
from common228 import Refusal,read,write,sha,canonical,deployment,source_check
import stage228
import gpu228
import observe228
import compare228
import return228
import common228

WORK=Path(os.environ.get('READ228_TEST_WORK','/scratch/jjyeung/orch_n30/so_reads228/work/tests_round1'))
WORK.mkdir(parents=True,exist_ok=True)
stage228.STAGE=WORK/"stage"

def directory():
    path=WORK/('a'+uuid.uuid4().hex);path.mkdir();return path

def copy_reference(*, local_provenance=True):
    dest=directory()
    for p in (HERE/'reference').rglob('*'):
        if p.is_file():
            target=dest/p.relative_to(HERE/'reference');target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,target)
    if local_provenance:
        write(dest/'SUMMARY.json',dict(completed=50,failure=None,complete=False))
        write(dest/'metadata/LOCAL_RUN.json',dict(backend='trinity-local',host='trinity-2-28',mode='OFF',synthetic_cpu_fixture=True))
        write(dest/'metadata/CARDS.json',dict(snapshot=dict(name='NVIDIA RTX 6000 Ada Generation')))
        identity=read(dest/'metadata/RETURN_ID.json');identity['job']='314159265'
        identity['token']=identity['token'][:-8]+format(314159265,'08x');write(dest/'metadata/RETURN_ID.json',identity)
        for path in (dest/'metadata/reads').glob('*/metadata/journals/*/*/environment.json'):
            value=read(path);value['host']='trinity-2-28';write(path,value)
    return dest

def edit_rows(root, change):
    p=root/'metadata/reads/0/metadata/journals/3/0/items.jsonl'
    rows=[json.loads(line) for line in p.read_text().splitlines()]
    change(rows)
    p.write_text(''.join(json.dumps(r)+'\n' for r in rows))

class PackageTests(unittest.TestCase):
    def test_effective_export_matches_sealed_plan(self):
        root,cfg,inputs,export=deployment(HERE/'A10b/package')
        self.assertEqual(export['step'],400)
        self.assertEqual(export['member_directory'],cfg['export_binding']['member_directory'])
        self.assertEqual(inputs['archives'][0]['sha256'],export['archive_sha256'])
        self.assertIn('/m544/',read(root/'package/a/0.json')['files']['heads']['path'])

    def test_source_and_operator_remain_sealed(self):
        pins=read(HERE/'A10b_PINS.json');source_check(HERE/'A10b/src',pins['source'])
        for name,digest in read(HERE/'A10b/package/PACKAGE.json')['files'].items():
            self.assertEqual(sha(HERE/'A10b/package'/name),digest)
        self.assertEqual(sha(HERE/'A10b/tower_sequence.py'),pins['operator_sha256'])

    def test_first50_is_original_schedule_prefix(self):
        fixed=read(HERE/'FIRST50.json');items=read(HERE/'A10b/src/items/devs1_routed.json')['items']
        wanted=[r['id'] for r in items if r['question_type']=='object_abs_distance'][:50]
        self.assertEqual(wanted,[r['id'] for r in fixed['items']])
        self.assertEqual(len(fixed['full_order']),636)

    def test_stage_budget_under_150gb(self):
        budget=read(HERE/'STAGE_PLAN.json')['budget']
        self.assertLess(budget['estimated_peak_bytes'],150_000_000_000)
        self.assertEqual(budget['estimated_peak_bytes'],124166664744)

    def test_path_map_preserves_pins_and_never_uses_project(self):
        plan=read(HERE/'STAGE_PLAN.json');mapping=stage228.archive_map(plan)
        original=read(HERE/'A10b/package/a/1.json');before=deepcopy(original)
        for group in original['archives']:
            for part in group['parts']:
                mapped=stage228.mapped_part(part,mapping)
                self.assertTrue(str(mapped).startswith('/scratch/jjyeung/orch_n30/reads228/'))
                self.assertNotIn('/project/',str(mapped))
        self.assertEqual(before,original)

    def test_unmapped_path_refused(self):
        with self.assertRaisesRegex(Refusal,'No local staging map'):
            stage228.mapped_part(dict(path='/project/unknown'),{})

    def test_wrong_sha_and_missing_file_refused(self):
        from common228 import checked
        p=directory()/'weight';p.write_bytes(b'abc')
        with self.assertRaisesRegex(Refusal,'Wrong sha256'):
            checked(p,dict(bytes=3,sha256='0'*64))
        with self.assertRaisesRegex(Refusal,'Missing file'):
            checked(p.with_name('missing'),dict(bytes=3,sha256=sha(p)))

    def test_wrong_size_refused_before_hash(self):
        from common228 import checked
        p=directory()/'weight';p.write_bytes(b'abc')
        with patch('common228.sha',side_effect=AssertionError('must not hash')):
            with self.assertRaisesRegex(Refusal,'Wrong size'):checked(p,dict(bytes=9,sha256='0'*64))

    def test_shell_launch_refuses_wrong_node_without_gpu_query(self):
        result=subprocess.run(['bash',str(HERE/'run228.sh'),str(HERE/'A10b'),'0',str(directory()/'out')],
                              env=dict(os.environ,READ228_CONTROL_PYTHON=sys.executable,READ228_CONTROL_ROOT=str(WORK/"control")),text=True,capture_output=True)
        self.assertEqual(result.returncode,2)
        self.assertIn('restricted to trinity-2-28',result.stderr)

    def test_preparation_receipt_selects_exact_versions(self):
        env=dict(versions=read(HERE/'STAGE_PLAN.json')['environment']['versions'],
                 python='/scratch/jjyeung/orch_n30/reads228/runtime/m/ap/19252904/e/bin/python',cuda='13.0',
                 prefix='/scratch/jjyeung/orch_n30/reads228/runtime/m/ap/19252904/e',
                 base_prefix='/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu',module_paths={},
                 python_version=[3,12,13],audit_roots=['/scratch/jjyeung/orch_n30/reads228/runtime/m/ap/19252904/e/lib/python3.12/site-packages'])
        result=types.SimpleNamespace(returncode=0,stdout=json.dumps(env),stderr='')
        with patch('stage228.subprocess.run',return_value=result):
            self.assertEqual(stage228.versions('python',dict(versions=env['versions']),{'TMPDIR':str(directory())})['versions'],env['versions'])
            with self.assertRaisesRegex(Refusal,'versions differ'):
                stage228.versions('python',dict(versions={}),{'TMPDIR':str(directory())})
        env['cuda']=None;result.stdout=json.dumps(env)
        with patch('stage228.subprocess.run',return_value=result):
            with self.assertRaisesRegex(Refusal,'CUDA-enabled'):
                stage228.versions('python',dict(versions=env['versions']),{'TMPDIR':str(directory())})

class StreamTests(unittest.TestCase):
    def fixture(self, *, unsafe=False):
        root=directory();buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode='w') as t:
            e=tarfile.TarInfo('../escape' if unsafe else 'm200/weight');e.size=3;t.addfile(e,io.BytesIO(b'abc'))
        raw=buf.getvalue();parts=[];mapping={}
        for i,b in enumerate((raw[:1000],raw[1000:])):
            p=root/str(i);p.write_bytes(b);name='/project/'+str(i)
            parts.append(dict(path=name,bytes=len(b),sha256=sha(p)));mapping[name]=p
        return root,dict(parts=parts,expanded_bytes=3,sha256=hashlib.sha256(raw).hexdigest()),mapping

    def test_ordered_stream_extract_and_reuse(self):
        root,group,mapping=self.fixture()
        record=stage228.extract_group(group,mapping,root/'dest')
        self.assertEqual((root/'dest/m200/weight').read_bytes(),b'abc')
        self.assertEqual(stage228.extract_group(group,mapping,root/'dest'),record)

    def test_wrong_part_sha_refuses(self):
        root,group,mapping=self.fixture();group['parts'][0]['sha256']='0'*64
        with self.assertRaisesRegex(Refusal,'part pin'):
            stage228.extract_group(group,mapping,root/'dest')

    def test_existing_member_mismatch_is_preserved(self):
        root,group,mapping=self.fixture();p=root/'dest/m200/weight';p.parent.mkdir(parents=True);p.write_bytes(b'bad')
        with self.assertRaisesRegex(Refusal,'Existing archive members differ'):
            stage228.extract_group(group,mapping,root/'dest')
        self.assertEqual(p.read_bytes(),b'bad')

    def test_unsafe_tar_refuses(self):
        root,group,mapping=self.fixture(unsafe=True)
        with self.assertRaisesRegex(Refusal,'Unsafe'):
            stage228.extract_group(group,mapping,root/'dest')

class IdleTests(unittest.TestCase):
    def idle(self):
        return dict(uuid='GPU-0123456789abcdef',name='NVIDIA RTX 6000 Ada Generation',memory_used_mib=0,
                    memory_total_mib=49140,processes=[])

    def test_two_readings_at_least_five_minutes_apart(self):
        now=[0];calls=[]
        def get(card):calls.append((card,now[0]));return self.idle()
        def sleep(n):now[0]+=n
        evidence=directory()/'idle.json'
        gpu228.idle_gate('0',evidence,get=get,sleep=sleep,clock=lambda:now[0])
        self.assertEqual(len(calls),2);self.assertEqual(calls[1][1]-calls[0][1],300)
        self.assertTrue(read(evidence)['complete'])

    def test_busy_first_reading_refuses_without_wait(self):
        value=self.idle();value['memory_used_mib']=100
        with self.assertRaisesRegex(Refusal,'busy'):
            gpu228.idle_gate('0',directory()/'idle.json',get=lambda _:value,
                             sleep=lambda _:self.fail('must not wait'))

    def test_process_even_with_zero_memory_refuses(self):
        value=self.idle();value['processes']=[dict(pid='123',type='G')]
        with self.assertRaisesRegex(Refusal,'busy'):gpu228.require_idle(value)

    def test_busy_second_reading_refuses(self):
        values=[self.idle(),self.idle()];values[1]['processes']=[dict(pid='999')];now=[0]
        with self.assertRaisesRegex(Refusal,'busy'):
            gpu228.idle_gate('0',directory()/'idle.json',get=lambda _:values.pop(0),
                sleep=lambda n:now.__setitem__(0,now[0]+n),clock=lambda:now[0])

    def test_uuid_changed_refuses(self):
        values=[self.idle(),self.idle()];values[1]['uuid']='GPU-ffffffffffffffff';now=[0]
        with self.assertRaisesRegex(Refusal,'identity changed'):
            gpu228.idle_gate('0',directory()/'idle.json',get=lambda _:values.pop(0),
                sleep=lambda n:now.__setitem__(0,now[0]+n),clock=lambda:now[0])

    def test_xml_includes_graphics_processes(self):
        xml='''<nvidia_smi_log><driver_version>example</driver_version><gpu><uuid>GPU-0123456789abcdef</uuid>
        <product_name>NVIDIA RTX 6000 Ada Generation</product_name><fb_memory_usage><used>0 MiB</used><total>49140 MiB</total></fb_memory_usage>
        <processes><process_info><pid>42</pid><type>G</type></process_info></processes></gpu></nvidia_smi_log>'''
        result=gpu228.snapshot('0',run=lambda *a,**k:types.SimpleNamespace(stdout=xml))
        self.assertEqual(result['processes'][0]['type'],'G')
        with self.assertRaisesRegex(Refusal,'busy'):gpu228.require_idle(result)

    def test_multiple_cards_and_wrong_device_refuse(self):
        with self.assertRaises(Refusal):gpu228.card_name('0,1')
        value=self.idle();value['name']='NVIDIA H100'
        with self.assertRaisesRegex(Refusal,'RTX'):gpu228.require_idle(value)

class ObservationTests(unittest.TestCase):
    def fixture(self, error=None):
        out=directory();events=[];payload=dict(text='unchanged',tokens=[1],finish='eos')
        def factory(*a,**k):
            def generate(item):
                events.append(('generate',item['id']))
                if error:raise error
                return payload
            return generate
        parity=types.SimpleNamespace(make_real=factory)
        launch=types.SimpleNamespace(commit_record=lambda f,r:events.append(('commit',r['id'])))
        cuda=types.SimpleNamespace(OutOfMemoryError=torch.cuda.OutOfMemoryError,
            synchronize=lambda d:events.append(('sync',d)),reset_peak_memory_stats=lambda d:events.append(('reset',d)),
            max_memory_allocated=lambda d:123,max_memory_reserved=lambda d:456)
        stub=types.SimpleNamespace(cuda=cuda)
        state=observe228.install(parity,launch,stub,out,out/'STOP',1,enabled=True)
        return out,events,payload,parity,launch,state

    def test_off_requires_explicit_observer_activation(self):
        with self.assertRaisesRegex(ValueError,'OFF'):
            observe228.install(None,None,None,None,None,None)

    def test_observer_keeps_output_and_stops_only_after_commit(self):
        out,events,payload,parity,launch,state=self.fixture()
        gen=parity.make_real();got=gen(dict(id='one'))
        self.assertIs(got,payload);self.assertFalse((out/'STOP').exists())
        launch.commit_record(None,dict(id='one',output=got,complete=True))
        self.assertTrue((out/'STOP').is_file());self.assertEqual(state['committed'],['one'])
        rows=[json.loads(line) for line in (out/'telemetry/memory.jsonl').read_text().splitlines()]
        self.assertEqual([r['phase'] for r in rows],['load','item'])
        self.assertEqual(rows[1]['max_memory_reserved'],456)
        self.assertEqual(sum(e[0]=='reset' for e in events),1)

    def test_first_oom_is_reported_and_never_committed_or_retried(self):
        out,events,payload,parity,launch,state=self.fixture(torch.cuda.OutOfMemoryError('synthetic CUDA OOM'))
        with self.assertRaises(torch.cuda.OutOfMemoryError):parity.make_real()(dict(id='one'))
        self.assertEqual(sum(e[0]=='generate' for e in events),1)
        self.assertEqual(state['committed'],[]);self.assertEqual(read(out/'telemetry/OOM.json')['item'],'one')
        self.assertTrue((out/'STOP').exists())

class CompareTests(unittest.TestCase):
    def test_identical(self):
        result=compare228.compare(HERE/'reference',HERE/'reference')
        self.assertEqual(result['verdict'],'DIAGNOSTIC_ONLY')
        self.assertFalse(result['eligible'])
        self.assertIn('trinity: missing LOCAL_RUN.json',result['ineligibility_reasons'])

    def test_changed_orchard_baseline_cannot_establish_parity(self):
        dest=copy_reference()
        edit_rows(dest,lambda rows:rows[0]['output']['tokens'].append(1234567))
        result=compare228.compare(dest,dest)
        self.assertEqual(result['verdict'],'DIAGNOSTIC_ONLY')
        self.assertIn('Orchard baseline bytes differ',result['ineligibility_reasons'][0])

    def test_one_answer_differs_is_49_of_50(self):
        dest=copy_reference()
        def change(rows):
            row=next(r for r in rows if r['output']['finish']!='max_calls')
            row['output']['text']+='<answer>synthetic changed answer</answer>'
        edit_rows(dest,change);result=compare228.compare(HERE/'reference',dest)
        self.assertEqual(result['verdict'],'SAME_INSTRUMENT');self.assertEqual(result['identical']['answer'],49)
        self.assertEqual(result['identical']['call_placement'],50)

    def test_two_answers_differ_is_diagnostic(self):
        dest=copy_reference()
        def change(rows):
            for row in [r for r in rows if r['output']['finish']!='max_calls'][:2]:
                row['output']['text']+='<answer>synthetic changed answer</answer>'
        edit_rows(dest,change);result=compare228.compare(HERE/'reference',dest)
        self.assertEqual(result['verdict'],'DIAGNOSTIC_ONLY');self.assertEqual(result['identical']['answer'],48)

    def test_one_call_moved_is_diagnostic(self):
        dest=copy_reference()
        def change(rows):
            row=next(r for r in rows if r['output']['calls']['records'])
            row['output']['calls']['records'][0]['at_token']+=1
        edit_rows(dest,change);result=compare228.compare(HERE/'reference',dest)
        self.assertEqual(result['verdict'],'DIAGNOSTIC_ONLY');self.assertEqual(result['identical']['answer'],50)
        self.assertEqual(result['identical']['call_placement'],49)

    def test_call_argument_change_is_diagnostic(self):
        dest=copy_reference()
        def change(rows):
            row=next(r for r in rows if r['output']['calls']['records'])
            row['output']['calls']['records'][0]['call']+=' changed_argument=1'
        edit_rows(dest,change);result=compare228.compare(HERE/'reference',dest)
        self.assertEqual(result['identical']['call_placement'],49)

    def test_trace_drift_is_reported_but_does_not_change_fixed_rule(self):
        dest=copy_reference()
        edit_rows(dest,lambda rows:rows[0]['output']['tokens'].append(1234567))
        result=compare228.compare(HERE/'reference',dest)
        self.assertEqual(result['verdict'],'SAME_INSTRUMENT');self.assertEqual(result['identical']['trace'],49)
        self.assertTrue(result['per_item'][0]['trace_diff'])

    def test_wrong_order_wrong_export_and_on_are_ineligible(self):
        dest=copy_reference()
        edit_rows(dest,lambda rows:rows.__setitem__(slice(0,2),[rows[1],rows[0]]))
        export=read(dest/'metadata/EXPORT_PIN.json');export['step']=544;write(dest/'metadata/EXPORT_PIN.json',export)
        write(dest/'metadata/LOCAL_RUN.json',dict(mode='ON',backend='trinity-local'))
        result=compare228.compare(HERE/'reference',dest)
        self.assertFalse(result['eligible']);self.assertGreaterEqual(len(result['ineligibility_reasons']),3)

    def test_missing_item_and_torn_journal_fail_closed(self):
        dest=copy_reference();edit_rows(dest,lambda rows:rows.pop())
        result=compare228.compare(HERE/'reference',dest)
        self.assertEqual(result['verdict'],'DIAGNOSTIC_ONLY');self.assertEqual(result['per_item'][-1]['missing'],'trinity')
        p=dest/'metadata/reads/0/metadata/journals/3/0/items.jsonl'
        with p.open('a') as f:f.write('{')
        with self.assertRaisesRegex(Refusal,'Torn'):compare228.compare(HERE/'reference',dest)

class ReturnTests(unittest.TestCase):
    def test_partial_return_accepted_by_original_a4_unpacker(self):
        # Real Orchard records exercise the actual unmodified unpacker. This is a layout test, not an Ada run.
        out=directory();ret=out/'ret'
        for p in (HERE/'reference').rglob('*'):
            if p.is_file():
                target=ret/p.relative_to(HERE/'reference');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        public=read(HERE/'A10b/package/0.json')
        return228.new_return_identity(out,public)
        summary=dict(completed=50,expected=636,complete=False,failure=None,reads=[dict(read=0,completed=50,expected=636,complete=False)])
        receipt=return228.package_return(out,public,summary,0)
        # The original unpacker requires its output under the operator workspace.
        operator=out/'operator';operator.mkdir()
        for name in ('tower_sequence.py','unpack_return.py','fetch_return.py'):
            shutil.copyfile(HERE/'A10b'/name,operator/name)
        (operator/'src').symlink_to(HERE/'A10b/src',target_is_directory=True)
        (operator/'package').symlink_to(HERE/'A10b/package',target_is_directory=True)
        accepted=out/'accepted'
        command=[sys.executable,'-I','-s','-B',str(HERE/'unpack228.py'),'--operator',str(operator),
                 '--archive',receipt['archive'],'--exit',receipt['exit'],'--out',str(accepted)]
        result=subprocess.run(command,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        response=json.loads(result.stdout);self.assertFalse(response['complete'])
        self.assertEqual(read(accepted/'SUMMARY.json')['expected'],636)
        self.assertFalse((accepted/'COMPLETE.json').exists())
        (WORK/'unpack_success.json').write_text(json.dumps(dict(command=command,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr),indent=2)+'\n')

    def test_no_complete_marker_on_oom(self):
        out=directory();public=read(HERE/'A10b/package/0.json');return228.new_return_identity(out,public)
        result=return228.package_return(out,public,dict(completed=0,expected=636,complete=False),42,failure='OOM')
        self.assertFalse(result['complete']);self.assertFalse((out/'ret/COMPLETE.json').exists())
        self.assertEqual(read(result['exit'])['returncode'],42)

class IntegrationTests(unittest.TestCase):
    def test_original_reader_resolver_accepts_observed_factory(self):
        # Exercise the real source-location guard, twice as the type loop does.
        code='''from pathlib import Path
import sys,types,inspect
sys.path.insert(0,sys.argv[1])
from common228 import install_imports
root=Path(sys.argv[1]);install_imports(root/'A10b/src')
from e2e_reader import parity
from h1eval.h10 import launch,parity_adapter
from observe228 import install
original=parity.make_real
state=install(parity,launch,None,None,None,None,enabled=True)
for i in range(2):
    result=launch.reader_factory(root/'A10b/src/b')
    assert result is parity_adapter.make_capped_real
    assert Path(inspect.getsourcefile(result)).name=='parity_adapter.py'
assert parity.make_real is not original
state['restore']()
assert parity.make_real is original
print('sealed resolver and maker binding unchanged')
'''
        p=directory()/'resolver.py';p.write_text(code)
        result=subprocess.run([sys.executable,'-I','-s','-B',str(p),str(HERE)],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('unchanged',result.stdout)

    def test_full_adapter_orchestration_with_cpu_worker_double(self):
        sys.path.insert(0,str(HERE/'tests'))
        from test_review3 import full_adapter
        full_adapter(self,HERE,directory())

    def test_on_refuses_unverified_overlay_delivery(self):
        import runner228
        with self.assertRaisesRegex(Refusal,'ON needs prepared'):
            runner228.extensions()

    def test_local_budget_deduplicates_links_and_nested_roots(self):
        root=directory();p=root/'a';p.write_bytes(b'abc');os.link(p,root/'b')
        (root/'nested').mkdir();(root/'nested/c').write_bytes(b'defg')
        result=stage228.local_bytes([root,root/'nested'])
        self.assertEqual(result['bytes'],7);self.assertEqual(result['files'],2)

if __name__=='__main__':unittest.main(verbosity=2)
