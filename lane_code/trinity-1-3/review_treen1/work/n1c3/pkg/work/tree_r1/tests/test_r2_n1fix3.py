"""Handover input, native optimizer-table and Unicode confirmation regressions."""
import ast
from copy import deepcopy
import json, sqlite3, sys, unittest
from pathlib import Path
from unittest.mock import patch
from student_pilot import r1_handover as H, carrier_c1_run as run, row_text_audit as audit
from student_pilot.p3_provenance import load, file_pin
from tests.test_r2_n1fix import handover_fixture, write
from tests import test_r2_n1fix as prior


class Confirmation3(unittest.TestCase):
    root = prior.N1Fix.root

    def test_depth_and_head_init(self):
        root=self.root('group_inputs')
        cfg,p,model,artifact=handover_fixture(root/'honest')
        self.assertEqual(H.progress(cfg,artifact)['step'],200)
        tables=H.verify_trainable_groups(cfg,model)
        self.assertEqual(tables['source'],tables['target'])
        self.assertIsNone(H.verify_trainable_groups({},model))
        bad=deepcopy(cfg);bad['depth_init']={'path':'not_loaded','sha256':'d'*64}
        for fn,args in ((H.progress,(bad,artifact)),(H.verify_trainable_groups,(bad,model))):
            with self.assertRaisesRegex(ValueError,'MISMATCH:depth_init'):fn(*args)
        initial=write(root/'initial.json',dict(head_init=dict(prefix='global_camera_head.',
            copied=['trunk.0.ls1','token_norm.weight'],derived=['embed_pose.bias'])))
        donor_init=dict(artifact=initial,heads=['pose','depth'],lm='full')
        c,p,m,a=handover_fixture(root/'inherited_matching_scales',donor_scales={
            'init_artifact':donor_init,'lm_lr_scale':cfg.get('lm_lr_scale',1.0),
            'pose_lr_scale':cfg.get('pose_lr_scale',1.0)})
        with self.assertRaisesRegex(ValueError,'MISMATCH:head_init'):H.progress(c,a)
        missing=deepcopy(c);missing['init_artifact']={'artifact':{'path':str(root/'absent'),'sha256':'e'*64}}
        with self.assertRaisesRegex(ValueError,'HEAD_INIT_UNVERIFIED'):H.optimizer_contract(missing)
        unavailable,_,_,export=handover_fixture(root/'unavailable_P_initialization',donor_scales={
            'init_artifact':dict(artifact={'path':'c1r/artifact.json','sha256':'e'*64},heads=['pose','depth'],lm='full'),
            'lm_lr_scale':cfg.get('lm_lr_scale',1.0),'pose_lr_scale':cfg.get('pose_lr_scale',1.0)})
        with self.assertRaisesRegex(ValueError,'HEAD_INIT_UNVERIFIED'):H.progress(unavailable,export)
        self.assertEqual(run.inherited_head_names(donor_init,H.head_init(p)),
            ['embed_pose.bias','token_norm.weight','trunk.0.ls1'])
        inherited=H.trainable_group_table(p,m)
        self.assertNotEqual(inherited,H.trainable_group_table(c,m))
        self.assertIn('heads_pretrained',[g['name'] for g in inherited['groups']])
        # Run the untouched base group builder against the same live topology.
        base=Path(__file__).resolve().parents[2]/'base/tree_b01ce449/student_pilot/carrier_c1.py'
        from student_pilot import carrier_c1
        node=next(n for n in ast.parse(base.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='parameter_groups')
        space=dict(vars(carrier_c1));exec(compile(ast.Module(body=[node],type_ignores=[]),str(base),'exec'),space)
        with patch.object(carrier_c1,'parameter_groups',space['parameter_groups']):
            self.assertEqual(inherited,H.trainable_group_table(p,m))
            self.assertEqual(tables,H.verify_trainable_groups(cfg,model))
        with patch.object(H,'trainable_group_table',side_effect=[{'x':1},{'x':2}]):
            with self.assertRaisesRegex(ValueError,'TRAINABLE_GROUP_MISMATCH'):H.verify_trainable_groups(cfg,model)
        write(root/'TABLES.json',dict(honest=tables,inherited_source=inherited,
            inherited_target=H.trainable_group_table(c,m),base_group_builder_matches=True,
            stand_in='Tiny native CPU model replaces pretrained GPU weights; native export and reader execute.'))

    def test_native_initialization_group_tables(self):
        from safetensors.torch import save_file
        from student_pilot.carrier_c1 import load_depth_stage1
        root=self.root('native_group_tables')
        cfg,p,model,artifact=handover_fixture(root/'producer')
        before=H.trainable_group_table(p,model)
        depth=model.auxiliary_heads.depth
        save_file({k:v.detach().clone().contiguous() for k,v in depth.model.visual.state_dict().items()},str(root/'encoder.safetensors'))
        save_file({'camera.point_depth.'+k:v.detach().clone().contiguous()
            for k,v in depth.auxiliary_heads.camera.point_depth.state_dict().items()},str(root/'heads.safetensors'))
        cfg['depth_init']=write(root/'depth.json',dict(schema='p3-head-artifact-v1',feature_backing='decoupled_vc',
            encoder_copy=dict(weights=file_pin(root/'encoder.safetensors')),weights=file_pin(root/'heads.safetensors')))
        load_depth_stage1(model,cfg['depth_init'])
        after=H.trainable_group_table(cfg,model)
        self.assertIn('encoder_copy',[g['name'] for g in before['groups']])
        self.assertNotIn('encoder_copy',[g['name'] for g in after['groups']])
        self.assertIn('auxiliary_heads.depth.model.visual',after['frozen_modules'])
        inherited=dict(artifact,head_init=dict(prefix='global_camera_head.',copied=['token_norm.weight'],derived=['embed_pose.bias']))
        spec=dict(artifact=write(root/'inherited.json',inherited),heads=['pose','depth','frame_embeddings'],lm='base')
        run.init_from_artifact(model,spec,part='heads')
        self.assertEqual(model.inherited_head_params,['embed_pose.bias','token_norm.weight'])
        head_table=H.trainable_group_table(dict(cfg,init_artifact=spec),model)
        self.assertIn('heads_pretrained',[g['name'] for g in head_table['groups']])
        write(root/'TABLES.json',dict(source=before,depth_initialized=after,head_initialized=head_table,
            functions=['carrier_c1.load_depth_stage1','carrier_c1_run.init_from_artifact','carrier_c1.parameter_groups'],
            stand_in='Tiny native CPU weights replace pretrained GPU weights; initialization and grouping functions are real.'))

    def test_extension_contract(self):
        for key in ('mdg','geometry_online'):
            self.assertNotEqual(H.optimizer_contract({}),H.optimizer_contract({key:{'changed':True}}))

    def test_checkpoint_step(self):
        root=self.root('checkpoint_step');cfg,_,_,artifact=handover_fixture(root)
        complete=load(cfg['r1_training']['p_run']['checkpoint']['path']);complete['step']=199
        cfg['r1_training']['p_run']['checkpoint']=write(root/'wrong_step.json',complete)
        with self.assertRaisesRegex(ValueError,'CHECKPOINT_BINDING_MISMATCH'):H.donor(cfg,artifact)

    def test_extra_unicode_and_cf(self):
        variants=['no'+c+'t seen' for c in ('\ufff9','\u0600','\u20dd','\u0e31')]
        variants+=['nοt seen','nоt seen','ɴᴏᴛ sᴇᴇɴ','not\u2800seen']
        reader=run.Rows(dict(streams={},r1_training={'schema':'r1-training-v1'}),None)
        conn=sqlite3.connect(':memory:');reader.connections['vqa']=conn
        conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        for text in variants:
            row=dict(target='<think>'+text+'</think>\n1')
            self.assertTrue(audit.reasons(row),text)
            conn.execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(row),'{}'))
            with patch.object(audit,'reasons',side_effect=AssertionError('gate called')),patch.object(audit,'PATTERNS',{}),patch.object(audit,'normalized_text',side_effect=AssertionError('gate called')):
                with self.assertRaisesRegex(ValueError,'rule_only_text',msg=text):reader.row('vqa',0)
        reader.close()
        write(self.root('extra_unicode')/'RESULT.json',dict(variants=variants,gate_refused=len(variants),reader_refused=len(variants)))

    def test_host_python_minimum(self):
        import launch_r1.build as build
        source=Path(build.__file__).read_text()
        script=next(n.value for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Constant)
            and isinstance(n.value,str) and n.value.startswith('import base64,hashlib,json,sys,tarfile'))
        prefix=script.split('def read(p):')[0]
        with patch.object(sys,'version_info',(3,11,9)):
            with self.assertRaisesRegex(RuntimeError,'Python 3.12 or newer required'):exec(compile(prefix,'host_prefix','exec'),{})
        with patch.object(sys,'version_info',(3,12,0)):exec(compile(prefix,'host_prefix','exec'),{})
