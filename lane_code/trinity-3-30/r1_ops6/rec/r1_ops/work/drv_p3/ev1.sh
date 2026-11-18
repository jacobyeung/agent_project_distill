#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
O=/project/community/jjyeung/okh7
BUN=$O/i_082d2d90
H=$O/x_3fdda0fb
OLD=$O/i_1be16f28
KH=$O/x_082d2d90
private() { [[ -d "$1" && ! -L "$1" && $(stat -c %a "$1") == 700 ]] || { echo "REFUSED: private directory required: $1" >&2; exit 3; }; }
fresh() { [[ ! -e "$1" && ! -L "$1" ]] || { echo "REFUSED: already exists: $1" >&2; exit 3; }; }
private "$O"
private "$BUN"
test -f "$BUN/r1.json" || { echo "PENDING: run rv1.sh after the five-review final-packet chain"; exit 4; }
fresh "$BUN/e"
fresh "$BUN/e0"
mkdir -m 700 "$BUN/e0"
cat > "$BUN/e0/r.py" <<'PYCODE'
"""Validate the independent review chain without turning conditions into GO."""
import hashlib
import re

REVIEWERS = ('review_r1p', 'review_r1p2', 'review_r1p3', 'review_r1p4', 'review_r1p5')
REVIEW_FILES = ('r1.txt', 'r2.txt', 'r3.txt', 'r4.txt', 'r5.txt')

def verdict(text, reviewer):
    header = next((line.strip() for line in text.splitlines() if line.strip()), '')
    header = header.lstrip('# ').replace('**', '')
    match = re.match(r'(?:REVIEW_VERDICT_R1P[2345]?\s*:\s*)?(GO AFTER FIXES|GO|NO[- ]GO)\b', header, re.I)
    if not match or match.group(1).upper() not in ('GO', 'GO AFTER FIXES'):
        raise ValueError(reviewer+' must state GO or GO AFTER FIXES on its first nonblank line')
    if reviewer == 'review_r1p5':
        tail = header[match.end():].strip()
        if tail and not tail.startswith(('(', '—', '–', '- ', ':')):
            raise ValueError('final verdict has an ambiguous suffix')
        if re.search(r'\b(?:AFTER|PENDING|CONDITIONAL|IF|UNLESS|SUBJECT TO|PROVIDED|CONTINGENT|NO[- ]GO)\b|[?]', tail, re.I):
            raise ValueError('final verdict has an unresolved condition')
    return match.group(1).upper()

def low_fixes(text):
    """Require explicit LOW labels on every remaining fix."""
    body = '\n'.join(text.strip().splitlines()[1:]).replace('**', '')
    # Findings may be numbered, bullets, or Markdown headings. Collect multiline
    # findings through the next item/heading; unlabelled fixes fail closed.
    chunks = re.split(r'(?m)^\s*(?=(?:\d+[.)]\s|[-*]\s|#{1,6}\s))', body)
    notes = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        label = re.sub(r'^(?:\d+[.)]\s*|[-*]\s*|#{1,6}\s*)', '', chunk)
        # A PASS finding can describe a resolved issue; it is not a remaining fix.
        if re.match(r'PASS\b', label, re.I):
            continue
        if re.search(r'\b(?:HIGH|MEDIUM|CRITICAL|BLOCKER)\b', chunk, re.I):
            raise ValueError('final conditional review contains a severity above LOW')
        has_low = bool(re.search(r'\bLOW\b', chunk, re.I))
        actionable = bool(re.search(r'\b(?:fix|fixes|required|must|should|todo)\b', chunk, re.I))
        item = bool(re.match(r'(?:\d+[.)]\s|[-*]\s)', chunk))
        # Section titles alone do not constitute a finding.
        title = chunk.lstrip('# ').strip().lower().rstrip(':')
        if title in ('fixes', 'remaining fixes', 'low non-blocking fixes', 'findings'):
            continue
        if has_low or actionable or item:
            nonblocking = re.search(r'\bnon[- ]blocking\b|\bdoes not block\b', chunk, re.I)
            blocking = re.search(r'\b(?:blocks?|blocking|required before|must (?:fix|resolve))\b',
                                 re.sub(r'non[- ]blocking|does not block', '', chunk, flags=re.I), re.I)
            if not has_low or blocking:
                raise ValueError('every final conditional fix must be explicitly LOW without blocking conditions')
            notes.append(chunk)
    if not notes:
        raise ValueError('final GO AFTER FIXES must list explicit LOW fixes')
    return notes

