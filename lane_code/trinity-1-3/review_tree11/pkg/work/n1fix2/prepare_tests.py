from pathlib import Path
import json, re
L=Path(__file__).resolve().parents[2]; B=L/'work/n1fix2'; T=L/'work/tree_r1'
p=T/'tests/test_r2_build_n1.py';s=p.read_text()
a=s.index('        from tests.test_carrier_c1 import fixture',s.index('    def test_export_load_and_continuation'))
b=s.index('        from student_pilot.r2_openers',a)
s=s[:a]+'''        from tests.test_r2_n1fix import handover_fixture
        root=self.root('export')
        cfg, donor, model, artifact = handover_fixture(root)
        artifact_pin=cfg['init_artifact']['artifact']
        self.assertEqual(contract.start(cfg),200)
        from student_pilot.decoupled_v import learning_rate
        import math
        recipe=run.recipe_for(configuration())
        lr=learning_rate(contract.start(cfg)+1,recipe)
        warm=math.ceil(recipe['steps']*recipe['warmup_ratio'])
        self.assertAlmostEqual(lr,recipe['learning_rate']*(1+math.cos(math.pi*(201-warm)/(recipe['steps']-warm)))/2)
''' + s[b:]
a=s.index('        root=self.root(\'host\')',s.index('    def test_host_empty_root_and_missing_inputs'))
b=s.index('\n    def ',a) if '\n    def ' in s[a:] else len(s)
s=s[:a]+'''        root=self.root('host')
        with self.assertRaisesRegex(ValueError,'JOB_TMP_REQUIRED'):
            frame_host(configuration(),root/'empty_validated',{'binaries':['python']})
''' + s[b:]
p.write_text(s)
p=T/'tests/test_r2_n1fix.py';s=p.read_text().replace("with self.assertRaisesRegex(ValueError,'NOT_FRESH'): entry.fresh_tmp(root/'present',{'job_tmp':str(root)})", "present=root/'present';present.mkdir(exist_ok=True)\n            with self.assertRaisesRegex(ValueError,'NOT_FRESH'): entry.fresh_tmp(present/'work',{'job_tmp':str(present)})")
p.write_text(s)
# Keep test fixture references inside this workspace; input bytes remain unchanged.
for p in [T/'tests/test_r2_data_path.py']:
    s=p.read_text()
    s=re.sub(r'/scratch/jjyeung/orch_n30/tree_rebuild_w/wm/wn2(?:_w)?(?:/w9f)?(?![\w])',str(L),s)
    p.write_text(s)
(B/'STATUS.md').write_text('# Build n1fix status\n\nN1–N5 source changes and targeted tests are implemented. CPU proof and mutation execution are next. GO=false.\n')
