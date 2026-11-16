"""Local CPU planning with tensor/processor fakes; never stage or read model bytes."""
import json
from pathlib import Path
import subprocess
import sys
import uuid
import trinity_read as T

RUNTIME = Path('/scratch/jjyeung/orch_n30/evalx27/work/pull/x27c/r2/sj/orch_cd')


def bind_fixture(request):
    sys.path.insert(0, str(T.KIT/'proof'))
    import fakes
    fakes.install()
    import namespace_worker as W
    import paired_read as P
    config = T.load(T.REFERENCE/'CONFIG.json')
    if request['family'] in ('main', 'camera'): config['spec']['paired_protocol'] = True
    if request.get('model_slot'):
        P.select_model(T.DEFAULT_ROOT, config, request['model_slot'])
    result = W.bind_plan(config, request['family'], Path(request['work']),
                        ids=request.get('ids'), first=request.get('first'),
                        reader=RUNTIME/'legs1_reads', kit=RUNTIME/'rv_merge_fix/work/r3/aws_vl64rt',
                        camera=T.physical(T.DEFAULT_ROOT, P.CAMERA))
    T.dump(Path(request['work'])/'SPEC.json', config['spec'])
    return result


def need_fixture(args):
    out = T.writable(args.out)
    if not T.inside(out, T.BUILD):
        raise ValueError('Fixture outputs must remain inside this build')
    results = {}
    for family in T.FAMILIES if args.all else (args.family,):
        work = out.parent/('fixture_'+family+'_'+uuid.uuid4().hex)
        request = dict(family=family, work=str(work), ids=T.read_ids(args.ids) if args.ids else None,
                       first=args.first, model_slot=args.model_slot)
        T.dump(work/'INPUT.json', request)
        command = [str(T.KIT/'.venv/bin/python'), '-B', str(T.BUILD/'fixture_need.py'), str(work/'INPUT.json')]
        subprocess.run(command, check=True, cwd=str(T.BUILD))
        results[family] = T.load(work/'NEED.json')
        results[family]['fixture_directory'] = str(work)
    hashes = sorted({h for r in results.values() for h in r['need']})
    ordered = set((T.AREA/'work/NEED_X27.txt').read_text().splitlines())
    extra = sorted(set(hashes)-ordered)
    out.write_text(''.join(h+'\n' for h in hashes))
    Path(str(out)+'.extra_vs_X27').write_text(''.join(h+'\n' for h in extra))
    report = dict(families=results, frames=len(hashes), extra_vs_X27=extra,
                  estimated_png_bytes=sum(max(r['estimated_frame_bytes'].get(h, 0) for r in results.values()) for h in hashes),
                  fixture=True, namespace_executed=False, pixel_bytes_verified=False,
                  estimate_basis='Uncompressed RGB height * width * 3, not measured PNG bytes')
    T.dump(str(out)+'.json', report)
    print(json.dumps(dict(out=str(out), frames=len(hashes), extra_vs_X27=len(extra),
                         estimated_bytes=report['estimated_png_bytes'], fixture=True)))


if __name__ == '__main__':
    bind_fixture(T.load(sys.argv[1]))
