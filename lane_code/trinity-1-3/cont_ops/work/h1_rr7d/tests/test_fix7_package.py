"""Check opaque payload integrity and the guarded patch against local copies."""
import base64,copy,hashlib,io,json,re,subprocess,sys,tarfile,tempfile,zlib
from pathlib import Path
H=Path(__file__).resolve().parents[1]
out=Path(tempfile.mkdtemp(prefix='package_',dir=H/'evidence/fix7_selection'))
s=(H/'build/q.sh').read_text();assert len(s.encode())<1_000_000
subprocess.run(['/bin/bash','-n',str(H/'build/q.sh')],check=True)
blob=re.search(r"base64.b64decode\('([^']+)'\)",s)[1]
raw=zlib.decompress(base64.b64decode(blob));expected=re.search(r"hexdigest\(\)!='([a-f0-9]+)'",s)[1]
assert hashlib.sha256(raw).hexdigest()==expected
files=json.loads(raw)
assert files['v.py']==(H/'tools/selection_check.py').read_text()
assert files['b.json']==(H/'payload/d_f232d4160d75b582.json').read_text()
assert files['c.json']==(H/'payload/7.json').read_text()
assert files['j.py']==(H/'tools/selection_stage.py').read_text()
authority=json.loads(files['j.json'])
assert authority['manifest_sha256']=='de6e7e0fac4036889fb4112792fbaa2d6f362a0cde09722ba6e93a6a39e7f32b'
assert 'metadata' not in authority
assert authority['packages']==[p for p in json.loads((H/'evidence/derivation/empty/k/0.json').read_text())['staged_inputs']['packages']
 if p['destination']=='u/eb3429c5']
scope={};exec(compile(files['j.py'],'<embedded-stager>','exec'),scope)
def encoded(value):return json.dumps(value,sort_keys=True).encode()
def pinned(data):return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
# Retained production metadata bytes can be tested locally using the retained
# fixture's own manifest; that fixture manifest is never shipped as authority.
retained=H/'evidence/derivation/empty'
production_metadata=(retained/'k/0.json').read_bytes()
assert pinned(production_metadata)==dict(bytes=1664013,
 sha256='620a7ed162cd2f9722724be13ef09bae4123b2aba70ea3147fcc25ce91eced83')
assert scope['metadata'](retained,dict(manifest_sha256=pinned((retained/'SHA256SUMS.txt').read_bytes())['sha256']))==json.loads(production_metadata)
# These synthetic sources stay inside this workspace; no production source opens.
fixture=out/'fixture';fixture.mkdir(mode=0o700)
kit=fixture/'k';kit.mkdir();(kit/'k').mkdir();(kit/'k/a.json').write_bytes(b'{}\n')
members={'a.jsonl.gz':b'fixture gzip bytes','nested/empty.jsonl':b''}
inventory=[dict(name=n,**pinned(v)) for n,v in members.items()]
inventory.append(dict(inventory[-1]))  # The production inventory repeats an empty pin.
def make_tar(path, entries, metadata=False):
 with tarfile.open(path,'w',format=tarfile.USTAR_FORMAT) as tf:
  for name,data,kind in entries:
   m=tarfile.TarInfo(name);m.size=len(data);m.type=kind
   if kind in (tarfile.SYMTYPE,tarfile.LNKTYPE):m.linkname='../escape'
   tf.addfile(m,io.BytesIO(data))
  if metadata:
   data=''.join(v['sha256']+'  '+v['name']+'\n' for v in inventory).encode()
   m=tarfile.TarInfo('SHA256SUMS');m.size=len(data);tf.addfile(m,io.BytesIO(data))
 return pinned(path.read_bytes())
entries=[(n,v,tarfile.REGTYPE) for n,v in members.items()]
package=fixture/'p.tar';package_pin=make_tar(package,entries+[entries[-1]],metadata=True)
entry=dict(source=str(package),destination='u/eb3429c5',members=2,inventory=inventory,**package_pin)
config=dict(staged_inputs=dict(schema='s1-staged-inputs-v1',packages=[entry],files=[],archives=[]))
fixture_authority=dict(inputs=[dict(relative='u/eb3429c5/'+n,**pinned(v)) for n,v in members.items()]+
 [dict(relative='k/a.json',**pinned(b'{}\n'))])
