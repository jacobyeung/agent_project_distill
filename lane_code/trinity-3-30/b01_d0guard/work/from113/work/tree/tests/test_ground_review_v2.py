"""Independent geometry edge cases and decode admission regressions."""
import copy
from types import SimpleNamespace
import unittest
from unittest import mock
import numpy as np
from student_pilot import ground_lifting as L, mdg_decode as D
from student_pilot.ground_admission import qualification, multiple_instances
from student_pilot.p3_printed_calculator import PrintedPointRegistry
from tests.test_ground_backend import Geometry, masks


class GeometryReview(unittest.TestCase):
    def test_camera_best_frame_has_known_nonidentity_pose(self):
        geo = Geometry()
        # A fixed world point seen from a translated, rotated frame 3.
        geo.cam = lambda k: (np.array([[0.,0,1],[1,0,0],[0,1,0]]) if k == 3 else
                              np.array([[1.,0,0],[0,0,1],[0,-1,0]]),
                              np.array([1.,2.,3.]) if k == 3 else np.zeros(3))
        camera, f1 = L.public_centres(geo, 3, np.array([5.,8.,10.]))
        np.testing.assert_array_equal(camera, [6.,-7.,4.])
        np.testing.assert_array_equal(f1, [5.,10.,8.])

    def test_edge_spread_rejects_dropped_points_before_median(self):
        class Edge(Geometry):
            def lift(self, k, uv, **kw):
                p, pc, _ = super().lift(k, uv, **kw)
                edge = np.minimum(uv, 1000-uv).min(1)
                # Most interior points are dropped; accepted median must be .03.
                spread = np.where(edge <= 40, .15, np.where(uv[:,0] < 500, .03, .30))
                return p, pc, spread
        m = np.zeros((32,100,100), bool); m[0,:,:] = True
        result = L.lift_object('x', m, np.ones(32), Edge(), tau=.5)
        self.assertTrue(result['seen'])
        self.assertEqual(result['spread'], .03)
        pts = np.asarray(result['points']['1'])
        # Independently count eroded pixels inside crop, away from narrow edge,
        # and left of the image centre (46 x 92).
        self.assertEqual(len(pts), 46*92)

    def test_crop_is_inclusive_and_erosion_precedes_crop(self):
        uv = L.mask_pixels(np.ones((100,100), bool))
        self.assertEqual(len(uv), 96*96)
        np.testing.assert_array_equal(uv.min(0), [25.,25.])
        np.testing.assert_array_equal(uv.max(0), [975.,975.])

    def test_horizontal_size_sorted_even_when_fit_returns_short_first(self):
        with mock.patch.object(L, 'fit_gbox', return_value=np.array([1.,3.,2.])):
            result = L.lift_object('x', masks(), np.ones(32), Geometry(), tau=.5)
        self.assertEqual(result['size'], [3.,1.,2.])

    def test_gap_minimum_and_smaller_area_frame_ranking(self):
        a = dict(name='a', seen=True, visible=[1,2], areas={'1':.9,'2':.4},
                 points={'1':[[0,0,0]],'2':[[0,0,0],[10,0,0]]})
        b = dict(name='b', seen=True, visible=[1,2], areas={'1':.1,'2':.3},
                 points={'1':[[8,0,0]],'2':[[1,0,0],[5,0,0]]})
        audit = []
        self.assertEqual(L.gap_objects(a,b,audit=audit), 1.)
        self.assertEqual(audit[0]['frames'], [2,2])

    def test_probability_is_audit_only(self):
        result = L.lift_object('x', masks(), np.ones(32)*.73, Geometry(), tau=.5)
        line = L.render_ground(result, PrintedPointRegistry()).splitlines()[0]
        self.assertEqual(line, 'x: frames 1,3 (best 3)')
        self.assertEqual(L.VERSION, '3.12.2')


