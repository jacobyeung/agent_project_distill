from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
for name in ('test_runner.py','compact_tmp.py','package.py','PACKAGE_TEST.sh','compare.py','coverage.py',
             'coverage_all.py','packet_runner.py','packet_final.py','PACKET_TEST.sh','seal.py','make_delivery.py'):
 p=L/'work/build6'/name
 if p.exists(): (B/name).write_text(p.read_text().replace('work/build6','work/build9').replace('build6-tree','build9-tree').replace('package6_','package9_'))
# New tests keep every proof in one fixed directory; the package runner supplies R2_PROOFS.
text=(B/'test_runner.py').read_text()
text=text.replace("if tree.name == 'tree_b01ce449' and not sys.argv[2:]:", "if False and tree.name == 'tree_b01ce449' and not sys.argv[2:]:")
(B/'test_runner.py').write_text(text)
