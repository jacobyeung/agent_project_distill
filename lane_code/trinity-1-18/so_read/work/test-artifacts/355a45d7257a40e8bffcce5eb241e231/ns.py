import subprocess,sys
a=sys.argv[2:]
if a[0]=="/bin/tar": a[a.index("-C")+1]=sys.argv[1]
else: a[-1]=sys.argv[1];a[0]=sys.executable
raise SystemExit(subprocess.call(a))