class AdmissionReview(unittest.TestCase):
    def test_literal_multiword_labels_and_arbitrary_qualifiers(self):
        self.assertFalse(qualification('office chair'))
        for name in ('wooden table','white cabinet','chair on the left','large chair'):
            self.assertTrue(qualification(name))
        backend = D.Backend(SimpleNamespace(mdg_head=object(), mdg_meta={'tau':.5}), None, None)
        with mock.patch.object(D, 'predict', side_effect=AssertionError('qualified name reached MDG')):
            self.assertEqual(backend.ground('wooden table', None, PrintedPointRegistry()), 'wooden table: not seen')
        self.assertTrue(backend.queries[0]['qualified'])
        self.assertEqual(backend.queries[0]['refusal_reason'], 'qualified_label')

    def test_multiple_substantial_components_are_audit_only_and_replay(self):
        m = np.zeros((1,32,30,30), bool)
        m[0,0,2:10,2:10] = True; m[0,0,20:28,20:28] = True
        values = dict(mask=m, prob=np.ones((1,32)))
        backend = D.Backend(SimpleNamespace(mdg_head=object(), mdg_meta={'tau':.5}), None, Geometry())
        with mock.patch.object(D, 'predict', return_value=(values,None)):
            text=backend.ground('chair',None,PrintedPointRegistry())
            self.assertNotIn('not seen',text)
        q = backend.queries[0]
        self.assertIsNone(q['multi_instance']); self.assertIsNone(q['refusal_reason'])
        self.assertEqual(q['mask_component_counts'][0],2)
        self.assertEqual(q['substantial_component_counts'][0],2)
        with mock.patch.object(L,'OwnGeometryAdapter',side_effect=lambda geometry:geometry):
            replay = D.ReplayBackend({'chair':q}, Geometry(), PrintedPointRegistry())
        self.assertEqual(replay.ground('chair'),text)
        m[0,0,20:28,20:28] = False; m[0,0,25,25] = True
        self.assertFalse(multiple_instances(m[0],np.ones(32),.5))


class QueryScopeReview(unittest.TestCase):
    def test_full_routing_stream_logits_closed_with_nonzero_adapters(self):
        import torch
        from student_pilot import carrier_c1_decode as decode, mdg_lora
        from tests.test_mdg_features import fixture,small_layers
        from tests.test_ground_backend import StubDecoder,StreamTokenizer
        model,batch=fixture();tokenizer=StreamTokenizer()
        processor=SimpleNamespace(tokenizer=tokenizer,_routing_tokens={'ids':{'<ground':2}})
        model.mdg_head=StubDecoder();model.mdg_meta={'tau':.5}
        def run():
            script=iter([2,6,2,3,4,6,1]);seen=[]
            def force(ids,logits):
                seen.append(logits.clone())
                out=torch.full_like(logits,-1e9);out[:,next(script)]=0;return out
            return decode.generate(model,processor,batch,logits_processor=force),torch.cat(seen)
        with torch.no_grad(),small_layers():
            before,logits=run()
            mdg_lora.install(model,2)
            for parameter in model.auxiliary_heads.mdg_lora.parameters():parameter.normal_(0,.5)
            # The toy tokenizer represents a whole call with one token; remove
            # this atomic-opener validation only for this numeric fixture.
            real=decode.mdg_decode.QueryStream if hasattr(decode,'mdg_decode') else D.QueryStream
            class ToyStream(real):
                def __init__(self,model_,tokenizer_):
                    config=model_.__dict__.pop('mdg_lora_config')
                    try:super().__init__(model_,tokenizer_)
                    finally:model_.mdg_lora_config=config
            with mock.patch.object(D,'QueryStream',ToyStream),mock.patch('student_pilot.mdg_stream.QueryStream',ToyStream):
                after,actual=run()
                torch.testing.assert_close(actual,logits,rtol=0,atol=0)
                self.assertEqual(before['text'],after['text'])
                consume=decode.consume_cache_tokens
                def open_main(native,ids,attention,cache,**kw):
                    with mdg_lora.suffix_mask(model,torch.ones((1,1),dtype=torch.bool)):
                        return consume(native,ids,attention,cache,**kw)
                with mock.patch.object(decode,'consume_cache_tokens',side_effect=open_main):
                    _,changed=run()
                self.assertFalse(torch.equal(changed,logits))
            for query in after['heads']['query_passes']:
                self.assertEqual(query['token_ids'],tokenizer.encode(f'<ground obj="{query["name"]}">'))
                self.assertEqual(query['gated_token_positions'],list(range(len(query['token_ids']))))
