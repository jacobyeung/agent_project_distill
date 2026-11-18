"""Validate the independent review chain without turning conditions into GO."""
import hashlib
import re

REVIEWERS = ('review_r1p', 'review_r1p2', 'review_r1p3', 'review_r1p4', 'review_r1p5', 'review_r1p6', 'review_r1p7', 'review_r1p8', 'review_r1c1')
REVIEW_FILES = ('r1.txt', 'r2.txt', 'r3.txt', 'r4.txt', 'r5.txt', 'r6.txt', 'r7.txt', 'r8.txt', 'rc1.txt')

def verdict(text, reviewer):
    header = next((line.strip() for line in text.splitlines() if line.strip()), '')
    header = header.lstrip('# ').replace('**', '')
    match = re.match(r'(?:REVIEW_VERDICT_R1P[2345678]?\s*:\s*)?(GO AFTER FIXES|GO|NO[- ]GO)\b', header, re.I)
    if not match or match.group(1).upper() not in ('GO', 'GO AFTER FIXES'):
        raise ValueError(reviewer+' must state GO or GO AFTER FIXES on its first nonblank line')
    if reviewer == 'review_r1p7':
        tail = header[match.end():].strip()
        if tail and not tail.startswith(('(', '—', '–', '- ', ':')):
            raise ValueError(f'final verdict has an ambiguous suffix')
        if re.search(r'\b(?:AFTER|PENDING|CONDITIONAL|IF|UNLESS|SUBJECT TO|PROVIDED|CONTINGENT|NO[- ]GO)\b|[?]', tail, re.I):
            raise ValueError(f'final verdict has an unresolved condition')
    return match.group(1).upper()

def low_fixes(text):
    """Require explicit LOW labels on every remaining fix."""
    body = '\n'.join(text.strip().splitlines()[1:]).replace('**', '')
    # Findings may be numbered, bullets, or Markdown headings. Collect multiline
    # findings through the next item/heading; unlabelled fixes fail closed.
    chunks = []
    current = []
    for line in body.splitlines():
        if re.match(r'^\s*(?:\d+[.)]\s|[-*]\s|#{1,6}\s)', line) and current:
            chunks.append('\n'.join(current))
            current = []
        current.append(line)
    if current:
        chunks.append('\n'.join(current))
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
            raise ValueError(f'final conditional review contains a severity above LOW')
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
                raise ValueError(f'every final conditional fix must be explicitly LOW without blocking conditions')
            notes.append(chunk)
    if not notes:
        raise ValueError(f'final GO AFTER FIXES must list explicit LOW fixes')
    return notes

def packet_section(text, packet):
    """Accept one explicit A section or A verdict row; never borrow B's text."""
    if packet not in ('A', 'C'):raise ValueError(f'Unsupported packet')
    lines = text.replace('**', '').replace('`', '').splitlines()
    starts = []
    for i, line in enumerate(lines):
        label = re.sub(r'^\s*(?:#{1,6}\s*|[-*]\s*)', '', line).strip()
        if re.match(r'Packet\s+'+packet+r'\b', label, re.I) or re.match(r'\|\s*(?:Packet\s+)?'+packet+r'\s*\|', label, re.I):
            starts.append(i)
    if len(starts) != 1:
        raise ValueError(f'final review requires exactly one explicit Packet C section or verdict row')
    start = starts[0]
    first = lines[start]
    if first.lstrip().startswith('|'):
        section = first
    else:
        end = len(lines)
        level = len(first.lstrip()) - len(first.lstrip().lstrip('#'))
        for j in range(start+1, len(lines)):
            line = lines[j]
            label = re.sub(r'^\s*(?:#{1,6}\s*|[-*]\s*)', '', line).strip()
            heading = re.match(r'^\s*(#{1,6})\s+', line)
            if re.match(r'Packet\s+[ABC]\b', label, re.I) or re.match(r'\|\s*(?:Packet\s+)?[ABC]\s*\|', label, re.I) or (level and heading and len(heading[1]) <= level):
                end = j
                break
        section = '\n'.join(lines[start:end])
    declarations = []
    for line in section.splitlines():
        label = line.lstrip('# -*').strip()
        if re.match(r'(?:Packet\s+'+packet+r'\b|(?:Final\s+)?Verdict\s*:|GO\b|NO[- ]GO\b)', label, re.I) or label.startswith('|'):
            found = list(re.finditer(r'(?<![A-Za-z-])(GO AFTER FIXES|NO[- ]GO|GO)(?![A-Za-z-])', label, re.I))
            declarations.extend((match.group(1).upper(), label[match.end():]) for match in found)
    if len(declarations) != 1:
        raise ValueError(f'Packet C must have exactly one unambiguous verdict')
    value, tail = declarations[0]
    tail = tail.strip()
    if tail and not tail.startswith(('(', '—', '–', '- ', ':', '|', '.')):
        raise ValueError(f'Packet C verdict has an ambiguous suffix')
    if re.search(r'\b(?:HIGH|MEDIUM|CRITICAL|BLOCKER)\b', tail, re.I):
        raise ValueError(f'Packet C verdict names a severity above LOW')
    if re.search(r'\b(?:fix|fixes|required|must|should|todo)\b', tail, re.I) and not re.search(r'\bLOW\b', tail, re.I):
        raise ValueError(f'Packet C verdict contains an unlabelled fix')
    conditions = re.sub(r'non[- ]blocking|does not block', '', tail, flags=re.I)
    if re.search(r'\b(?:blocks?|blocked|blocking|required before|must (?:fix|resolve))\b', conditions, re.I):
        raise ValueError(f'Packet C verdict contains a blocking condition')
    if value not in ('GO', 'GO AFTER FIXES'):
        raise ValueError(f'Packet C is not approved')
    if re.search(r'\b(?:AFTER|PENDING|CONDITIONAL|IF|UNLESS|SUBJECT TO|PROVIDED|CONTINGENT)\b|[?]', tail, re.I):
        raise ValueError(f'Packet C verdict has an unresolved condition')
    return value, section


