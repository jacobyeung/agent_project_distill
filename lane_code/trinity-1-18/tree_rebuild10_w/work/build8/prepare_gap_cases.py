"""Add concrete native-reader negative cases after the frozen pass identifies gaps."""
from pathlib import Path
L=Path(__file__).resolve().parents[2];P=L/'work/tree_r1/tests/test_r2_build8_frames.py'
text=P.read_text()
anchor='                rotation,centre=geometry.camera(count)\n'
replacement=anchor+'''                pose=readout['pose'][0].double().cpu().numpy()
                up=readout['gravity'][0].double().cpu().numpy()
                # Malformed tensor shapes stand in only at the model boundary;
                # the native geometry reader must reject both before use.
                with self.assertRaisesRegex(R.RenderError,'own pose readout'):
                    R.OwnGeometry(pose[:-1],up,None)
                with self.assertRaisesRegex(R.RenderError,'own FoV readout'):
                    R.OwnGeometry(pose,up,None,fov=pose[:-1,7:9])
'''
assert anchor in text and 'pose=readout' not in text
text=text.replace(anchor,replacement)
anchor="            self.assertEqual(batch['aux_camera_positions'].shape[1],count)\n"
replacement=anchor+'''            malformed=copy.deepcopy(row)
            malformed['student_input']['frames']=malformed['student_input']['frames'][:-1]
            malformed['student_input']['frame_indices']=malformed['student_input']['frame_indices'][:-1]
            invalid=root/'invalid.jsonl';invalid.write_text(json.dumps(malformed)+'\\n')
            with self.assertRaisesRegex(ValueError,'C1 preservation rows require'):
                data.build_stream(file_pin(invalid),file_pin(division),root/'invalid_store','vqa',training_mode='final')
'''
assert anchor in text
text=text.replace(anchor,replacement)
P.write_text(text)