def bind_config(value):
 data=encoded(value);(kit/'k/0.json').write_bytes(data)
 manifest=(pinned(data)['sha256']+'  k/0.json\n').encode()
 (kit/'SHA256SUMS.txt').write_bytes(manifest)
 return dict(fixture_authority,manifest_sha256=pinned(manifest)['sha256'],
  packages=copy.deepcopy(value['staged_inputs']['packages']))
fixture_authority=bind_config(config)
fixture_files=dict(files);fixture_files['j.json']=json.dumps(fixture_authority)
fixture_raw=json.dumps(fixture_files,sort_keys=True,separators=(',',':')).encode()
fixture_blob=base64.b64encode(zlib.compress(fixture_raw,9)).decode()
assert '--unshare-net' in s and 'nice -n 19' in s and 'HF_HUB_OFFLINE=1' in s
# Run the exact stdlib bootstrap with local argv; no bubblewrap or login invocation.
w=out/'w';w.mkdir();b=out/'b';b.mkdir()
import os
os.link(H/'payload/t_9588661986650d29.tar',b/'t_9588661986650d29.tar')
start=s.index("<<'P' >\"$W/b.log\" 2>&1\n")+len("<<'P' >\"$W/b.log\" 2>&1\n")
bootstrap=s[start:s.index('\nP\n',start)]
fixture_bootstrap=bootstrap.replace(blob,fixture_blob).replace(expected,hashlib.sha256(fixture_raw).hexdigest())
subprocess.run([sys.executable,'-I','-B','-',str(w),str(b),str(kit)],input=fixture_bootstrap,text=True,check=True,capture_output=True)
assert (w/'v.py').read_text()==files['v.py']
assert (w/'p').stat().st_mode & 0o777==0o700
assert (w/'p/u/eb3429c5').stat().st_mode & 0o777==0o700
for n,v in members.items():
 p=w/'p/u/eb3429c5'/n;assert p.read_bytes()==v and p.stat().st_mode & 0o777==0o400
assert not (w/'p/u/eb3429c5/SHA256SUMS').exists()
assert (w/'m').read_bytes()==str(w/'p/u/eb3429c5').encode()+b'\0u/eb3429c5\0'
assert len(json.loads((w/'s.json').read_text()))==3
refusals=[]
def refuse(label, cfg, auth=None):
 case=out/label;case.mkdir(mode=0o700)
 if auth is None:auth=bind_config(cfg)
 try:scope['stage'](kit,case,auth)
 except (ValueError,FileExistsError):pass
 else:raise AssertionError('Accepted '+label)
 assert not (case/'m').exists(),label
 refusals.append(label)
# Each fixture substitutes only its sealed authority. Production q.sh retains
# the production digest, never the fixture manifest or its reconstructed bytes.
refuse('production_authority_rejects_fixture_manifest',config,authority)
auth=bind_config(config);(kit/'k/0.json').write_bytes(b'{}')
refuse('fixture_metadata_pin_mismatch',config,auth)
for field in ('source','bytes','sha256','members','inventory','destination'):
 changed=copy.deepcopy(config);changed_entry=changed['staged_inputs']['packages'][0]
 if field in ('bytes','members'):changed_entry[field]+=1
 elif field=='inventory':changed_entry[field]=list(reversed(changed_entry[field]))
 else:changed_entry[field]+='changed'
 auth=bind_config(changed);auth['packages']=copy.deepcopy([entry])
 case=out/('changed_package_'+field);case.mkdir()
 try:scope['stage'](kit,case,auth)
 except ValueError:pass
 else:raise AssertionError('Accepted changed package '+field)
 assert not (case/'p').exists()
 refusals.append('changed_package_'+field)
# JSON bool/int equality must not bypass the package contract.
auth=bind_config(config);auth['packages'][0]['bytes']=float(entry['bytes'])
refuse('package_type_mismatch',config,auth)
bad=copy.deepcopy(config);bad['staged_inputs']['packages'][0]['sha256']='0'*64;refuse('wrong_archive_sha',bad)
bad=copy.deepcopy(config);bad['staged_inputs']['packages'][0]['bytes']+=1;refuse('wrong_archive_size',bad)
for label,extra in [('extra_member',[('extra',b'x',tarfile.REGTYPE)]),
 ('symlink',[('link',b'',tarfile.SYMTYPE)]),('hardlink',[('link',b'',tarfile.LNKTYPE)]),
 ('traversal',[('../escape',b'x',tarfile.REGTYPE)]),('absolute',[('/escape',b'x',tarfile.REGTYPE)]),
 ('conflicting_duplicate_hash',[(entries[0][0],b'x'*len(entries[0][1]),tarfile.REGTYPE)]),
 ('conflicting_duplicate_size',[(entries[-1][0],b'x',tarfile.REGTYPE)]),
 ('sparse',[('sparse',b'',tarfile.GNUTYPE_SPARSE)]),
 ('unsafe_directory',[('../escape/',b'',tarfile.DIRTYPE)])]:
 p=fixture/(label+'.tar');pin=make_tar(p,entries+extra)
 bad=copy.deepcopy(config);bad['staged_inputs']['packages'][0].update(source=str(p),**pin)
 refuse(label,bad)
