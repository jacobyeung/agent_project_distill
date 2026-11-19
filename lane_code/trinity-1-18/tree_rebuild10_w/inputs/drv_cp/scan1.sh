#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_ee227714
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_ee227714
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
packet() { printf '%s  %s\n' '3233765535fc95eb34b876b2e96895b5f684bd8b4e6c5c93f9e23123d320317b' "$BUN/p.tar" | sha256sum -c --quiet; }
private "$O"
private "$BUN"
packet
python3 -B - <<'PYCODE'
import hashlib,json,os,re,stat,tarfile
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_ee227714');K=B.parent/'x_ee227714';H=B.parent/'x_3fdda0fb'
pattern=re.compile(r'split|revsi|vsibench|vsi|distill|qgen|scannet|arkit|qwen|sft|student|benchmark|eval',re.I)
old_code=set(json.loads((H/'k/7.json').read_text())['files'])
old={line.split('  ',1)[1] for line in (H/'SHA256SUMS.txt').read_text().splitlines()}
new=[];inherited=[]
for root in (B,K):
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink(), 'symlink in private tree'
  if p.is_dir():
   expected=0o500 if root==K and (p==K/'b' or (K/'b') in p.parents) else 0o700
   assert stat.S_IMODE(p.stat().st_mode)==expected, 'directory mode differs'
  assert p.name!='__pycache__', 'bytecode in sealed kit'
  rel=str(p.relative_to(root));line=str(p)
  (inherited if root==K and rel in old else new).append(line)
# Archive member names are visible only inside private trees; never print file contents.
for root,archive in [(B,B/'t.tar'),(K,K/'k'/Path(json.loads((B/'c.json').read_text())['archive']['path']).name)]:
 with tarfile.open(archive) as tf:
  for member in tf:
   (inherited if member.name in old_code else new).append(str(archive)+' :: '+member.name)
new += ['a15_cot_ap6ed2c7aa',str(B),str(K),'/tmp/jjyeung/a_6ed2c7aa',str(B.parent/'r/6ed2c7aa')]
new += (B/'e.txt').read_text().splitlines()
new += [str(B/n) for n in ('a.json','job.id','sbatch.out','submission.started','p0.lock','go.json','training.lock','training.started','training.sbatch.out','training.job.id','training.json')]
new += [str(K/n) for n in ('sess.json','ANON_OK.json','arm','runs')]
new += [str(K/'o'/('<job>.'+n)) for n in ('out','err','steps','w.steps','proof.json','proof.log','vt.json')]
new += ['/tmp/jjyeung/p_6ed2c7aa_<job>/'+n for n in ('entry.sh','tmp','slots','arm','runs')]

argv='TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap6ed2c7aa -A mt01 -p general -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue -o '+str(K)+'/o/%j.out -e '+str(K)+'/o/%j.err '+str(B)+'/p_6ed2c7aa.sh '+str(B)+'/a.json'
new.extend([argv,argv.replace('-p general ', '-p bootstrap ')])
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
for p in [B/'s.sh',B/'p_6ed2c7aa.sh',B/'jb.sh',K/'job.sh',K/'b/c.sh',K/'b/r.sh',K/'b/i.py']:
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
print('PACKET 774503e26f274a10c96ad06210d339c49ebc9a704ac254df81f389b0da4d98a1 ARCHIVE 3233765535fc95eb34b876b2e96895b5f684bd8b4e6c5c93f9e23123d320317b RUN 6ed2c7aa')
print('MANIFEST',hashlib.sha256((K/'SHA256SUMS.txt').read_bytes()).hexdigest())
print('PENDING independent complete content scan and manifest-bound ANON_OK.json; this listing grants no CLEAN claim')

PYCODE
