from pathlib import Path
L=Path(__file__).resolve().parents[2];p=L/'work/build24b/resolver_tests.py';s=p.read_text();at=s.index("if __name__=='__main__':")
s=s[:at]+''' def test_11_default_listing_resolves_without_fill(self):
  import resolver21e as R
  R.K=K;R.D=O/'auto';R.D.mkdir(exist_ok=True);f=R.fixture();original=J.load
  sp=deepcopy(original(K/'k/p.json'));sp['n_root']=str(f['pool']/'x_22c714e1');root=Path(sp['n_root']);(root/'w').mkdir(parents=True,exist_ok=True)
  listing=J.load(f['listing'])
  for i,part in enumerate(listing['objects']):(root/'w'/str(i)).write_bytes(Path(part['pool_path']).read_bytes())
  J.write(root/'l.json',dict(metadata=listing['metadata']))
  with tarfile.open(f['m']/'s.tar') as archive:sp['m4']['v']=hashlib.sha256(archive.extractfile('MANIFEST.json').read()).hexdigest()
  marker=(f['pool']/sp['p_root']/'o/gcs_6ed2c7aa_m400.done').read_text().split();sp['m4'].update(t=marker[2],b=int(marker[1]))
  with R.external_boundary(f),patch.object(J,'load',side_effect=lambda p:deepcopy(sp) if Path(p)==K/'k/p.json' else original(p)):
   result=J.resolve(K,f['pool'],None,O/'auto_resolved.json')
  self.assertEqual(result['request']['milestone'],400);self.assertEqual(result['config']['r1_training']['proof_mode'],'train')
  self.assertEqual([x['path'] for x in result['parts']],[str(root/'w'/str(i)) for i in range(4)])
  self.assertEqual(result['config']['init_artifact']['artifact']['sha256'],sp['m4']['a'])
''' +s[at:];p.write_text(s)
p=L/'work/build24b/evidence.py';s=p.read_text().replace("if isinstance(n,ast.stmt)}", "if isinstance(n,ast.stmt) and not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))}")
s=s.replace("folders=[D/'proofs/init',", "folders=[D/'proofs/proof_control',D/'proofs/init',");p.write_text(s)
