"""The SAM native gate and the frozen 0.5 m, one-vote-per-frame selector."""
import numpy as np
from ofs import core as O, hrp_reference as H
from .ground_sources import native_gate


def select(name, source, geometry, selector, grids=None):
    if hasattr(source, 'selector_candidates'):
        clicks = source.selector_candidates(name)
    else:
        grids = O.lift_grid(geometry) if grids is None else grids
        proposals, _ = source.proposals_for(name, geometry, selector, grids)
        clicks = [H.Candidate(p.frame, H.centroid(p.mask), p.joint, p.index, p.mask, 'own')
                  for p in sorted(native_gate(proposals), key=lambda p: (p.frame, p.index))
                  if H.centroid(p.mask) is not None]
    selection = H.select(clicks, geometry, radius=.5)
    values = O.empty_values(1)
    proposals = []
    for index in selection['candidate_indices']:
        c = clicks[index]
        k = c.frame - 1
        values['mask'][0, k] = c.mask
        values['prob'][0, k] = 1.
        values['uv'][0, k] = np.rint(c.uv)
        # Selection uses the centroid lift, independently of surface eligibility.
        points, camera, _ = geometry.lift(c.frame, np.asarray(c.uv)[None], mode='center')
        proposals.append(O.Proposal(c.frame, c.instance, c.confidence, 1., c.mask,
                                    points, points[0], 0., float(camera[0, 2]), O.voxel_set(points)))
    values['iou'] = values['prob'].copy()
    values['frame_prob'] = values['prob'].copy()
    values['area'] = values['mask'].mean(axis=(-1, -2))
    candidates = [O.Candidate(name, name+':native', proposals,
                    features=dict(peak=float(np.mean(sorted((p.joint for p in proposals), reverse=True)[:2])),
                                  support=len(proposals)))] if proposals else []
    # Rescue can select a different object hypothesis. Retain every gated
    # primary mask for its projection match, including unselected hypotheses.
    primary = [O.Proposal(c.frame,c.instance,c.confidence,1.,c.mask,
                         np.empty((0,3)),np.zeros(3),0.,0.,frozenset()) for c in clicks]
    return candidates, values, selection, primary