def packet_a_section(text):
    return packet_section(text, 'A')

def build_chain(texts, identity, tree, outer):
    if set(texts) != set(REVIEW_FILES):
        raise ValueError(f'all nine independent verdicts are required')
    reviews = {}
    for name, short in zip(REVIEWERS, REVIEW_FILES):
        text = texts[short]
        value = packet_section(text, 'C')[0] if name == 'review_r1c1' else (packet_a_section(text)[0] if name in ('review_r1p6','review_r1p7','review_r1p8') and re.search(r'Packet\s+A\b', text, re.I) else verdict(text, name))
        reviews[name] = dict(verdict=value, sha256=hashlib.sha256(text.encode()).hexdigest(),
                             file=short, role='final' if name == REVIEWERS[-1] else 'antecedent')
    value, final = packet_section(texts['rc1.txt'], 'C')
    declaration = re.sub(r'^\s*(?:#{1,6}\s*|[-*]\s*)', '', final.splitlines()[0].replace('**', '').replace('`', '')).strip()
    if not re.match(r'Packet\s+C\s*:', declaration, re.I) or not re.search(r'\b(GO AFTER FIXES|GO)\b', declaration, re.I):
        raise ValueError(f'final review requires an explicit Packet C: GO or GO AFTER FIXES line')
    if not any(re.search(r'(?<![0-9a-f])'+pin+r'(?![0-9a-f])', final) for pin in (identity, outer)):
        raise ValueError(f'Packet C section must name its full archive SHA or config identity')
    fix_body = '\n'.join(line for line in final.splitlines() if not re.match(r'^\s*(?:#{1,6}\s*|[-*]\s*)?(?:Packet C\b|(?:Final )?Verdict\s*:|GO(?: AFTER FIXES)?\b)', line, re.I))
    notes = low_fixes('# '+value+'\n'+fix_body) if value == 'GO AFTER FIXES' else []
    return dict(config_sha256=identity, source_revision='sha256:'+tree,
                operator_archive_sha256=outer, packet='C', reviews=reviews,
                reviewers=list(REVIEWERS), final_reviewer='review_r1c1',
                final_verdict=value, fix_rounds=[4, 5, 6, 7, 8, 9, 10, 11, 12], nonblocking_fixes=notes,
                accepted_for_cpu_proof=True, production_go_granted=False)

import copy,hashlib,importlib.util,json,os,stat,sys,tarfile
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_7f1589c1');H=B.parent/'x_3fdda0fb';OLD=B.parent/'i_1be16f28'
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
 rv.update(verdict='PASS',reviewer=', '.join(review_input['reviewers']),reviewers=review_input['reviewers'],config_sha256=ident,source_revision=revision,admission_contract_sha256=ids['contract'],admission_scope='pinned-template-and-native-data-derivation',attestation='The nine-review chain ends with review_r1c1 accepting packet C; production CPU preparation proof remains required.',evidence=review_input)
 au=copy.deepcopy(load(old/'4.json'))
 # Inherit the envelope, never the H1 production permissions or source-specific attestations.
 for k in ('written_authorization','written_authorizations','admission_evidence','omission_authority'):au.pop(k,None)
 au.update(config_sha256=ident,source_revision=revision,admission_contract_sha256=ids['contract'],partition='bootstrap',allowed_partitions=['bootstrap','general'],account='mt01',modes=['p'],new_gpus={'p':0},gpu_cap=4,max_parallel_jobs=1,production_go_granted=False,production_go_required_separately=True,full_population_admission=False,native_memory_sufficiency_proven=False,review=None,scope='One mode-p CPU proof; production GO remains pending.',wall_seconds=14400,allocation_memory_gib=800,conditions=['One CPU proof; refuse any other same-name C job; unrelated held jobs do not block.','The final manifest requires independent content certification.','Production submission requires a separate identity-bound GO.'])
 for n,d in [('review.json',rv),('staging.json',st),('archive.json',ar),('4.json',au)]:write(ev/n,d)

