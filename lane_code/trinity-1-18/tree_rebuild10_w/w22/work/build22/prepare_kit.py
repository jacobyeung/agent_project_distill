from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build22'
s=(B/'kit.py').read_text().replace("B=L/'work/build21'","B=L/'work/build22'")
s=s.replace("sys.path[:0]=[str(T),str(B)]", "sys.path[:0]=[str(T),str(B),str(L/'work/build21')]")
s=s.replace("B/'proofs/receipts/", "L/'work/build21/proofs/receipts/")
s=s.replace("if sha256(path)!=h:raise ValueError('Static pin mismatch '+str(path))", """if sha256(path)!=h:
                        sealed=L/'work/build21/upload/u'/h
                        if sealed.is_file() and sha256(sealed)==h:path=sealed
                        else:missing[h]=dict(path=value['path'],sha256=h,reason='Existing local bytes differ; no matching sealed upload');path=None""")
s=s.replace("uploads[h]=dict(local_path=str(path),opaque_name='u/'+h,sha256=h,bytes=path.stat().st_size)\n                    if path.suffix=='.json'", "if path:uploads[h]=dict(local_path=str(path),opaque_name='u/'+h,sha256=h,bytes=path.stat().st_size)\n                    if path and path.suffix=='.json'")
s=s.replace("'15387646fd4ac47b43c107129db3109545a981c1bd45a3910ac038d8c5432022'))", "'15387646fd4ac47b43c107129db3109545a981c1bd45a3910ac038d8c5432022','e3c72962e3fd774c7e15fa1e4aeae1b6642264bf4f3cf54b9e350b8d7bfb9707','7b3d696d580386f9e8af3240fa142e2ad50eebb277a8718c97e2db497dcc925e'))")
(D/'kit.py').write_text(s)
(D/'joblib.py').write_bytes((B/'joblib.py').read_bytes())
(D/'upload.py').write_text((B/'upload.py').read_text().replace('work/build21/','work/build22/'))
# Keep the historical scanner for baseline-kit regressions; pin the new inventories in a separate copy.
(D/'naming22.py').write_bytes((B/'naming21.py').read_bytes())
