from pathlib import Path
W=Path(__file__).resolve().parents[1];O=W/'out'
p=W/'work/test_sequence.py';s=p.read_text().replace('786','134').replace('len(result),2','len(result),1').replace("'verify' if i==1 else 'on'","'on'").replace("ids if i==1 else []","[]").replace('n=636 if i==0 else 150','n=134').replace('[(1,3),(0,3),(0,0),(0,1),(0,2),(0,4)]','[(0,4)]').replace("T.RULES[1]","'candidates_argmax'").replace('items/devs1_routed.json','items/room134.json').replace('two settings/identities, two workers, six type journals.','one settings identity, one worker, one type journal.')
p.write_text(s)
p=W/'work/test_fixes.py';s=p.read_text().replace('all_six_journals','room_journal').replace('[1,0]','[0]').replace('len(journals),6','len(journals),1').replace('786','134').replace('((0,636),(1,150))','((0,134),)').replace(';self.assertNotEqual(pids[0],pids[1])','').replace('type=3','type=4').replace('journals/3/0','journals/4/0').replace('items/devs1_routed.json','items/room134.json');s=s.replace("'--arms','tower','--modes'","'--types','room_size_estimation','--arms','tower','--modes'");p.write_text(s)
p=W/'work/test_return_cli.py';s=p.read_text().replace('==6','==1').replace('full_journals=6','full_journals=1');p.write_text(s)
p=W/'work/test_memo_binding.py';s=p.read_text().replace('items/devs1_routed.json','items/room134.json').replace("'--types','object_abs_distance'","'--types','room_size_estimation'").replace('for i in (0,1):','for i in (0,):');p.write_text(s)
# Rebase package tests on W5; retain their applicable restore and export guards.
p=O/'tests/test_package.py';s=p.read_text();s=s.replace("PROD=Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/repin/out/production')","PROD=ROOT.parent/'b1g/out/src'")
s=s.replace("read(Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/repin')/'in/prod_pkg/a/1.json')","read(OUT/'inputs_tower.json')")
s=s.replace("str(Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/repin')/'in/prod_pkg/a/1.json')","str(OUT/'inputs_tower.json')")
s=s.replace("with self.assertRaises(KeyError):check_inputs(self.old,self.cfg,package=package)","bad=copy.deepcopy(self.old);bad.pop('export_pin')\n        with self.assertRaises(KeyError):check_inputs(bad,self.cfg,package=package)")
a=s.index('    def test_544_identity_with_h11_prep_refuses');b=s.index('    def test_restore_structural_guards',a)
s=s[:a]+'''    def test_544_identity_with_wrong_prep_refuses(self):
        root,pins,req=self.metadata_fixture()
        obj=read(root/'heads/artifact.json');obj['config_sha256']='0'*64;write(root/'heads/artifact.json',obj)
        pins['artifact']=fill_export.pin((root/'heads/artifact.json').read_bytes())
        with self.assertRaisesRegex(ValueError,'export architecture or identity differs'):self.call_restore(root,pins,req)

''' +s[b:]
a=s.index('    def test_identity_and_byte_inventory');b=s.index('\n\nclass StreamingHelper',a)
s=s[:a]+'''    def test_identity_and_byte_inventory(self):
        with tarfile.open(OUT/'0.tgz') as t:
            payload={m.name:t.extractfile(m).read() for m in t if m.isfile()}
        self.assertEqual([n for n in payload if n.startswith('items/')],['items/room134.json'])
        for name,pin in self.cfg['payload_pins'].items():self.assertEqual(fill_export.pin(payload[name]),pin)
        for folder in ('b/e2e_reader','b/parity_kit','b/heads','tree'):
            for p in (PROD/folder).rglob('*'):
                if p.is_file() and p.suffix!='.pyc':self.assertEqual(p.read_bytes(),(SRC/p.relative_to(PROD)).read_bytes())
''' +s[b:]
s=s.replace("items/devs1_routed.json","items/room134.json").replace("'--arms','own'","'--arms','tower','--types','room_size_estimation'").replace("32,['own'],[]","32,['tower'],[]")
s=s.replace("config=dict(package=str(SRC),output=str(root)","config=dict(package=str(SRC),items=str(SRC/'items/room134.json'),output=str(root)")
p.write_text(s)
