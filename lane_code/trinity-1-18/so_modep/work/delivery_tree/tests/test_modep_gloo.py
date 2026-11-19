"""Optional two-rank CPU/Gloo parity; run only where local sockets are available."""
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest


def _worker(rank, root, port):
    import torch
    import torch.distributed as dist
    from student_pilot import orchard_paths
    from student_pilot.p3_provenance import file_pin
    from student_pilot.s1_admission import FrameAudit, verify_frames
    torch.set_num_threads(8)
    root = Path(root)
    project = root/'project'
    frames = project/'data2root'
    orchard_paths.PROJECT = project
    os.environ.update(Q_E1='1', Q_E4=json.dumps({'/data2': str(frames)}))
    dist.init_process_group('gloo', init_method=f'tcp://127.0.0.1:{port}', rank=rank, world_size=2)
    try:
        pins = [dict(path='/data2/'+str(i), sha256=file_pin(frames/str(i))['sha256']) for i in range(32)]
        digests = []
        for flag in ('0', '1'):
            os.environ['S1_PREP_FAST_PATHS'] = flag
            output = root/f'rank{rank}_{flag}'
            output.mkdir()
            audit = FrameAudit(output, [frames], sample_size=8)
            try:
                for i in range(16):
                    audit.keep(dict(student_input=dict(frames=pins[i:]+pins[:i])), 'vqa')
                report = audit.finish()
            finally:
                audit.close()
            verify_frames(report)
            digests.append(hashlib.sha256((output/'frame_inventory.sqlite').read_bytes()).hexdigest())
        assert digests[0] == digests[1]
        gathered = [None, None]
        dist.all_gather_object(gathered, digests)
        assert gathered[0] == gathered[1]
        (root/f'rank{rank}.json').write_text(json.dumps({'inventory_sha256': digests, 'ranks_identical': True}))
    finally:
        dist.destroy_process_group()


@unittest.skipUnless(os.environ.get('MODEP_RUN_GLOO') == '1', 'lane must run work/run_gloo.sh outside the socket sandbox')
class GlooParity(unittest.TestCase):
    def test_native_frame_inventory_matches_across_two_cpu_ranks(self):
        import torch
        import torch.multiprocessing as mp
        torch.set_num_threads(8)
        root = Path(tempfile.mkdtemp(prefix='modep_gloo_', dir=os.environ['TMPDIR']))
        frames = root/'project/data2root'
        frames.mkdir(parents=True)
        for i in range(32):(frames/str(i)).write_bytes(bytes([i])*256)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        mp.spawn(_worker, args=(str(root), port), nprocs=2, join=True)
        self.assertEqual(json.loads((root/'rank0.json').read_text()), json.loads((root/'rank1.json').read_text()))


if __name__ == '__main__':unittest.main()
