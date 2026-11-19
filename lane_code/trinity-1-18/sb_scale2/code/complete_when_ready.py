"""Publish reports after the one active scoring process finishes; never relaunch it."""
import os,subprocess,time,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
python='/scratch/jjyeung/envs/p1cpu/bin/python'
while not (root/'out/ITEMS12.md').exists():
    resource=root/'out/resources.log'
    if resource.exists() and '\tExit status:' in resource.read_text():
        raise RuntimeError('Scoring ended without ITEMS12; inspect resources.log. No retry.')
    time.sleep(60)
for script in ('finish_report.py','validate_outputs.py'):
    subprocess.run([python,'-B',str(root/'code'/script)],cwd=root,check=True)
print('ALL DELIVERABLES COMPLETE',flush=True)
