"""A trace-local claim must never change the next question's candidate memory."""
import unittest
from student_pilot.svp_stages import SVPStages,RescuePass
from student_pilot import carrier_c1_decode as D,verify_pass as V
from tests.test_ground_r2 import svp,own_source
from tests.test_verify_r2 import integration_fixture,force
from tests.test_svp_stages_r2 import fixture


class RescueClaims(unittest.TestCase):
    def test_claimed_object_is_not_an_object_level_rescue_miss(self):
        g,other,frames=fixture();model,p,row=integration_fixture();queries=[]
        source=own_source(other,lambda name:[(1,0,14,19,.9),(3,0,14,19,.9)])
        original=source.fetch
        source.fetch=lambda *a:queries.append(a[0]) or original(*a)
        stages=SVPStages(rescue=RescuePass(other,source,other.frame_map,frames,'shared'),world_reference='shared')
        b=svp(g,own_source(g),stages=stages,verify_threshold=0.)
        row.update(frame_indices=list(g.frame_map.source_indices),hrp_frame_indices=list(g.frame_map.source_indices),
                   frame_rgb_sha256=list(g.frame_map.rgb_sha256),ground_frames=frames)
        record=D.generate(model,p,row,mask_source='svp_own',ground_backend=b,verify=V.Config(b),logits_processor=force([40,43,1]))
        self.assertEqual(record['calls'][1]['response'],'table: not seen')
        self.assertEqual(queries,[])
        later=D.generate(model,p,row,mask_source='svp_own',ground_backend=b,verify=V.Config(b),logits_processor=force([43,1]))
        fresh=svp(g,own_source(g),stages=stages,verify_threshold=0.)
        clean=D.generate(model,p,row,mask_source='svp_own',ground_backend=fresh,verify=V.Config(fresh),logits_processor=force([43,1]))
        self.assertEqual(later['text'],clean['text']);self.assertIn('frames',later['text'])
        self.assertFalse(b.memory.get('table',b.config_hash,scene=b.scene).get('rescue'))


if __name__=='__main__':unittest.main()