def build_chain(texts, identity, tree, outer):
    if set(texts) != set(REVIEW_FILES):
        raise ValueError('all five independent verdicts are required')
    reviews = {}
    for name, short in zip(REVIEWERS, REVIEW_FILES):
        text = texts[short]
        value = verdict(text, name)
        reviews[name] = dict(verdict=value, sha256=hashlib.sha256(text.encode()).hexdigest(),
                             file=short, role='final' if name == REVIEWERS[-1] else 'antecedent')
    final = texts['r5.txt']
    if not any(re.search(r'(?<![0-9a-f])'+pin+r'(?![0-9a-f])', final) for pin in (identity, outer)):
        raise ValueError('review_r1p5 must name the full final archive SHA or config identity')
    notes = low_fixes(final) if reviews['review_r1p5']['verdict'] == 'GO AFTER FIXES' else []
    return dict(config_sha256=identity, source_revision='sha256:'+tree,
                operator_archive_sha256=outer, reviews=reviews,
                reviewers=list(REVIEWERS), final_reviewer='review_r1p5',
                final_verdict=reviews['review_r1p5']['verdict'],
                fix_rounds=[4, 5, 6, 7, 8, 9], nonblocking_fixes=notes,
                accepted_for_cpu_proof=True, production_go_granted=False)

import copy,hashlib,importlib.util,json,os,stat,sys,tarfile
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_082d2d90');H=B.parent/'x_3fdda0fb';OLD=B.parent/'i_1be16f28'
MAN='661ccd85b7a8f1afd25297869dc3a28539e64a3a0ab9a74ee928c0c5ab8a66c3'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def load(p):return json.loads(p.read_text())
def write(p,d):
 with p.open('x') as f:json.dump(d,f,sort_keys=True,separators=(',',':'));f.write('\n')
def make_records(b,h,old,ev,checks,review_input):
 ids=load(b/'ids.json');binding=load(b/'BINDING.json');code=load(b/'c.json')
 ident=ids['identity'];revision='sha256:'+binding['tree_sha256'];arc=b/'t.tar'
 st=copy.deepcopy(load(old/'staging.json'))
 st.update(status='PASS',source_revision=revision,config_sha256=ident,missing=[],project_community_write_bytes=0,
  evidence=dict(checks_sha256=sha(ev/'c.json'),inherited_staging_sha256=sha(h/'k/staging.json'),inherited_scope='availability plus supplied sealed staging attestation; native c.sh rechecks bytes'),
  scope='read-only changed-payload verification; excludes upload, extraction and derivation writes')
 ar=copy.deepcopy(load(old/'archive.json'))
 ar.update(schema='s1-source-archive-v1',status='ARCHIVED',durable=True,location=str(arc),sha256=sha(arc),tree_sha256=binding['tree_sha256'],bytes=arc.stat().st_size,verification_scope='read-back SHA256 on login-node project storage')
 rv=copy.deepcopy(load(old/'review.json'))
 rv.update(verdict='PASS',reviewer=', '.join(review_input['reviewers']),reviewers=review_input['reviewers'],config_sha256=ident,source_revision=revision,admission_contract_sha256=ids['contract'],admission_scope='pinned-template-and-native-data-derivation',attestation='The five-review chain ends with review_r1p5 accepting the final packet; production CPU preparation proof remains required.',evidence=review_input)
 au=copy.deepcopy(load(old/'4.json'))
 # Inherit the envelope, never the H1 production permissions or source-specific attestations.
 for k in ('written_authorization','written_authorizations','admission_evidence','omission_authority'):au.pop(k,None)
 au.update(config_sha256=ident,source_revision=revision,admission_contract_sha256=ids['contract'],partition='general',allowed_partitions=['general','advanced'],account='mt01',modes=['p'],new_gpus={'p':0},gpu_cap=4,max_parallel_jobs=1,production_go_granted=False,production_go_required_separately=True,full_population_admission=False,native_memory_sufficiency_proven=False,review=None,scope='One mode-p CPU proof; production GO remains pending.',wall_seconds=14400,allocation_memory_gib=800,conditions=['One CPU proof; refuse any a15_cot_ap or jjy_ job on the requested partition.','The final manifest requires independent content certification.','Production submission requires a separate identity-bound GO.'])
 for n,d in [('review.json',rv),('staging.json',st),('archive.json',ar),('4.json',au)]:write(ev/n,d)

