"""Inject local metadata/byte faults while keeping the producer functions real."""
from contextlib import contextmanager
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import unittest
from copy import deepcopy
from tests.test_r2_data_path import directory, LANE
from tests.test_r2_build5_persistence import fixture, records
from student_pilot.p3_provenance import file_pin, load


@contextmanager
def changed_on_read(path, ordinal, action):
    state=dict(active=True,reads=0)
    def audit(event,args):
        if (not state['active'] or event!='open' or not isinstance(args[0],str)
                or Path(args[0])!=path or args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT)):
            return
        state['reads']+=1
        if state['reads']==ordinal:
            state['active']=False
            action()
    sys.addaudithook(audit)
    try:yield state
    finally:state['active']=False


class Faults(unittest.TestCase):
    def test_raw_simulated_miss_keeps_its_printed_response(self):
        from student_pilot.r2_adapters import normalize
        raw=json.loads(next((LANE/'rows/slices_final/a0_recovery.jsonl').open()))
        record={**deepcopy(raw['ground_record']), 'suffix':raw['target'],
                'canonical':raw['provenance']['canonical'],'frame_indices':raw['frame_indices'],
                'provenance':deepcopy(raw['provenance'])}
        indices=raw['frame_indices'];fps=raw['provenance']['fps_source']['value']
        frames={raw['qid']:dict(fps=fps,total_num_frames=max(indices)+1,
            frames=[dict(path='/fixture/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
        result=normalize(record,frames)
        self.assertEqual(result['target'],raw['target'])
        self.assertTrue(any(e.get('audit',{}).get('status')=='not seen' for e in result['ground_record']['events']))

    def test_validator_source_pin_refuses_changed_bytes(self):
        from student_pilot import r2_grammar as G
        root=directory();path=root/'changed.py';path.write_text('fixture = True\n')
        previous=G.shared.__file__
        try:
            G.shared.__file__=str(path)
            with self.assertRaisesRegex(ValueError,'Shared grammar digest differs'):G.check_shared()
        finally:G.shared.__file__=previous

    def test_published_span_and_raw_response_refusals(self):
        from student_pilot.r2_adapters import normalize
        with self.assertRaisesRegex(ValueError,'paired with a printed call'):
            normalize(dict(suffix='<tool_response>unsupported</tool_response>'))
        raw=json.loads(next((LANE/'rows/slices_final/a0_units.jsonl').open()))
        raw={k:v for k,v in raw.items() if k!='events'}
        raw['tool_output_spans'][0]['start']+=1
        with self.assertRaisesRegex(ValueError,'Published event target or response spans differ'):normalize(raw)

    def test_render_integrity_after_native_validation(self):
        from student_pilot.r2_adapters import normalize
        from student_pilot import r2_contract as C, ground_rows
        raw=json.loads(next((LANE/'rows/slices_final/a0_units.jsonl').open()))
        indices=raw['frame_indices'];fps=raw['provenance']['fps_source']['value']
        frames={raw['qid']:dict(fps=fps,total_num_frames=max(indices)+1,
            frames=[dict(path='/fixture/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
        row=normalize(raw,frames)
        C.event_row(row)
        bad=deepcopy(row);bad['ground_record']['unit']='unknown'
        with self.assertRaisesRegex(ValueError,'Unknown absolute label unit'):ground_rows.validate(bad)
        previous=sys.getprofile()
        def corrupt(frame,event,arg):
            if event=='return' and frame.f_code is ground_rows.validate.__code__:
                frame.f_locals['row']['tool_output_spans'][0]['start']+=1
        try:
            sys.setprofile(corrupt)
            with self.assertRaisesRegex(ValueError,'R2 events differ'):C.event_row(row)
        finally:sys.setprofile(previous)

    def test_parent_configuration_result_integrity(self):
        from launch_r2.parent import reproduce
        from student_pilot.r2_config import configure
        previous=sys.getprofile()
        def corrupt(frame,event,arg):
            if event=='return' and frame.f_code is configure.__code__ and isinstance(arg,dict):
                arg['injected_fixture_fault']=True
        try:
            sys.setprofile(corrupt)
            with self.assertRaisesRegex(ValueError,'Override-free configuration differs'):
                reproduce(LANE/'work/kit07ca49df_meta/m',directory()/'result')
        finally:sys.setprofile(previous)

    def test_parent_metadata_changes_between_reads(self):
        from launch_r2.parent import reproduce
        source=LANE/'work/kit07ca49df_meta/m'
        root=directory();base=root/'base';(base/'k').mkdir(parents=True)
        key=load(source/'k/1.json')['0']
        for name in (key+'.json','launch.json','0.json','1.json','7.json'):
            (base/'k'/name).write_bytes((source/'k'/name).read_bytes())
        path=base/'k'/(key+'.json');changed={**load(path),'injected_fixture_fault':True}
        with changed_on_read(path,2,lambda:path.write_text(json.dumps(changed))):
            with self.assertRaisesRegex(ValueError,'serialization differs'):reproduce(base,root/'result')

    def test_archive_inventory_fault(self):
        from launch_r2.persistence import upload
        cfg,state=fixture()
        archive=state.parent/'persist'/(file_pin(state/'artifact.json')['sha256']+'.tar')
        def extra():
            with tarfile.open(archive,'a') as handle:
                item=tarfile.TarInfo('injected');item.size=1
                handle.addfile(item,io.BytesIO(b'x'))
        with changed_on_read(archive,1,extra):
            with self.assertRaisesRegex(ValueError,'Archive inventory differs'):
                upload(cfg,state,'export',records)

    def test_source_bytes_change_during_archive_creation(self):
        from launch_r2.persistence import upload
        cfg,state=fixture();path=state/'w.bin';changed=path.read_bytes().upper()
        with changed_on_read(path,2,lambda:path.write_bytes(changed)):
            with self.assertRaisesRegex(ValueError,'Archive or source changed'):
                upload(cfg,state,'export',records)
