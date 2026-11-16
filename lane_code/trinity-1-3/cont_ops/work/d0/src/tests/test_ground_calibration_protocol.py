"""Small independent score fixture validates protocol calibration arithmetic."""
import unittest
from student_pilot.mdg_train import choose_tau,metrics_at

class CalibrationFixture(unittest.TestCase):
    def test_tau_grid_objective_and_miss_rate(self):
        r=dict(labels=[True,True,False,False],scores=[.8,.4,.3,.1],point_hits=[True,True,False,False],
               null_scores=[.3,.1],clip_labels=[True,False],clip_scores=[.8,.1],mask_ious=[1.],items=2)
        tau,objective=choose_tau(r)
        self.assertEqual(tau,.31);self.assertEqual(objective,1.)
        self.assertEqual(metrics_at(r,tau)['presence_recall'],1.)
