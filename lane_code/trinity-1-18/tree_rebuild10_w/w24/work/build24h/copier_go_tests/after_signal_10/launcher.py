import subprocess,sys,os
raise SystemExit(subprocess.run([sys.executable,"-B",sys.argv[1],sys.argv[2]],env={**os.environ,"RANK":"0","LOCAL_RANK":"0"}).returncode)