def evidence(b,h,old,ev,verify):
 ids=load(b/'ids.json');binding=load(b/'BINDING.json');code=load(b/'c.json');cfg=load(b/'config.json')
 ident=ids['identity'];revision='sha256:'+binding['tree_sha256']
 assert code['commit']==revision and ident==binding['config_identity']
 # Require the operator's uploaded exact-packet independent verdict record.
 review_input=load(b/'r1.json')
 assert review_input['config_sha256']==ident and review_input['source_revision']==revision
 assert review_input['operator_archive_sha256']=='3401c318e552cf0ba23f691d197b8f022550639693632abeeaa3bf3b08658384'
 texts={short:(b/short).read_bytes().decode() for short in REVIEW_FILES}
 assert review_input==build_chain(texts,ident,binding['tree_sha256'],'3401c318e552cf0ba23f691d197b8f022550639693632abeeaa3bf3b08658384'), 'Review chain differs'
 assert sha(h/'SHA256SUMS.txt')==MAN
 manifest=dict(reversed(x.split('  ',1)) for x in (h/'SHA256SUMS.txt').read_text().splitlines())
 for n in ('k/0.json','k/staging.json','k/review.json','k/archive.json','k/4.json'):
  assert sha(h/n)==manifest[n], 'H1 source evidence differs'
 inherited=load(h/'k/staging.json')
 assert inherited['status']=='PASS' and inherited['missing']==[] and inherited['project_community_write_bytes']==0
 # Use the H1 bundle schemas; require the sealed kit's corresponding records to agree.
 for n in ('review.json','staging.json','archive.json','4.json'):
  assert load(old/n)==load(h/'k'/n), 'H1 bundle evidence differs from sealed kit: '+n
 ev.mkdir(mode=0o700)
 arc=b/'t.tar';assert sha(arc)==code['archive']['sha256']
 files={}
 with tarfile.open(arc) as tf:
  for m in tf:
   assert m.isfile() and m.name in code['files'] and m.name not in files
   files[m.name]=hashlib.sha256(tf.extractfile(m).read()).hexdigest()
 assert files==code['files']
 assert hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()==binding['tree_sha256']
 # Mirror only d.py's staging-record additions. No archive extraction or data copy is needed.
 cur=load(h/'k/0.json');extra={}
 extra[str(Path(cfg['streams']['vqa']['path']).parent/'d.db')]={'parts':[binding['orchard_store']],'sha256':binding['database_sha256']}
 store=Path(binding['orchard_store']);assert not store.is_symlink() and stat.S_IMODE(store.stat().st_mode)==0o400
 assert binding.get('unit_binding'), 'Proof 2 requires the unit source'
 for name,value in binding['unit_binding']['artifacts'].items():
  assert sha(b/name)==value['sha256'], 'Unit artifact differs: '+name
  extra[value['path']]={'parts':[str(b/name)],'sha256':value['sha256']}
 prefix='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/'+binding['store_key']
 for name in binding['record_files']:
  assert sha(b/name)==sha(b/'records'/name)
  extra[prefix+'/'+name]={'parts':[str(b/name)],'sha256':sha(b/'records'/name)}
 assert sha(b/'s.json')==sha(b/'proof/selection/r.json')==binding['selection_sha256']
 extra[prefix+'/s.json']={'parts':[str(b/'s.json')],'sha256':sha(b/'s.json')}
 for dest,item in extra.items():
  assert all(x.get('dest')!=dest for x in cur.get('extra',[]))
  cur.setdefault('extra',[]).append(dict(dest=dest,**item))
 stage=ev/'s';(stage/'k').mkdir(parents=True,mode=0o700)
 write(stage/'k/0.json',cur)
 checks=verify(stage,h/'k/0.json');write(ev/'c.json',checks)
 assert checks['missing']==[], 'missing staging inputs'
 make_records(b,h,old,ev,checks,review_input)
 print('PASS four evidence records; staging missing=0; durable archive read-back verified; production_go_granted=false')
