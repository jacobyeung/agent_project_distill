import os, sys, json
out = {}
out['python'] = sys.version.partition(' ')[0]
out['cwd'] = os.getcwd()
live = '/project/community/jjyeung/okh7/x_22c714e1/o/174134/live'
for p in ('/tmp/q_22c714e1/p/q/c.json', '/tmp/q_22c714e1/r.json', '/tmp/q_22c714e1/p/s/launch_r1/production_proof.py',
          os.environ['Q_KIT'] + '/b/a.py', '/tmp/a15_dbg_174134', os.environ.get('R1_RUNTIME_RECORD', ''),
          live, '/project/community/jjyeung/okh7/x_22c714e1/o/174134/HOLD.txt'):
    out['has ' + p] = os.path.exists(p)
# write permission as the kernel reports it; no file is created
for d in ('/tmp/q_22c714e1', '/tmp/q_22c714e1/p', '/tmp/q_22c714e1/p/q', '/tmp/q_22c714e1_174134', '/tmp/q_22c714e1_174134/p/q/p',
          '/tmp/a15_dbg_174134', '/project/community/jjyeung/okh7/x_22c714e1/o/174134', live,
          os.environ['R1_MOUNT'] + '/runs', os.environ['R1_MOUNT']):
    out['writable ' + d] = os.access(d, os.W_OK)
out['live names'] = sorted(os.listdir(live))[:20]
out['env'] = {k: os.environ.get(k) for k in ('PYTHONPATH', 'CUDA_VISIBLE_DEVICES', 'TMPDIR', 'HF_HOME', 'Q_E4', 'OMP_NUM_THREADS', 'PATH', 'SLURM_JOB_ID', 'C1_EXPECT_FLA')}
import torch, numpy
out['torch'] = torch.__version__; out['numpy'] = numpy.__version__
out['cuda_available'] = torch.cuda.is_available(); out['device_count'] = torch.cuda.device_count()
if torch.cuda.is_available():
    x = torch.zeros(4, device='cuda:0'); out['cuda0'] = torch.cuda.get_device_name(0); out['sum'] = float(x.sum())
print(json.dumps(out, indent=1))
