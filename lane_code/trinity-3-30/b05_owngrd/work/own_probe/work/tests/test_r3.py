"""Rulings, train-only statistics, real-image correspondence, and phase gates."""
import copy,json,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import numpy as np
import torch
from torch.nn import functional as F
from PIL import Image
import card,extract,feature_data,probe_common as pc,run_arm
from own_feats.core import readout_maps
from own_feats.standardize import ChannelMoments,EnergyAudit,standardize_maps
from spatial_flip import correspondence,corrupt,validate_correspondence
from test_r2 import folder,metric


def arm(values):
    scenes=pc.gate.authority()['tuning_scenes'][:len(values)]
    return dict(rules={k:'PASS' for k in ('R1','R2','R3','R1+','R4')},tasks={'T1':{'predictions':[
        dict(object_id=s+'::obj',scene=s,on_target=v) for s,v in zip(scenes,values)]}})


class Decisions(unittest.TestCase):
    def test_card_prints_t1_choice_intervals_and_two_controls_without_teacher(self):
        root=folder();results=root/'results'
        from provenance import sha256
        for name,values in [('A1',[1,0,0,0]),('A2',[0,1,1,0]),('A7',[1,0,1,0])]:
            data=arm(values)['tasks']['T1']
            data.update(arm=name,task='T1',status='feature_complete_fusion_pending',readout='four',
                rules_sha256=sha256(pc.RULES_PATH),features={k:metric(.95,.9,1) for k in ('on_target','name_consistent','training_val_top1')})
            p=results/name/'T1.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(data))
        card.run(NS(results=str(results),out=str(root/'card'),availability=None))
        output=json.loads((root/'card/P0_CARD.json').read_text());page=(root/'card/P0_CARD.md').read_text()
        self.assertEqual(output['decision']['provisional_keys'],'A1')
        self.assertEqual(output['decision']['status'],'PROVISIONAL_T1')
        self.assertIn('T1 provisionally chooses A1',page);self.assertIn('A1-A2',page)
        self.assertIn('Unstandardized four taps',page);self.assertIn('Standardized final layer',page)
        self.assertEqual(output['arms']['A1']['rules']['R2'],'PENDING')

    def test_challenger_positive_point_straddles_zero(self):
        arms={'A1':arm([1,0,0,0]),'A2':arm([1,0,0,0]),'A5':arm([0,1,1,0])}
        decision=card.choose(arms);self.assertEqual(decision['keys'],'A1')
        delta=card.paired_difference(arms['A5']['tasks']['T1']['predictions'],arms['A1']['tasks']['T1']['predictions'])
        self.assertGreater(delta['value'],0);self.assertLess(delta['lo'],0)

    def test_high_resolution_positive_point_straddles_zero(self):
        arms={'A1':arm([1,0,0,0]),'A2':arm([0,1,1,0])}
        decision=card.choose(arms);self.assertEqual(decision['keys'],'A1')
        delta=decision['paired_differences']['A1-A2'];self.assertLess(delta['value'],0);self.assertGreater(delta['hi'],0)

    def test_pending_teacher_labels_preserve_provisional_choice(self):
        arms={'A1':arm([0,0,0,0]),'A2':arm([1,1,1,1]),'A5':arm([1,1,1,1])}
        for row in arms.values():row['rules'].update(R2='PENDING',R3='PENDING',R1='INCONCLUSIVE')
        d=card.choose(arms);self.assertEqual(d['keys'],'A2');self.assertEqual(d['provisional_keys'],'A2')
        self.assertEqual(len(d['paired_differences']),3);self.assertEqual(d['mask_keys'],'A7')
        self.assertEqual(d['pending_rules'],['R2','R3']);self.assertFalse(d['ready_for_downstream'])
        arms['A2']['rules']['R3']='PASS';self.assertTrue(card.choose(arms)['ready_for_downstream'])

    def test_masks_never_choose_selection_or_presence(self):
        arms={'A1':arm([1,1,0,0]),'A2':arm([1,1,0,0]),'A5':arm([0,0,0,0])}
        for name,row in arms.items():
            row['tasks']['T2']={'records':[dict(scene=p['scene'],object_id=p['object_id'],frames=[dict(slot=0,area=.005,sam_valid=True,sam_iou=.9 if name=='A5' else .4)]) for p in row['tasks']['T1']['predictions']]}
        arms['A1']['rules']['R2']='FAIL';d=card.choose(arms)
        self.assertEqual((d['keys'],d['presence_keys'],d['mask_keys']),('A1','A1','A5'))
        with patch('card.paired_mask_difference',return_value=metric(.02,-.02,.06)):
            self.assertEqual(card.choose(arms)['mask_keys'],'A7')
        arms['A1']['rules']['R2']='PASS';self.assertEqual(card.choose(arms)['mask_keys'],'A1')