# A repeat must not depend on an inventory repeat, including nonempty payloads.
# Opening an output twice in xb mode would fail these successful cases.
archive_passes=['duplicate_empty_member_and_SUMS_line_bootstrap']
def accept_archive(label, rows, *, changes=None, trailer=b''):
 p=fixture/(label+'.tar');make_tar(p,rows)
 if trailer:
  with p.open('ab') as f:f.write(trailer)
 candidate=dict(entry,source=str(p),**pinned(p.read_bytes()))
 if changes:candidate.update(changes)
 target=out/label;scope['archive'](candidate,target)
 for row in candidate['inventory']:
  value=target/row['name']
  assert pinned(value.read_bytes())=={k:row[k] for k in ('bytes','sha256')}
 assert not (target/'SHA256SUMS').exists()
 archive_passes.append(label)
 return candidate
sums=''.join(v['sha256']+'  '+v['name']+'\n' for v in inventory).encode()
sums_member=('SHA256SUMS',sums,tarfile.REGTYPE)
accept_archive('repeats_with_unique_inventory',entries+entries+entries+[sums_member],
 changes=dict(inventory=inventory[:-1]))
accept_archive('identical_repeated_SUMS_member',entries+[sums_member,sums_member])
accept_archive('dot_names_and_parent_dirs',[('.',b'',tarfile.DIRTYPE),('nested/',b'',tarfile.DIRTYPE)]+
 [('./'+n,d,k) for n,d,k in entries])
accept_archive('extra_safe_directory',entries+[('extra/',b'',tarfile.DIRTYPE)])
assert not (out/'extra_safe_directory/extra').exists()
accept_archive('normalized_repeats',entries+[('././'+n.replace('/', '//'),d,k) for n,d,k in entries])
prefix_inventory=[dict(row,name='prefix/'+row['name']) for row in inventory[:-1]]
accept_archive('matching_prefix',[('prefix/'+n,d,k) for n,d,k in entries],
 changes=dict(inventory=prefix_inventory,member_prefix='prefix'))
for label,rows,changes in [
 ('conflicting_SUMS_line',entries+[('SHA256SUMS',sums+b'0'*64+b'  a.jsonl.gz\n',tarfile.REGTYPE)],{}),
 ('conflicting_SUMS_member',entries+[sums_member,('SHA256SUMS',sums+b'\n',tarfile.REGTYPE)],{}),
 ('oversized_SUMS',entries+[('SHA256SUMS',b'x'*65537,tarfile.REGTYPE)],{}),
 ('missing_SUMS_row',entries+[('SHA256SUMS',sums.splitlines(keepends=True)[0],tarfile.REGTYPE)],{}),
 ('wrong_prefix',entries,dict(member_prefix='prefix')),
 ('prefix_boundary',[('prefix-other/'+n,d,k) for n,d,k in entries],
  dict(member_prefix='prefix',inventory=[dict(row,name='prefix-other/'+row['name']) for row in inventory[:-1]])),
 ('wrong_member_count',entries,dict(members=3))]:
 p=fixture/(label+'.tar');pin=make_tar(p,rows)
 bad=copy.deepcopy(config);bad['staged_inputs']['packages'][0].update(source=str(p),**pin,**changes)
 refuse(label,bad)
