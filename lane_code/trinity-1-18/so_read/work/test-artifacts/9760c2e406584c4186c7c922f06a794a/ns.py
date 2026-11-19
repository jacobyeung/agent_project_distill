import subprocess,sys
a=sys.argv[2:]
a[a.index("-C")+1]=sys.argv[1]
raise SystemExit(subprocess.call(a))
