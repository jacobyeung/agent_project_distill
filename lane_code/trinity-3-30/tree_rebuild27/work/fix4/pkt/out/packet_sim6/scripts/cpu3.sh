set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/w28fix; SRC=$F/src; P1=/scratch/jjyeung/envs/p1cpu/bin/python
if [ ! -d $F/ovl_fla/einops ]; then $P1 -I -c "
import zipfile,hashlib
p='$SRC/einops-0.8.2-py3-none-any.whl'
assert hashlib.sha256(open(p,'rb').read()).hexdigest()=='54058201ac7087911181bfec4af6091bb59380360f069276601256a76af08193'
zipfile.ZipFile(p).extractall('$F/ovl_fla');print('einops wheel unpacked')"; fi
bash $SRC/cpu2.sh $1
