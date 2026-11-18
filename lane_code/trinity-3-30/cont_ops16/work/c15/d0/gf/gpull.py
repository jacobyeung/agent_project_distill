"""cont_ops7: run one governed pull. Usage: gpull.py LANE EXPECTED_BYTES OUTFILE -- argv...
Root = this helper's child 'groot' (python, stops itself, then runs argv as ITS child and waits; never execs);
member = ratelimit.py writing OUTFILE. Registers tier 3, pull, 8 MB/s, io-weight 1, allow-resume; waits; renames record."""
import os, sys, time, subprocess, json
GOV='/scratch/jjyeung/io_governor'; STREAMS='/data3/jjyeung/orch_n13_20261026/io_governor/streams'
lane, nbytes, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]; argv = sys.argv[sys.argv.index('--')+1:]
ROOT = "import os,signal,subprocess,sys; os.kill(os.getpid(), signal.SIGSTOP); sys.exit(subprocess.call(sys.argv[1:]))"
def state(pid):
    s=open('/proc/%d/stat'%pid).read(); return s[s.rindex(')')+2]
r, w = os.pipe()
root = subprocess.Popen(['/usr/bin/python3','-s','-c',ROOT,*argv], stdout=w, stdin=subprocess.DEVNULL)
os.close(w)
for _ in range(100):
    if state(root.pid) in 'Tt': break
    time.sleep(0.1)
else: sys.exit('root did not stop')
outf = open(out, 'xb')
rl = subprocess.Popen(['/usr/bin/python3','-s',GOV+'/ratelimit.py','-q','-L','1000','-B','65536'], stdin=r, stdout=outf)
os.close(r); outf.close()
for _ in range(100):
    if open('/proc/%d/comm'%rl.pid).read().strip()=='ratelimit': break
    time.sleep(0.1)
else: sys.exit('ratelimit comm not set')
if os.environ.get('GPULL_DRY'):
    class _R: returncode=0; stdout='dry'; stderr=''
    reg=_R(); os.kill(root.pid, 18); open('/tmp/ratelimit-%d/%d.dryrate'%(os.getuid(),rl.pid),'w') if False else None
else:
  reg = subprocess.run(['/usr/bin/python3','-s',GOV+'/register.py','--lane',lane,'--pid',str(root.pid),'--member-pid',str(rl.pid),
    '--rl-pid',str(rl.pid),'--expected-bytes',str(nbytes),'--tier','3','--kind','pull','--nominal-mbps','8','--io-weight','1','--allow-resume'],
    capture_output=True, text=True)
print('register rc', reg.returncode, reg.stdout[-500:], reg.stderr[-500:], flush=True)
if reg.returncode: root.kill(); os.kill(root.pid, 18); sys.exit('registration failed')
rc_root = root.wait(); rc_rl = rl.wait()
size = os.path.getsize(out)
print(json.dumps(dict(rc_root=rc_root, rc_rl=rc_rl, bytes=size, expected=nbytes, end=time.strftime('%FT%TZ', time.gmtime()))), flush=True)
src = os.path.join(STREAMS, lane+'.json')
if os.path.exists(src): os.rename(src, os.path.join(STREAMS, '%s.done.%d' % (lane, int(time.time()))))
sys.exit(0 if (rc_root==0 and rc_rl==0 and size==nbytes) else 1)
