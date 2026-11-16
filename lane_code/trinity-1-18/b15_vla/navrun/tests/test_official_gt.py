import copy
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
from navrun.episodes import load_gt, training_gt, load_split
from navrun.rows import prepare_tracks
from navrun.click import gt_lead_point
from navrun.policies import OracleGTClickPolicy
from navrun.config import Config
from navrun.paths import OUT
from navrun.io import write_json

class OfficialGTTests(unittest.TestCase):
    def setUp(self):
        self.track=dict(actions=[1,0], forward_steps=1, locations=[[0,0,0],[0,0,-.25]])

    def test_keys_are_episode_ids(self):
        with patch('navrun.episodes.read_json',return_value={'17':self.track}):
            gt=load_gt('train',episodes=[SimpleNamespace(episode_id='17',start_position=[0,0,0])])
        self.assertEqual(set(gt),{'17'})
        self.assertEqual(gt['17']['source'],'supplied_official_r2r_ce_gt')

    def test_missing_episode_rejected(self):
        with patch('navrun.episodes.read_json',return_value={'17':self.track}):
            with self.assertRaisesRegex(ValueError,'Missing official'):
                load_gt('train',episodes=[SimpleNamespace(episode_id='18',start_position=[0,0,0])])

    def test_bad_start_rejected(self):
        with patch('navrun.episodes.read_json',return_value={'17':self.track}):
            with self.assertRaisesRegex(ValueError,'start pose'):
                load_gt('train',episodes=[SimpleNamespace(episode_id='17',start_position=[1,0,0])])

    def test_bad_streams_rejected(self):
        for field,value in [('actions',[0,1]),('actions',[4,0]),('forward_steps',2),('locations',[[0,0,0]]),
                            ('locations',[[0,0,0],[float('nan'),0,0]])]:
            track=dict(self.track,**{field:value})
            with patch('navrun.episodes.read_json',return_value={'17':track}):
                with self.assertRaises(ValueError):load_gt('train')

    def test_official_coverage_and_no_fallback(self):
        train=load_split('train')
        with patch('navrun.episodes.r2rie_training_gt',side_effect=AssertionError('fallback used')):
            tracks=training_gt(train)
        self.assertEqual(len(tracks),10819)
        self.assertEqual(len(load_gt('val_unseen',episodes=load_split('val_unseen'))),1839)
        self.assertEqual(len(load_gt('val_seen')),778)

    def test_official_refreshes_cached_reconstruction(self):
        e=load_split('train')[0]
        path=OUT/'tests/official_cache.json'
        write_json(path,{e.episode_id:dict(self.track,source='reconstructed_reference_follower')})
        tracks=prepare_tracks([e],path)
        self.assertEqual(tracks[e.episode_id],training_gt([e])[e.episode_id])

class GTLeadTests(unittest.TestCase):
    def test_follows_arc_not_goal_chord(self):
        path=[[0,0,0],[1,0,0],[1,0,2]]
        np.testing.assert_allclose(gt_lead_point(path,[0,0,0]),[1,0,1])

    def test_nearest_index_and_default_leg(self):
        np.testing.assert_allclose(gt_lead_point([[0,0,0],[0,0,3],[0,0,6]],[0,0,2.9]),[0,0,5])

    def test_endpoint_and_duplicates(self):
        np.testing.assert_allclose(gt_lead_point([[0,0,0],[0,0,0],[0,0,1]],[0,0,0]),[0,0,1])
        np.testing.assert_allclose(gt_lead_point([[0,0,0],[0,0,1]],[0,0,1]),[0,0,1])

    def test_tie_uses_first_index(self):
        np.testing.assert_allclose(gt_lead_point([[0,0,0],[0,0,4],[0,0,0]],[0,0,0]),[0,0,2])

    def test_empty_path_rejected(self):
        with self.assertRaises(ValueError):gt_lead_point([],[0,0,0])

    def test_stop_at_success_radius_strict_boundary(self):
        env=SimpleNamespace(config=Config(output_format='click'),position=np.zeros(3),heading=0.,distance=lambda:2.9)
        policy=OracleGTClickPolicy(env,{'17':[[0,0,0],[0,0,-4]]});policy.reset('17')
        self.assertEqual(policy.act([None]*32,'',{}),'stop')
        env.distance=lambda:3.
        self.assertTrue(policy.act([None]*32,'',{}).startswith('<goal'))

    def test_resume_identity_covers_gt(self):
        env=SimpleNamespace(config=Config())
        a=OracleGTClickPolicy(env,{'1':[[0,0,0]]})
        b=OracleGTClickPolicy(env,{'1':[[0,0,1]]})
        self.assertNotEqual(a.resume_identity(),b.resume_identity())

if __name__=='__main__':unittest.main()
