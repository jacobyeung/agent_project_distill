import ast,difflib,hashlib,json,re,subprocess,tarfile
from pathlib import Path
H=Path(__file__).resolve().parents[1];D=H.parent/'d0'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
w=lambda p,v:Path(p).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
ids=json.loads((H/'ids.json').read_text());code=json.loads((H/'payload/7.json').read_text());old=json.loads((D/'kitfull/k/7.json').read_text())
changed={n:dict(before=old['files'].get(n),after=h) for n,h in code['files'].items() if old['files'].get(n)!=h}
assert not set(old['files'])-set(code['files'])
w(H/'evidence/tree_changes.json',changed)
with tarfile.open(D/'kitfull/k/t_b01ce449beffe35b.tar') as t: base=t.getmembers()
with tarfile.open(H/'payload'/ids['trainer']['file']) as t: new=t.getmembers()
def layout(ms):return dict(members=len(ms),types=sorted({m.type.decode() for m in ms}),metadata=sorted({str((m.uid,m.gid,m.uname,m.gname,m.mtime,oct(m.mode))) for m in ms}),sorted=[m.name for m in ms]==sorted(m.name for m in ms))
w(H/'evidence/archive_layout.json',dict(sealed=layout(base),derived=layout(new),deterministic_rebuild_matches=sha(H/'evidence/rebuilt.tar')==ids['trainer']['sha256']))
paths=[H/'in/h1_1_kit_ready.tar',H/'in/receipt_real_forced.tar',H/'source/h1_1_code.tar',H/'in/SHA256SUMS_inner',D/'tools/derive_kit.py',D/'kitfull/SHA256SUMS.txt',D/'kitfull/k/7.json',D/'kitfull/k/t_b01ce449beffe35b.tar',D/'jobB/jb.sh',D/'jobB/4b.json',D/'a2/v5b/over_fx.json']
w(H/'evidence/input_pins.json',{str(p):sha(p) for p in paths})
# A content pre-scan is evidence for the independent reviewer, never a CLEAN certificate.
pattern=re.compile(r'(?i)scannet(?:pp)?|arkit|vsibench|vstibench|dsibench|qwen|/scratch/jjyeung|/home/jjyeung|orch_n30')
hits=[]
for n in changed:
 p=H/'build/tree'/n
 try:txt=p.read_text()
 except UnicodeDecodeError:continue
 if old['files'].get(n):
  with tarfile.open(D/'kitfull/k/t_b01ce449beffe35b.tar') as tf: before=tf.extractfile(n).read().decode()
  added=[x[1:] for x in difflib.unified_diff(before.splitlines(),txt.splitlines(),n=0) if x.startswith('+') and not x.startswith('+++')]
 else:added=txt.splitlines()
 count=sum(len(pattern.findall(x)) for x in added)
 if count:hits.append(dict(member=n,new_match_count=count))
w(H/'evidence/anon_prescan.json',dict(status='UNREVIEWED',new_source_identifying_matches=hits,required_pinned_room_list='auth/R0_ROOMS.txt',scope='Added lines in changed source members; full artifact/content review including inherited matches and generated records remains required. Upload destination basenames use opaque tokens; Python module paths inside the source archive are preserved.'))
for p in list((H/'tools').glob('*.py'))+list((H/'tests').glob('*.py'))+list((H/'payload').glob('*.py')):ast.parse(p.read_text(),filename=str(p))
for p in list((H/'payload').glob('*.sh'))+[H/'orch_h1.sh',H/'fin_h1.sh',H/'runtime/jb.sh']:subprocess.run(['/bin/bash','-n',str(p)],check=True)
w(H/'evidence/final_static_checks.json',dict(status='PASS',syntax=True,export_names=len((H/'EXPORT_OBJECTS.txt').read_text().splitlines()),payload_under_20MB=all(p.stat().st_size<20_000_000 for p in (H/'payload').iterdir() if p.is_file())))
# Line-by-line rationale accompanies the exact unified diff; no Git is used.
a=(D/'tools/derive_kit.py').read_text().splitlines();b=(H/'tools/derive_kit_h1.py').read_text().splitlines();diff='\n'.join(difflib.unified_diff(a,b,fromfile='D0/tools/derive_kit.py',tofile='tools/derive_kit_h1.py'))+'\n'
(H/'evidence/derive.patch').write_text(diff)
functions={};current='module'
for i,line in enumerate(b,1):
 if line.startswith('def '):current=line[4:line.index('(')]
 functions[i]=current
