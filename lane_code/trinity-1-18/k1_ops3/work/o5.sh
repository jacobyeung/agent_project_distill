F=/project/community/jjyeung/cp4tk_fr
ls -d $F/venv/lib/python*/site-packages/opencv* $F/venv/lib/python*/site-packages/numpy-* 2>&1 | head
$F/venv/bin/python -c 'import cv2,numpy,sys;print(cv2.__version__,numpy.__version__,sys.version.split()[0])' 2>&1 | tail -1
