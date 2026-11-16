"""CPU precision fixtures and planted regressions for the GPU acceptance gates."""
from dataclasses import replace
from contextlib import ExitStack, redirect_stdout
import io,json,os,tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from student_pilot.sam3_tower import FrameDetections
from student_pilot.run_live_parity import probability_parity
from scripts.sam3_validate import compare, compare_noise_aware, prediction, summarize_parity


def fixture():
    scores=torch.tensor([.9,.85,.8,.75,.7,.65,.1])
    masks=torch.zeros(5,40,100,dtype=torch.bool)
    for i in range(5):masks[i,i*5:i*5+10]=True
    return FrameDetections(.8,scores[:5],scores[:5]*.8,torch.zeros(5,4),masks,torch.arange(5),scores)


def check(old,new):
    ref=prediction(old)
    return dict(compare(ref,new),noise_aware=compare_noise_aware(ref,new))


def report(checks):
    return summarize_parity([dict(scene='scene'+str(i),checks=checks[i::10]) for i in range(10)])


class AcceptanceParity(unittest.TestCase):
    def test_precision_noise_passes_with_strict_failures_and_rare_outliers(self):
        old=fixture();scores=old.all_scores-.004
        noisy=replace(old,all_scores=scores,presence=.796,query_ids=old.query_ids.flip(0),
                      masks=old.masks.flip(0),scores=scores[:5].flip(0),joint_scores=(scores[:5]*.796).flip(0))
        checks=[check(old,noisy) for _ in range(100)]
        masks=noisy.masks.clone();masks[-1,0,:24]=False  # IoU 0.976.
        scores=scores.clone();scores[0]=old.all_scores[0]-.02
        checks[0]=check(old,replace(noisy,masks=masks,all_scores=scores))
        result=report(checks)
        self.assertTrue(result['ok']);self.assertEqual(result['strict']['failed'],100)
        self.assertEqual(result['mask_failures'],1);self.assertEqual(result['score_failures'],1)
        self.assertEqual(result['matched_instances'],500)
        self.assertAlmostEqual(result['mask_pass_fraction'],.998)

    def test_confident_cap_exchange_fails_even_below_one_percent(self):
        old=fixture();checks=[check(old,old) for _ in range(1000)]
        ids=old.query_ids.clone();ids[-1]=5
        checks[0]=check(old,replace(old,query_ids=ids))
        result=report(checks)
        self.assertEqual(result['real_identity_changes'],1)
        self.assertEqual(result['cap_exchange_failures'],1);self.assertFalse(result['ok'])

    def test_shifted_masks_fail_the_matched_instance_fraction(self):
        old=fixture();checks=[check(old,old) for _ in range(100)]
        for i in range(3):checks[i]=check(old,replace(old,masks=old.masks.roll(5,1)))
        result=report(checks)
        self.assertEqual(result['mask_failures'],15);self.assertFalse(result['ok'])

    def test_cap_exchange_cannot_hide_a_confident_removal_with_a_near_gate_addition(self):
        old=fixture();scores=old.all_scores.clone();scores[5]=.31
        old=replace(old,all_scores=scores)
        ids=old.query_ids.clone();ids[-1]=5
        checks=[check(old,old) for _ in range(1000)];checks[0]=check(old,replace(old,query_ids=ids))
        result=report(checks)
        self.assertEqual(result['cap_exchange_failures'],1);self.assertFalse(result['ok'])

    def test_dropped_raw_proposal_is_invalid_even_below_one_percent(self):
        old=fixture();checks=[check(old,old) for _ in range(1000)]
        checks[0]=check(old,replace(old,all_scores=old.all_scores[:-1]))
        result=report(checks)
        self.assertEqual(result['invalid_checks'],1);self.assertFalse(result['ok'])

    def test_dropped_retained_proposals_use_name_frame_fraction(self):
        old=fixture();checks=[check(old,old) for _ in range(100)]
        dropped=replace(old,query_ids=old.query_ids[:-1],masks=old.masks[:-1],
                        scores=old.scores[:-1],joint_scores=old.joint_scores[:-1],boxes=old.boxes[:-1])
        checks[0]=check(old,dropped)
        self.assertTrue(report(checks)['ok'])  # Exactly 1% is allowed.
        checks[1]=check(old,dropped)
        self.assertFalse(report(checks)['ok'])

    def test_gate_band_is_point_zero_three_and_symmetric(self):
        old=fixture();scores=old.all_scores.clone();scores[4]=.321;scores[5]=.1
        old=replace(old,all_scores=scores,scores=scores[:5])
        low=scores.clone();low[4]=.299
        new=replace(old,all_scores=low,query_ids=old.query_ids[:-1],masks=old.masks[:-1],
                    scores=low[:4],joint_scores=low[:4]*.8,boxes=old.boxes[:4])
        for a,b in ((old,new),(new,old)):
            result=report([check(a,b) for _ in range(100)])
            self.assertTrue(result['ok']);self.assertEqual(result['near_tie_name_frames'],100)
            self.assertEqual(result['real_identity_changes'],0)

    def test_score_fraction_counts_matched_ids_and_boundary(self):
        old=fixture();scores=old.all_scores.clone();scores[0]-=.02
        checks=[check(old,old) for _ in range(100)]
        for i in range(5):checks[i]=check(old,replace(old,all_scores=scores))
        self.assertTrue(report(checks)['ok'])  # 495/500 pass.
        checks[5]=check(old,replace(old,all_scores=scores))
        self.assertFalse(report(checks)['ok'])

    def test_presence_and_nan_cannot_be_diluted(self):
        old=fixture()
        for changed in (replace(old,presence=.78),replace(old,all_scores=old.all_scores*float('nan'))):
            checks=[check(old,old) for _ in range(1000)];checks[0]=check(old,changed)
            self.assertFalse(report(checks)['ok'])

    def test_ten_unique_nonempty_scenes_are_required(self):
        with self.assertRaises(ValueError):summarize_parity([])
        with self.assertRaises(ValueError):summarize_parity([dict(scene='same',checks=[check(fixture(),fixture())])]*10)
        with self.assertRaises(ValueError):summarize_parity([dict(scene=str(i),checks=[]) for i in range(10)])

    def test_verify_requires_measured_reference_and_input_evidence(self):
        from tests.test_precision_parity_r12 import crop,PROVENANCE
        row=crop(.5,.5005,.5005)
        result=probability_parity([row],PROVENANCE,PROVENANCE)
        self.assertTrue(result['ok']);self.assertEqual(result['strict_failures'],0)
        row.update(reference=.502,reference_grouped=.502)
        result=probability_parity([row],PROVENANCE,PROVENANCE)
        self.assertFalse(result['ok']);self.assertEqual(result['strict_failures'],1)

    def test_command_pools_all_ten_scenes_before_gating(self):
        from PIL import Image
        import scripts.sam3_validate as validation
        root=Path(tempfile.mkdtemp(prefix='parity_command_',dir=os.environ['TMPDIR']))
        im=root/'frame.png';Image.new('RGB',(100,40)).save(im)
        receipt=root/'receipt.json';receipt.write_text('{}')
        old=fixture();fresh=replace(old,all_scores=old.all_scores-.004,presence=.796)
        scenes=[]
        for i in range(10):
            cache=root/(str(i)+'.json')
            cache.write_text(json.dumps(dict(scene=str(i),phrases=['chair'],
                frames={str(k):dict(phrases={'chair':prediction(old)}) for k in range(32)})))
            scenes.append(dict(scene=str(i),phrases=['chair'],frames=[str(im)]*32,
                               reference=str(cache),reference_sha256=validation.sha256(cache)))
        manifest=root/'manifest.json'
        manifest.write_text(json.dumps(dict(scenes=scenes,receipt_sha256=validation.sha256(receipt),contract={})))
        class Tower:
            current=-1
            def _load(self):pass
            def encode(self,frames):
                self.current+=1
                return SimpleNamespace(frames=({'features':[torch.zeros(1)]},))
            def detect(self,*args):return [fresh]*32
            def detect_cache_reference(self,*args):
                values=[fresh]*32
                if self.current==0:
                    values[:2]=[replace(fresh,masks=fresh.masks.roll(5,1))]*2
                return values
        args=SimpleNamespace(enable_sam3_tower=True,command='parity',manifest=manifest,
            receipt=receipt,checkpoint=root/'weights',source_root=root,precision='bf16',
            image_batch_size=1,native_image_batch=False,out=root/'output',max_seconds=60,
            max_write_bytes=1000000,parity_rule='noise-aware')
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ,CUDA_VISIBLE_DEVICES='cpu-fixture'))
            stack.enter_context(patch.object(validation,'attach_sam3_tower',return_value=Tower()))
            stack.enter_context(patch.object(validation,'load_cache',side_effect=lambda p:json.loads(Path(p).read_text())))
            for name,value in [('device_count',1),('synchronize',None),('reset_peak_memory_stats',None),
                               ('max_memory_allocated',0),('max_memory_reserved',0),('get_device_name','CPU mock')]:
                stack.enter_context(patch.object(torch.cuda,name,return_value=value))
            args.start_check=False
            with redirect_stdout(io.StringIO()):validation.run(args)
        result=json.loads((args.out/'REPORT.json').read_text())
        self.assertTrue(result['ok']);self.assertFalse(result['strict_ok'])
        self.assertFalse(result['scenes'][0]['ok'])
        self.assertEqual(result['aggregate']['strict']['failed'],320)
        self.assertEqual(result['aggregate']['mask_failures'],10)
        self.assertAlmostEqual(result['aggregate']['mask_pass_fraction'],.99375)


if __name__=='__main__':unittest.main()
