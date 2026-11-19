"""Pinned goal-benchmark scene tokens, checked before scene assets are opened."""
from functools import lru_cache

from .common import ProvenanceError, Refusal, pinned, read_json

RESTI_EXCLUSIONS = {
    "path": "/scratch/jjyeung/orch_cd/streams2/work/flt/RESTI_EXCLUSIONS_20261109.json",
    "sha256": "ec38428b2c720956894eb16bd91e74fd6d86a8389cecdb715842dbd9a3c85415",
}


@lru_cache(maxsize=8)
def _tokens(path, sha256):
    tokens = read_json(pinned({"path": path, "sha256": sha256}))["tokens_flat"]
    if not isinstance(tokens, list) or not tokens or any(not isinstance(t, str) or not t for t in tokens):
        raise ProvenanceError("invalid goal-benchmark exclusion tokens")
    return frozenset(tokens)


def goal_tokens(config=None):
    pin = (config or {}).get("goal_benchmark_exclusions", RESTI_EXCLUSIONS)
    if not (config or {}).get("infrastructure_only") and pin != RESTI_EXCLUSIONS:
        raise ProvenanceError("goal-benchmark exclusion pin differs from ReSTI authority")
    return _tokens(pin["path"], pin["sha256"])


def refuse_goal_scene(canonical, *aliases, config=None):
    if goal_tokens(config).intersection(scene_tokens(canonical, *aliases)):
        raise Refusal("goal_benchmark_scene", canonical)


def scene_tokens(*identities):
    """Include the documented d1 namespace for native ScanNet identities."""
    from .provenance import rung1_alias
    result = set(identities)
    for identity in identities:
        if identity.startswith('scannet/'):
            result.add('d1/'+identity.split('/',1)[1])
            result.add(rung1_alias(identity, 'd1/'))
    return result
