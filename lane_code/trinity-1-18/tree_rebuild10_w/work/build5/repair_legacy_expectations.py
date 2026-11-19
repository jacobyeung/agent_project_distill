"""Keep legacy checks aligned with the required visual-only connector contract."""
from pathlib import Path
L=Path(__file__).resolve().parents[2]
for name in ('test_gf1.py','test_gf1_contracts.py'):
    p=L/'work/tree_r1/tests'/name
    text=p.read_text().replace('geometry_encoder.calls,2','geometry_encoder.calls,1').replace('encoder.calls,2','encoder.calls,1')
    p.write_text(text)
p=L/'work/tree_r1/tests/test_gf1_contracts.py'
text=p.read_text()
start=text.index('        with torch.no_grad():model.auxiliary_heads.pose.cam_token_connector.mlp[2].weight.fill_(.01)')
end=text.index('\n    def test_stage1_bf16',start)
text=text[:start]+'''        self.assertIsNone(model.auxiliary_heads.pose.cam_token_connector)
        # No inherited camera path exists in the visual-only arm. The legacy
        # nonzero-path validator still applies to a model that has such a head.
        legacy=copy.deepcopy(model)
        legacy.auxiliary_heads.pose.cam_token_connector=torch.nn.Module()
        legacy.auxiliary_heads.pose.cam_token_connector.mlp=torch.nn.Sequential(
            torch.nn.Identity(),torch.nn.Identity(),torch.nn.Linear(2,2))
        with self.assertRaisesRegex(ValueError,'camera context'):gf1.check_camera_context(legacy,{})
        gf1.check_camera_context(legacy,dict(geometry_online=copy.deepcopy(legacy.geometry_online)))
        donor=copy.deepcopy(legacy.geometry_online);donor.pop('gf1')
        gf1.check_camera_context(legacy,dict(geometry_online=donor))
        donor['input']='wrong'
        with self.assertRaisesRegex(ValueError,'camera context'):gf1.check_camera_context(legacy,dict(geometry_online=donor))
''' +text[end:]
p.write_text(text)
p=L/'work/tree_r1/tests/test_gf1_review.py';text=p.read_text()
text=text.replace('            model.auxiliary_heads.pose.cam_token_connector.mlp[2].weight.normal_(std=.01)\n            model.auxiliary_heads.pose.cam_token_connector.rms_cam.fill_(.7)\n','')
# Keep native export/load equality, while asserting the unsupported evaluation
# entry refuses. The native artifact reader is permitted without a bank.
text=text.replace("            restored,_,_,_=run.inference(cfg,artifact,torch.device('cpu'))",'''            with self.assertRaisesRegex(ValueError,'no authenticated R2 bank adapter'):
                run.inference(cfg,artifact,torch.device('cpu'))
            restored=copy.deepcopy(model)
            with torch.no_grad():
                for output in restored.auxiliary_heads.gf1.outputs:output.weight.zero_()
            run.load_artifact(restored,artifact)''')
text=text.replace("with self.assertRaisesRegex(ValueError,'GF1 export requires gf1')", "with self.assertRaisesRegex(ValueError,'no authenticated R2 bank adapter')")
p.write_text(text)
