"""Extend the native preparation fixture without replacing its producers."""
from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1'
text=(T/'tests/test_r2_preparation.py').read_text()
text=text.replace('class PreparationProof(unittest.TestCase):','class PreparationProof(unittest.TestCase):')
text=text.replace('def test_native_preparation_membership(self):','def prepare_native(self):')
text=text.replace("            manifests.append(manifest(root/stream, [row], stream))", """            if stream == 'routing':
                from tests.coverage_b8_rows import camera_row
                raw=camera_row(row['student_input']['frames'])
                row.update(raw)
                row['student_input']['question']=raw['question']
                row['student_input']['options']=raw['options']
            manifests.append(manifest(root/stream, [row], stream))""")
text=text.replace("            prepared = trainer.prepare(cfg)","""            from tests.test_r2_build8 import inputs
            cfg['b7_inputs']=inputs(root)
            cfg['h1']={'faithful_own_camera_rows':True}
            cfg['scheduled_sampling'].update(max_own_probability=.5,force_from_step=1)
            cfg['r2']['mixture_sha256']=digest({key:cfg.get(key) for key in ('recipe','streams','route_table')})
            try:
                trainer.prepare(cfg)
            except ValueError as error:
                self.assertIn('faithful identity',str(error))
                faithful_refusal=load(root/'prepared/receipt.json')
                self.assertFalse(faithful_refusal['h1_faithful_identity']['passes'])
            else:
                raise AssertionError('R2 answer delimiters unexpectedly passed the bare-answer materializer')
            cfg['h1']={'faithful_own_camera_rows':False}
            cfg['preparation_output']=str(root/'prepared_off')
            prepared = trainer.prepare(cfg)""")
text=text.replace("load(root/'prepared/receipt.json')['r2_membership']", "load(root/'prepared_off/receipt.json')['r2_membership']")
text += "\n            cfg['preparation']=file_pin(root/'prepared_off/receipt.json')\n            return cfg,prepared,faithful_refusal\n"
(T/'tests/coverage_b8_preparation.py').write_text(text)
