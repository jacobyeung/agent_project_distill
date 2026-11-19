from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');p=L/'work/src/u0/tests/test_round3.py';s=p.read_text();pos=s.index('    def test_f3_both_base_')
s=s[:pos]+'''    def test_f1_valid_boundary_allows_deadline_resume_and_public_merge(self):
        self.assertTrue(hasattr(C.ReadCache,'weight_boundary'),'Missing weight boundary')
        fixtures=load('round3_resume_fixture',SRC/'u0/tests/test_read_journal.py')
        case=fixtures.RunnerTests();case.setUp()
        original_json=fixtures.launch.json;original_journal_json=fixtures.J.json
        try:
            m,store=visual()
            def factory(*a,**kw):
                def generate(item):
                    with torch.no_grad():m(torch.ones(1,32))
                    return fixtures.row(item['id'])['output']
                generate.weight_boundary=store.weight_boundary
                return generate
            args=case.args('graceful');commit=fixtures.launch.commit_record
            def interrupted(stream,row):
                if row.get('id')=='1':raise fixtures.launch.ReadDeadline()
                return commit(stream,row)
            with patch.object(fixtures.launch,'commit_record',side_effect=interrupted):
                with self.assertRaises(fixtures.launch.ReadDeadline):fixtures.launch.run(args,make_real=factory)
            self.assertIs(json.loads((Path(args.out)/'WEIGHTS.json').read_text())['verified'],True)
            self.assertEqual(fixtures.launch.run(args,make_real=factory)['completed'],5)
            private=fixtures.merge(case.manifest,[args.out],case.root/'merged-private')
            args=case.args('public-checked');args.opaque=True
            fixtures.launch.run(args,make_real=factory)
            from a9 import Codec,read_wire
            self.assertTrue(read_wire(json.loads((Path(args.out)/'WEIGHTS.json').read_text()))['verified'])
            result=fixtures.merge(case.manifest,[args.out],case.root/'merged-public',
                                  public_codec=Codec(case.manifest,vars(args)))
            self.assertEqual(result['items'],private['items'])
        finally:
            fixtures.launch.json=original_json;fixtures.J.json=original_journal_json
            case.doCleanups()

'''+s[pos:];p.write_text(s)
p=L/'work/run_checks.py';p.write_text(p.read_text().replace("'FAILED (failures=14)',[]","'FAILED (failures=15)',[]"))
