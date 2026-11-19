from pathlib import Path
import sys,json,shutil
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";sys.path.insert(0,str(L/"work/build24"));import joblib as J
for name in ("checks","resolver_tests","resolver600_tests","resolver23_tests","launch_tests","refresh_tests","naming_tests","kit_tests","suites","guard_q_legacy","guard_q_new","guard_n_legacy","guard_n_new"):
 s=(L/"work/build24d"/(name+".py")).read_text().replace("work/build24d/", "work/build24e/").replace("work/build24d\x27","work/build24e\x27").replace("naming24d_","naming24e_")
 # Historical before evidence stays immutable.
 s=s.replace("attic/build24e/","attic/build24d/")
 if name=="kit_tests":
  s=s.replace("J.load(c[\x27r1_training\x27][\x27row_sources\x27][\x27path\x27])","J.load(paths[c[\x27r1_training\x27][\x27row_sources\x27][\x27sha256\x27]])")
  s=s.replace("self.assertEqual(c[\x27remove_files\x27],before[\x27remove_files\x27])","self.assertEqual([v[\x27sha256\x27] for v in c[\x27remove_files\x27]],[v[\x27sha256\x27] for v in before[\x27remove_files\x27]])")
  s=s.replace("self.assertEqual(c[\x27r1_training\x27][key],before[\x27r1_training\x27][key])","self.assertEqual(normalized(c[\x27r1_training\x27][key]),normalized(before[\x27r1_training\x27][key]))")
  s=s.replace("import joblib as J,environment21f as E","import joblib as J,environment21f as E\nsys.path.insert(0,str(L/\x27work/build24d\x27))\nfrom i import normalized")
  s=s.replace("J.load(D/(\x27UPLOADS_\x27+name+\x27.json\x27))","J.load(L/\x27work/build24e\x27/(\x27UPLOADS_\x27+name+\x27.json\x27))")
 (D/(name+".py")).write_text(s)
for name in ("guard_q","guard_n"):(D/name).mkdir(exist_ok=True)
s=(L/"work/build24d/uploads.py").read_text().replace("work/build24d","work/build24e").replace("build24d-","build24e-").replace("UPLOADS_24D","UPLOADS_24E")
s=s.replace("(\x27UPLOADS_24B.json\x27,\x27UPLOADS_24C.json\x27)","(\x27UPLOADS_24B.json\x27,\x27UPLOADS_24C.json\x27,\x27UPLOADS_24D.json\x27)")
s=s.replace("\x27UPLOADS_24C.json\x27)]","\x27UPLOADS_24C.json\x27,\x27UPLOADS_24D.json\x27)]")
s=s.replace("files += [dict(local_path=", "files += list(J.load(D/\x27CLOSURE.json\x27)[\x27added\x27].values())\n files += [dict(local_path=")
(D/"uploads.py").write_text(s)
