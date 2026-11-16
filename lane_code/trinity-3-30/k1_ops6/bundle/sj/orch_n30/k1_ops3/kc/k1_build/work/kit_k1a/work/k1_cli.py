"""K1 phase command line; explicit fixtures replace only neural forwards."""
import argparse
from types import SimpleNamespace

import bindings as B
import k1_pipeline as K
import k1_phases as F


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=['preflight', 'cache', 'tables', 'render'])
    p.add_argument('--manifest', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--cache')
    p.add_argument('--fit')
    p.add_argument('--phase', choices=F.PHASES)
    p.add_argument('--max-seconds', type=int, default=14400)
    p.add_argument('--max-bytes', type=int, default=1_500_000_000)
    p.add_argument('--tower-cache')
    p.add_argument('--own-cache')
    p.add_argument('--cpu-fixture', action='store_true')
    p.add_argument('--preflight-out')
    p.add_argument('--gt-set')
    p.add_argument('--sensitivity', action='store_true')
    a = p.parse_args()
    if (a.gt_set or a.sensitivity) and a.stage not in ('tables', 'render'):
        p.error('--gt-set/--sensitivity are downstream only')
    if a.max_bytes <= 0:
        p.error('--max-bytes must be a positive integer')
    if a.stage in ('cache', 'preflight') and (not a.phase or a.max_seconds <= 0):
        p.error('cache/preflight requires a phase and positive time cap')
    m = B.load(a.manifest)
    if a.cpu_fixture:
        import run
        if m.get('production_ready') or a.stage not in ('cache', 'preflight'):
            raise ValueError('CPU stand-ins cannot run production manifests or render')
        run.validate_manifest(m, synthetic=True)
    else:
        K.check_manifest(m, a.phase if a.stage in ('cache', 'preflight') else 'downstream', a.gt_set, a.sensitivity)
    if a.stage == 'preflight':
        B.write(a.out, dict(manifest_sha256=B.digest(m), captures=len(m['captures']), phase=a.phase,
                            fixture_only=a.cpu_fixture, gpu_run=False))
        return 0
    if a.stage == 'cache':
        if a.preflight_out:
            B.write(a.preflight_out, dict(manifest_sha256=B.digest(m), captures=len(m['captures']),
                                         phase=a.phase, fixture_only=a.cpu_fixture, gpu_run=False))
        if a.cpu_fixture:
            from boundaries import CPU
            boundary = CPU()
        elif a.phase == 'convert':
            boundary = SimpleNamespace(synthetic=False, checkpoint=m['gpu']['artifact'])
        else:
            import torch
            if torch.version.cuda is None:
                raise ValueError('GPU phase requires a CUDA interpreter')
            from boundaries import GPU
            boundary = GPU(m['gpu'], phase=a.phase)
        return F.run(m, a.out, boundary, a.phase, a.max_seconds, a.tower_cache, a.own_cache,
                     max_bytes=a.max_bytes)
    if a.stage == 'tables':
        K.tables(m, a.cache, a.out, a.gt_set, a.sensitivity)
    if a.stage == 'render':
        K.responses(m, a.cache, a.fit, a.out, a.gt_set, a.sensitivity)
    return 0
