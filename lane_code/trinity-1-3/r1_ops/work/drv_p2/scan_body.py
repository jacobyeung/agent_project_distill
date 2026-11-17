import hashlib,json,os,re,stat,tarfile
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_@STORE@');K=B.parent/'x_@STORE@';H=B.parent/'x_3fdda0fb'
pattern=re.compile(r'split|revsi|vsibench|vsi|distill|qgen|scannet|arkit|qwen|sft|student|benchmark|eval',re.I)
old_code=set(json.loads((H/'k/7.json').read_text())['files'])
old={line.split('  ',1)[1] for line in (H/'SHA256SUMS.txt').read_text().splitlines()}
new=[];inherited=[]
for root in (B,K):
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink(), 'symlink in private tree'
  if p.is_dir():assert stat.S_IMODE(p.stat().st_mode)==0o700, 'directory must be 0700'
  rel=str(p.relative_to(root));line=str(p)
  (inherited if root==K and rel in old else new).append(line)
# Archive member names are visible only inside private trees; never print file contents.
for root,archive in [(B,B/'t.tar'),(K,K/'k'/Path(json.loads((B/'c.json').read_text())['archive']['path']).name)]:
 with tarfile.open(archive) as tf:
  for member in tf:
   (inherited if member.name in old_code else new).append(str(archive)+' :: '+member.name)
new += ['a15_cot_ap@RUN@',str(B),str(K),'/tmp/jjyeung/a_@RUN@',str(B.parent/'r/@RUN@')]
new += (B/'e.txt').read_text().splitlines()
new += [str(B/n) for n in ('a.json','job.id','sbatch.out','submission.started','p0.lock')]
new += [str(K/n) for n in ('sess.json','ANON_OK.json','arm','runs')]
new += [str(K/'o'/('<job>.'+n)) for n in ('out','err','steps','w.steps','proof.json','proof.log','vt.json')]
new += ['/tmp/jjyeung/p_@RUN@_<job>/'+n for n in ('entry.sh','tmp','slots','arm','runs')]

argv='TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap@RUN@ -A mt01 -p general -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o '+str(K)+'/o/%j.out -e '+str(K)+'/o/%j.err '+str(B)+'/p_@RUN@.sh '+str(B)+'/a.json'
new.extend([argv,argv.replace('-p general ', '-p advanced ')])
# Include locators appearing in the staging arguments and planned export file names.
cur=json.loads((K/'k/0.json').read_text())
oldcur=json.loads((H/'k/0.json').read_text())
known={json.dumps(e,sort_keys=True) for key in ('tars','extra') for e in oldcur.get(key,[])}
for key in ('tars','extra'):
 for entry in cur.get(key,[]):
  target=inherited if json.dumps(entry,sort_keys=True) in known else new
  target.extend(entry['parts'])
  if 'dest' in entry:target.append(entry['dest'])
# All payload scripts are non-secret sealed files. Collect command lines for independent argv review.
commands=[]
for p in [B/'p_@RUN@.sh',B/'jb.sh',K/'job.sh',K/'b/c.sh',K/'b/r.sh',K/'b/i.py']:
 for number,line in enumerate(p.read_text().splitlines(),1):
  if len(line)<2000 and re.search(r'exec |subprocess|Popen|run\(|--|python|bwrap|srun|gcsput|argv',line):commands.append(f'{p}:{number}: {line}')
print('NEW / BUNDLE NAMES AND SUBMISSION ARGV')
print('\n'.join(sorted(set(new))))
print('INHERITED NAMES INSIDE VERIFIED 0700 TREES / INHERITED STAGING LOCATORS')
print('\n'.join(sorted(set(inherited))))
print('SEALED SCRIPT COMMAND LINES FOR ARGV REVIEW (NO SESSION CONTENTS)')
print('\n'.join(commands))
print('GREP NEW NAMES')
hits=[s for s in new if pattern.search(s)];print('\n'.join(hits) if hits else 'NO HITS')
print('GREP INHERITED NAMES / ARGV (account for each under the ruling)')
print('\n'.join(s for s in inherited+commands if pattern.search(s)))
print('PACKET @IDENTITY@ ARCHIVE @OUTER@ RUN @RUN@')
print('MANIFEST',hashlib.sha256((K/'SHA256SUMS.txt').read_bytes()).hexdigest())
print('PENDING independent complete content scan and manifest-bound ANON_OK.json; this listing grants no CLEAN claim')
