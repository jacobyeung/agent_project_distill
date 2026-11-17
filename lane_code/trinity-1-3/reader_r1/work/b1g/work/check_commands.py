from pathlib import Path
import ast,json,re,subprocess
O=Path('out');token=(O/'TOKEN').read_text().strip();text=(O/'OPERATIONS_TOWER.md').read_text()
blocks=re.findall(r'```bash\n(.*?)```',text,re.S);assert len(blocks)==5
for block in blocks:
 result=subprocess.run(['bash','-n'],input=block,text=True,capture_output=True)
 assert result.returncode==0,result.stderr
 for embedded in re.findall(r"<<'PYCODE'\n(.*?)\nPYCODE",block,re.S):ast.parse(embedded)
assert re.findall(r'```bash\n(.*?)```',(O/'REPORT.md').read_text(),re.S)==blocks
cpu=blocks[1];assert '--partition=general' in cpu and '--job-name=a15_cot_ap'+token in cpu
assert '--cpus-per-task=8' in cpu and '--gres' not in cpu and '--gpus' not in cpu
assert json.loads((O/'DELIVERY_SHA256.json').read_text())['1.tgz'] in blocks[0]
assert 'submit --gpus 1 --time 05:00:00' in blocks[2]
assert 'print('+repr(token) in blocks[3]
assert 'work/b1g' in blocks[4] and 'metadata/reads/0' in blocks[4] and 'metadata/reads/1' in blocks[4]
print(json.dumps(dict(passed=True,shell_blocks=len(blocks),commands_executed=False,cpu_job_name='a15_cot_ap'+token)))
