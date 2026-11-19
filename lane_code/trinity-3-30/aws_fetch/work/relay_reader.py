"""Gated reader: stop self before payload; on CONT stream one Orchard file to stdout via a child ssh (no exec)."""
import os, signal, subprocess, sys
os.kill(os.getpid(), signal.SIGSTOP)
src = '/project/community/jjyeung/distill/okit/in/cr/rt_b8b60bcef027.tar'
p = subprocess.Popen(['timeout', '10800', 'bash', '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh', 'cat ' + src], stdout=subprocess.PIPE, bufsize=0)
out = sys.stdout.buffer
while True:
    b = p.stdout.read(65536)
    if not b:
        break
    out.write(b); out.flush()
sys.exit(p.wait())
