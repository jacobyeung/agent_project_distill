"""Bind CPU write probes to the delivered writer's size and budget contract."""


def patch(nf,B,here):
    s=nf['a/5.py'].decode()
    s=B.once(s,'def check_bundle_guard(package, root):',(here/'runtime/receipt.py').read_text()+'\n\ndef check_bundle_guard(package, root):')
    s=B.once(s,'_, _, results, _, _ = template()','_, _, results, transport, _ = template()')
    s=B.once(s,"    if json.loads((root/'0.json').read_text()) != json.loads((package/'0.json').read_text()):\n        raise ValueError('Bundle descriptor differs')",
             "    compare('Bundle descriptor differs',json.loads((package/'0.json').read_text()),json.loads((root/'0.json').read_text()))")
    s=B.once(s,"    if (root/'7.py').read_bytes() != expected:\n        raise ValueError('Bundled operator differs')",
             "    compare('Bundled operator differs',hashlib.sha256(expected).hexdigest(),hashlib.sha256((root/'7.py').read_bytes()).hexdigest())")
    s=B.once(s,"    if (root/'6.py').read_bytes() != vendor.read_bytes():\n        raise ValueError('Process guard did not exercise its write target')",
             "    compare('Process guard did not exercise its write target',sha(vendor),sha(root/'6.py'))")
    s=B.once(s,"    if sha(root/'7.py') != before:\n        raise ValueError('Process guard changed bundled operator')",
             "    compare('Process guard changed bundled operator',before,sha(root/'7.py'))")
    start=s.index("    if receipt['bytes'] != 4*1024**2")
    end=s.index('    vendor = ',start)
    s=s[:start]+'''    compare('Write-test receipt differs',
            dict(bytes=transport.WRITE_TEST_BYTES, evidence_bytes=transport.WRITE_TEST_BYTES,
                 sha256=receipt.get('sha256'), charged=transport.WRITE_TEST_BYTES+32),
            dict(bytes=receipt.get('bytes'), evidence_bytes=evidence.stat().st_size,
                 sha256=sha(evidence), charged=int((pool/(token+'.0')).read_text())))
'''+s[end:]
    start=s.index("    if (proof['pool'] != str(root/'wpool')")
    end=s.index("    before = proof['operator_sha256_before']",start)
    s=s[:start]+'''    from orchard_h10.common import template
    transport=template()[3]
    compare('Entry write-test evidence differs',
            dict(pool=str(root/'wpool'),bytes=transport.WRITE_TEST_BYTES,
                 evidence_bytes=transport.WRITE_TEST_BYTES,sha256=proof['write_test']['sha256'],
                 guard=proof['guard_target_sha256'],charged=transport.WRITE_TEST_BYTES+32),
            dict(pool=proof['pool'],bytes=proof['write_test']['bytes'],
                 evidence_bytes=evidence.stat().st_size,sha256=sha(evidence),
                 guard=sha(root/'6.py'),charged=int((root/'wpool'/(proof['token']+'.0')).read_text())))
'''+s[end:]
    s=B.once(s,'    except Exception as e:\n', '    except Exception as e:\n        try:cpu_failure(e)\n        except Exception as diagnostic_error:\n            print("E89:"+type(diagnostic_error).__name__.encode().hex())\n')
    start=s.index("    if (settings['stage1_select_rule']")
    end=s.index('    run_cfg=',start)
    s=s[:start]+'''    expected=dict(stage1_select_rule='null_argmax',perception_memo='off',
                  perception_memo_modules=['g3t'],perception_memo_verify_ids=[])
    compare('Prepared default settings differ',expected,{k:settings.get(k) for k in expected})
'''+s[end:]
    s=B.once(s,"    if proof.get('passed') is not True or proof.get('events') != ['guard_installed', 'write_test']:\n        raise ValueError('Write test must precede operator dispatch')",
             "    compare('Write test must precede operator dispatch',[True,['guard_installed','write_test']],[proof.get('passed'),proof.get('events')])")
    s=B.once(s,"        if dispatched[-2:] != [str(operator), str(root/'a/1.json')]:\n            raise ValueError('Bootstrap did not dispatch bundled operator')",
             "        compare('Bootstrap did not dispatch bundled operator',[str(operator),str(root/'a/1.json')],dispatched[-2:])")
    s=B.once(s,"    if len(calls) != 1 or sha(operator) != before:\n        raise ValueError('Dispatched operator changed')",
             "    compare('Dispatched operator changed',dict(calls=1,sha256=before),dict(calls=len(calls),sha256=sha(operator)))")
    nf['a/5.py']=s.encode()
    # The pre-submission receipt check reads the size from the sealed writer, too.
    s=nf['a/9.py'].decode()
    s=B.once(s,"assert type(w['bytes']) is int and w['bytes']==4*1024**2\n",
             "with tarfile.open(p/'0.tgz') as archive:\n"
             "    sizes=__import__('re').findall(r'(?m)^WRITE_TEST_BYTES = (\\d+)$',archive.extractfile('orchard_h10/vendor/return_io.py').read().decode())\n"
             "assert len(sizes)==1,dict(check='Sealed write-test size',expected=1,found=sizes)\n"
             "assert type(w['bytes']) is int and w['bytes']==int(sizes[0]),dict(check='Write-test receipt differs',expected=int(sizes[0]),found=w['bytes'])\n")
    nf['a/9.py']=s.encode()