reasons={'validate_h1':'Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field.', 'code_records':'Exempt only independently validated regenerated code records from the data-only placement comparison.', 'read_override_pin':'Require an exact file/SHA256 pin before reading code or archive evidence.', 'replace_once':'Apply each fixed runtime patch only when the sealed source matches exactly.', 'install_code':'Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge.', 'close':'Retain data placement checks while treating validated code records as regenerated kit records.', 'derive':'Apply the bounded additions and bind the resulting config, source seal and launch identity.', 'module':'Document and expose only the declared code-tree and config override fields.'}
rows=[]
for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(a=a,b=b).get_opcodes():
 if tag=='equal':continue
 for i in range(i1,i2):rows.append(f'| D0 {i+1} | − | `{a[i].replace("|","&#124;")}` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |')
 for j in range(j1,j2):rows.append(f'| H1 {j+1} | + | `{b[j].replace("|","&#124;")}` | {reasons.get(functions[j+1],reasons["module"])} |')
text='The derivation tool retains D0’s data-only rules and adds one separately validated code-tree override. No arbitrary `b/`, job-script, code-pin, optimizer, or recipe override is accepted.\n\n'
text+='The exact patch is [evidence/derive.patch](evidence/derive.patch). Every changed line appears below with its purpose. Blank lines only separate the corresponding blocks.\n\n'
text+='| Location | Change | Line | Reason |\n|---|---|---|---|\n'+'\n'.join(rows)+'\n\n'
text+='**Trainer and shipped-runtime changes**\n\n'
for n,reason,basepath,newpath in [
 ('student_pilot/carrier_c1_run.py','Poll the job-specific stop request at startup and after each optimizer update. The existing all-reduce, checkpoint, milestone export and stop path remain intact.',H/'source/code/tree/student_pilot/carrier_c1_run.py',H/'build/tree/student_pilot/carrier_c1_run.py'),
 ('student_pilot/h1_r0.py','Resolve the pinned room file inside the flat trainer archive. Its bytes remain bdb5d402…; no room membership changes.',H/'source/code/tree/student_pilot/h1_r0.py',H/'build/tree/student_pilot/h1_r0.py'),
 ('b/r.sh','Write the request into the run directory that c.sh binds into every rank’s namespace. Job-specific names prevent stale requests from stopping a resumed allocation.',D/'kitfull/b/r.sh',H/'build/fx/b/r.sh'),
 ('b/h.py','Continue walking when a process namespace denies /proc access.',D/'kitfull/b/h.py',H/'build/fx/b/h.py'),
 ('b/i.py','Do not unwind the supervisor when /proc/<pid>/environ is denied. The run-file stop bridge remains available.',D/'kitfull/b/i.py',H/'build/fx/b/i.py'),
 ('job.sh','Declare the 13-hour allocation; retain the recipe’s sealed 24-hour horizon and stop reserve.',D/'kitfull/job.sh',H/'build/fx/job.sh'),
 ('jb.sh','Use only the new run, kit, persistent root and verifier; set the allocation and fallback deadline to 13 hours. Retain R11’s slot publication checks.',D/'jobB/jb.sh',H/'runtime/jb.sh')]:
 text+=f'`{n}`: {reason}\n\n```diff\n'+''.join(difflib.unified_diff(basepath.read_text().splitlines(True),newpath.read_text().splitlines(True),fromfile='supplied/'+n,tofile='shipped/'+n))+'```\n\n'
text+='The trainer also adds the exact supplied `auth/R0_ROOMS.txt` inside its archive. All supplied H1 tree changes relative to D0 are enumerated with before/after hashes in [evidence/tree_changes.json](evidence/tree_changes.json).\n\n'
text+='`payload/f.py` preserves the faithful gate computation, uses the opaque deployed tree directory, records the input receipt hash, and classifies unreadable/invalid SQLite inputs as exit 2. The new read-only staging verifier checks actual tar members and whole-archive digests, including trailing bytes.\n\n'
text+='Tests: `evidence/derivation.json`, `evidence/archive_layout.json`, `evidence/stop_bridge/result.json`, `evidence/gate_binding.json`, `evidence/staging_test/result.json`, and `evidence/cpu/fallback_final/result.json`. The four-rank torchrun chain is blocked by denied sockets; its failure log is retained. The step-200 fallback uses a native tiny model and real checkpoint/export serialization with local one-rank collective stand-ins.\n'
(H/'DIFF.md').write_text(text)
print('Source changes:',len(changed),'prescan:',hits)
