"""Native preparation propagates membership, using the base's CPU rehearsal gate."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from student_pilot import carrier_c1_run as trainer
from student_pilot.r2_contract import CONTRACT, INIT
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.p3_provenance import digest, file_pin, load, sha256, source_files, write
from student_pilot.source_seal import inventory
from student_pilot.r2_materialize import materialize
from tests.test_r2_data_path import RECORDS, SOURCES, TinyProcessor, directory, fixture, manifest


class PreparationProof(unittest.TestCase):
    def test_native_preparation_membership(self):
        root = directory()
        manifests = []
        for stream in ('pose', 'vqa', 'pointing', 'routing'):
            row = fixture(root, qid=stream, stream=stream)
            if stream == 'pose':
                from student_pilot.pose_samples import AUGMENT, SCHEMA
                target = row['target_record']
                from student_pilot.camera_targets import trajectory_scale
                target['trajectory_scale'] = trajectory_scale(target['camera'], target['camera_mask'])
                row.update(category='camera_pose_only', pose_sample=dict(schema=SCHEMA,
                    recording=dict(sampling=dict(variant='all_frames32')), frames=32, positions=list(range(32)),
                    temporal_grouping='fused_pairs_all_frames', anchors=list(range(1,33)),
                    augment={**AUGMENT,'seed':17, **{k:0 for k in ('brightness','contrast','saturation','hue','blur_p','grayscale_p')}}, metric=True,
                    **{k:target[k] for k in ('camera','camera_mask','trajectory_scale','gravity','gravity_mask')}))
            manifests.append(manifest(root/stream, [row], stream))
        with patch.dict('os.environ', STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2': str(root/'frames')}), S1_CPU_REHEARSAL='1'):
            report = materialize(manifests, root/'stores')
            native = load(report['receipt']['path'])
            write(root/'division.json', dict(train_scenes=['d1/fixture_clean'], heldout_scenes=[]))
            division = file_pin(root/'division.json')
            # Metadata stands in at the unavailable pretrained-model boundary.
            # No model weights or producer/reader functions are replaced.
            model_root = root/'model'
            model_root.mkdir()
            write(model_root/'config.json', dict(model_type='qwen3_5',
                text_config=dict(hidden_size=32, num_hidden_layers=1),
                vision_config=dict(hidden_size=32, depth=1)))
            write(root/'model.json', dict(kind='base', base_identity='synthetic-rehearsal',
                root=str(model_root), rehearsal=True, files={'config.json': sha256(model_root/'config.json')}))
            tree = Path(trainer.__file__).parent.parent
            sources = {str(p.relative_to(tree)): sha256(p) for p in source_files([Path(trainer.__file__)])}
            code_sha256 = digest(inventory(tree))
            write(root/'source.json', dict(schema='c1-rehearsal-source-v1', sources=sources,
                content_sha256=digest(sources), tree_sha256=code_sha256))
            receipts = {}
            for name, stream in native['streams'].items():
                receipt = dict(schema='c1-stream-v1', stream=name, division=division,
                    count=stream['count'], database=stream['database'], heldout_overlap=0, gt_masks_only=True)
                if name == 'pose':
                    receipt.update(schema='decoupled-v-preparation-v1', rehearsal=True,
                        model=file_pin(root/'model.json'), inputs=dict(division=division),
                        settings=dict(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames',
                                      camera=dict(point_depth={})))
                if name == 'routing':
                    receipt['schema'] = trainer.routing.ROUTING_SCHEMA
                write(root/(name+'_receipt.json'), receipt)
                receipts[name] = file_pin(root/(name+'_receipt.json'))
            cfg = dict(schema='carrier-c1-run-v1', trace_program_version='3.14', training_mode='final',
                carrier_placement=trainer.data.C1_A, init='base', parallel='fsdp', all_frames=True,
                base_identity='synthetic-rehearsal', code=file_pin(root/'source.json'), streams=receipts,
                preparation_output=str(root/'prepared'), frame_layout='duplicate', r2_membership=native['r2_membership'],
                depth_fov_source='pose_head', world_size=4, mix=list(receipts),
                exclusions=file_pin(RECORDS/SOURCES['benchmark']),
                init_artifact=dict(artifact=dict(path=str(root/'unavailable-export'), sha256=INIT['artifact_sha256']), lm='full', heads=[]))
            cfg['scheduled_sampling'] = dict(seed=0, max_own_probability=0., pose_open_deg=1., pose_full_deg=0.,
                fov_open_deg=1., depth_open_absrel=1., ema_steps=1, force_from_step=None,
                exposure_from_step=None, exposure_probability=0.)
            cfg['recipe'] = recipe_for(cfg)
            # Preparation authenticates metadata; the unavailable weight load is outside this proof.
            write(root/'EXPORT_ARTIFACT.json', INIT)
            cfg['r2'] = dict(contract=CONTRACT, init=INIT, mode='warm_start', run_id='synthetic-preparation',
                code_sha256=code_sha256, mixture_sha256=digest({key: cfg.get(key) for key in ('recipe', 'streams', 'route_table')}),
                export_metadata=file_pin(root/'EXPORT_ARTIFACT.json'))
            prepared = trainer.prepare(cfg)
            self.assertEqual({name: value['count'] for name, value in prepared['streams'].items()}, dict(pose=1, vqa=1, pointing=1, routing=1))
            self.assertEqual(prepared['r2_membership'], native['r2_membership'])
            self.assertEqual(load(root/'prepared/receipt.json')['r2_membership'], native['r2_membership'])
            reader = trainer.Rows(prepared, TinyProcessor())
            self.assertEqual(reader.row('vqa', 0)[0]['qid'], 'vqa')
