"""Test copied code at its original absolute paths; never run GPU work."""
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from build_sources import ROOT, KIT, MANIFEST, TOWER


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'inner':
        sys.path[:0] = [str(KIT / 'work'), str(KIT / 'native_kit')]
        import verify_sources
        import bindings as B
        import k1_phases as F
        from phase_support import compare_binding
        result = dict(verified_sources=verify_sources.verify(),
                      binding=compare_binding(B, F, B.load(MANIFEST), B.load(TOWER)),
                      manifest_byte_sha256=B.sha(MANIFEST), synthetic=True)
        Path(sys.argv[2], 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
        return
    from namespace_adapter import namespace
    native = ROOT / 'reference/sj/orch_cd/evalx/work/milestone'
    sys.path.insert(0, str(native))
    import orchard_stage as S
    run = ROOT / 'evidence' / ('namespace_' + uuid.uuid4().hex[:10])
    run.mkdir()
    stage = run / 'stage'
    out = run / 'out'
    out.mkdir()
    archive = ROOT / 'payload/d64c8e20.tar'
    S.unpack(archive, stage)
    config = dict(build=str(ROOT), output=str(out), runtime_paths=[
        '/scratch/jjyeung/envs/p1cpu',
        '/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu'])
    command = namespace(stage, config) + [sys.executable, '-B', str(Path(__file__).resolve()),
                                         'inner', str(out)]
    (run / 'ARGV.json').write_text(json.dumps(command, indent=2) + '\n')
    with (run / 'probe.log').open('x') as log:
        process = subprocess.run(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''),
                                 stdout=log, stderr=subprocess.STDOUT)
    status = dict(run=str(run), returncode=process.returncode,
                  full_job_rehearsal=False, production_runtime=False)
    (ROOT / 'evidence/NAMESPACE.json').write_text(json.dumps(status, indent=2) + '\n')
    print(json.dumps(status, indent=2))


if __name__ == '__main__':
    main()