class Standardization(unittest.TestCase):
    def test_online_all_arms_use_frozen_statistics_and_equal_scale(self):
        import online_probe
        from provenance import sha256,digest
        root=folder();rows=pc.gate.read_manifest(pc.ROOT/'out/b2_manifest.jsonl')[:32]
        self.assertEqual([r['slot'] for r in rows],list(range(32)))
        weights=root/'weights.json';weights.write_text(json.dumps({kind:{} for kind,size in pc.ARMS.values()}))
        generator=torch.Generator().manual_seed(61)
        raw=[torch.randn(1,3,4,1152,generator=generator)+torch.arange(1152)/50 for _ in range(4)]
        stats=dict(taps=[dict(mean=(torch.arange(1152)/50).tolist(),std=[2.]*1152) for _ in range(4)])
        for a,(kind,size) in pc.ARMS.items():
            if a=='A8':continue
            p=root/a/'CHANNEL_STATS.json';p.parent.mkdir()
            p.write_text(json.dumps(dict(arm=a,rules_sha256=sha256(pc.RULES_PATH),encoder={},size=list(size),training_only=True,
                rows=[dict(scene=rows[0]['scene'],slot=0,split='train')],statistics=stats,statistics_sha256=digest(stats))))
        def loader(*args):return NS(metadata={},encode=lambda images,size:[m.repeat(len(images),1,1,1) for m in raw])
        with patch('online_probe.load',side_effect=loader),patch.object(online_probe.OnlineFeatures,'read_image',return_value=Image.new('RGB',(4,4))):
            for a in pc.ARMS:
                for readout in ('four','final','unstandardized'):
                    online=online_probe.OnlineFeatures(a,str(weights),rows,'cpu',readout,str(root));actual=online(rows[0])
                    expected=[]
                    selected=list(range(4)) if readout!='final' else [3]
                    for k in selected:
                        x=raw[k] if readout=='unstandardized' else (raw[k]-torch.tensor(stats['taps'][k]['mean']))/2
                        x=F.layer_norm(x,(1152,));width=1024//len(selected)
                        x=F.adaptive_avg_pool1d(x.reshape(-1,1,1152),width).reshape(1,3,4,width)
                        expected.append(F.layer_norm(x,(width,)))
                    expected=torch.cat(expected,-1)
                    if a=='A8':
                        expected=torch.cat([expected,expected],-1)
                        expected=F.adaptive_avg_pool1d(expected.reshape(-1,1,2048),1024).reshape(1,3,4,1024)
                    expected=F.layer_norm(expected,(1024,))
                    torch.testing.assert_close(actual,expected)
                    self.assertTrue(torch.allclose(actual.square().mean(-1),torch.ones(1,3,4),atol=1e-3))

    def test_streaming_statistics_and_dominant_channel(self):
        torch.manual_seed(4);maps=[torch.randn(3,4,5,64) for _ in range(4)]
        for m in maps:m[...,0]=m[...,0]*200+2000;m[...,1]=3
        moments=ChannelMoments()
        for i in range(3):moments.update([m[i:i+1] for m in maps])
        stats=moments.finish();normalized=standardize_maps(maps,stats)
        for raw,s,x in zip(maps,stats['taps'],normalized):
            torch.testing.assert_close(torch.tensor(s['mean']),raw.mean((0,1,2)),rtol=1e-5,atol=1e-5)
            self.assertTrue(torch.isfinite(x).all());self.assertLess(float(x.mean((0,1,2)).abs().max()),1e-5)
        audit=EnergyAudit();audit.update(maps,stats,'train');rows=audit.finish()
        before=[r['mean_token_largest_channel_share'] for r in rows if r['stage']=='before']
        after=[r['mean_token_largest_channel_share'] for r in rows if r['stage']=='after']
        self.assertTrue(min(before)>.95);self.assertTrue(max(after)<.2)
        for readout in ('four','final','unstandardized'):
            for width in (1024,1152):
                raw=[torch.randn(1,2,3,width)*100 for _ in range(4)]
                result=torch.cat(readout_maps(raw,readout),-1)
                self.assertTrue(torch.allclose(result.square().mean(-1),torch.ones(1,2,3),atol=1e-3))

    def test_calibration_excludes_val_and_tuning(self):
        root=folder();image=root/'rgb.png';Image.new('RGB',(4,4)).save(image)
        manifests=pc.gate.read_manifest(pc.ROOT/'out/b2_manifest.jsonl')
        train=dict(next(r for r in manifests if r['split']=='train'),rgb_path=str(image),slot=0)
        val=dict(next(r for r in manifests if r['split']=='val'),rgb_path='must-not-open-val',slot=0)
        train.pop('rgb_sha256',None)
        seen=[]
        def encode(images,size):seen.append(len(images));return [torch.arange(32).reshape(1,2,2,8).float()+i for i in range(4)]
        enc=NS(encode=encode,metadata={'test':'train-only'})
        stats=extract.calibrate(enc,'stub',(4,4),[val,train],'binding',root/'stats.json','A5')
        self.assertEqual(seen,[1]);saved=json.loads((root/'stats.json').read_text())
        self.assertEqual({r['split'] for r in saved['rows']},{'train'});self.assertEqual(stats['taps'][0]['tokens'],4)

    def test_a8_composes_both_normalized_components_for_all_readouts(self):
        records=[dict(region_id='one')];x=torch.randn(1,1024);y=torch.randn(1,1024)
        original=feature_data.load_features
        for readout in ('four','final','unstandardized'):
            with patch('feature_data.load_features',side_effect=[(x,records,[]),(y,records,[])]) as loader:
                combined,_,_=original('unused','A8','training',readout)
            self.assertEqual([c.args[1] for c in loader.call_args_list],['A2','A4'])
            self.assertTrue(all(c.args[3]==readout for c in loader.call_args_list));self.assertEqual(combined.shape,(1,1024))


