from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build21';T=L/'work/tree_r1/student_pilot'
aliases={'STUDENT_ORCHARD':'Q_E1','STUDENT_SLURM_SITE':'Q_E2','STUDENT_MODEL_ROOT':'Q_E3','STUDENT_FRAME_ROOT_MAP':'Q_E4','R1_STUDENT_HEX':'Q_E5'}
(T/'job_env.py').write_text('''"""Opaque deployment names preserve the legacy environment contract."""
import os
ALIASES = '''+repr(aliases)+'''
def key(name):
    alias=ALIASES.get(name)
    return alias if alias is not None and alias in os.environ else name
''')
for name in json.loads((B/'ENV_CHANGES.json').read_text()):
 p=L/'work/tree_r1'/name;text=p.read_text();changed=False
 for old,new in aliases.items():
  for quote in ("'",'"'):
   expr=f'{quote}{new}{quote} if {quote}{new}{quote} in os.environ else {quote}{old}{quote}'
   if expr in text:text=text.replace(expr,'env_key('+repr(old)+')');changed=True
 if changed:
  # Insert after a module docstring, before imports; these modules have no future directive.
  import ast
  nodes=ast.parse(text).body;lines=text.splitlines(True)
  first=nodes[0];line=first.end_lineno if isinstance(first,ast.Expr) and isinstance(first.value,ast.Constant) and isinstance(first.value.value,str) else 0
  lines.insert(line,'from .job_env import key as env_key\n');p.write_text(''.join(lines))
print('Centralized the legacy/opaque environment selection')
