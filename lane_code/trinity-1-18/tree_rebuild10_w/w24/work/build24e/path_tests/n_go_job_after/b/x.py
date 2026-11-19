import pathlib,sys
p=pathlib.Path(sys.argv[2]);print('E88:'+str(p)+':'+str(p.is_file()));raise SystemExit(1)