candidate=accept_archive('pinned_trailing_bytes',entries,trailer=b'pinned trailer')
p=Path(candidate['source'])
with p.open('r+b') as f:f.seek(-1,2);f.write(b'X')
bad=copy.deepcopy(config);bad['staged_inputs']['packages'][0]=candidate
refuse('trailing_digest_mismatch',bad)
bad=dict(entry);bad.pop('inventory')
try:scope['archive'](bad,out/'missing_inventory')
except KeyError:refusals.append('missing_inventory')
else:raise AssertionError('Accepted archive without inventory')
assert not (out/'missing_inventory').exists()
for label,entries_bad in [('wrong_member_sha',[(entries[0][0],b'x'*len(entries[0][1]),tarfile.REGTYPE),entries[1]]),
 ('missing_member',entries[:1])]:
 p=fixture/(label+'.tar');pin=make_tar(p,entries_bad)
 bad=copy.deepcopy(config);bad['staged_inputs']['packages'][0].update(source=str(p),**pin)
 refuse(label,bad)
bad=copy.deepcopy(config);bad['staged_inputs']['packages'][0]['destination']='../escape';refuse('unsafe_destination',bad)
bad=copy.deepcopy(config);bad['staged_inputs']['packages'][0]['inventory'][-1]['sha256']='0'*64
refuse('conflicting_inventory',bad)
auth=bind_config(config);(kit/'k/0.json').write_bytes(b'{}');refuse('metadata_tamper',config,auth)
bind_config(config)
try:scope['stage'](kit,w,fixture_authority)
except FileExistsError:refusals.append('existing_stage')
else:raise AssertionError('Reused stage accepted')
corrupt=bootstrap.replace(blob,('A' if blob[0]!='A' else 'B')+blob[1:])
f=out/'bad';f.mkdir()
r=subprocess.run([sys.executable,'-I','-B','-',str(f),str(b),str(kit)],input=corrupt,text=True,capture_output=True)
assert r.returncode!=0 and not list(f.iterdir())
# Check visible shell/Python literals after excluding authenticated opaque data.
visible=s.replace(blob,'OPAQUE')
for prefix in ['/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung','/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung']:
 visible=visible.replace(prefix,'/sealed')
forbidden=re.compile(r'(?i)(?<![a-z0-9])(?:distill|vsi|revsi|scannet|arkit|sft|h1|r0|qwen|cot)(?![a-z0-9])')
assert not forbidden.search(visible)
# The real wrapper must refuse existing output, including dangling symlinks,
# before invoking either Python or bubblewrap. Every path is local to the fixture.
operator=out/'operator';operator.mkdir(mode=0o700)
for n in ('i_1be16f28','x_07ca49df'):(operator/n).mkdir(mode=0o700)
output_name=re.search(r'W=\$BUN/(q_[a-f0-9]+)',s)[1]
assert output_name not in ('q_7b62108a','q_c492e8d1','q_91f06d2e')
run1=operator/'i_1be16f28/q_7b62108a';run1.mkdir();(run1/'marker').write_text('preserve')
run2=operator/'i_1be16f28/q_c492e8d1';run2.mkdir();(run2/'marker').write_text('preserve')
run3=operator/'i_1be16f28/q_91f06d2e';run3.mkdir();(run3/'marker').write_text('preserve')
existing=operator/'i_1be16f28'/output_name;existing.mkdir();(existing/'marker').write_text('preserve')
wrapper=out/'refuse.sh';wrapper.write_text(s.replace('O=/project/community/jjyeung/okh7','O='+str(operator)))
r=subprocess.run(['/bin/bash',str(wrapper)],capture_output=True,text=True)
assert r.returncode==2 and 'Output already exists.' in r.stderr
assert (existing/'marker').read_text()=='preserve' and (run1/'marker').read_text()=='preserve'
assert (run2/'marker').read_text()=='preserve'
assert (run3/'marker').read_text()=='preserve'
alias=out/'refuse_link.sh';(operator/'i_1be16f28/q_eeeeeeee').symlink_to('absent')
alias.write_text(wrapper.read_text().replace(output_name,'q_eeeeeeee'))
r=subprocess.run(['/bin/bash',str(alias)],capture_output=True,text=True)
assert r.returncode==2 and 'Output already exists.' in r.stderr
assert '"${inputs[@]}"' in s and '--ro-bind "$W/p" "$W/p"' in s
for root in ('AS','AL'):
 assert '--ro-bind "$source" "$'+root+'/ap/8865619b/$destination"' in s
