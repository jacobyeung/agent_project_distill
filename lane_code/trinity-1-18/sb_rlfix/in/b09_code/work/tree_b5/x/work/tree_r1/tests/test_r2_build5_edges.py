"""Small byte fixtures for CPU-reachable refusal branches."""
import base64
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tarfile
import unittest
import os
from unittest.mock import patch
from tests.test_r2_data_path import directory, fixture, LANE
from student_pilot.p3_provenance import file_pin, load, write


class Edges(unittest.TestCase):
    def test_legacy_arithmetic_and_measurement_boundaries(self):
        from student_pilot import r2_grammar as G
        for expression,allowed in [('1/0',{0,1}),('1+',{1}),('1e308*1e308',{1e308})]:
            with self.assertRaises(ValueError):G.arithmetic(expression,allowed)
        start='Locate: the chair is seen in frame 1.\n'
        question='Which chair is closer to the table? 1 2'
        def target(body):return '<think>\n'+start+body+'\n</think>\nA'
        self.assertEqual(G.legacy_direct(target('Step: compute 1+1 = 2.'),question,32),'A')
        with self.assertRaisesRegex(ValueError,'result differs'):
            G.legacy_direct(target('Step: compute 1+1 = 3.'),question,32)
        with self.assertRaisesRegex(ValueError,'states a measurement'):
            G.legacy_direct(target('Relate: the chair is 1 m to the right of the table.'),question,32)

    def test_statement_receipt_trace(self):
        import sys
        from launch_r2 import runtime
        selected=[dict(source=dict(path=runtime.__file__),line=1,category='fixture')]
        previous=sys.gettrace()
        try:
            sys.settrace(lambda frame,event,arg: None)
            with runtime.statement_hits(selected) as hits:
                runtime.obligations()
            self.assertTrue(any(path==runtime.__file__ for path,line in hits))
            with self.assertRaisesRegex(ValueError,'not reached'):runtime.checked_hits(selected,hits)
        finally:
            sys.settrace(previous)

    def test_plan_unknown_inputs_and_worker_environment(self):
        from launch_r2.plan import make
        from launch_r2.distributed import worker
        base=LANE/'work/kit07ca49df_meta/m'
        with self.assertRaisesRegex(ValueError,'Unknown relative'):
            make(dict(path='u/none'),{},base)
        with self.assertRaisesRegex(ValueError,'Unresolved relative'):
            make(dict(path='u/none'),{'/unknown':'u/none'},base)
        for original in ('/models/test','/art/test'):
            result=make(dict(path='u/one'),{original:'u/one'},base)
            self.assertIn('directory',result['entries']['u/one'])
        result=make(dict(input=dict(path='u/new',sha256='0'*64)),{},base)
        self.assertIn('parts',result['entries']['u/new'])
        root=directory();write(root/'k/7.json',dict(files={}))
        with patch.dict(os.environ,K2=str(Path(__file__).parents[1]),K4='fixture-map'):
            with self.assertRaisesRegex(ValueError,'Worker source differs'):worker(root,'t','0')
            self.assertEqual(os.environ['STUDENT_FRAME_ROOT_MAP'],'fixture-map')

    def test_capsules_and_real_archive_staging(self):
        from launch_r2 import staging as S, bootstrap as B, build
        from student_pilot import p3_provenance as P
        root=directory();raw=b'fixture';h=hashlib.sha256(raw).hexdigest()
        path=root/'v.json';path.write_bytes(build.capsule_json(dict(x=1)))
        self.assertEqual(S.read(path),{'x':1});self.assertEqual(B.read(path),{'x':1})
        value=json.loads(path.read_text());value['sha256']='0'*64;path.write_text(json.dumps(value))
        for reader in (S.read,B.read,P.load):
            with self.assertRaisesRegex(ValueError,'Capsule'):reader(path)
        with self.assertRaisesRegex(ValueError,'Unexpected'):
            build.scan_value(dict(value,extra=True),{})
        (root/'a').write_bytes(raw[:2]);(root/'b').write_bytes(raw[2:])
        self.assertEqual(S.assemble(dict(parts=[str(root/'a'),str(root/'b')],sha256=h),root/'joined').read_bytes(),raw)
        with self.assertRaisesRegex(ValueError,'inventory'):
            S.assemble(dict(parts=[]),root/'empty')
        S.assemble(dict(parts=[],inventory={'x':h}),root/'inventory')
        with self.assertRaisesRegex(ValueError,'Unresolved'):
            S.validate_plan(dict(path='u/a'),{'u/a':{}})
        archive=root/'one.tar'
        with tarfile.open(archive,'w') as f:
            m=tarfile.TarInfo('f');m.size=len(raw);f.addfile(m,io.BytesIO(raw))
        source=dict(parts=[str(archive)],sha256=file_pin(archive)['sha256'],inventory={'f':h})
        entries={'u/a':dict(archive=source,member='f',sha256=h),
                 'u/b':dict(archive=source,member='f',sha256=h),
                 'u/c':dict(directory=source,member='',sha256=source['sha256'])}
        S.stage_inputs(entries,root/'staged')
        self.assertEqual((root/'staged/u/a').read_bytes(),raw)
        self.assertEqual((root/'staged/u/c/f').read_bytes(),raw)
        with self.assertRaisesRegex(ValueError,'target escaped'):
            S.stage_inputs({'../escape':entries['u/a']},root/'unsafe_target')
        with self.assertRaisesRegex(ValueError,'member escaped'):
            S.stage_inputs({'u/a':{**entries['u/a'],'member':'../f'}},root/'unsafe_member')
        with self.assertRaisesRegex(ValueError,'inventory escaped'):
            S.stage_inputs({'u/a':{**entries['u/a'],'archive':{**source,'inventory':{'../f':h}}}},root/'unsafe_inventory')
        with self.assertRaisesRegex(ValueError,'archive identity'):
            S.stage_inputs({'u/a':{**entries['u/a'],'archive':{**source,'sha256':'../escape'}}},root/'unsafe_identity')
        for name,link in [('inside','f'),('outside','../../escape')]:
            p=root/(name+'.tar')
            with tarfile.open(p,'w') as f:
                m=tarfile.TarInfo('f');m.size=len(raw);f.addfile(m,io.BytesIO(raw))
                m=tarfile.TarInfo('s');m.type=tarfile.SYMTYPE;m.linkname=link;f.addfile(m)
            if name=='outside':
                with self.assertRaisesRegex(ValueError,'escaped'):S.unpack(p,root/name)
            else:S.unpack(p,root/name)
        (root/'bw').write_bytes(b'not executable; command construction only')
        command=S.command(root,'h',root/'local',dict(bwrap={'file':str(root/'bw'),'sha256':file_pin(root/'bw')['sha256']}))
        self.assertIn('--unshare-user',command)

    def test_parent_and_bank_refusals(self):
        from launch_r2.parent import validate_parent
        from student_pilot import r2_policy as P, r2_openers as O
        parent=load(LANE/'work/kit07ca49df_meta/m/k/b02e4385.json')
        parent['streams']['pose']={}
        with self.assertRaisesRegex(ValueError,'stream record'):validate_parent(parent)
        root=directory();write(root/'bank.json',[{'id':'same'},{'id':'same'}])
        with self.assertRaisesRegex(ValueError,'Repeated'):P.seal_catalog({'dev-S1':file_pin(root/'bank.json')})
        with self.assertRaisesRegex(ValueError,'Unknown'):O.preparation(dict(routing_opener_init='other'))

    def test_legacy_grammar_cases(self):
        from student_pilot import r2_grammar as G
        question='Which chair is closest to the table?'
        prefix='Locate: the chair is seen in frame 1.\n'
        cases=['', '<tool_response>x</tool_response>', 'Locate: at 2 seconds.', 'Locate: 12cm tall.',
            'Locate: two chairs.', 'nonsense', 'Locate: chair in frame 0.',
            prefix+'Locate: the chair is seen in frame 2.', 'Relate: the chair is right.',
            prefix+'Relate: the lamp is uncertain.', prefix+'Step: list [chair;chair]; count = 2.',
            prefix+'Step: compute 1+1 = 3.',prefix+'Step: compute 1+1 = 2.',
            prefix+'Step: nonsense.',prefix+'Relate: the chair is 57 right.',
            prefix+'Relate: the chair is 1 m right.',prefix+'Step: list [the chair]; count = 1.']
        outcomes=[]
        for body in cases:
            try:outcomes.append(G.legacy_direct('<think>\n'+body+'\n</think>\nA',question,32))
            except ValueError as error:outcomes.append(str(error))
        self.assertTrue(all(outcomes))
        with self.assertRaises(ValueError):G.arithmetic('1//1',{1.0})
        with self.assertRaises(ValueError):G.legacy_direct('x',question,32)

    def test_native_mix_empty_wrong_and_complete(self):
        from student_pilot import r2_mix as M
        from tests.test_r2_sampling import binding
        root=directory();pins,_,_=binding(root);spec=dict(mix_pin=pins['mix'],counts_pin=pins['counts'])
        with self.assertRaisesRegex(ValueError,'Empty'):M.check_actual([],spec)
        with self.assertRaisesRegex(ValueError,'membership'):M.check_actual([dict(stream='vqa')],spec)
        small=[dict(stream=c['stream'],mix_cell=dict(type=c['type'])) for c in M.table()['cells']]
        with self.assertRaisesRegex(ValueError,'repeats'):M.check_actual(small,spec)
        large=[]
        populations=load(pins['counts']['path'])['cells']
        for c in M.table()['cells']:
            large.extend([dict(stream=c['stream'],mix_cell=dict(type=c['type']))]*populations[c['type']])
        self.assertEqual(M.check_actual(large,spec),populations)
        with self.assertRaisesRegex(ValueError,'membership'):M.reindex([dict(stream='vqa')],spec,root/'wrong')
        with self.assertRaisesRegex(ValueError,'pair identity'):
            M.reindex([dict(stream='vqa',mix_cell=dict(type='facing_pairs'))],spec,root/'pair')
