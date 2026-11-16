"""Visibility adapter for supplied scan witnesses, not a target generator.

The mesh owner supplies the minimum and a tolerance set of true closest pairs.
This adapter selects visible members and retains unavailable full targets.
"""
import numpy as np
from .surface_rows_v313 import visible, pair_allowed


def scan_target(reference, geometry, masks, frames, *, z_tolerance_m=.01, pair_tolerance_m=1e-6):
    minimum=float(reference['distance_m'])
    if not np.isfinite(minimum) or minimum<0 or len(masks)!=2 or len(frames)!=2:
        raise ValueError('invalid_scan_reference')
    for pair in reference['closest_pairs_world']:
        if not pair_allowed(pair,minimum,tolerance_m=pair_tolerance_m):
            raise ValueError('scan_pair_outside_tolerance_set')
        selected=[]
        for point,mask,candidates in zip(pair,masks,frames):
            found=None
            for frame in sorted(candidates):
                check=visible(geometry,point,frame,mask,z_tolerance_m=z_tolerance_m)
                if check['visible']:
                    found=(int(frame),check);break
            selected.append(found)
        if all(s is not None for s in selected):
            # Trace coordinates are the supplied scan surface points. Depth
            # verifies visibility; predicted-geometry lifts are a different route.
            return dict(status='ok',positions=pair,frames=[s[0] for s in selected],
                        distance_m=float(np.linalg.norm(np.subtract(*pair))),
                        observed_surface_points=True,true_closest_visible=True,
                        full_surface_distance_m=minimum,pair_tolerance_m=pair_tolerance_m,
                        visibility_checks=[s[1] for s in selected],reference_authority=reference['authority'],
                        full_surface_authority=reference['authority'])
    return dict(status='unavailable',full_surface_distance_m=None,true_closest_visible=False,
                reason='no_visible_true_pair_in_supplied_set',
                all_ties_examined=bool(reference.get('complete_tolerance_set',False)),
                reference_authority=reference['authority'])
