"""Retain native serialization checks beside required reader refusals."""
from pathlib import Path
L=Path(__file__).resolve().parents[2]
p=L/'work/tree_r1/tests/test_mdg_eval.py';text=p.read_text()
def replace_method(name,body):
    global text
    start=text.index('    def '+name+'(')
    end=text.find('\n    def ',start+1)
    if end<0:raise ValueError('Expected another method')
    text=text[:start]+'    def '+name+'(self):\n'+body+'\n'+text[end:]
replace_method('test_export_union_one_prefix_resume_and_packed_masks', '''        with self.assertRaisesRegex(ValueError,'no authenticated R2 bank adapter'):
            self.run_export()
        self.assertFalse(self.export.exists())
        self.assertEqual(self.head.video_calls,0)
        # The supported low-level producer and packed reader retain their round trip.
        from student_pilot import carrier_c1_canary as C,mdg_stream
        names=['chair','missing','never']
        features=SimpleNamespace(capture_prefix=self.capture)
        with mock.patch.object(C,'prompt_batch',return_value=dict(input_ids=torch.tensor([[2,3]]))), \\
             mock.patch.object(mdg_stream,'stream_suffix_states',
                 side_effect=lambda model,prefix,batch,names,chunk:self.suffix(model,prefix,names,chunk)), \\
             mock.patch.dict('sys.modules',{'student_pilot.mdg_features':features}):
            values,audit=E.predict(self.model,None,{},self.entry,names,self.png,'cpu',8)
        path=self.root/'packed.npz'
        E.save_npz(path,names,values,audit)
        actual,restored,recorded=E.read_npz(path)
        self.assertEqual(actual,names);self.assertEqual(recorded,audit)
        self.assertEqual(self.head.video_calls,1)
        self.assertEqual(self.suffixes,[names])
        for key in values:np.testing.assert_array_equal(restored[key],values[key])
        with np.load(path) as packed:self.assertEqual(packed['masks'].shape,(3,32,8,2))
        with self.assertRaises(FileExistsError):E.save_npz(path,names,values,audit)
''')
replace_method('test_rank_coverage_and_changed_world_refused', '''        for rank,world in ((1,2),(0,2),(0,1)):
            with self.subTest(rank=rank,world=world),self.assertRaisesRegex(ValueError,'no authenticated R2 bank adapter'):
                self.run_export(rank,world)
        self.assertFalse(self.export.exists())
        self.assertEqual(self.head.video_calls,0)
''')
replace_method('test_export_tampering_and_unjournaled_recovery', '''        self.export.mkdir()
        journal=self.export/'export-0.jsonl'
        journal.write_text('untrusted fixture journal\\n')
        before=journal.read_bytes()
        with self.assertRaisesRegex(ValueError,'no authenticated R2 bank adapter'):
            self.run_export()
        self.assertEqual(journal.read_bytes(),before)
        self.assertEqual(self.head.video_calls,0)
''')
start=text.index('    def test_changed_png_and_config_fail_closed')
end=text.index('    def test_record_schema',start)
part=text[start:end].replace("self.assertRaisesRegex(ValueError, 'pinned input')", "self.assertRaisesRegex(ValueError, 'no authenticated R2 bank adapter')")
text=text[:start]+part+text[end:]
p.write_text(text)