STAGING_VERIFY='"""Read-only check of changed staging entries and availability of inherited parts."""\nimport hashlib,json,sys,tarfile\nfrom pathlib import Path\n\ndef sha(p):\n h=hashlib.sha256()\n with Path(p).open(\'rb\') as f:\n  for b in iter(lambda:f.read(1<<20),b\'\'):h.update(b)\n return h.hexdigest()\n\ndef enc(v):return json.dumps(v,sort_keys=True,separators=(\',\',\':\'))\nclass Reader:\n def __init__(self,parts):self.parts=iter(parts);self.f=None;self.h=hashlib.sha256()\n def read(self,n=-1):\n  if n<0:n=1<<20\n  buf=b\'\'\n  while len(buf)<n:\n   if self.f is None:\n    p=next(self.parts,None)\n    if p is None:break\n    self.f=open(p,\'rb\')\n   b=self.f.read(n-len(buf))\n   if not b:self.f.close();self.f=None;continue\n   buf+=b\n  self.h.update(buf);return buf\n\ndef main(kit,base):\n kit=Path(kit);cur=json.loads((kit/\'k/0.json\').read_text());sealed=json.loads(Path(base).read_text());known={enc(x) for k in (\'tars\',\'extra\') for x in sealed.get(k,[])}\n missing=[];verified=[];inherited=[]\n for k in (\'tars\',\'extra\'):\n  for e in cur.get(k,[]):\n   for p in e[\'parts\']:\n    if not Path(p).is_file():missing.append(p)\n   if any(not Path(p).is_file() for p in e[\'parts\']):continue\n   if enc(e) in known:inherited.extend(e[\'parts\']);continue\n   if k==\'extra\':\n    r=Reader(e[\'parts\'])\n    while r.read(1<<20):pass\n    if r.h.hexdigest()!=e[\'sha256\']:raise ValueError(\'extra digest differs\')\n   else:\n    r=Reader(e[\'parts\']);seen={}\n    with tarfile.open(fileobj=r,mode=\'r|\') as tf:\n     for m in tf:\n      if m.name.startswith(\'/\') or \'..\' in Path(m.name).parts:raise ValueError(\'unsafe tar path\')\n      if m.isdir():continue\n      if not m.isfile() or m.name not in e[\'files\'] or m.name in seen:raise ValueError(\'unexpected tar member\')\n      h=hashlib.sha256()\n      f=tf.extractfile(m)\n      for b in iter(lambda:f.read(1<<20),b\'\'):h.update(b)\n      seen[m.name]=h.hexdigest()\n    while r.read(1<<20):pass\n    if seen!=e[\'files\'] or r.h.hexdigest()!=e[\'sha256\']:raise ValueError(\'tar contents or digest differ\')\n   verified.append(e[\'parts\'])\n return dict(missing=missing,verified=verified,inherited_parts_present=sorted(set(inherited)))\n\nif __name__=="__main__":\n result=main(*sys.argv[1:]);print(json.dumps(result,sort_keys=True));sys.exit(1 if result["missing"] else 0)\n'
if __name__=='__main__':
 # STAGING_VERIFY is the byte-for-byte H1 payload/v.py module embedded by the builder.
 scope={'__name__':'inherited_staging'};exec(compile(STAGING_VERIFY,'v.py','exec'),scope)
 evidence(B,H,OLD,B/'e',scope['main'])

PYCODE
cat > "$BUN/e0/r.sh" <<'SHCODE'
#!/bin/bash
set +x
set -uo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/project/community/jjyeung/okh7/i_082d2d90
python3 -B "$BUN/e0/r.py"
rc=$?
printf '%s\n' "$rc" > "$BUN/e0/rc"
exit "$rc"
SHCODE
nohup nice -n 19 ionice -c 3 bash "$BUN/e0/r.sh" > "$BUN/e0/o.log" 2>&1 < /dev/null &
printf '%s\n' "$!" > "$BUN/e0/pid"
echo "STARTED e0; pid $!; poll once per minute"
