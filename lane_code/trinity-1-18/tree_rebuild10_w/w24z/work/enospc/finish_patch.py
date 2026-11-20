from pathlib import Path
import json,base64,hashlib,difflib
W=Path(__file__).resolve().parent;J=W.parents[1];K=J/'out/kit_n_go';P=W/'proposed'
s=(P/'b/pc.py').read_text().replace("done = self.state/('gcs_'+directory.name+'.done')", "done = self.state/('gcs_'+directory.name+('_stop' if labels == ['ckstop'] else '')+'.done')")
s=s.replace("(self.state/('gcs_'+directory.name+'.done')).exists()", "(self.state/('gcs_'+directory.name+'_stop.done')).exists()")
(P/'b/pc.py').write_text(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files={str(p.relative_to(P)):sha(p) for p in P.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
(P/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(files.items())))
build=json.loads((K/'BUILD.json').read_text());value=json.loads(base64.b64decode(build['payload']));old=value['kit_sha256'];value['kit_sha256']=sha(P/'SHA256SUMS.txt')
raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode();build['payload']=base64.b64encode(raw).decode();build['sha256']=hashlib.sha256(raw).hexdigest();(P/'BUILD.json').write_text(json.dumps(build,sort_keys=True)+'\n')
changed=[n for n in sorted(files) if sha(P/n)!=sha(K/n)]+['SHA256SUMS.txt','BUILD.json']
patch=''.join(''.join(difflib.unified_diff((K/n).read_text().splitlines(True),(P/n).read_text().splitlines(True),fromfile='a/out/kit_n_go/'+n,tofile='b/out/kit_n_go/'+n)) for n in changed)
(J/'out/KIT_CHANGE_24M4Z.patch').write_text(patch)
(W/'patch_seals.json').write_text(json.dumps(dict(changed=changed,old_kit=old,proposed_kit=value['kit_sha256'],unchanged_tree=value['source_seal'],changed_file_hashes={n:sha(P/n) for n in changed}),indent=2)+'\n')
print('proposed kit',value['kit_sha256'])