# Exercise the real wrapper and both read-only logical mounts on a tiny fixture.
# The probe below is explicitly TEST_ONLY; it never regenerates a selection.
probe=r'''
import errno,hashlib,json,os,sys
from pathlib import Path
work=Path(__file__).parent
for prefix in ('/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung',
               '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'):
 p=Path(prefix)/'ap/8865619b/u/eb3429c5/a.jsonl.gz'
 assert p.read_bytes()==b'fixture gzip bytes'
 assert os.statvfs(p).f_flag & os.ST_RDONLY
 try:
  with p.open('ab') as f:f.write(b'bad')
 except OSError as exc:assert exc.errno in (errno.EROFS,errno.EACCES)
 else:raise AssertionError('Logical mount is writable')
p=work/'p/u/eb3429c5/a.jsonl.gz'
assert os.statvfs(p).f_flag & os.ST_RDONLY
try:
 with p.open('ab') as f:f.write(b'bad')
except OSError as exc:assert exc.errno in (errno.EROFS,errno.EACCES)
else:raise AssertionError('Staging alias is writable')
output=work/'o';output.mkdir();data=b'TEST_ONLY mount probe\n'
(output/'r.json').write_bytes(data)
(output/'q.json').write_text(json.dumps(dict(status='EQUAL',regenerated=True,
 selection_sha256=hashlib.sha256(data).hexdigest(),TEST_ONLY='mount probe, no selection')))
'''
mount_files=dict(fixture_files);mount_files['v.py']=probe
mount_raw=json.dumps(mount_files,sort_keys=True,separators=(',',':')).encode()
mount_blob=base64.b64encode(zlib.compress(mount_raw,9)).decode()
mount_operator=out/'mount_operator';mount_operator.mkdir(mode=0o700)
mount_bun=mount_operator/'i_1be16f28';mount_bun.mkdir(mode=0o700)
mount_kit=mount_operator/'x_07ca49df';mount_kit.mkdir(mode=0o700);(mount_kit/'k').mkdir()
for p in (kit/'k').iterdir():os.link(p,mount_kit/'k'/p.name)
os.link(kit/'SHA256SUMS.txt',mount_kit/'SHA256SUMS.txt')
os.link(H/'payload/t_9588661986650d29.tar',mount_bun/'t_9588661986650d29.tar')
mount_script=out/'mount.sh';mount_script.write_text(s.replace(blob,mount_blob)
 .replace(expected,hashlib.sha256(mount_raw).hexdigest())
 .replace('O=/project/community/jjyeung/okh7','O='+str(mount_operator))
 # The local sandbox denies NETLINK_ROUTE setup; this probe makes no network
 # calls. Only its fixture wrapper omits the network namespace. q.sh retains it.
 .replace('--unshare-net ',''))
env=dict(os.environ,PY_GATE=sys.executable,BW_GATE='/usr/bin/bwrap')
r=subprocess.run(['/bin/bash',str(mount_script)],env=env,capture_output=True,text=True)
(out/'mount.log').write_text(r.stdout+r.stderr)
assert r.returncode==0,(r.stderr,(mount_bun/output_name/'r.log').read_text())
assert json.loads((mount_bun/output_name/'o/q.json').read_text())['TEST_ONLY']
# Preserve earlier test evidence: redirect the existing patch regression's output.
src=(H/'tests/test_config_patch.py').read_text().replace("H/'evidence/fix6_patch'",repr(str(out/'patch')))
src=src.replace("OUT="+repr(str(out/'patch')),"OUT=Path("+repr(str(out/'patch'))+")")
src=src.replace('evidence/fix6_patch_manifest.json','evidence/fix7_patch_manifest.json')
exec(compile(src,'<local-patch-regression>','exec'),{'__file__':str(H/'tests/test_config_patch.py')})
# Every upload member and immutable payload pin must agree.
u=json.loads((H/'UPLOAD.json').read_text())
for row in u['files']:assert hashlib.sha256((H/'payload'/row['name']).read_bytes()).hexdigest()==row['sha256']
assert hashlib.sha256((H/'build'/u['archive']).read_bytes()).hexdigest()==u['sha256']
(H/'evidence/fix7_selection/package_tests.json').write_text(json.dumps(dict(status='PASS',path=str(out),script_bytes=len(s.encode()),bootstrap='PASS',archive_passes=archive_passes,staging_refusals=refusals,existing_output_refused=True,corrupt_blob_refused=True,patch_cases=7,visible_names='PASS',local_bwrap='PASS: both logical roots and staging alias read-only; fixture omits network namespace because sandbox denies NETLINK_ROUTE; shipped wrapper retains --unshare-net',login_bwrap='NOT RUN'),indent=2)+'\n')
print(out)
