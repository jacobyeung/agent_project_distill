"""Paired robustness and optional error-detection scores."""
import numpy as np
from scipy.stats import rankdata
from .episodes import load_ie

def detection_auc(labels, scores):
    labels, scores = np.asarray(labels), np.asarray(scores, float)
    if labels.shape != scores.shape or labels.ndim != 1 or not np.isfinite(scores).all() or not np.isin(labels, [0, 1]).all():
        raise ValueError('Invalid detection labels/scores')
    pos, neg = int(sum(labels)), int(sum(1-labels))
    if not pos or not neg:
        return None
    return float((rankdata(scores)[labels == 1].sum()-pos*(pos+1)/2)/(pos*neg))

def detection_atd(onsets, detections, horizons):
    """Mean primitive-step delay; misses are right-censored at episode horizon.

    Onsets must be supplied by the caller; token offsets are not action times.
    Early alarms are excluded from delay and counted separately.
    """
    if not (len(onsets) == len(detections) == len(horizons)):
        raise ValueError('Mismatched detection sequences')
    delays, early, misses = [], 0, 0
    for onset, detected, horizon in zip(onsets, detections, horizons):
        if onset < 0 or horizon < onset:
            raise ValueError('Invalid detection onset/horizon')
        if detected is not None and detected < onset:
            early += 1
            continue
        if detected is None:
            misses += 1
        delays.append((horizon if detected is None else min(detected, horizon))-onset)
    return dict(ATD=float(np.mean(delays)) if delays else None, n=len(delays), early_alarms=early, censored_misses=misses)

def pair_drop(pairs, results):
    by_id = {r['episode_id']:r for r in results}
    if len(by_id) != len(results):
        raise ValueError('Duplicate results')
    out = {}
    for metric in ('SR', 'SPL'):
        clean = [by_id[p['clean'].episode_id][metric] for p in pairs]
        perturbed = [by_id[p['perturbed'].episode_id][metric] for p in pairs]
        out[metric] = dict(clean=float(np.mean(clean)), perturbed=float(np.mean(perturbed)),
                           drop_clean_minus_perturbed=float(np.mean(np.array(clean)-perturbed)))
    return dict(pairs=len(pairs), **out)
