"""CPU crash fixtures. READ_INPUT_SRC points to the read-only A4/src tree."""
import hashlib
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import types
import unittest
import uuid
from unittest.mock import patch

import torch
torch.set_num_threads(8)
SRC=Path(__file__).resolve().parents[2]
INPUT=Path(os.environ['READ_INPUT_SRC'])
sys.path[:0]=[str(SRC),str(INPUT/'tree'),str(INPUT)]
from h1eval.h10 import atomic_journal as J
from h1eval.h10.merge_read import merge,semantic,canonical
from h1eval.h10 import launch
from h1eval import items as item_module

ROOT=Path(os.environ.get('READ_TEST_TMP',str(Path.cwd()/'work/test-artifacts')))


def directory():
    p=ROOT/uuid.uuid4().hex;p.mkdir(parents=True);return p


def row(identifier):
    return dict(id=identifier,arm='tower',mode='none',type='camera_rotation',room_key='room-'+identifier,
                complete=True,seconds=2.,output=dict(text='</think>\n1',tokens=[1,2],finish='eos',
                    calls={'records':[]},heads={'pose9':[-0.,1.]},seconds=1.,timings={'total_s':1.},
                    audit={'violations':[]},perception_memo={'hits':1},scores={'answer':1.}))


class JournalTests(unittest.TestCase):
    def test_torn_utf8_projection_and_commit_before_projection(self):
        root=directory();journal=J.AtomicJournal(root)
        journal.recover();journal.commit(row('a'));journal.commit(row('b'))
        (root/'items.jsonl').write_bytes(J.encoded(row('a'))+b'{"id":"\xe2')
        again=J.AtomicJournal(root);self.assertEqual([r['id'] for r in again.recover()],['a','b'])
        self.assertEqual((root/'items.jsonl').read_bytes(),J.encoded(row('a'))+J.encoded(row('b')))
        self.assertEqual(len(list(root.glob('items.jsonl.recovery.*'))),1)

    def test_interrupted_pending_file_is_not_committed(self):
        root=directory();journal=J.AtomicJournal(root);journal.recover()
        with patch.object(J.os,'replace',side_effect=RuntimeError('simulated interruption before rename')):
            with self.assertRaises(RuntimeError):journal.commit(row('a'))
        self.assertEqual(J.AtomicJournal(root).recover(),[])
        self.assertEqual(len(list((root/'committed').glob('.*pending.*'))),1)
        journal.commit(row('a'));self.assertEqual(len(J.AtomicJournal(root).recover()),1)

    def test_duplicate_corruption_and_unowned_jsonl_fail(self):
        root=directory();journal=J.AtomicJournal(root);journal.recover();journal.commit(row('a'))
        journal.commit(row('a'));self.assertEqual(len(journal.rows),1)
        altered=row('a');altered['output']['text']='changed'
        with self.assertRaisesRegex(ValueError,'Conflicting'):journal.commit(altered)
        (root/'items.jsonl').write_bytes(J.encoded(row('x')))
        with self.assertRaisesRegex(ValueError,'absent'):J.AtomicJournal(root).recover()
        path=root/'committed'/(J.file_key(row('a'))+'.json')
        value=json.loads(path.read_bytes());value['row']['output']['text']='corrupt'
        path.write_bytes(J.encoded(value))
        with self.assertRaisesRegex(ValueError,'Corrupt'):J.AtomicJournal(root).read()

    def test_scene_sets_disjoint_complete_stable_and_colocated(self):
        items=[dict(id=str(i),room_key=str(i//3)) for i in range(13)]
        shards=[J.scene_selected(items,i,4) for i in range(4)]
        self.assertEqual(sorted(r['id'] for s in shards for r in s),sorted(r['id'] for r in items))
        self.assertEqual(sum(len(s) for s in shards),len(items))
        for room in {r['room_key'] for r in items}:
            self.assertEqual(sum(any(r['room_key']==room for r in s) for s in shards),1)
        self.assertEqual(shards,[J.scene_selected(items,i,4) for i in range(4)])


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.root=directory();self.generated=[]
        self.manifest={'name':'fixture','count':5,'items':[
            dict(id=str(i),question_type='camera_rotation',room_key='room-'+str(i//2)) for i in range(5)],
            'item_set_sha256':'fixture-item-set','r0_check':{'pin':{'path':'fixture','sha256':'0'*64}}}
        self.pin=self.root/'pin.json';self.pin.write_text(json.dumps({'lineage':'SFT','step':600}))
        self.patches=[patch.object(launch,'load_manifest',return_value=self.manifest),
                      patch.object(item_module,'read_contract'),patch.object(launch,'sha',return_value='0'*64),
                      patch.object(launch,'code_hash',return_value='1'*64),
                      patch.object(launch,'export_hash',return_value='2'*64)]
        for p in self.patches:p.start()
        self.addCleanup(lambda:[p.stop() for p in reversed(self.patches)])
        self.capture=redirect_stdout(io.StringIO());self.capture.__enter__()
        self.addCleanup(lambda:self.capture.__exit__(None,None,None))

    def args(self,name,shard='0/1',atomic=True,scene=False):
        return types.SimpleNamespace(items=str(self.root/'manifest.json'),shard=shard,types=None,
            arms='tower',modes='none',reader_root=str(INPUT/'b'),reader_entry='fixture:make_real',
            export=str(self.root/'export'),artifact_manifest=str(self.root/'artifact.json'),
            export_pin=str(self.pin),out=str(self.root/name),device='cpu',stop_at=None,finish_by=None,
            stop_file=None,atomic_journal=atomic,scene_shards=scene)

    def make_real(self,export,artifact,items,**kwargs):
        def generate(item):
            self.generated.append(item['id'])
            return row(item['id'])['output']
        return generate

    def test_reader_resume_committed_item_without_regeneration(self):
        args=self.args('resume');original=launch.commit_record
        def interrupted(stream,value):
            if value.get('id')=='1':
                stream.write('{"torn"');stream.flush()
                raise launch.ReadDeadline()
            original(stream,value)
        with patch.object(launch,'commit_record',side_effect=interrupted):
            with self.assertRaises(launch.ReadDeadline):launch.run(args,make_real=self.make_real)
        self.assertEqual(self.generated,['0','1'])
        result=launch.run(args,make_real=self.make_real)
        self.assertEqual(result,dict(added=3,skipped=2,completed=5,expected=5))
        self.assertEqual(self.generated,['0','1','2','3','4'])
        result=launch.run(args,make_real=self.make_real)
        self.assertEqual(result['added'],0);self.assertEqual(len(self.generated),5)
        changed=self.args('resume',shard='0/2')
        with self.assertRaisesRegex(ValueError,'binding differs'):launch.run(changed,make_real=self.make_real)

    def test_default_path_rejects_torn_tail_and_has_no_commit_store(self):
        args=self.args('default',atomic=False);launch.run(args,make_real=self.make_real)
        root=Path(args.out);self.assertFalse((root/'committed').exists())
        with (root/'items.jsonl').open('ab') as f:f.write(b'{')
        with self.assertRaisesRegex(ValueError,'Incomplete JSONL tail'):launch.run(args,make_real=self.make_real)

    def test_shards_merge_byte_identical_to_single_and_reject_missing_duplicate(self):
        one=self.args('one',scene=True);launch.run(one,make_real=self.make_real)
        shards=[self.args('part'+str(i),shard=f'{i}/3',scene=True) for i in range(3)]
        for args in shards:launch.run(args,make_real=self.make_real)
        first=merge(self.manifest,[one.out],self.root/'merged-one')
        second=merge(self.manifest,[a.out for a in reversed(shards)],self.root/'merged-many')
        self.assertEqual(first,second)
        self.assertEqual((self.root/'merged-one/answer_trace_return.tgz').read_bytes(),
                         (self.root/'merged-many/answer_trace_return.tgz').read_bytes())
        with self.assertRaisesRegex(ValueError,'missing'):merge(self.manifest,[shards[0].out],self.root/'missing')
        with self.assertRaisesRegex(ValueError,'Repeated'):merge(self.manifest,[shards[0].out]*2,self.root/'duplicate')
        bad=Path(shards[0].out)/'environment.json';value=json.loads(bad.read_text())
        value['binding']['export_sha256']='bad';bad.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'bindings differ'):
            merge(self.manifest,[a.out for a in shards],self.root/'bad')

    def test_semantic_comparison_preserves_calls_tokens_scores_and_signed_zero(self):
        a=row('a');b=row('a');b['seconds']=99;b['output']['timings']={'total_s':88}
        self.assertEqual(canonical(semantic(a)),canonical(semantic(b)))
        b['output']['tokens'].append(3)
        self.assertNotEqual(canonical(semantic(a)),canonical(semantic(b)))
        b=row('a');b['output']['heads']['pose9'][0]=0.
        self.assertNotEqual(canonical(semantic(a)),canonical(semantic(b)))

    def test_type_journals_support_empty_scene_shards(self):
        self.manifest['items'][0]['question_type']='camera_displacement'
        roots=[]
        for i in range(3):
            args=self.args('types'+str(i),shard=f'{i}/3',scene=True)
            args.types='camera_displacement,camera_rotation'
            result=launch.run_types(args,make_real=self.make_real)
            roots.extend(sorted(Path(args.out).glob('*/*')))
        result=merge(self.manifest,roots,self.root/'types-merged')
        self.assertEqual(result['items'],5)


if __name__=='__main__':unittest.main(verbosity=2)
