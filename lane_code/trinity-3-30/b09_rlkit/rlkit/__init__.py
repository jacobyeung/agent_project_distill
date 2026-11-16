"""RL kit (brief 09): rounds of sampling, scoring, selection and update for the C1 student.

Modules: common (hashing, atomic files, seeds), store (per-draw commits, resume),
forcing (path forcing and the sampling choice), sampler (native decode driver),
towercache (per-clip frozen-tower cache), score (benchmark score c), gate (grammar
and provenance gate g), reward (r = c*g - length term), baselines, select (mode a),
grpo (mode b advantages and loss math).
"""
KIT_VERSION = 'rlkit-v1'