class Spatial(unittest.TestCase):
    def test_real_frame_and_mask_reject_shift_transpose_noise(self):
        row=pc.gate.read_manifest(pc.ROOT/'out/b2_manifest.jsonl')[0]
        with Image.open(row['rgb_path']) as im:x=torch.from_numpy(np.asarray(im.resize((64,48))).copy()).float()/255
        # A deterministic pointwise image descriptor preserves exact mirror correspondence.
        descriptors=torch.cat([torch.sin(x*(i+1)) for i in range(24)],-1)
        maps=[descriptors[None]+.01*k for k in range(4)]
        raster=extract.raster_masks(row)
        masks=[torch.from_numpy(v[row['slot']].copy()) for v in raster.values() if v[row['slot']].any()]
        masks=[m for m in masks if (m&m.flip(-1)).sum()<.1*m.sum()]
        self.assertTrue(masks);mask=torch.stack(masks)
        # One descriptor grid per instance, using the same real frame.
        maps=[m.repeat(len(mask),1,1,1) for m in maps];flipped=[m.flip(2) for m in maps]
        verified=validate_correspondence(maps,flipped,mask)
        self.assertEqual(verified['status'],'PASS')
        self.assertTrue(all(value=='FAIL' for value in verified['mutant_grid_tests'].values()))
        for kind in ('left','right','transpose'):
            self.assertEqual(correspondence(corrupt(maps,kind),corrupt(flipped,kind),mask)['status'],'FAIL',kind)
        generator=torch.Generator().manual_seed(42)
        noise=[torch.randn(m.shape,generator=generator) for m in maps]
        self.assertEqual(correspondence(maps,noise,mask)['status'],'FAIL')

    def test_outside_extract_requires_successful_smoke(self):
        from test_resume import ResumeTests
        root,a=ResumeTests().fixture();a.arm='A5';a.phases='extract'
        (root/'LOCAL_PIN.json').write_text('{}');Path(a.weights).write_text(json.dumps({'cradio_v4_so400m':{'path':str(root)}}))
        with patch('run_arm.gate.read_manifest',return_value=[]),patch('run_arm.subprocess.run') as launch:
            with self.assertRaisesRegex(ValueError,'smoke gate'):run_arm.run(a)
        launch.assert_not_called()


if __name__=='__main__':unittest.main()
