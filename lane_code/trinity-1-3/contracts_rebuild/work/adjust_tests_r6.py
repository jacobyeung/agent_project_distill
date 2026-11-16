from pathlib import Path
L=Path(__file__).resolve().parents[1]
p=L/'work/tests_r6/test_heading_r2.py';s=p.read_text().replace('''                # Same geometry and arithmetic; only availability policy is disabled.
                with contract_epoch(False):expected=respond(call,PrintedPointRegistry(),own)[0]
''','''                # A vertical reference has no sealed basis. Compare the ON
                # adapters there; OFF must retain the sealed error below.
                with contract_epoch(kind == 'vertical'):
                    expected=respond(call,PrintedPointRegistry(),own)[0]
                if kind == 'vertical':
                    with contract_epoch(False):
                        assert respond(call,PrintedPointRegistry(),own)[0]=='error: vertical_camera_heading'
''');p.write_text(s)
p=L/'work/row_families_r6/integrity.py';s=p.read_text().replace("path=L/'work/trees'/arm/rel", "path=(L/'work/base/work/base/tree_b01ce449' if arm=='r6_base' else L/'work/trees'/arm)/rel").replace('4_000_000_000','3_900_000_000');p.write_text(s)