def evidence(b,h,old,ev,verify):
 ids=load(b/'ids.json');binding=load(b/'BINDING.json');code=load(b/'c.json');cfg=load(b/'config.json')
 ident=ids['identity'];revision='sha256:'+binding['tree_sha256']
 assert code['commit']==revision and ident==binding['config_identity']
 # Require the operator's uploaded exact-packet independent verdict record.
 review_input=load(b/'r1.json')
 assert review_input['config_sha256']==ident and review_input['source_revision']==revision
 assert review_input['operator_archive_sha256']=='c60b901594843989b909cb785a5fdc9ad544ea0fdec8d78c63bf173e4f6e136c'
 texts={short:(b/short).read_bytes().decode() for short in REVIEW_FILES}
 assert review_input==build_chain(texts,ident,binding['tree_sha256'],'c60b901594843989b909cb785a5fdc9ad544ea0fdec8d78c63bf173e4f6e136c'), 'Review chain differs'
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
 assert binding.get('unit_binding'), 'Packet C requires the unit source'
 for name,value in binding['unit_binding']['artifacts'].items():
  assert sha(b/name)==value['sha256'], 'Unit artifact differs: '+name
  extra[value['path']]={'parts':[str(b/name)],'sha256':value['sha256']}
 prefix='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/'+binding.get('record_key',binding['store_key'])
 assert cfg['remove_files'][-1]==dict(path='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/n.json',sha256='02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411')
 assert 'n.json' in binding['record_files']
 assert sha(b/'n.json')==sha(b/'records/n.json')=='02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411', 'REMOVE list differs'
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
 assert [str(b/'n.json')] in checks['verified'], 'REMOVE list was not hashed'
 print('PASS REMOVE n.json SHA 02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411; staged for packet C')
 make_records(b,h,old,ev,checks,review_input)
 print('PASS four evidence records; staging missing=0; durable archive read-back verified; production_go_granted=false')
STAGING_VERIFY='"""Read-only check of changed staging entries and availability of inherited parts."""\nimport hashlib,json,sys,tarfile\nfrom pathlib import Path\n\ndef sha(p):\n h=hashlib.sha256()\n with Path(p).open(\'rb\') as f:\n  for b in iter(lambda:f.read(1<<20),b\'\'):h.update(b)\n return h.hexdigest()\n\ndef enc(v):return json.dumps(v,sort_keys=True,separators=(\',\',\':\'))\nclass Reader:\n def __init__(self,parts):self.parts=iter(parts);self.f=None;self.h=hashlib.sha256()\n def read(self,n=-1):\n  if n<0:n=1<<20\n  buf=b\'\'\n  while len(buf)<n:\n   if self.f is None:\n    p=next(self.parts,None)\n    if p is None:break\n    self.f=open(p,\'rb\')\n   b=self.f.read(n-len(buf))\n   if not b:self.f.close();self.f=None;continue\n   buf+=b\n  self.h.update(buf);return buf\n\ndef main(kit,base):\n kit=Path(kit);cur=json.loads((kit/\'k/0.json\').read_text());sealed=json.loads(Path(base).read_text());known={enc(x) for k in (\'tars\',\'extra\') for x in sealed.get(k,[])}\n missing=[];verified=[];inherited=[]\n for k in (\'tars\',\'extra\'):\n  for e in cur.get(k,[]):\n   for p in e[\'parts\']:\n    if not Path(p).is_file():missing.append(p)\n   if any(not Path(p).is_file() for p in e[\'parts\']):continue\n   if enc(e) in known:inherited.extend(e[\'parts\']);continue\n   if k==\'extra\':\n    r=Reader(e[\'parts\'])\n    while r.read(1<<20):pass\n    if r.h.hexdigest()!=e[\'sha256\']:raise ValueError(\'extra digest differs\')\n   else:\n    r=Reader(e[\'parts\']);seen={}\n    with tarfile.open(fileobj=r,mode=\'r|\') as tf:\n     for m in tf:\n      if m.name.startswith(\'/\') or \'..\' in Path(m.name).parts:raise ValueError(\'unsafe tar path\')\n      if m.isdir():continue\n      if not m.isfile() or m.name not in e[\'files\'] or m.name in seen:raise ValueError(\'unexpected tar member\')\n      h=hashlib.sha256()\n      f=tf.extractfile(m)\n      for b in iter(lambda:f.read(1<<20),b\'\'):h.update(b)\n      seen[m.name]=h.hexdigest()\n    while r.read(1<<20):pass\n    if seen!=e[\'files\'] or r.h.hexdigest()!=e[\'sha256\']:raise ValueError(\'tar contents or digest differ\')\n   verified.append(e[\'parts\'])\n return dict(missing=missing,verified=verified,inherited_parts_present=sorted(set(inherited)))\n\nif __name__=="__main__":\n result=main(*sys.argv[1:]);print(json.dumps(result,sort_keys=True));sys.exit(1 if result["missing"] else 0)\n'
if __name__=='__main__':
 # STAGING_VERIFY is the byte-for-byte H1 payload/v.py module embedded by the builder.
 scope={'__name__':'inherited_staging'};exec(compile(STAGING_VERIFY,'v.py','exec'),scope)
 evidence(B,H,OLD,B/'e',scope['main'])
