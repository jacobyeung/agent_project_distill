"""Legacy direct sources preserve concrete traces and refuse empty reasoning."""
import copy,io,json,os,sqlite3,sys
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch
from tests import test_r2_data_path as D
from tests.test_r2_build8 import folder
from student_pilot.p3_provenance import file_pin
from student_pilot import carrier_c1_routing as R

def processor():
    value=D.TinyProcessor();tok=value.tokenizer;tok.special=dict(tok.special)
    tok.get_vocab=lambda:dict(tok.special)
    def add_tokens(values):
        for token in values:tok.special[str(token)]=500+len(tok.special)
    tok.add_tokens=add_tokens
    return value

class DirectTrace(unittest.TestCase):
    def test_producer_and_training_suffix_refuse_empty_think(self):
        p=folder('empty_direct');raw=D.fixture(p)
        for target in ('<think>\n\n</think>\n\nA','<think>\n \t\n</think>\n\nA','A',None):
            bad={**raw,'target':target}
            with self.assertRaisesRegex(ValueError,'LEGACY_DIRECT_SOURCE_EMPTY_THINK_REFUSED'):R.direct_row(bad)
            with self.assertRaisesRegex(ValueError,'LEGACY_DIRECT_SOURCE_EMPTY_THINK_REFUSED'):
                R.suffix_tokens(processor(),bad,target,[])
        from tests.coverage_b8_rows import camera_row
        empty=camera_row();empty.update(events=[],target=R.THINK+'\n</think>\n\n'+empty['answer'],tool_output_spans=[])
        with self.assertRaisesRegex(ValueError,'LEGACY_DIRECT_SOURCE_EMPTY_THINK_REFUSED'):R.check_row(empty)
        for count in (32,64):
            valid=copy.deepcopy(raw)
            valid['student_input'].update(frames=[file_pin(p/'frames'/f'{i}.png') for i in range(count)],frame_indices=list(range(count)))
            row=R.direct_row(valid)
            self.assertEqual(R.render(row['routing']['events'],row['routing']['answer'])[0],valid['target'])
            ids,train,_=R.suffix_tokens(processor(),row,row['target'],[])
            self.assertTrue(ids and all(train))
        invalid=copy.deepcopy(raw);invalid['student_input']['frame_indices']=[]
        with self.assertRaisesRegex(ValueError,'32 or 64 pinned'):R.direct_row(invalid)
        with self.assertRaisesRegex(ValueError,'declared answer'):R.direct_row({**raw,'answer':'B'})
        with self.assertRaisesRegex(ValueError,'training renderer'):R.direct_row({**raw,'target':raw['target'].replace('\n\nA','\nA')})

    def test_native_stream_producer_reader_and_empty_source_refusal(self):
        from student_pilot import decoupled_v_run,carrier_c1_run as run
        p=folder('direct_stream');raw=D.fixture(p)
        raw['student_input']['frames']=[file_pin(p/'frames'/Path(f['path']).name) for f in raw['student_input']['frames']]
        source=p/'routed.jsonl';source.write_text('')
        index=p/'index.json';index.write_text(json.dumps({'manifests':{}}))
        division=p/'division.json';division.write_text(json.dumps(dict(schema='diagnostic-whole-scene-division-v1',
            training_only=True,train_scenes=[R.alias_of(raw['canonical'])],heldout_scenes=[])))
        direct=p/'direct.jsonl';direct.write_text(json.dumps(raw)+'\n'+json.dumps(raw)+'\n')
        with patch.object(decoupled_v_run,'processor_for',side_effect=lambda _:processor()),patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP=''):
            args=['routing','--source',json.dumps(file_pin(source)),'--rgb-index',json.dumps(file_pin(index)),
                  '--division',json.dumps(file_pin(division)),'--output',str(p/'store'),'--processor','fixture',
                  '--direct-source',json.dumps(file_pin(direct)),'--policy','both-path-20261116',
                  '--exclusions',json.dumps(file_pin(D.RECORDS/D.SOURCES['benchmark']))]
            with patch.object(sys,'argv',args),redirect_stdout(io.StringIO()):R.main()
            receipt=json.loads((p/'store/receipt.json').read_text())
            self.assertEqual(receipt['count'],1)
            self.assertEqual(receipt['refused']['direct:duplicate_qid'],1)
            rows=run.Rows(dict(streams={'routing':receipt}),processor())
            try:stored,_=rows.row('routing',0)
            finally:rows.close()
            self.assertEqual(stored['answer_form'],'direct');self.assertEqual(stored['target'],raw['target'])
            bad={**raw,'target':R.THINK+'\n</think>\n\nA'};direct.write_text(json.dumps(bad)+'\n')
            with self.assertRaisesRegex(ValueError,'LEGACY_DIRECT_SOURCE_EMPTY_THINK_REFUSED'):
                R.build_routing_stream(file_pin(source),file_pin(index),file_pin(division),p/'refused','fixture',
                    direct_source=file_pin(direct),policy='both-path-20261116',exclusions=file_pin(D.RECORDS/D.SOURCES['benchmark']))
        (Path(os.environ['R2_PROOFS'])/'DIRECT.json').write_text(json.dumps(dict(count=receipt['count'],
            refused=receipt['refused'],target_sha256=__import__('hashlib').sha256(stored['target'].encode()).hexdigest(),
            stand_in='tiny pretrained tokenizer only',functions=['direct_row','build_routing_stream','Rows.row','suffix_tokens'])))
