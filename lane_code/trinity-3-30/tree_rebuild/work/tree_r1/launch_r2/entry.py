"""One production preparation/admission/training path for the repaired leg."""
import os
from pathlib import Path
from student_pilot.p3_provenance import file_pin, load, pinned, write, digest


def host_receipt(root, launch):
    """Reuse the reviewed host output without rebuilding or copying its stores."""
    from student_pilot.r2_portable import bound
    from .runtime import obligations
    if not launch.get('prepared'):
        return None
    value = load(bound(launch['prepared'],root))
    packet = load(bound(launch['inputs'],root))
    expected = {(s['source']['sha256'],s['line'],s['category']) for s in obligations()}
    reached = {(s['source']['sha256'],s['line'],s['category']) for s in value.get('statements',[]) if s.get('reached') is True}
    if (value.get('schema') != 'r2-host-preparation-v1' or value.get('full_store') is not True
            or value.get('source_revision') != launch['source_revision']
            or value.get('packet_digest') != digest(packet) or reached != expected):
        raise ValueError('Frame-host receipt differs from the source, packet or statement obligations')
    cfg = value['config']
    if (packet.get('configuration', {}).get('sha256') != launch['config']['sha256']
            or value.get('bound_config_sha256') != launch['config']['sha256']
            or value.get('prepared_config_sha256') != digest(cfg)):
        raise ValueError('Host configuration differs from bound kit')
    expected_rows = {(r,s) for r in range(cfg['world_size']) for s in cfg['streams']}
    actual = {(r['rank'],r['stream']) for r in value['first_batch'] if r.get('forward') is False and r.get('tokens',0)>0}
    if cfg['world_size']!=4 or not expected_rows <= actual:
        raise ValueError('Frame-host receipt lacks every rank and stream')
    return value


def execute(cfg, mode, *, ranks=None):
    from student_pilot import carrier_c1_run as run
    if mode not in ('p', 'c'):
        raise ValueError('Unknown production mode')
    if mode == 'p':
        return run.prepare(cfg)
    if mode == 'c':
        return run.first_batch_check(cfg, list(range(cfg['world_size'])) if ranks is None else ranks,
                                     Path(cfg['output'])/'0.json', device='cpu', encode_only=True)


def main(root, mode):
    root = Path(root).resolve()
    from .build import scan
    scan(root)
    launch = load(root/'k/launch.json')
    cfg = load(root/launch['config']['file'])
    if mode == 'h':
        from .host import run_packet, cpu_guard
        import sys
        cpu_guard(sys.argv, os.environ, load(root/'b/wh.json'))
        if not launch.get('inputs'):
            raise ValueError('Missing frame-host input inventory')
        return run_packet(root, launch['inputs'], full=True)
    # Enter the real trainer preparation even for an incomplete closure: it owns
    # the evidence gate and names the first missing component before weight IO.
    from student_pilot.r2_policy import preparation
    preparation(cfg['r2_build2'], root)
    packet = launch.get('inputs')
    if not packet:
        raise ValueError('Missing frame-host input inventory')
    from .host import run_packet
    prepared = host_receipt(root,launch)
    if prepared is None:
        prepared = run_packet(root, packet, full=True)
    cfg = prepared['config']
    if mode in ('p', 'c'):
        return prepared
    if not launch.get('production_authorized'):
        raise ValueError('Missing production authorization and independent review')
    from .distributed import launch as launch_workers
    return launch_workers(root,cfg,mode,launch)
