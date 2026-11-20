from pathlib import Path
L=Path.cwd();p=L/'work/build24m4q/run_suite.py';s=p.read_text().replace('import sys,runpy,os,resource','import sys,runpy,os,resource,tempfile')
s=s.replace("sys.path[:0]=", "local_tmp=D/'tmp';local_tmp.mkdir(exist_ok=True);tempfile.tempdir=str(local_tmp)\nfor key in ('TMPDIR','XDG_CACHE_HOME','HF_HOME','TORCH_HOME','TORCHINDUCTOR_CACHE_DIR','TRITON_CACHE_DIR','MPLCONFIGDIR'):\n os.environ[key]=str(local_tmp/key.lower())\n Path(os.environ[key]).mkdir(exist_ok=True)\nsys.path[:0]=")
a=L/'attic/build24m4q/run_suite1.py';p.rename(a);p.write_text(s)
