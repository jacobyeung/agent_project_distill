"""corpus: one governed pull from Orchard. Usage: gpull.py LANE REMOTE_PATH BYTES OUTFILE
Root = python child that stops itself, then runs ossh.sh 'cat REMOTE' as ITS child (never execs) into a pipe;
member = ratelimit.py between the pipe and OUTFILE. Registers tier 3, copy, 8 MB/s, io-weight 1, allow-resume; waits; renames the record."""
import os, sys, time, subprocess, json
GOV='/scratch/jjyeung/io_governor'; STREAMS='/data3/jjyeung/orch_n13_20261026/io_governor/streams'
OSSH='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh'
lane, remote, nbytes, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
ROOT = "import os,signal,subprocess,sys; os.kill(os.getpid(), signal.SIGSTOP); sys.exit(subprocess.call(['timeout','3600','bash',sys.argv[1],'cat '+sys.argv[2]]))"
def state(pid):
    s=open('/proc/%d/stat'%pid).read(); return s[s.rindex(')')+2]
r1, w1 = os.pipe()
root = subprocess.Popen(['/usr/bin/python3','-s','-c',ROOT,OSSH,remote], stdout=w1, stdin=subprocess.DEVNULL)
os.close(w1)
for _ in range(100):
    if state(root.pid) in 'Tt': break
    time.sleep(0.1)
else: sys.exit('root did not stop')
fo = open(out, 'xb')
rl = subprocess.Popen(['/usr/bin/python3','-s',GOV+'/ratelimit.py','-q','-L','1000','-B','65536'], stdin=r1, stdout=fo)
os.close(r1); fo.close()
for _ in range(100):
    if open('/proc/%d/comm'%rl.pid).read().strip()=='ratelimit': break
    time.sleep(0.1)
else: sys.exit('ratelimit comm not set')
reg = subprocess.run(['/usr/bin/python3','-s',GOV+'/register.py','--lane',lane,'--pid',str(root.pid),'--member-pid',str(rl.pid),
    '--rl-pid',str(rl.pid),'--expected-bytes',str(nbytes),'--tier','3','--kind','copy','--nominal-mbps','8','--io-weight','1','--allow-resume'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
print('register rc', reg.returncode, reg.stdout[-500:], reg.stderr[-500:], flush=True)
if reg.returncode: root.kill(); os.kill(root.pid, 18); sys.exit('registration failed')
rc_root = root.wait(); rc_rl = rl.wait()
print(json.dumps(dict(rc_root=rc_root, rc_rl=rc_rl, bytes=os.path.getsize(out), expected=nbytes, end=time.strftime('%FT%TZ', time.gmtime()))), flush=True)
rec = os.path.join(STREAMS, lane+'.json')
if os.path.exists(rec): os.rename(rec, os.path.join(STREAMS, '%s.done.%d' % (lane, int(time.time()))))
sys.exit(0 if (rc_root==0 and rc_rl==0 and os.path.getsize(out)==nbytes) else 1)
