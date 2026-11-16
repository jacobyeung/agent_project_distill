"""Audit new shell surfaces and Python string literals; retain explicit sealed-name exceptions."""
import ast,difflib,json,re,shlex
from pathlib import Path
H=Path(__file__).resolve().parents[1]
D=Path('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0')
forbidden=re.compile(r'(?i)(?<![a-z0-9])(?:distill|split|vsi(?:bench)?|revsi|scannet(?:pp)?|arkit(?:scenes)?|sft|h1|r0|qwen(?:3(?:\.5)?)?|cot|vstibench|dsibench)(?![a-z0-9])')
# These exact logical prefixes are bound by the sealed input identities.
inherited=['/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung','/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung']
checked=[]
def visible_line(name,line):
 # The account mandates this exact prefix only in the submitter's job-name argument.
 if name=='payload/s.sh':
  line=re.sub(r'^(TZ=UTC env -u TK_JOB_START sbatch -J )a15_cot_ap(?=[0-9a-f]+(?:\s|$))',r'\1a_',line)
 return line
def check(name,text):
 for line in text.splitlines():
  if line.lstrip().startswith('#'):continue
  # Attribute names such as str.split() are code, not visible naming values.
  line=re.sub(r'\.split\(','.operation(',line)
  for prefix in inherited:line=line.replace(prefix,'/sealed/prefix')
  line=visible_line(name,line)
  assert not forbidden.search(line),(name,line)
 checked.append(name)
for name in ['orch_h1.sh','fin_h1.sh','payload/o.sh','payload/g.sh','payload/z.sh','payload/s.sh']:
 s=(H/name).read_text()
 if name=='orch_h1.sh':
  begin=s.index("<<'B64'\n")+len("<<'B64'\n");end=s.index('\nB64\n',begin);s=s[:begin]+s[end:]
 check(name,s)
for name in ['b/c.sh','b/p0.sh','b/r.sh','b/h.py','b/i.py','job.sh']:
 old=(D/'kitfull'/name).read_text().splitlines();new=(H/'build/fx'/name).read_text().splitlines()
 added='\n'.join(x[1:] for x in difflib.unified_diff(old,new) if x.startswith('+') and not x.startswith('+++'))
 check('build/fx/'+name+' additions',added)
old=(D/'jobB/jb.sh').read_text().splitlines();new=(H/'runtime/jb.sh').read_text().splitlines()
check('runtime/jb.sh additions','\n'.join(x[1:] for x in difflib.unified_diff(old,new) if x.startswith('+') and not x.startswith('+++')))
for name in ['payload/r.py']:
 tree=ast.parse((H/name).read_text());strings=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
 check(name+' string values','\n'.join(strings))
# Verify the original exposure is gone and both extraction argv use only bundle paths.
s=(H/'payload/g.sh').read_text()
assert 'distill' not in s and 'python3 -B r.py copy' in s
assert 'tar -xf "$BUN/a_b8b60bce.tar"' in s
assert s.index('r.py copy')<s.index('tar -xf')
assert 'sha256' in s[:s.index('tar -xf')]
# Public entrypoint names are opaque; these local delivery filenames are never passed to Orchard.
ids=json.loads((H/'ids.json').read_text());tokens=json.loads((H/'TOKENS_H1.json').read_text())
assert ids['tokens']==tokens and tokens['job']=='5ee9da63'
assert ids['job_name']=='a15_cot_ap'+tokens['job']=='a15_cot_ap5ee9da63'
assert json.loads((H/'payload/ids.json').read_text())==ids
assert json.loads((H/'payload/go.template.json').read_text())['job_name']==ids['job_name']
submit=(H/'payload/s.sh').read_text()
assert re.findall(r'\bsbatch -J (\S+)',submit)==[ids['job_name']]
command='TZ=UTC env -u TK_JOB_START sbatch -J '
assert not forbidden.search(visible_line('payload/s.sh',command+ids['job_name']))
# The exception must not hide other methods, malformed suffixes, paths, logs or env values.
for name,line in [
 ('payload/g.sh',command+ids['job_name']),
 ('payload/s.sh','echo '+ids['job_name']),
 ('payload/s.sh','JOB='+ids['job_name']),
 ('payload/s.sh','/tmp/'+ids['job_name']),
 ('payload/s.sh',command+'a15_cot_ap'),
 ('payload/s.sh',command+'a15_cot_apxyz'),
 ('payload/s.sh',command+ids['job_name']+'_cot'),
 ('payload/s.sh',command+ids['job_name']+' -o /tmp/cot'),
 ('payload/s.sh',command+'a15_cot_ap_cot5ee9da63'),
]:
 assert forbidden.search(visible_line(name,line)),(name,line)
for word in ('distill','split','vsi','vsibench','revsi','scannet','scannetpp','arkit','arkitscenes','sft','h1','r0','qwen','qwen3.5','cot','vstibench','dsibench'):
 assert forbidden.search(visible_line('payload/s.sh',command+ids['job_name']+' -o /tmp/'+word)),word
# Pinned inherited compute-node sources must remain byte-identical.
old=(D/'kitfull/b/c.sh').read_text();new=(H/'build/fx/b/c.sh').read_text()
for needle in ['R=/project/community/jjyeung/distill/okit','models--Qwen--Qwen3.5-9B']:
 assert [x for x in old.splitlines() if needle in x]==[x for x in new.splitlines() if needle in x]
result=dict(status='PASS',surfaces=checked,inherited_exact_prefixes=inherited,job_name=ids['job_name'],job_prefix_exception='a15_cot_ap only in payload/s.sh sbatch -J with a hex suffix',exception_negative_checks='PASS',scope='New shell argv/path/env/log literals, added runtime lines, and r.py string values. Private trainer contents require separate content review.')
(H/'evidence/visible_names.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
