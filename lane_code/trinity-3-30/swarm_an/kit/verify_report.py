"""Rerun a report's CLASSIFIER appendix (code is piped to python on stdin; nothing is written).
usage: verify_report.py <final_message.md> [max_lines]"""
import re, subprocess, sys
p = sys.argv[1]; mx = int(sys.argv[2]) if len(sys.argv) > 2 else 60
t = open(p).read()
i = t.rfind('CLASSIFIER'); blocks = re.findall(r'```(?:python)?\n(.*?)```', t[i:] if i >= 0 else t, re.S)
if not blocks: sys.exit('no code block after CLASSIFIER')
code = max(blocks, key=len)
py = '/scratch/jjyeung/envs/planner_local_v1/bin/python' if 'K.routed' in code else '/usr/bin/python3'
r = subprocess.run([py, '-'], input=code, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=600)
out = (r.stdout + ('\nSTDERR:\n' + r.stderr[-1500:] if r.returncode else '')).splitlines()
print('\n'.join(out[:mx])); print('[exit %d, %d lines, code %d lines, %s]' % (r.returncode, len(out), len(code.splitlines()), py))
