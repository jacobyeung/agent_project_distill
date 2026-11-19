from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');E=L/'work/src/u0/tests'
def edit(p,old,new):
 s=p.read_text();assert old in s,(p,old[:100]);p.write_text(s.replace(old,new))
# Production fixtures carry the fixed reviewed metadata; tensor/data work stays synthetic.
p=E/'test_round4.py'
edit(p,"    write(root/'binding.json',binding)","    if not BEFORE and os.environ.get('READ_NODE4_BEFORE')!='1':\n        binding=json.loads((L/'out/operations/binding.default.json').read_text())\n    write(root/'binding.json',binding)")
edit(p,"    # Match the real fill helper's bytes, retained by prepare at d/6.json.","    if binding['step']==400:\n        export=json.loads((L/'out/operations/BOUND_EXPORT.json').read_text())\n    # Match the real fill helper's bytes, retained by prepare at d/6.json.")
edit(p,"        if argv[0]=='/bin/tar':", "        if argv[0]=='/usr/bin/python3' and '-c' in argv and 'os.execv' in argv[argv.index('-c')+1]:\n            argv=list(argv);argv[-1]=str(physical(root,argv[-1]));argv[0]=sys.executable\n            return subprocess.run(argv,**kwargs)\n        if argv[0]=='/bin/tar':")
p=E/'test_round5.py'
edit(p,"        write(cls.root/'binding.json',cls.binding)","        if not BEFORE:\n            cls.binding=json.loads((L/'out/operations/binding.default.json').read_text())\n        write(cls.root/'binding.json',cls.binding)")
edit(p,"art['step']=400;", "art['step']=binding['step']+1;")
edit(p,"'--step 600'", "'--step '+str(self.binding['step'])")
p=E/'test_round6.py'
edit(p,"    write(package/'a/c/MEMORY.json',memory)","    write(package/'a/c/ENVIRONMENT.json',dict(versions=dict(torch='2.11.0+cu129',transformers='5.12.0'),cuda='12.9'))\n    proof['ready']['environment']=sha(package/'a/c/ENVIRONMENT.json')\n    write(package/'a/c/MEMORY.json',memory)")
edit(p,"    write(root/'export-pin.json',identity)","    if binding['step']==400:\n        identity=json.loads((L/'out/operations/BOUND_EXPORT.json').read_text())\n    write(root/'ENVIRONMENT.json',dict(versions=dict(torch='2.11.0+cu129',transformers='5.12.0'),cuda='12.9'))\n    proof['ready']['environment']=sha(root/'ENVIRONMENT.json')\n    write(root/'export-pin.json',identity)")
edit(p,"    return config\n", "    config['environment_receipt']=str(root/'ENVIRONMENT.json')\n    return config\n")
edit(p,"    if 'bound_export' not in inspect.signature(helper.gate).parameters:return helper.gate(*args)\n", "    if not hasattr(helper,'DEFAULT_BOUND_EXPORT'):return helper.gate(*args)\n")
edit(p,"(root/'1.json','1.json')):","(root/'1.json','1.json'),(root/'ENVIRONMENT.json','ENVIRONMENT.json')):")
edit(p,"    return helper.gate(*args,asset_receipts=receipts,bound_export=template['export_pin'])", "    kwargs={'bound_export':template['export_pin']} if 'bound_export' in inspect.signature(helper.gate).parameters else {}\n    return helper.gate(*args,asset_receipts=receipts,**kwargs)")
edit(p,"    write(package/'a/g.json',{'u0':pack(value)})", "    environment=json.loads((package/'a/c/ENVIRONMENT.json').read_text())\n    value['adoption_environment']=dict(sha256=sha(package/'a/c/ENVIRONMENT.json'),torch=environment['versions']['torch'],transformers=environment['versions']['transformers'],cuda=environment['cuda'])\n    write(package/'a/g.json',{'u0':pack(value)})")
edit(p,"pin['step']=400;", "pin['step']+=1;")
p=E/'test_round7.py'
# Test the real namespace invocation without rewriting tar's argv.
edit(p,"        wrapper.write_text('import subprocess,sys\\na=sys.argv[2:]\\na[a.index(\"-C\")+1]=sys.argv[1]\\nraise SystemExit(subprocess.call(a))\\n')", "        wrapper.write_text('import subprocess,sys\\na=sys.argv[2:]\\nif a[0]==\"/bin/tar\": a[a.index(\"-C\")+1]=sys.argv[1]\\nelse: a[-1]=sys.argv[1];a[0]=sys.executable\\nraise SystemExit(subprocess.call(a))\\n')")
edit(p,"self.assertTrue(tar.getmember('./link').isfile())", "self.assertTrue(tar.getmember('./link').issym())")
edit(p,'regular file and dereferenced link preserved','regular file and symlink preserved')
edit(p,"        value=identity or dict(json.loads(ep.read_text()),artifact=dict(sha256='a'*64,bytes=123))", "        value=identity or json.loads(ep.read_text())")
edit(p,"        cfg['adoption_kit']=got;root=fresh();self.kit.write_gate_receipt(root,cfg,True)", "        cfg['adoption_kit']=got;root=fresh()\n        with patch.object(self.kit,'validate_environment',return_value=value['adoption_environment'],create=True):\n            self.kit.write_gate_receipt(root,cfg,True)")
start=p.read_text().index('    def test_rebind_default400_and_explicit600(self):')
s=p.read_text();s=s[:start]+'''    def test_rebind_step400_only(self):
        if BEFORE:
            self.assertIn('bound_export',inspect.signature(self.helper.gate).parameters,'Gate lacks reviewed export binding')
        self.assertNotIn('bound_export',inspect.signature(self.helper.gate).parameters)
        default=json.loads((L/'out/operations/BOUND_EXPORT.json').read_text())
        self.assertEqual(default['step'],400)
        self.assertEqual(default['artifact']['sha256'],'5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd')
        root,p,args,kwargs=self.fixture(identity=default)
        config=self.helper.gate(*args)
        self.assertEqual(config['adoption_assets']['export_pin'],sha(root/'export-pin.json'))
        changed=copy.deepcopy(default);changed['artifact']['sha256']='b'*64
        root,p,args,kwargs=self.fixture(identity=changed)
        with self.assertRaisesRegex(ValueError,'step-400 export'):self.helper.gate(*args)
        print('Only reviewed step-400 export passes; changed artifact and selectable-export API refuse.')


if __name__=='__main__':unittest.main(verbosity=2)
''';p.write_text(s)
print('Updated fixtures to fixed step-400 metadata, namespace link validation and environment receipts.')
