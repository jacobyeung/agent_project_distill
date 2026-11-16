"""Load the unmodified native decoder and build its per-question context."""
import os
import sys
from pathlib import Path
from .paths import C8, TREE
from .io import load, sha


def install():
    os.environ['LEGS1_TREE'] = str(TREE)
    for path in (TREE, C8.parent.parent/'orchard_native', C8.parent.parent, C8):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    import common
    common.TREE = TREE
    import perception
    from .paths import ROOT
    receipt=ROOT/'out/ARCHIVE_TRANSPORT.json'
    if receipt.exists():
        for row in load(receipt):
            if row['path'].endswith('/mask_kit/kit_combo3.tar.gz'):
                path=ROOT/row['path']
                if sha(path)!=row['sha256']:raise ValueError('transport archive differs')
                perception.frozen_kit.ARCHIVE_SHA=row['sha256']
    return perception


class ItemRefusal(ValueError):
    pass


class Context:
    """Use C8r's prompt, geometry, mask validation, and backend constructors."""
    def __init__(self, processor, config, captures, frames_root, geometry_manifest, masks,
                 audit_dir, device, *, policy=None):
        self.P = install()
        self.processor, self.config = processor, config
        self.captures, self.frames_root = captures, frames_root
        self.geometry_manifest, self.masks = geometry_manifest, masks
        self.audit_dir, self.device = audit_dir, device
        self.policy = policy

    def prompt(self, frames, question):
        from routed import trainer_row
        from common import move_batch
        from evalpath import runtime
        from evalpath.items import assert_prompt_equal
        scene = question.get('native', question['dataset']+':'+question['scene_name'])
        capture = self.captures[scene]
        task = dict(question, scene=scene, native=scene)
        row = trainer_row(task, capture, self.frames_root, verify=True)
        assert_prompt_equal(self.processor, row)
        batch = move_batch(runtime.prompt_batch(self.processor, row, self.config, 'routed'), self.device)
        return row,batch

    def __call__(self,frames,question):
        row,batch=self.prompt(frames,question)
        scene=question.get('native',question['dataset']+':'+question['scene_name'])
        disposition=next(r for r in self.geometry_manifest['records'] if r['native']==scene)
        if disposition['status']=='REFUSED':
            raise ItemRefusal(disposition['error']['code'])
        geometry = self.P.load_geometry(self.geometry_manifest, row)
        backend = None
        if self.masks is not None and scene in self.masks.captures:
            source = self.masks.for_item(scene, row, batch)
            if self.policy is None:
                backend = self.P.backend(row, batch, geometry, source, self.audit_dir)
            else:
                from student_pilot.ground_profiles import build_profile
                from student_pilot.scene_state import SceneState,FrameMap
                scene_state=SceneState(batch['video_sha256'],FrameMap(tuple(batch['frame_indices'])),geometry.identity)
                backend=build_profile('native_selector',scene_state,geometry,source,depth_source='tower_scaled',
                                      audit_dir=self.audit_dir,ground_candidate_policy=self.policy,
                                      question_type=row['question_type'])
                if backend.geometry_error:raise ValueError(backend.geometry_error)
                backend.allow_own_geometry_fallback=False
                backend.geometry_source='checkpoint_conditioned_frozen_g3t'
                backend.frozen_mask_source=source
        return batch, geometry, backend


def load_model(config, artifact, data_receipt, device):
    install()
    import read_runtime
    from routed import source_pins
    sources = {n.removeprefix('student_pilot/'): h for n,h in source_pins().items()
               if n.startswith('student_pilot/')}
    return read_runtime.load_model(config, artifact, data_receipt, device=device,
                                  selected_trainer={'root':str(TREE), 'sources':sources})
