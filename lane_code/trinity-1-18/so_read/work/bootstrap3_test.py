from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');p=L/'work/src/u0/tests/test_operator_round3.py';s=p.read_text()
s=s.replace("from orchard_h10 import common,runner,prepare", "from orchard_h10 import common,runner,prepare,job",1)
needle="""        boot.make_dispatch(root,dispatch,common.sha(root/'7.py'))(
            [sys.executable,'-I','-s','-B',str(root/'a/5.py'),str(cfgpath)])"""
replacement="""        def run_job(directory):
            assert directory==root
            job.checked_run([sys.executable,'-I','-s','-B',str(root/'a/5.py'),str(cfgpath)])
        def mapped_path(value):
            return root/'shared-root' if str(value)=='/project/community/jjyeung/okh7' else Path(value)
        public=json.loads((root/'0.json').read_text())
        shared=root/'shared-root'/('a15_cot_ap'+public['token'])
        proof_path=shared/'a/c/CPU.json';proof=json.loads(proof_path.read_text())
        with patch.object(boot,'Path',side_effect=mapped_path),patch.object(sys,'argv',[str(root/'0.py'),str(root)]), \\
             patch.object(job,'main',side_effect=run_job) as main_job,patch.object(job,'checked_run',side_effect=dispatch):
            # Run the real admission branch. Only the hardcoded shared root and
            # job staging boundary are redirected to private CPU fixtures.
            proof_path.write_text(json.dumps(dict(proof,bundle_guard_passed=False)))
            try:boot.main()
            except ValueError as error:assert str(error)=='Full CPU check differs'
            else:raise AssertionError('Bootstrap accepted a failed CPU proof')
            main_job.assert_not_called()
            proof_path.write_text(json.dumps(proof))
            boot.main();main_job.assert_called_once_with(root)"""
assert needle in s;s=s.replace(needle,replacement)
needle="        (root/'0.py').write_bytes(bundled['0.py']);(root/'7.py').write_bytes(OPERATOR.read_bytes())"
s=s.replace(needle,needle+"\n        (root/'0.json').write_bytes((package/'0.json').read_bytes())")
needle="        import time\n        for action in (0,1):"
s=s.replace(needle,"""        public=json.loads((root/'0.json').read_text())
        shared=root/'shared-root'/('a15_cot_ap'+public['token']);(shared/'a/c').mkdir(parents=True)
        (shared/'0.tgz').write_bytes((package/'0.tgz').read_bytes())
        (shared/'a/1.json').write_text(json.dumps(inputs))
        operator=load('operator_proof_source',OPERATOR)
        memory=operator.memory_bound() if BEFORE else operator.memory_bound(read_extensions=True,read_cache_bytes=12*1024**3)
        proof=dict(passed=True,bundle_guard_passed=True,entry_sequence_passed=True,
                   payload=public['payload_sha256'],plan=public['plan_sha256'],
                   inputs=hashlib.sha256((shared/'a/1.json').read_bytes()).hexdigest(),
                   operator_sha256=hashlib.sha256(OPERATOR.read_bytes()).hexdigest(),memory=memory)
        (shared/'a/c/CPU.json').write_text(json.dumps(proof))
        import time
        for action in (0,1):""")
p.write_text(s)
# Keep the saved report generator and final note in sync with source wording.
p=L/'work/write_round3_report.py';s=p.read_text().replace('runs real action-0 settings/artifact construction with heavy restore/admission scans stubbed',
 'runs real bootstrap admission (including rejection of a failed CPU proof) and action-0 settings/artifact construction with heavy restore/export-admission scans stubbed')
s=s.replace('Measured CPU validation/cache overhead: **','Measured CPU validation/cache overhead falls from **').replace(':.1f} → {cost',':.1f} to {cost')
p.write_text(s)
