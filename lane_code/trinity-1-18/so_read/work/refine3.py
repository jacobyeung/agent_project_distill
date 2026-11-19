from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');E=L/'work/src/u0'
p=E/'a12.py';s=p.read_text().replace('processor_only=False, operator_bootstrap','processor_only=False, caches_only=False, operator_bootstrap')
s=s.replace("    if processor_only and not enable_extensions:raise ValueError('Processor-only requires --enable-extensions')", "    if (processor_only or caches_only) and not enable_extensions:raise ValueError('Cache profiles require --enable-extensions')")
s=s.replace('    if operator_source:\n        # The A4 operator',"    if processor_only or caches_only:\n        cfg.update(read_scene_shards=False,read_atomic_journal=False)\n    if operator_source:\n        # The A4 operator")
s=s.replace("    p.add_argument('--processor-only',action='store_true')","    p.add_argument('--processor-only',action='store_true')\n    p.add_argument('--caches-only',action='store_true')")
s=s.replace('processor_only=a.processor_only,','processor_only=a.processor_only,caches_only=a.caches_only,');p.write_text(s)
p=E/'a0.py';s=p.read_text().replace('self.provider=provider;self.failed=False','self.provider=provider;self.failed=False;self.pid=os.getpid()').replace('if self.failed or weight_stamp(self.provider())!=self.stamp:self.fail()', 'if self.failed or os.getpid()!=self.pid or weight_stamp(self.provider())!=self.stamp:self.fail()');p.write_text(s)
p=E/'tests/test_operator_round3.py';s=p.read_text();start=s.index('    def prepare_stub(');end=s.index('    def execute_worker(',start)
s=s[:start]+'''    # Exercise real a18 settings/artifact construction; only the heavy restore,
    # export admission, and artifact scan use CPU stubs.
    import transformers,scipy
    torchvision=types.ModuleType('torchvision');torchvision.__version__='cpu-fixture'
    from parity_kit import stage_restore,build_manifest
    from orchard_h10 import export_pins
    def stage_stub(*args,**kwargs):
        dest=Path(args[3]);dest.mkdir(parents=True,exist_ok=True)
        (dest/'RESTORE.json').write_text('{}')
    def build_stub(*args,**kwargs):
        assert kwargs['code_roots']['extensions']==p/'u0'
        return {'code_roots':{k:str(v) for k,v in kwargs['code_roots'].items()}}
    if action==0:
        receipt={'versions':{m.__name__:m.__version__ for m in (torch,torchvision,transformers,scipy)}}
        (root/'d/environment.json').write_text(json.dumps(receipt))
'''+s[end:]
s=s.replace("with patch.object(common,'install_process_guard'),patch.object(prepare,'run',side_effect=prepare_stub),patch.object(runner,'run',side_effect=execute_sequence):", "with patch.object(common,'install_process_guard'),patch.object(stage_restore,'stage',side_effect=stage_stub), \\\n         patch.object(build_manifest,'build',side_effect=build_stub),patch.object(export_pins,'validate'), \\\n         patch.dict(sys.modules,{'torchvision':torchvision}),patch.object(runner,'run',side_effect=execute_sequence):")
s=s.replace("    if action==0:assert observed==['5.py','prepare'],observed", """    if action==0:
        assert observed==['5.py'],observed
        settings=json.loads((root/'d/settings.json').read_text())
        assert all(settings[k]=='on' for k in ('read_processor_cache','read_vision_cache','read_sam_cache'))
        assert settings['read_cache_bytes']==12*1024**3
        from e2e_reader import read_cache,parity,stage1
        for module,name in ((read_cache,'a0.py'),(parity,'a1.py'),(stage1,'a3.py')):
            assert Path(module.__file__).read_bytes()==(p/'u0'/name).read_bytes()
        assert json.loads((root/'d/binding.json').read_text())['code_roots']['extensions']==str(p/'u0')""")
s=s.replace("before=load('original_memory_operator',L/'work/operator3-original/7.py')", "before=load('original_memory_operator',INPUT.parent/'tower_sequence.py')")
s=s.replace("config=dict(cfg,package=str(root/'p'),output=str(root/'output'),settings=str(root/'settings.json'),", "(root/'d').mkdir();(root/'d/config.json').write_text('{}')\n        files={name:{'path':str(root/'d'/name)} for name in ('environment.json','full_weights','artifact',\n               'base_config','original_model','sam_receipt','sam_checkpoint','g3t_weights','selector_config')}\n        inputs=dict(files=files,environment_receipt='environment.json',sam_source=str(root/'d/source'),\n                    frames_root=str(root/'d/frames'),_export={'preparation':{'config':{'path':'config.json'}}})\n        config=dict(cfg,logical=str(root),stage1_select_rule='candidates_argmax',perception_memo='on',\n             package=str(root/'p'),output=str(root/'output'),settings=str(root/'d/settings.json'),")
s=s.replace('config=config,inputs={},end=time.time()+10000','config=config,inputs=inputs,end=time.time()+10000')
s=s.replace("            self.assertFalse(config['read_scene_shards'])", "            self.assertFalse(config['read_scene_shards']);self.assertFalse(config['read_atomic_journal'])")
p.write_text(s)
