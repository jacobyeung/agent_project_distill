"""Candidate adapters for cached SAM instances and mask-decoder exports."""
import sys
import numpy as np
from .pointing import RKIT
from .selector import Candidate, centroid


def sam_candidates(cache, name, tau, proposal_gate=False):
    sys.path.insert(0, str(RKIT))
    from rk.sam3mask import tower, instance_masks
    text = tower().phrase(name)
    if text not in cache['phrases']:
        return []
    result = []
    for k in range(32):
        record = cache['frames'][str(k)]['phrases'][text]
        # Default preserves the kit's frozen frame gate. Native mode gates EACH
        # proposal strictly, without depending on the top proposal's click.
        if not proposal_gate and not tower().accepted(record, tau):
            continue
        for j, (mask, score) in enumerate(instance_masks(record)):
            confidence = float(record['presence'])*score
            if proposal_gate and confidence <= tau:
                continue
            uv = centroid(mask)
            if uv is not None:
                result.append(Candidate(k+1, uv, confidence, j, mask, 'sam3'))
    return result


def decoder_candidates(values, label_index, tau):
    result = []
    for k in range(32):
        if values['prob'][label_index, k] < tau or not values['mask'][label_index, k].any():
            continue
        result.append(Candidate(k+1, values['uv'][label_index, k].tolist(),
                                float(values['prob'][label_index, k]),
                                mask=values['mask'][label_index, k], source='mask_decoder'))
    return result
