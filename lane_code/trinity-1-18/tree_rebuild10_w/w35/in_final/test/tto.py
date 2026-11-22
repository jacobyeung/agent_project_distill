"""fix21 timeout test: the tree's own launch_r2.persistence.milestone on a gloo world of 4 (CPU), as run_steps calls it
after a save (carrier_c1_run.py:2453), with upload() stubbed to sleep U seconds on rank 0 while ranks 1-3 wait in its
broadcast_object_list. The default group is created as carrier_c1_run.py:2876 creates it, with the GPU-branch timeout
read from the tree's source line and scaled by 1/SCALE (the cpu branch is a fixed 30 s, so the harness passes the
scaled value itself). Usage: tto.py <tree> <label> <upload seconds at real scale> [scale]"""
import ast, datetime, json, os, re, sys, time
from pathlib import Path
import torch.multiprocessing as mp
TREE = Path(sys.argv[1]).resolve(); LABEL = sys.argv[2]; UPLOAD = float(sys.argv[3]); SCALE = float(sys.argv[4]) if len(sys.argv) > 4 else 60.
src = (TREE/'student_pilot/carrier_c1_run.py').read_text()
m = re.search(r"dist\.init_process_group\('gloo' if cpu else 'nccl', timeout=datetime\.timedelta\(seconds=30 if cpu else (\d+)\)\)", src)
GPU_TIMEOUT = int(m.group(1))
def worker(rank, port, q):
    os.environ.update(MASTER_ADDR='127.0.0.1', MASTER_PORT=str(port), RANK=str(rank), WORLD_SIZE='4')
    sys.path.insert(0, str(TREE))
    import torch.distributed as dist
    import launch_r2.persistence as P
    assert P.__file__.startswith(str(TREE))
    P.upload = lambda cfg, directory, kind: time.sleep(UPLOAD/SCALE)
    dist.init_process_group('gloo', rank=rank, world_size=4, timeout=datetime.timedelta(seconds=GPU_TIMEOUT/SCALE))
    t = time.monotonic()
    try:
        P.milestone({'r2_identity': {}}, '/nonexistent', 'checkpoint', rank, True); r = 'PASS'
    except Exception as e:
        r = 'FAIL ' + type(e).__name__ + ': ' + str(e).splitlines()[0][:120]
    q.put((rank, r, round(time.monotonic()-t, 2)))
    try: dist.destroy_process_group()
    except Exception: pass
if __name__ == '__main__':
    ctx = mp.get_context('spawn'); q = ctx.Queue(); port = 29600 + (os.getpid() % 300)
    ps = [ctx.Process(target=worker, args=(r, port, q)) for r in range(4)]
    for p in ps: p.start()
    res = sorted(q.get(timeout=GPU_TIMEOUT/SCALE + UPLOAD/SCALE + 120) for _ in ps)
    for p in ps: p.join(30)
    ok = all(r[1] == 'PASS' for r in res)
    print(json.dumps(dict(tree=LABEL, gpu_timeout_s=GPU_TIMEOUT, upload_s=UPLOAD, scale=SCALE,
        scaled_timeout_s=GPU_TIMEOUT/SCALE, scaled_upload_s=UPLOAD/SCALE, ranks=res, all_pass=ok)))
