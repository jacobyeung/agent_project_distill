"""Wait for the first payload byte on stdin, then open the Orchard ssh and pump stdin into it (no exec, no retry)."""
import subprocess, sys
inp = sys.stdin.buffer
first = inp.read1(65536) if hasattr(inp, 'read1') else inp.read(65536)
if not first:
    sys.exit(3)
p = subprocess.Popen(['timeout', '7200', 'bash', '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh', sys.argv[1]],
                     stdin=subprocess.PIPE)
p.stdin.write(first)
while True:
    b = inp.read1(1 << 20) if hasattr(inp, 'read1') else inp.read(1 << 20)
    if not b:
        break
    p.stdin.write(b)
p.stdin.close()
sys.exit(p.wait())
